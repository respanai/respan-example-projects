"""Tests for respan_hook.py, on synthetic Claude Code transcripts.

Run: pip install pytest && pytest python/dev-tools/claude-code/tests
"""

import importlib
import json
import sys
import os
import threading
import time
from collections import Counter
from pathlib import Path

import pytest

HOOK_DIR = Path(__file__).resolve().parents[1]
SESSION = "11111111-2222-3333-4444-555555555555"
T0 = 1_760_000_000.0


def iso(t):
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(t)) + ".000Z"


# --------------------------------------------------------------------------- #
# Transcript builder
# --------------------------------------------------------------------------- #


class Transcript:
    def __init__(self, root: Path, session: str = SESSION):
        self.session = session
        self.dir = root / "projects" / "-tmp-project"
        self.dir.mkdir(parents=True, exist_ok=True)
        self.path = self.dir / f"{session}.jsonl"
        self.path.touch()
        self.t = T0
        self.n = 0

    def _uuid(self):
        self.n += 1
        return f"u-{self.n:08d}"

    def _write(self, path: Path, line: dict):
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(line) + "\n")

    def tick(self, seconds=1.0):
        self.t += seconds
        return self.t

    def line(self, kind, message, path=None, agent=None, **extra):
        line = {
            "type": kind,
            "uuid": self._uuid(),
            "sessionId": extra.pop("session_id", self.session),
            "timestamp": iso(self.tick()),
            "message": message,
        }
        if agent:
            line["isSidechain"] = True
            line["agentId"] = agent
        line.update(extra)
        self._write(path or self.path, line)
        return line

    def prompt(self, text, path=None, agent=None, **extra):
        return self.line("user", {"role": "user", "content": text}, path, agent, **extra)

    def reply(self, msg_id, text=None, tools=(), path=None, agent=None, usage=None, thinking=None, **extra):
        content = []
        if thinking:
            content.append({"type": "thinking", "thinking": thinking})
        if text:
            content.append({"type": "text", "text": text})
        for tool_id, name, tool_input in tools:
            content.append({"type": "tool_use", "id": tool_id, "name": name, "input": tool_input})
        usage = usage or {"input_tokens": 10, "output_tokens": 5, "cache_read_input_tokens": 100}
        return self.line(
            "assistant",
            {"id": msg_id, "role": "assistant", "model": "claude-opus-5-5", "content": content, "usage": usage},
            path, agent, requestId=f"req_{msg_id}", **extra,
        )

    def result(self, tool_id, output, path=None, agent=None, use_result=None, is_error=False):
        extra = {"toolUseResult": use_result} if use_result is not None else {}
        return self.line(
            "user",
            {"role": "user", "content": [{"type": "tool_result", "tool_use_id": tool_id, "content": output, "is_error": is_error}]},
            path, agent, **extra,
        )

    def subagent(self, agent_id, tool_use_id, depth=1, background=False):
        folder = self.dir / self.session / "subagents"
        folder.mkdir(parents=True, exist_ok=True)
        meta = {
            "agentType": "general-purpose",
            "description": f"agent {agent_id}",
            "toolUseId": tool_use_id,
            "spawnDepth": depth,
            "requestShape": "background" if background else "foreground",
        }
        (folder / f"agent-{agent_id}.meta.json").write_text(json.dumps(meta))
        path = folder / f"agent-{agent_id}.jsonl"
        path.touch()
        return path


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #


class Collector:
    def __init__(self):
        self.payloads = []
        self.fail = 0  # number of upcoming requests to fail with 503
        self.delay = 0.0
        self.lock = threading.Lock()

    def post(self, url, data, headers, timeout):
        assert url.endswith("/v2/traces")
        if self.delay:
            time.sleep(self.delay)
        with self.lock:
            if self.fail:
                self.fail -= 1
                return 503, "unavailable"
            self.payloads.append(json.loads(data))
        return 200, "ok"

    @property
    def all_spans(self):
        """Every span as sent (open containers are sent twice: at first sight and at close)."""
        out = []
        for payload in self.payloads:
            for resource in payload["resourceSpans"]:
                for scope in resource["scopeSpans"]:
                    out.extend(scope["spans"])
        return out

    @property
    def spans(self):
        """One span per span id, the last one sent (what span-id dedupe keeps)."""
        latest = {}
        for span in self.all_spans:
            latest.pop(span["spanId"], None)
            latest[span["spanId"]] = span
        return list(latest.values())


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("CC_RESPAN_STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setenv("TRACE_TO_RESPAN", "true")
    monkeypatch.setenv("RESPAN_API_KEY", "test-key")
    monkeypatch.setenv("RESPAN_CUSTOMER_ID", "cust-1")
    monkeypatch.setenv("RESPAN_METADATA", json.dumps({"team": "core"}))
    monkeypatch.syspath_prepend(str(HOOK_DIR))
    sys.modules.pop("respan_hook", None)
    hook = importlib.import_module("respan_hook")
    hook.SEND_ATTEMPTS = 1
    collector = Collector()
    monkeypatch.setattr(hook, "http_post", collector.post)
    monkeypatch.setattr(hook.time, "sleep", lambda s: None)
    return hook, collector, Transcript(tmp_path)


def fire(hook, transcript, event="PostToolUse", agent_id=None, at=None):
    payload = {"hook_event_name": event, "session_id": transcript.session, "transcript_path": str(transcript.path)}
    if agent_id:
        payload["agent_id"] = agent_id
    hook.append_event(payload)
    if at is not None:
        # Rewrite the timestamp of the event just queued (Stop ordering tests).
        lines = hook.EVENTS_FILE.read_text().splitlines()
        last = json.loads(lines[-1])
        last["at"] = at
        lines[-1] = json.dumps(last)
        hook.EVENTS_FILE.write_text("\n".join(lines) + "\n")
    return hook.run_worker("test-key", "https://example.test/api")


def attrs(span):
    out = {}
    for a in span["attributes"]:
        value = a["value"]
        out[a["key"]] = next(iter(value.values()))
    return out


def by_id(spans):
    return {s["spanId"]: s for s in spans}


def chain_to_root(span, index):
    chain = [span]
    while chain[-1].get("parentSpanId"):
        parent = index.get(chain[-1]["parentSpanId"])
        assert parent is not None, f"parent of {chain[-1]['name']} was never exported"
        assert parent["traceId"] == span["traceId"], "parent is in another trace"
        chain.append(parent)
    return chain


ALLOWED_CLAUDE_CODE_METADATA = {
    "respan.metadata.claude_code.agent_id",
    "respan.metadata.claude_code.agent_type",
    "respan.metadata.claude_code.spawn_depth",
    "respan.metadata.claude_code.turn",
    "respan.metadata.claude_code.resumed_from_session",
}


def assert_plain_spans(spans):
    """No span links; only the agreed claude_code.* metadata."""
    for span in spans:
        assert "links" not in span
        extra = {k for k in attrs(span) if k.startswith("respan.metadata.claude_code.")} - ALLOWED_CLAUDE_CODE_METADATA
        assert not extra, extra


def one_turn_with_subagents(t: Transcript):
    """Turn 1 spawns A (foreground), B (foreground, spawns C at depth 2) and D
    (background, finishes during turn 2)."""
    t.prompt("Investigate the bug")
    t.reply("m1", "Spawning agents", tools=[
        ("toolu_A", "Agent", {"description": "A", "prompt": "do A"}),
        ("toolu_B", "Agent", {"description": "B", "prompt": "do B"}),
        ("toolu_D", "Agent", {"description": "D", "prompt": "do D", "run_in_background": True}),
    ])
    a = t.subagent("aaa", "toolu_A")
    b = t.subagent("bbb", "toolu_B")
    d = t.subagent("ddd", "toolu_D", background=True)
    t.prompt("do A", path=a, agent="aaa")
    t.reply("ma1", tools=[("toolu_a_read", "Read", {"file_path": "/x.py"})], path=a, agent="aaa")
    t.result("toolu_a_read", "file body", path=a, agent="aaa")
    t.reply("ma2", "A done", path=a, agent="aaa")
    t.prompt("do B", path=b, agent="bbb")
    t.reply("mb1", tools=[("toolu_C", "Agent", {"description": "C", "prompt": "do C"})], path=b, agent="bbb")
    c = t.subagent("ccc", "toolu_C", depth=2)
    t.prompt("do C", path=c, agent="ccc")
    t.reply("mc1", tools=[("toolu_c_bash", "Bash", {"command": "ls"})], path=c, agent="ccc")
    t.result("toolu_c_bash", "a b c", path=c, agent="ccc")
    t.reply("mc2", "C done", path=c, agent="ccc")
    t.result("toolu_C", "C result", path=b, agent="bbb", use_result={"agentId": "ccc", "status": "completed"})
    t.reply("mb2", "B done", path=b, agent="bbb")
    t.prompt("do D", path=d, agent="ddd")
    t.result("toolu_A", "A result", use_result={"agentId": "aaa", "status": "completed"})
    t.result("toolu_B", "B result", use_result={"agentId": "bbb", "status": "completed"})
    t.result("toolu_D", "launched", use_result={"agentId": "ddd", "status": "async_launched"})
    t.reply("m2", "Waiting on D")
    return a, b, c, d


# --------------------------------------------------------------------------- #
# Tests
# --------------------------------------------------------------------------- #


def test_plain_turn_exports_root_llm_tool_and_ids(env):
    hook, collector, t = env
    t.prompt("Fix the typo")
    t.reply("m1", "Reading", tools=[("toolu_1", "Read", {"file_path": "/a.py"})], thinking="hmm")
    t.result("toolu_1", "content")
    t.reply("m2", "Fixed it")
    fire(hook, t, "Stop")

    spans = collector.spans
    names = sorted(s["name"].split(":")[0].split(" (")[0] for s in spans)
    assert names == ["Tool", "Turn 1", "claude.chat", "claude.chat"]
    first_llm = next(s for s in spans if attrs(s).get("gen_ai.completion.0.reasoning_content") == "hmm")
    assert attrs(first_llm)["gen_ai.completion.0.content"] == "Reading"
    root = next(s for s in spans if s["name"].startswith("Turn 1"))
    assert "parentSpanId" not in root
    assert attrs(root)["respan.metadata.claude_code.turn"] == "1"
    assert_plain_spans(spans)
    assert len({s["traceId"] for s in spans}) == 1
    index = by_id(spans)
    for span in spans:
        a = attrs(span)
        assert a["respan.threads.thread_identifier"] == f"claudecode_{SESSION}"
        assert a["respan.sessions.session_identifier"] == f"claudecode_{SESSION}"
        assert a["respan.customer_params.customer_identifier"] == "cust-1"
        assert a["respan.metadata.team"] == "core"
        assert chain_to_root(span, index)[-1] is root
    llm = next(s for s in spans if s["name"].startswith("claude.chat"))
    llm_attrs = attrs(llm)
    assert llm_attrs["gen_ai.request.model"] == "claude-opus-5-5"
    assert llm_attrs["gen_ai.usage.prompt_tokens"] == "10"
    assert llm_attrs["gen_ai.usage.cache_read_input_tokens"] == "100"


def test_subagents_nest_under_their_agent_tool_span_at_any_depth(env):
    hook, collector, t = env
    a, b, c, d = one_turn_with_subagents(t)
    fire(hook, t, "SubagentStop", agent_id="aaa")
    fire(hook, t, "SubagentStop", agent_id="ccc")
    fire(hook, t, "SubagentStop", agent_id="bbb")
    fire(hook, t, "Stop")

    spans = collector.spans
    index = by_id(spans)
    turn1 = next(s for s in spans if s["name"].startswith("Turn 1"))
    assert {s["traceId"] for s in spans} == {turn1["traceId"]}

    subagents = {attrs(s)["respan.metadata.claude_code.agent_id"]: s for s in spans if s["name"].startswith("Sub-agent")}
    assert set(subagents) == {"aaa", "bbb", "ccc"}  # ddd still running: its root comes at close
    assert_sent_once(collector)
    tool_spans = {
        tool_id: index[hook.span_id_for(SESSION, f"tool:{tool_id}")]
        for tool_id in ("toolu_A", "toolu_B", "toolu_C", "toolu_c_bash")
    }
    assert subagents["aaa"]["parentSpanId"] == tool_spans["toolu_A"]["spanId"]
    assert subagents["bbb"]["parentSpanId"] == tool_spans["toolu_B"]["spanId"]
    assert subagents["ccc"]["parentSpanId"] == tool_spans["toolu_C"]["spanId"]
    assert tool_spans["toolu_C"]["parentSpanId"] != turn1["spanId"]  # inside B, not the turn

    deepest = tool_spans["toolu_c_bash"]
    chain = chain_to_root(deepest, index)
    assert [s["name"].split(":")[0] for s in chain] == ["Tool", "Sub-agent", "Tool", "Sub-agent", "Tool", "Turn 1"]
    assert attrs(subagents["ccc"])["respan.metadata.claude_code.spawn_depth"] == "2"
    assert attrs(subagents["aaa"])["respan.metadata.claude_code.agent_type"] == "general-purpose"
    assert_plain_spans(spans)
    # Sub-agent model calls are their own LLM spans with their own usage.
    c_llm = [s for s in spans if s["name"].startswith("claude.chat") and s["parentSpanId"] == subagents["ccc"]["spanId"]]
    assert len(c_llm) == 2 and all(attrs(s)["gen_ai.usage.completion_tokens"] == "5" for s in c_llm)


def test_background_subagent_finishing_in_a_later_turn_stays_in_the_spawning_trace(env):
    hook, collector, t = env
    a, b, c, d = one_turn_with_subagents(t)
    fire(hook, t, "Stop")
    t.prompt("Anything from D?")
    t.reply("ms2", "Still waiting")
    t.reply("md1", "D working", path=d, agent="ddd")
    t.reply("md2", "D done", path=d, agent="ddd")
    fire(hook, t, "SubagentStop", agent_id="ddd")
    fire(hook, t, "Stop")

    spans = collector.spans
    turns = sorted((s for s in spans if s["name"].startswith("Turn")), key=lambda s: s["name"])
    assert [s["name"][:6] for s in turns] == ["Turn 1", "Turn 2"]
    d_root = next(s for s in spans if s["name"].startswith("Sub-agent") and attrs(s)["respan.metadata.claude_code.agent_id"] == "ddd")
    assert d_root["traceId"] == turns[0]["traceId"] != turns[1]["traceId"]
    assert attrs(turns[1])["respan.metadata.claude_code.turn"] == "2"
    sessions = {attrs(s)["respan.sessions.session_identifier"] for s in spans}
    assert sessions == {f"claudecode_{SESSION}"}  # both turns group into one session
    assert_plain_spans(spans)


def test_sidechain_lines_in_the_main_file_are_not_turns(env):
    hook, collector, t = env
    t.prompt("Hello")
    t.prompt("sub-agent prompt written inline by an old Claude Code", agent="old1")
    t.reply("ms", "sub-agent reply", agent="old1")
    t.reply("m1", "Hi")
    fire(hook, t, "Stop")
    turns = [s for s in collector.spans if s["name"].startswith("Turn")]
    assert len(turns) == 1 and turns[0]["name"].startswith("Turn 1: Hello")


def test_long_session_is_read_incrementally_never_from_the_start(env):
    hook, collector, t = env
    total_read = 0
    for turn in range(2000):
        t.prompt(f"step {turn}")
        t.reply(f"m{turn}", "ok", tools=[(f"toolu_{turn}", "Bash", {"command": "true"})])
        t.result(f"toolu_{turn}", "done")
        t.reply(f"n{turn}", "done")
        if turn % 100 == 99:
            total_read += fire(hook, t, "Stop")
    size = t.path.stat().st_size
    assert total_read == size  # every byte read exactly once across 20 runs
    turns = [s for s in collector.spans if s["name"].startswith("Turn")]
    assert len(turns) == 2000
    assert_sent_once(collector)
    assert {attrs(s)["respan.threads.thread_identifier"] for s in turns} == {f"claudecode_{SESSION}"}
    assert sorted(int(attrs(s)["respan.metadata.claude_code.turn"]) for s in turns) == list(range(1, 2001))


def test_send_failure_keeps_the_cursor_and_resends_identical_ids(env):
    hook, collector, t = env
    t.prompt("Hello")
    t.reply("m1", "Hi", tools=[("toolu_1", "Bash", {"command": "ls"})])
    t.result("toolu_1", "x")
    collector.fail = 10
    fire(hook, t, "PostToolUse")
    assert collector.spans == []
    state = json.loads(hook.STATE_FILE.read_text()) if hook.STATE_FILE.exists() else {"sessions": {}}
    offsets = [f["offset"] for f in state["sessions"].get(SESSION, {}).get("files", {}).values()]
    assert all(o == 0 for o in offsets)
    collector.fail = 0
    t.reply("m2", "Bye")
    fire(hook, t, "Stop")
    names = sorted(s["name"].split(":")[0].split(" (")[0] for s in collector.spans)
    assert names == ["Tool", "Turn 1", "claude.chat", "claude.chat"]
    first_ids = {s["spanId"] for s in collector.spans}
    # Deleting only the state file does not re-send: the seen-lines file remembers.
    hook.STATE_FILE.unlink()
    collector.payloads.clear()
    fire(hook, t, "Stop")
    assert collector.spans == []
    # A full reset (state + seen lines) re-exports with the same ids.
    hook.STATE_FILE.unlink()
    hook.SeenLines.path_for(SESSION).unlink()
    collector.payloads.clear()
    fire(hook, t, "Stop")
    assert {s["spanId"] for s in collector.spans} == first_ids


def test_concurrent_invocations_never_double_export(env):
    hook, collector, t = env
    t.prompt("Hello")
    t.reply("m1", "Hi", tools=[("toolu_1", "Bash", {"command": "ls"})])
    t.result("toolu_1", "x")
    collector.delay = 0.3
    first = threading.Thread(target=fire, args=(hook, t, "PostToolUse"))
    first.start()
    time.sleep(0.1)
    # While the first worker holds the lock, more events arrive.
    t.reply("m2", "Bye")
    fire(hook, t, "Stop")
    fire(hook, t, "PostToolUse")
    first.join()
    ids = [s["spanId"] for s in collector.spans]
    assert len(ids) == len(set(ids))
    names = sorted(s["name"].split(":")[0].split(" (")[0] for s in collector.spans)
    assert names == ["Tool", "Turn 1", "claude.chat", "claude.chat"]


def test_resumed_session_records_the_session_it_resumed_and_skips_copied_history(env, tmp_path):
    hook, collector, t = env
    t.prompt("First session")
    t.reply("m1", "Answer")
    fire(hook, t, "Stop")
    first_root = next(s for s in collector.spans if s["name"].startswith("Turn"))

    resumed = Transcript(tmp_path, session="99999999-2222-3333-4444-555555555555")
    resumed.t = t.t
    # --resume copies the earlier conversation (with its old sessionId) first.
    resumed.prompt("First session", session_id=SESSION)
    resumed.reply("m1", "Answer", session_id=SESSION)
    resumed.prompt("Continue please")
    resumed.reply("m9", "Continuing")
    collector.payloads.clear()
    fire(hook, resumed, "Stop")
    spans = collector.spans
    turns = [s for s in spans if s["name"].startswith("Turn")]
    assert len(turns) == 1 and turns[0]["name"].startswith("Turn 1: Continue please")
    assert attrs(turns[0])["respan.metadata.claude_code.resumed_from_session"] == SESSION
    assert turns[0]["traceId"] != first_root["traceId"]
    assert_plain_spans(spans)


def test_a_turn_ending_on_a_tool_call_is_still_exported(env):
    hook, collector, t = env
    t.prompt("Run the tests")
    t.reply("m1", tools=[("toolu_1", "Bash", {"command": "pytest"})])
    fire(hook, t, "SessionEnd")
    names = sorted(s["name"].split(":")[0].split(" (")[0] for s in collector.spans)
    assert "Turn 1" in names and "claude.chat" in names


def test_stop_does_not_close_a_turn_a_newer_prompt_opened(env):
    hook, collector, t = env
    t.prompt("One")
    t.reply("m1", "1")
    stop_time = t.t
    t.prompt("Two")
    t.reply("m2", "partial")
    fire(hook, t, "Stop", at=stop_time)
    closed = lambda: [s["name"][:6] for s in collector.spans if s["name"].startswith("Turn") and s["endTimeUnixNano"] != s["startTimeUnixNano"]]
    assert closed() == ["Turn 1"]  # Turn 2 is only at its first sight
    t.reply("m3", "rest of two")
    fire(hook, t, "Stop")
    assert sorted(closed()) == ["Turn 1", "Turn 2"]


def test_hook_entrypoint_returns_fast_and_queues_the_event(env, monkeypatch):
    hook, collector, t = env
    started = []
    monkeypatch.setattr(hook.subprocess, "Popen", lambda *a, **k: started.append(a))
    monkeypatch.setattr(hook, "read_payload", lambda: {"hook_event_name": "Stop", "session_id": SESSION, "transcript_path": str(t.path)})
    monkeypatch.setattr(sys, "argv", ["respan_hook.py"])
    t0 = time.monotonic()
    hook.main()
    assert time.monotonic() - t0 < 0.5
    assert started and hook.EVENTS_FILE.exists()


def test_finished_subagents_close_without_subagentstop(env):
    """Backfill: sub-agents that finished before the hook ran never get a SubagentStop."""
    hook, collector, t = env
    one_turn_with_subagents(t)
    fire(hook, t, "PostToolUse")  # no SubagentStop, no Stop
    sends = Counter(attrs(s)["respan.metadata.claude_code.agent_id"] for s in collector.all_spans if s["name"].startswith("Sub-agent"))
    assert sends == Counter({"aaa": 1, "bbb": 1, "ccc": 1})  # foreground agents whose results came back; ddd still running
    roots = set(sends)
    index = by_id(collector.spans)
    for span in collector.spans:
        if span.get("parentSpanId"):
            parent = index.get(span["parentSpanId"])
            # every exported sub-agent child has its sub-agent root exported too
            if attrs(span).get("respan.metadata.claude_code.agent_id") in roots:
                assert parent is not None


def test_one_chat_span_per_api_response_from_the_real_line_shape(env):
    """Claude Code 2.1.30x writes one API response as several assistant lines (one per
    content block) sharing message.id / requestId and repeating the same usage, plus
    api-request (send time) and api-request-blob records that are not conversation.
    The api-request for the NEXT call can be written before this response's lines."""
    hook, collector, t = env
    t.prompt("Lint the file")
    first_request = t.line("api-request", None, id="req-ref-1", requestDigest="x")
    sent_at = t.t
    t.tick(4)
    usage = {"input_tokens": 2, "output_tokens": 635, "cache_read_input_tokens": 490290}
    for kind in ("api-request-blob", "api-request-blob"):
        with open(t.path, "a") as f:
            f.write(json.dumps({"type": kind, "hash": "h", "message": {"content": [{"type": "text", "text": "REQUEST BLOB"}]}}) + "\n")
    # The next request's record lands BEFORE this response's lines, with a later time.
    next_request_ts = t.t + 3
    with open(t.path, "a") as f:
        f.write(json.dumps({"type": "api-request", "id": "req-ref-2", "timestamp": iso(next_request_ts)}) + "\n")
    for content in (
        [{"type": "thinking", "thinking": ""}],
        [{"type": "thinking", "thinking": "plan the fix"}],
        [{"type": "tool_use", "id": "toolu_x", "name": "Bash", "input": {"command": "ruff check"}}],
    ):
        t.line("assistant", {"id": "msg_1", "role": "assistant", "model": "claude-opus-5-5", "content": content, "usage": usage},
               requestId="req_1", requestRef="req-ref-1")
    t.result("toolu_x", "E731 ...")
    t.line("attachment", None)
    t.line("assistant", {"id": "msg_2", "role": "assistant", "model": "claude-opus-5-5",
                         "content": [{"type": "text", "text": "Fixed"}], "usage": {"input_tokens": 1, "output_tokens": 3}},
           requestId="req_2", requestRef="req-ref-2")
    fire(hook, t, "Stop")

    chats = [s for s in collector.spans if s["name"].startswith("claude.chat")]
    assert len(chats) == 2  # not one per line, nothing from api-request / blobs
    first = next(s for s in chats if attrs(s).get("gen_ai.usage.completion_tokens") == "635")
    a = attrs(first)
    assert a["gen_ai.usage.prompt_tokens"] == "2"  # usage counted once, not summed per line
    assert a["gen_ai.usage.cache_read_input_tokens"] == "490290"
    assert json.loads(a["gen_ai.completion.0.tool_calls"])[0]["function"]["name"] == "Bash"
    assert a["gen_ai.completion.0.content"]  # a tool-call-only response is not empty
    assert a["gen_ai.completion.0.reasoning_content"] == "plan the fix"
    start = int(first["startTimeUnixNano"]) / 1e9
    end = int(first["endTimeUnixNano"]) / 1e9
    assert abs(start - sent_at) < 0.01  # starts when its api-request was sent
    assert end - start > 3  # real latency, not 0
    second = next(s for s in chats if s is not first)
    assert abs(int(second["startTimeUnixNano"]) / 1e9 - next_request_ts) < 0.01
    assert all("REQUEST BLOB" not in json.dumps(s) for s in collector.spans)


def assert_sent_once(collector):
    ids = Counter(s["spanId"] for s in collector.all_spans)
    resent = [s["name"] for s in collector.all_spans if ids[s["spanId"]] > 1]
    assert not resent, resent


def test_every_span_is_sent_once_and_roots_arrive_when_they_close(env):
    """Mid-turn: a foreground sub-agent still working (its Agent call has no result yet)
    and a background one. Their spans go out as they happen; the containers (turn root,
    sub-agent roots, the Agent call) go out once, when they close. Until then the trace
    shows their children at the top level; they nest once the parent arrives."""
    hook, collector, t = env
    t.prompt("Big task")
    t.reply("m1", "Starting", tools=[
        ("toolu_F", "Agent", {"description": "F", "prompt": "fg"}),
        ("toolu_G", "Agent", {"description": "G", "prompt": "bg", "run_in_background": True}),
    ])
    f = t.subagent("fff", "toolu_F")
    g = t.subagent("ggg", "toolu_G", background=True)
    t.result("toolu_G", "launched", use_result={"agentId": "ggg", "status": "async_launched"})
    t.prompt("fg", path=f, agent="fff")
    t.reply("mf1", tools=[("toolu_f1", "Bash", {"command": "make"})], path=f, agent="fff")
    t.result("toolu_f1", "ok", path=f, agent="fff")
    t.prompt("bg", path=g, agent="ggg")
    t.reply("mg1", tools=[("toolu_g1", "Grep", {"pattern": "x"})], path=g, agent="ggg")
    t.result("toolu_g1", "hits", path=g, agent="ggg")
    fire(hook, t, "PostToolUse", agent_id="fff")
    names = {s["name"].split(":")[0] for s in collector.spans}
    assert "Turn 1" not in names and "Sub-agent" not in names  # still running
    # Finished tool calls are out already; a response's chat span goes out when the next
    # response starts (its tool calls may still be writing).
    assert {"Tool: Bash", "Tool: Grep"} <= {s["name"] for s in collector.spans}
    t.reply("mf2", "F done", path=f, agent="fff")
    t.result("toolu_F", "F result", use_result={"agentId": "fff", "status": "completed"})
    t.reply("mg2", "G done", path=g, agent="ggg")
    t.reply("m2", "All done")
    fire(hook, t, "SubagentStop", agent_id="ggg")
    fire(hook, t, "Stop")
    assert_sent_once(collector)
    index = by_id(collector.spans)
    for span in collector.spans:  # once everything closed, every parent is there
        if span.get("parentSpanId"):
            assert span["parentSpanId"] in index, span["name"]
    roots = {attrs(s)["respan.metadata.claude_code.agent_id"]: s for s in collector.spans if s["name"].startswith("Sub-agent")}
    for agent_id in ("fff", "ggg"):
        assert int(roots[agent_id]["endTimeUnixNano"]) > int(roots[agent_id]["startTimeUnixNano"])
    agent_tool = index[hook.span_id_for(SESSION, "tool:toolu_F")]
    assert attrs(agent_tool)["traceloop.entity.output"] == "F result"


def test_a_subagent_continued_after_it_finished_gets_a_fresh_root(env):
    hook, collector, t = env
    t.prompt("Start")
    t.reply("m1", tools=[("toolu_K", "Agent", {"description": "K", "prompt": "k"})])
    k = t.subagent("kkk", "toolu_K")
    t.prompt("k", path=k, agent="kkk")
    t.reply("mk1", "first run done", path=k, agent="kkk")
    t.result("toolu_K", "K result", use_result={"agentId": "kkk", "status": "completed"})
    t.reply("m2", "ok")
    fire(hook, t, "SubagentStop", agent_id="kkk")
    fire(hook, t, "Stop")
    t.prompt("Ask K again")
    t.reply("m3", tools=[("toolu_send", "SendMessage", {"to": "kkk", "message": "more"})])
    t.prompt("more", path=k, agent="kkk")  # the continuation, in the same sub-agent file
    t.tick(30)
    t.reply("mk2", "second run done", path=k, agent="kkk")
    t.result("toolu_send", "sent")
    t.reply("m4", "done")
    fire(hook, t, "SubagentStop", agent_id="kkk")
    fire(hook, t, "Stop")
    assert_sent_once(collector)
    runs = sorted((s for s in collector.spans if s["name"].startswith("Sub-agent")), key=lambda s: s["startTimeUnixNano"])
    assert [s["name"] for s in runs] == ["Sub-agent: agent kkk", "Sub-agent: agent kkk (continued 1)"]
    first, second = runs
    assert first["parentSpanId"] == second["parentSpanId"] == hook.span_id_for(SESSION, "tool:toolu_K")
    assert int(first["endTimeUnixNano"]) < int(second["startTimeUnixNano"])  # the first root is not stretched
    second_llm = next(s for s in collector.spans if attrs(s).get("gen_ai.completion.0.content") == "second run done")
    assert second_llm["parentSpanId"] == second["spanId"]


def test_missed_subagentstop_closes_on_a_later_run_of_another_session(env, tmp_path):
    """A background sub-agent outlives its session's last hook event and never gets a
    SubagentStop: once its file is quiet, any later hook run (any session) closes it."""
    hook, collector, t = env
    t.prompt("Kick off")
    t.reply("m1", tools=[("toolu_Z", "Agent", {"description": "Z", "prompt": "z", "run_in_background": True})])
    z = t.subagent("zzz", "toolu_Z", background=True)
    t.result("toolu_Z", "launched", use_result={"agentId": "zzz", "status": "async_launched"})
    t.reply("m2", "Launched")
    t.prompt("z", path=z, agent="zzz")
    t.reply("mz1", "Z finished its work", path=z, agent="zzz")
    fire(hook, t, "Stop")
    root_sends = lambda: [s for s in collector.all_spans if s["name"].startswith("Sub-agent")]
    assert len(root_sends()) == 0  # still open: its root goes out when it closes
    old = time.time() - 3600
    os.utime(z, (old, old))
    other = Transcript(tmp_path / "other", session="77777777-2222-3333-4444-555555555555")
    other.prompt("Unrelated session")
    other.reply("o1", "ok")
    fire(hook, other, "Stop")
    assert len(root_sends()) == 1  # closed on the other session's run
    assert_sent_once(collector)
    final = root_sends()[-1]
    assert int(final["endTimeUnixNano"]) > int(final["startTimeUnixNano"])


def test_history_reappended_to_the_transcript_is_not_sent_again(env):
    """Claude Code can re-append a session's whole history (same uuids and timestamps)
    to its transcript, e.g. after a bridge/restore. Nothing is sent twice and the new
    turn after it is turn 3, not turn 5."""
    hook, collector, t = env
    t.prompt("One")
    t.reply("m1", "1", tools=[("toolu_1", "Bash", {"command": "ls"})])
    t.result("toolu_1", "x")
    t.reply("m2", "done 1")
    t.prompt("Two")
    t.reply("m3", "2")
    fire(hook, t, "Stop")
    history = t.path.read_text()
    with open(t.path, "a") as f:
        f.write(json.dumps({"type": "bridge-session", "sessionId": SESSION}) + "\n")
        f.write(history)  # the same lines again
    t.prompt("Three")
    t.reply("m4", "3")
    fire(hook, t, "Stop")
    assert_sent_once(collector)
    turns = sorted(s["name"].split(":")[0] for s in collector.spans if s["name"].startswith("Turn"))
    assert turns == ["Turn 1", "Turn 2", "Turn 3"]
    three = next(s for s in collector.spans if s["name"].startswith("Turn 3"))
    assert three["name"] == "Turn 3: Three"


def test_tool_results_between_lines_of_one_response_do_not_split_it(env):
    """A response with two tool calls: the first tool runs (and its result is written)
    before the response's second tool_use line. Still one chat span, sent once."""
    hook, collector, t = env
    t.prompt("Edit and test")
    usage = {"input_tokens": 3, "output_tokens": 40}
    t.line("assistant", {"id": "msg_x", "role": "assistant", "model": "claude-opus-5-5", "usage": usage,
                         "content": [{"type": "tool_use", "id": "toolu_e", "name": "Edit", "input": {"file_path": "/a"}}]},
           requestId="req_x")
    t.result("toolu_e", "edited")
    t.line("assistant", {"id": "msg_x", "role": "assistant", "model": "claude-opus-5-5", "usage": usage,
                         "content": [{"type": "tool_use", "id": "toolu_b", "name": "Bash", "input": {"command": "pytest"}}]},
           requestId="req_x")
    t.result("toolu_b", "passed")
    t.reply("msg_y", "All green")
    fire(hook, t, "Stop")
    assert_sent_once(collector)
    chats = [s for s in collector.spans if s["name"].startswith("claude.chat")]
    assert len(chats) == 2
    first = next(s for s in chats if "tool_calls" in json.dumps(s))
    calls = json.loads(attrs(first)["gen_ai.completion.0.tool_calls"])
    assert [c["function"]["name"] for c in calls] == ["Edit", "Bash"]


def test_a_fork_subagent_copying_its_parents_messages_sends_nothing_twice(env):
    """A fork sub-agent's transcript starts with a copy of its parent's conversation:
    new line uuids, but the same message ids and tool_use ids."""
    hook, collector, t = env
    t.prompt("Fork it")
    spawn = t.line("assistant", {"id": "msg_p", "role": "assistant", "model": "claude-opus-5-5",
                                 "usage": {"input_tokens": 1, "output_tokens": 2},
                                 "content": [{"type": "tool_use", "id": "toolu_fk", "name": "Agent", "input": {"prompt": "go"}}]},
                   requestId="req_p")
    fork = t.subagent("fk1", "toolu_fk")
    t.result("toolu_fk", "Fork started", use_result={"agentId": "fk1", "status": "async_launched"})
    t.reply("m2", "Forked")
    # The fork's file: the parent's prompt and spawning response copied (new uuids), then its own work.
    t.prompt("Fork it", path=fork, agent="fk1")
    t.line("assistant", spawn["message"], path=fork, agent="fk1", requestId="req_p")
    t.result("toolu_fk", "Fork started", path=fork, agent="fk1")
    t.prompt("go", path=fork, agent="fk1")
    t.reply("mf", "fork done", path=fork, agent="fk1")
    fire(hook, t, "SubagentStop", agent_id="fk1")
    fire(hook, t, "Stop")
    assert_sent_once(collector)
    assert any(attrs(s).get("gen_ai.completion.0.content") == "fork done" for s in collector.spans)
