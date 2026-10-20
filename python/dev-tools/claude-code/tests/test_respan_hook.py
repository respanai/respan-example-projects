"""Tests for respan_hook.py, on synthetic Claude Code transcripts.

Run: pip install pytest requests && pytest python/dev-tools/claude-code/tests
"""

import importlib
import json
import sys
import threading
import time
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


class FakeResponse:
    def __init__(self, status):
        self.status_code = status
        self.text = "ok" if status < 300 else "error"


class Collector:
    def __init__(self):
        self.payloads = []
        self.fail = 0  # number of upcoming requests to fail with 503
        self.delay = 0.0
        self.lock = threading.Lock()

    def post(self, url, data=None, headers=None, timeout=None):
        assert url.endswith("/v2/traces")
        if self.delay:
            time.sleep(self.delay)
        with self.lock:
            if self.fail:
                self.fail -= 1
                return FakeResponse(503)
            self.payloads.append(json.loads(data))
        return FakeResponse(200)

    @property
    def spans(self):
        out = []
        for payload in self.payloads:
            for resource in payload["resourceSpans"]:
                for scope in resource["scopeSpans"]:
                    out.extend(scope["spans"])
        return out


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
    monkeypatch.setattr(hook.requests, "post", collector.post)
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


def link_types(span):
    return [attrs({"attributes": link["attributes"]})["respan.link.type"] for link in span.get("links", [])]


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
    assert names == ["Thinking", "Tool", "Turn 1", "claude.chat", "claude.chat"]
    root = next(s for s in spans if s["name"].startswith("Turn 1"))
    assert "parentSpanId" not in root
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
    assert set(subagents) == {"aaa", "bbb", "ccc"}  # ddd still running
    tool_spans = {attrs(s)["respan.metadata.claude_code.tool_use_id"]: s for s in spans if s["name"].startswith("Tool:")}
    assert subagents["aaa"]["parentSpanId"] == tool_spans["toolu_A"]["spanId"]
    assert subagents["bbb"]["parentSpanId"] == tool_spans["toolu_B"]["spanId"]
    assert subagents["ccc"]["parentSpanId"] == tool_spans["toolu_C"]["spanId"]
    assert tool_spans["toolu_C"]["parentSpanId"] != turn1["spanId"]  # inside B, not the turn

    deepest = tool_spans["toolu_c_bash"]
    chain = chain_to_root(deepest, index)
    assert [s["name"].split(":")[0] for s in chain] == ["Tool", "Sub-agent", "Tool", "Sub-agent", "Tool", "Turn 1"]
    for agent_id, span in subagents.items():
        assert link_types(span) == ["spawned_by"]
        assert span["links"][0]["spanId"] == span["parentSpanId"]
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
    assert attrs(d_root)["respan.metadata.claude_code.background"] is True
    assert link_types(turns[1]) == ["previous_turn"]
    assert turns[1]["links"][0]["traceId"] == turns[0]["traceId"]
    assert turns[1]["links"][0]["spanId"] == turns[0]["spanId"]


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
    assert len({s["spanId"] for s in collector.spans}) == len(collector.spans)  # no re-sends
    # Every turn after the first links to its predecessor.
    linked = sum(1 for s in turns if link_types(s) == ["previous_turn"])
    assert linked == 1999


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
    # A full replay from scratch produces the same ids (idempotent re-export).
    hook.STATE_FILE.unlink()
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


def test_resumed_session_links_to_the_session_it_resumed_and_skips_copied_history(env, tmp_path):
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
    assert link_types(turns[0]) == ["resumed_from"]
    assert turns[0]["links"][0]["spanId"] == first_root["spanId"]
    assert turns[0]["links"][0]["traceId"] == first_root["traceId"]


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
    roots = [s["name"][:6] for s in collector.spans if s["name"].startswith("Turn")]
    assert roots == ["Turn 1"]
    t.reply("m3", "rest of two")
    fire(hook, t, "Stop")
    roots = [s["name"][:6] for s in collector.spans if s["name"].startswith("Turn")]
    assert roots == ["Turn 1", "Turn 2"]


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
    roots = {attrs(s)["respan.metadata.claude_code.agent_id"] for s in collector.spans if s["name"].startswith("Sub-agent")}
    assert roots == {"aaa", "bbb", "ccc"}  # foreground agents whose results came back; ddd still running
    index = by_id(collector.spans)
    for span in collector.spans:
        if span.get("parentSpanId"):
            parent = index.get(span["parentSpanId"])
            # every exported sub-agent child has its sub-agent root exported too
            if attrs(span).get("respan.metadata.claude_code.agent_id") in roots:
                assert parent is not None
