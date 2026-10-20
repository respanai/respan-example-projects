#!/usr/bin/env python3
"""
Respan hook for Claude Code.

Sends Claude Code sessions to Respan as traces, including every sub-agent, as the
session runs. Long sessions (hours, many sub-agents) are captured in full:

- One trace per user turn of the main session, all grouped by one session/thread id
  (``claudecode_<session id>``), so a 10-hour session never keeps one trace open.
- Sub-agents (the Agent / Task tool) are nested in the trace of the turn that spawned
  them: ``claude_code.subagent`` is a child of the Agent tool span, and its model calls
  and tool calls are its children. Sub-agents spawned by sub-agents nest the same way,
  at any depth. Background sub-agents that finish after the turn still land there.
- Spans are exported incrementally (on PostToolUse, SubagentStop and Stop), from a
  byte offset per transcript file: a file is never re-read from the start.
- Span and trace ids are derived from the transcript (sha256). A file's offset only
  moves after Respan accepted the spans.

The hook itself returns immediately; the work runs in a detached worker.

Usage:
    Copy this file to ~/.claude/hooks/respan_hook.py and register it for the
    Stop, SubagentStop and PostToolUse hooks in ~/.claude/settings.json
    (see .claude/settings.json.example). Python 3.8+; uses ``requests`` when
    installed and the standard library otherwise.

Environment:
    TRACE_TO_RESPAN=true      enable tracing
    RESPAN_API_KEY            your Respan API key
    RESPAN_BASE_URL           default https://api.respan.ai/api
    RESPAN_CUSTOMER_ID        customer identifier on every span (default "claude-code")
    RESPAN_METADATA           JSON object added to every span's metadata
    CC_RESPAN_MAX_CHARS       max characters kept per input/output field (default 4000)
    CC_RESPAN_DEBUG=true      verbose log in ~/.claude/state/respan_hook.log
"""

import contextlib
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

import ssl
import urllib.error
import urllib.request

try:  # optional: used when present (it carries its own CA bundle)
    import requests
except ImportError:
    requests = None  # type: ignore[assignment]

HOOK_VERSION = "2.3.3"

STATE_DIR = Path(os.environ.get("CC_RESPAN_STATE_DIR", str(Path.home() / ".claude" / "state")))
LOG_FILE = STATE_DIR / "respan_hook.log"
STATE_FILE = STATE_DIR / "respan_state_v2.json"
LOCK_FILE = STATE_DIR / "respan_hook_v2.lock"
DIRTY_FILE = STATE_DIR / "respan_hook_v2.dirty"
EVENTS_FILE = STATE_DIR / "respan_hook_v2.events"

DEBUG = (
    os.environ.get("CC_RESPAN_DEBUG", "").lower() == "true"
    or os.environ.get("RESPAN_HOOK_DEBUG", "").lower() in ("1", "true")
)
# The log is rotated once it passes this size (one previous file is kept).
LOG_MAX_BYTES = 5 * 1024 * 1024


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except (TypeError, ValueError):
        return default


MAX_CHARS = _int_env("CC_RESPAN_MAX_CHARS", 4000)
MAX_SPANS_PER_REQUEST = 500
MAX_PENDING_REQUESTS = 1000
MAX_BYTES_PER_REQUEST = 4 * 1024 * 1024
# Lines read per file per commit: the state is saved after each chunk is accepted.
MAX_CHUNK_BYTES = _int_env("CC_RESPAN_CHUNK_BYTES", 2 * 1024 * 1024)
SEND_ATTEMPTS = 3
SEND_TIMEOUT_SECONDS = 30
LOCK_STALE_SECONDS = 15 * 60
STATE_RETENTION_SECONDS = 30 * 24 * 3600
# A sub-agent whose file has not grown for this long is closed when the turn ends,
# or on any hook event after the longer timeout (sub-agents that finished before
# the hook was installed never get a SubagentStop).
SUBAGENT_IDLE_CLOSE_SECONDS = 120
SUBAGENT_STALE_CLOSE_SECONDS = 600

WORKFLOW_NAME = "claude-code"
AGENT_TOOL_NAMES = ("Agent", "Task")

# Respan span attributes (respan_sdk.constants.span_attributes); this file is
# standalone, so the strings are mirrored here.
ATTR_THREAD = "respan.threads.thread_identifier"
ATTR_SESSION = "respan.sessions.session_identifier"
ATTR_CUSTOMER = "respan.customer_params.customer_identifier"
ATTR_LOG_TYPE = "respan.entity.log_type"
ATTR_METADATA_PREFIX = "respan.metadata."

OTEL_STATUS_OK = 1
OTEL_STATUS_ERROR = 2
OTEL_KIND_INTERNAL = 1
OTEL_KIND_CLIENT = 3


# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #


def log(level: str, message: str) -> None:
    """Append to the hook's own log (rotated, size-capped). Never raises."""
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        with contextlib.suppress(OSError):
            if LOG_FILE.stat().st_size > LOG_MAX_BYTES:
                os.replace(str(LOG_FILE), str(LOG_FILE) + ".1")
        stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"{stamp} [{level}] pid={os.getpid()} {message[:2000]}\n")
    except Exception:
        pass


def debug(message: str) -> None:
    if DEBUG:
        log("DEBUG", message)


# --------------------------------------------------------------------------- #
# Ids, time, text
# --------------------------------------------------------------------------- #


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def trace_id_for(session_id: str, turn_key: str) -> str:
    return _sha(f"cc:trace:{session_id}:{turn_key}")[:32]


def span_id_for(session_id: str, key: str) -> str:
    return _sha(f"cc:span:{session_id}:{key}")[:16]


def thread_id_for(session_id: str) -> str:
    return f"claudecode_{session_id}"


def parse_ts(value: Any) -> Optional[float]:
    """ISO timestamp -> epoch seconds."""
    if not isinstance(value, str) or not value:
        return None
    try:
        text = value[:-1] + "+00:00" if value.endswith("Z") else value
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.timestamp()
    except ValueError:
        return None


def to_nanos(seconds: Optional[float]) -> str:
    if seconds is None:
        seconds = time.time()
    return str(int(round(seconds * 1_000_000)) * 1000)


def truncate(text: str, limit: int = MAX_CHARS) -> str:
    if limit <= 0 or len(text) <= limit:
        return text
    return text[:limit] + f"\n... (truncated, {len(text)} chars)"


def content_of(line: Dict[str, Any]) -> Any:
    message = line.get("message")
    if isinstance(message, dict):
        return message.get("content")
    return None


def text_of(content: Any) -> str:
    if isinstance(content, str):
        return content
    parts: List[str] = []
    if isinstance(content, list):
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text", "")))
    return "\n".join(p for p in parts if p)


def blocks(content: Any, kind: str) -> List[Dict[str, Any]]:
    if not isinstance(content, list):
        return []
    return [b for b in content if isinstance(b, dict) and b.get("type") == kind]


def format_tool_input(name: str, tool_input: Any) -> str:
    if not tool_input:
        return ""
    if isinstance(tool_input, dict):
        if name in ("Read",):
            return f"File: {tool_input.get('file_path', tool_input.get('path', ''))}"
        if name in ("Bash", "Shell"):
            return truncate(f"Command: {tool_input.get('command', '')}")
    try:
        return truncate(json.dumps(tool_input, indent=2, ensure_ascii=False))
    except (TypeError, ValueError):
        return truncate(str(tool_input))


def format_tool_output(output: Any) -> str:
    if output is None:
        return ""
    if isinstance(output, str):
        return truncate(output)
    if isinstance(output, list):
        parts = []
        for item in output:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text", "")))
            elif isinstance(item, dict) and item.get("type") == "image":
                parts.append("[image]")
            elif isinstance(item, str):
                parts.append(item)
        return truncate("\n".join(parts))
    try:
        return truncate(json.dumps(output, ensure_ascii=False))
    except (TypeError, ValueError):
        return truncate(str(output))


def customer_metadata() -> Dict[str, Any]:
    raw = os.environ.get("RESPAN_METADATA")
    if not raw:
        return {}
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        debug("RESPAN_METADATA is not valid JSON, ignored")
        return {}
    return value if isinstance(value, dict) else {}


# --------------------------------------------------------------------------- #
# State (one JSON file, written atomically, guarded by the worker lock)
# --------------------------------------------------------------------------- #


def load_state() -> Dict[str, Any]:
    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        if isinstance(data, dict) and isinstance(data.get("sessions"), dict):
            return data
    except (OSError, ValueError):
        pass
    return {"version": 2, "sessions": {}}


def save_state(state: Dict[str, Any]) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(STATE_DIR), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(state, f, separators=(",", ":"))
        os.replace(tmp, STATE_FILE)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp)
        raise


def prune_state(state: Dict[str, Any], now: float) -> None:
    sessions = state.get("sessions", {})
    for session_id in list(sessions):
        if now - float(sessions[session_id].get("updated", now)) > STATE_RETENTION_SECONDS:
            del sessions[session_id]
            with contextlib.suppress(OSError):
                SeenLines.path_for(session_id).unlink()


class SeenLines:
    """Transcript line uuids already exported (and span ids already sent), per session.

    Claude Code sometimes re-appends a session's whole history to its transcript (same
    uuids and timestamps, e.g. after a bridge/restore). Those lines were exported the
    first time; skipping them keeps every span sent once and turn numbers right. Stored
    as 48-bit hashes in an append-only file next to the state; new hashes are written
    only after Respan accepted the spans of the lines they belong to.
    """

    def __init__(self, session_id: str) -> None:
        self.path = SeenLines.path_for(session_id)
        self.seen = set()
        with contextlib.suppress(OSError):
            self.seen = set(self.path.read_text(encoding="ascii").split())
        self.pending: List[str] = []

    @staticmethod
    def path_for(session_id: str) -> Path:
        return STATE_DIR / f"respan_seen_{_sha(session_id)[:16]}.txt"

    @staticmethod
    def key(uuid: str) -> str:
        return _sha(f"cc:line:{uuid}")[:12]

    def __contains__(self, key: str) -> bool:
        return key in self.seen

    def add(self, key: str) -> None:
        self.seen.add(key)
        self.pending.append(key)

    def commit(self) -> None:
        if not self.pending:
            return
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        with open(self.path, "a", encoding="ascii") as f:
            f.write("\n".join(self.pending) + "\n")
        self.pending = []

    def rollback(self) -> None:
        for key in self.pending:
            self.seen.discard(key)
        self.pending = []


def new_session_state() -> Dict[str, Any]:
    return {
        "files": {},  # path -> {"offset": int, "parser": {...}}
        "turn_count": 0,
        "last_turn": None,  # {"trace": .., "span": .., "ts": ..} of the last CLOSED turn root
        "spawns": {},  # Agent tool_use id -> {"trace": .., "span": .., "ts": ..}
        "agent_tools": {},  # agentId -> Agent tool_use id (from toolUseResult.agentId)
        "closed_agents": [],
        "close_requests": [],  # agent ids SubagentStop reported done
        "resumed_from": None,
        "updated": time.time(),
    }


# --------------------------------------------------------------------------- #
# Worker lock (portable: O_EXCL lock file with a staleness timeout)
# --------------------------------------------------------------------------- #


@contextlib.contextmanager
def worker_lock() -> Iterator[bool]:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    acquired = False
    try:
        try:
            fd = os.open(str(LOCK_FILE), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            acquired = True
        except FileExistsError:
            try:
                age = time.time() - LOCK_FILE.stat().st_mtime
            except OSError:
                age = 0
            if age > LOCK_STALE_SECONDS:
                with contextlib.suppress(OSError):
                    os.unlink(str(LOCK_FILE))
                try:
                    fd = os.open(str(LOCK_FILE), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                    os.write(fd, str(os.getpid()).encode())
                    os.close(fd)
                    acquired = True
                except FileExistsError:
                    acquired = False
        yield acquired
    finally:
        if acquired:
            with contextlib.suppress(OSError):
                os.unlink(str(LOCK_FILE))


def touch_lock() -> None:
    with contextlib.suppress(OSError):
        os.utime(str(LOCK_FILE), None)


# --------------------------------------------------------------------------- #
# Spans
# --------------------------------------------------------------------------- #


class SpanBuilder:
    """Collects OTLP JSON spans for one session."""

    def __init__(self, session_id: str, seen: Optional["SeenLines"] = None) -> None:
        self.session_id = session_id
        self.seen = seen
        self.spans: List[Dict[str, Any]] = []
        self.customer_id = os.environ.get("RESPAN_CUSTOMER_ID", "claude-code")
        self.metadata = customer_metadata()

    def add(
        self,
        *,
        trace_id: str,
        span_id: str,
        parent_id: Optional[str],
        name: str,
        log_type: str,
        start: Optional[float],
        end: Optional[float],
        input_text: str = "",
        output_text: str = "",
        model: Optional[str] = None,
        usage: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        is_error: bool = False,
        error_message: str = "",
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        reasoning: str = "",
    ) -> None:
        if self.seen is not None:
            # Hard send-once: a span id already sent in this session is never sent again,
            # whatever the transcript repeats (e.g. a fork sub-agent's transcript starts
            # with a copy of its parent's messages, same message and tool ids).
            sent_key = f"s{span_id}"
            if sent_key in self.seen:
                return
            self.seen.add(sent_key)
        start = start if start is not None else end
        end = end if end is not None else start
        if start is not None and end is not None and end < start:
            end = start
        thread = thread_id_for(self.session_id)
        attrs: Dict[str, Any] = {
            ATTR_THREAD: thread,
            ATTR_SESSION: thread,
            ATTR_CUSTOMER: self.customer_id,
            ATTR_LOG_TYPE: log_type,
            "traceloop.workflow.name": WORKFLOW_NAME,
        }
        if log_type == "chat":
            attrs["llm.request.type"] = "chat"
            if input_text:
                attrs["gen_ai.prompt.0.role"] = "user"
                attrs["gen_ai.prompt.0.content"] = input_text
            if output_text or tool_calls or reasoning:
                attrs["gen_ai.completion.0.role"] = "assistant"
                attrs["gen_ai.completion.0.content"] = output_text
            if tool_calls:
                attrs["gen_ai.completion.0.tool_calls"] = json.dumps(tool_calls, ensure_ascii=False)
            if reasoning:
                attrs["gen_ai.completion.0.reasoning_content"] = reasoning
        else:
            attrs["traceloop.span.kind"] = {"agent": "agent", "tool": "tool"}.get(log_type, "task")
            if input_text:
                attrs["traceloop.entity.input"] = input_text
            if output_text:
                attrs["traceloop.entity.output"] = output_text
        if model:
            attrs["gen_ai.request.model"] = model
            attrs["gen_ai.system"] = "anthropic"
        if usage:
            attrs["gen_ai.usage.prompt_tokens"] = int(usage.get("input_tokens", 0) or 0)
            attrs["gen_ai.usage.completion_tokens"] = int(usage.get("output_tokens", 0) or 0)
            if usage.get("cache_read_input_tokens"):
                attrs["gen_ai.usage.cache_read_input_tokens"] = int(usage["cache_read_input_tokens"])
            if usage.get("cache_creation_input_tokens"):
                attrs["gen_ai.usage.cache_creation_input_tokens"] = int(
                    usage["cache_creation_input_tokens"]
                )
        merged = dict(self.metadata)
        merged.update(metadata or {})
        for key, value in merged.items():
            if value is None:
                continue
            attrs[ATTR_METADATA_PREFIX + str(key)] = value
        span: Dict[str, Any] = {
            "traceId": trace_id,
            "spanId": span_id,
            "name": name[:255],
            "kind": OTEL_KIND_CLIENT if log_type == "chat" else OTEL_KIND_INTERNAL,
            "startTimeUnixNano": to_nanos(start),
            "endTimeUnixNano": to_nanos(end),
            "attributes": otlp_attributes(attrs),
            "status": {"code": OTEL_STATUS_ERROR, "message": truncate(error_message, 500)}
            if is_error
            else {"code": OTEL_STATUS_OK},
        }
        if parent_id:
            span["parentSpanId"] = parent_id
        self.spans.append(span)


def otlp_attributes(attrs: Dict[str, Any]) -> List[Dict[str, Any]]:
    out = []
    for key, value in attrs.items():
        if isinstance(value, bool):
            out.append({"key": key, "value": {"boolValue": value}})
        elif isinstance(value, int):
            out.append({"key": key, "value": {"intValue": str(value)}})
        elif isinstance(value, float):
            out.append({"key": key, "value": {"doubleValue": value}})
        elif isinstance(value, str):
            out.append({"key": key, "value": {"stringValue": value}})
        else:
            out.append({"key": key, "value": {"stringValue": json.dumps(value, ensure_ascii=False)}})
    return out


# --------------------------------------------------------------------------- #
# Transcript parsing
# --------------------------------------------------------------------------- #


def is_tool_result_line(line: Dict[str, Any]) -> bool:
    return bool(blocks(content_of(line), "tool_result"))


def is_prompt_line(line: Dict[str, Any]) -> bool:
    """A user line that starts a new turn (not a tool result, meta note or summary)."""
    if line.get("type") != "user":
        return False
    if line.get("isMeta") or line.get("isCompactSummary") or line.get("isVisibleInTranscriptOnly"):
        return False
    if is_tool_result_line(line):
        return False
    return bool(text_of(content_of(line)).strip() or blocks(content_of(line), "image"))


def new_parser() -> Dict[str, Any]:
    return {
        "turn": None,  # open turn (main file) {"trace", "span", "key", "start", "input", "output", "n"}
        "agent": None,  # sub-agent root (sub-agent files) {"trace", "span", "parent", "start", ...}
        "message": None,  # assistant message being assembled {"id", "start", "end", "model", ...}
        "tools": {},  # open tool_use id -> {...}
        "last_ts": None,
        "last_input": "",
        # api-request record id -> its timestamp (when the request was sent). A
        # response's requestRef points at it: that is the response's start time.
        "requests": {},
    }


class FileProcessor:
    """Turns new transcript lines into spans for one file.

    ``kind`` is "main" (one trace per user turn) or "agent" (a sub-agent: every span goes
    into the trace of the Agent tool call that spawned it).
    """

    def __init__(
        self,
        *,
        session_id: str,
        session: Dict[str, Any],
        builder: SpanBuilder,
        kind: str,
        parser: Dict[str, Any],
        agent_id: Optional[str] = None,
        agent_meta: Optional[Dict[str, Any]] = None,
        seen: Optional[SeenLines] = None,
    ) -> None:
        self.seen = seen
        self.session_id = session_id
        self.session = session
        self.builder = builder
        self.kind = kind
        self.p = parser
        self.agent_id = agent_id
        self.agent_meta = agent_meta or {}

    # -- context --------------------------------------------------------- #

    def context(self) -> Optional[Tuple[str, str]]:
        """(trace id, parent span id) for spans of the current line."""
        if self.kind == "agent":
            agent = self.p.get("agent")
            return (agent["trace"], agent["span"]) if agent else None
        turn = self.p.get("turn")
        if turn:
            return turn["trace"], turn["span"]
        last = self.session.get("last_turn")
        # Lines after a turn was closed (e.g. Stop raced a new prompt) still nest
        # under that turn instead of being dropped.
        return (last["trace"], last["span"]) if last else None

    # -- turn (main file) -------------------------------------------------- #

    def open_turn(self, line: Dict[str, Any], ts: Optional[float]) -> None:
        key = str(line.get("uuid") or line.get("promptId") or ts)
        self.session["turn_count"] = int(self.session.get("turn_count", 0)) + 1
        text = text_of(content_of(line))
        self.p["turn"] = {
            "trace": trace_id_for(self.session_id, key),
            "span": span_id_for(self.session_id, f"turn:{key}"),
            "key": key,
            "n": self.session["turn_count"],
            "start": ts,
            "end": ts,
            "input": truncate(text),
            "output": "",
        }

    def close_turn(self) -> None:
        turn = self.p.get("turn")
        if not turn:
            return
        self.flush_message()
        self.emit_turn(turn)
        self.session["last_turn"] = {"trace": turn["trace"], "span": turn["span"], "ts": turn["start"]}
        self.p["turn"] = None

    def emit_turn(self, turn: Dict[str, Any]) -> None:
        preview = turn["input"].replace("\n", " ").strip()
        preview = (preview[:60] + "...") if len(preview) > 60 else (preview or f"turn {turn['n']}")
        metadata: Dict[str, Any] = {"claude_code.turn": turn["n"]}
        if self.session.get("resumed_from"):
            metadata["claude_code.resumed_from_session"] = self.session["resumed_from"].get("session_id")
        self.builder.add(
            trace_id=turn["trace"],
            span_id=turn["span"],
            parent_id=None,
            name=f"Turn {turn['n']}: {preview}",
            log_type="agent",
            start=turn["start"],
            end=turn["end"],
            input_text=turn["input"],
            output_text=truncate(turn["output"]),
            metadata=metadata,
        )

    # -- sub-agent root ------------------------------------------------------ #

    def open_agent(self, spawn: Dict[str, Any], line: Dict[str, Any], ts: Optional[float], run: int = 0) -> None:
        # run > 0: the sub-agent was continued (SendMessage) after it finished; each
        # continuation is its own Sub-agent span under the same Agent call.
        key = f"agent:{self.agent_id}" if run == 0 else f"agent:{self.agent_id}:run{run}"
        self.p["agent"] = {
            "trace": spawn["trace"],
            "span": span_id_for(self.session_id, key),
            "run": run,
            "parent": spawn["span"],
            "start": ts,
            "end": ts,
            "input": truncate(text_of(content_of(line))),
            "output": "",
            "closed": False,
        }

    def close_agent(self) -> None:
        agent = self.p.get("agent")
        if not agent or agent.get("closed"):
            return
        self.flush_message()
        for tool_id in list(self.p["tools"]):
            self.finish_tool(tool_id, None, None, missing=True)
        self.emit_agent(agent)
        agent["closed"] = True
        closed = self.session.setdefault("closed_agents", [])
        if self.agent_id not in closed:
            closed.append(self.agent_id)

    def emit_agent(self, agent: Dict[str, Any]) -> None:
        meta = self.agent_meta
        name = meta.get("description") or meta.get("agentType") or "sub-agent"
        if agent.get("run"):
            name = f"{name} (continued {agent['run']})"
        self.builder.add(
            trace_id=agent["trace"],
            span_id=agent["span"],
            parent_id=agent["parent"],
            name=f"Sub-agent: {name}",
            log_type="agent",
            start=agent["start"],
            end=agent["end"],
            input_text=agent["input"],
            output_text=truncate(agent["output"]),
            metadata={
                "claude_code.agent_id": self.agent_id,
                "claude_code.agent_type": meta.get("agentType"),
                "claude_code.spawn_depth": meta.get("spawnDepth"),
            },
        )

    # -- assistant messages (one LLM span per API response) ------------------ #

    def flush_message(self) -> None:
        msg = self.p.get("message")
        if not msg:
            return
        self.p["message"] = None
        name = f"claude.chat ({msg['model']})" if msg.get("model") else "claude.chat"
        output = msg.get("output", "")
        tool_calls = msg.get("tool_calls") or []
        if not output and tool_calls:
            # A tool-call-only response: say what it called rather than nothing.
            output = "\n".join(f"[tool_use] {c['function']['name']}" for c in tool_calls)
        self.builder.add(
            trace_id=msg["trace"],
            span_id=msg["span"],
            parent_id=msg["parent"],
            name=name,
            log_type="chat",
            start=msg["start"],
            end=msg["end"],
            input_text=msg.get("input", ""),
            output_text=truncate(output),
            model=msg.get("model"),
            usage=msg.get("usage"),
            tool_calls=tool_calls,
            reasoning=truncate("\n\n".join(msg.get("thinking", []))),
            metadata={"claude_code.agent_id": self.agent_id},
        )

    def on_assistant(self, line: Dict[str, Any], ts: Optional[float]) -> None:
        ctx = self.context()
        if not ctx:
            return
        trace, parent = ctx
        message = line.get("message") or {}
        # One API response is written as several lines (one per content block), all
        # with the same message.id / requestId and the same usage.
        msg_id = str(message.get("id") or line.get("requestId") or line.get("uuid") or ts)
        current = self.p.get("message")
        if current and current["id"] != msg_id:
            self.flush_message()
            current = None
        if not current:
            start = self.p.setdefault("requests", {}).pop(str(line.get("requestRef") or ""), None)
            if start is None:
                start = self.p.get("last_ts")
            if start is None or (ts is not None and start > ts):
                start = ts
            current = {
                "id": msg_id,
                "trace": trace,
                "parent": parent,
                "span": span_id_for(self.session_id, f"llm:{msg_id}"),
                "start": start,
                "end": ts,
                "model": message.get("model"),
                "input": self.p.get("last_input", ""),
                "output": "",
                "thinking": [],
                "tool_calls": [],
                "usage": None,
            }
            self.p["message"] = current
        current["end"] = ts or current["end"]
        current["model"] = message.get("model") or current.get("model")
        if isinstance(message.get("usage"), dict):
            current["usage"] = message["usage"]
        content = message.get("content")
        text = text_of(content)
        if text:
            current["output"] = (current["output"] + "\n" + text).strip()
            holder = self.p.get("agent") if self.kind == "agent" else self.p.get("turn")
            if holder is not None:
                holder["output"] = truncate(text)
        for block in blocks(content, "thinking"):
            if block.get("thinking"):
                current["thinking"].append(truncate(str(block["thinking"])))
        for block in blocks(content, "tool_use"):
            current["tool_calls"].append({
                "id": str(block.get("id") or ""),
                "type": "function",
                "function": {
                    "name": str(block.get("name") or "tool"),
                    "arguments": truncate(json.dumps(block.get("input") or {}, ensure_ascii=False)),
                },
            })
            self.open_tool(block, trace, parent, ts)

    # -- tools ---------------------------------------------------------------- #

    def open_tool(self, block: Dict[str, Any], trace: str, parent: str, ts: Optional[float]) -> None:
        tool_id = str(block.get("id") or "")
        if not tool_id:
            return
        name = str(block.get("name") or "tool")
        span = span_id_for(self.session_id, f"tool:{tool_id}")
        self.p["tools"][tool_id] = {
            "trace": trace,
            "parent": parent,
            "span": span,
            "name": name,
            "start": ts,
            "input": format_tool_input(name, block.get("input")),
        }
        if name in AGENT_TOOL_NAMES:
            # Sub-agents spawned by this call nest under this tool span, in this trace.
            self.session["spawns"][tool_id] = {"trace": trace, "span": span}


    def finish_tool(
        self,
        tool_id: str,
        result: Optional[Dict[str, Any]],
        line: Optional[Dict[str, Any]],
        *,
        missing: bool = False,
        ts: Optional[float] = None,
    ) -> None:
        tool = self.p["tools"].pop(tool_id, None)
        if not tool:
            return
        use_result = (line or {}).get("toolUseResult") if line else None
        metadata: Dict[str, Any] = {"claude_code.agent_id": self.agent_id}
        if isinstance(use_result, dict):
            for src, dst in (("durationMs", "duration_ms"), ("numFiles", "num_files"), ("truncated", "truncated")):
                if src in use_result:
                    metadata[dst] = use_result[src]
            spawned = use_result.get("agentId")
            if spawned:
                self.session["agent_tools"][str(spawned)] = tool_id
                if use_result.get("status") not in (None, "async_launched", "running"):
                    # A foreground sub-agent returned: it is finished.
                    done = self.session.setdefault("close_requests", [])
                    if str(spawned) not in done:
                        done.append(str(spawned))
        is_error = bool(result and result.get("is_error"))
        output = "(no result recorded)" if missing else format_tool_output((result or {}).get("content"))
        self.builder.add(
            trace_id=tool["trace"],
            span_id=tool["span"],
            parent_id=tool["parent"],
            name=f"Tool: {tool['name']}",
            log_type="tool",
            start=tool["start"],
            end=ts or tool["start"],
            input_text=tool["input"],
            output_text=output,
            metadata=metadata,
            is_error=is_error,
            error_message=output if is_error else "",
        )

    def on_tool_results(self, line: Dict[str, Any], ts: Optional[float]) -> None:
        # No flush here: Claude Code starts running a response's first tool before it
        # writes the response's later blocks, so a tool result can sit between two
        # lines of the same response. The response is flushed when the next one starts.
        inputs = []
        for block in blocks(content_of(line), "tool_result"):
            tool_id = str(block.get("tool_use_id") or "")
            self.finish_tool(tool_id, block, line, ts=ts)
            inputs.append(format_tool_output(block.get("content")))
        self.p["last_input"] = truncate("\n".join(i for i in inputs if i))

    # -- main loop ------------------------------------------------------------ #

    def feed(self, line: Dict[str, Any]) -> bool:
        """Process one transcript line. Returns False if the file must wait (sub-agent
        whose spawning Agent call is not known yet)."""
        ts = parse_ts(line.get("timestamp"))
        kind = line.get("type")
        if kind == "api-request" and line.get("id") and ts:
            pending = self.p.setdefault("requests", {})
            pending[str(line["id"])] = ts
            while len(pending) > MAX_PENDING_REQUESTS:
                pending.pop(next(iter(pending)))
            return True
        if kind not in ("user", "assistant"):
            # api-request-blob, attachment, mode, ... are not conversation lines and
            # their timestamps are out of order with it: ignore them entirely.
            return True
        line_key = SeenLines.key(str(line["uuid"])) if self.seen is not None and line.get("uuid") else None
        if line_key is not None and line_key in self.seen:
            return True  # a re-appended copy of a line already exported
        if not self.feed_message(line, ts, kind):
            return False
        if line_key is not None:
            self.seen.add(line_key)
        return True

    def feed_message(self, line: Dict[str, Any], ts: Optional[float], kind: Any) -> bool:
        if self.kind == "main":
            if line.get("isSidechain"):
                # Old Claude Code wrote sub-agent lines into the main file; they are not
                # turns of this session. (Current versions write subagents/agent-*.jsonl.)
                return True
            line_session = line.get("sessionId")
            if line_session and line_session != self.session_id:
                # History copied from the session this one resumed: already traced there.
                if not self.session.get("resumed_from"):
                    self.session["resumed_from"] = {"session_id": line_session}
                return True
            if is_prompt_line(line):
                self.close_turn()
                self.open_turn(line, ts)
                self.p["last_input"] = self.p["turn"]["input"]
            elif self.p.get("turn") is None and not self.session.get("last_turn"):
                return True
        else:
            if self.p.get("agent") is None:
                spawn = self.resolve_spawn()
                if spawn is None:
                    return False
                self.open_agent(spawn, line, ts)
                self.p["last_input"] = self.p["agent"]["input"]
            elif self.p["agent"].get("closed") and is_prompt_line(line):
                # A finished sub-agent was continued (SendMessage): a fresh root, so the
                # new work does not nest under a root that already ended.
                previous = self.p["agent"]
                self.flush_message()
                self.open_agent({"trace": previous["trace"], "span": previous["parent"]}, line, ts, run=int(previous.get("run", 0)) + 1)
                self.p["last_input"] = self.p["agent"]["input"]
                closed = self.session.setdefault("closed_agents", [])
                if self.agent_id in closed:
                    closed.remove(self.agent_id)
        holder = self.p.get("agent") if self.kind == "agent" else self.p.get("turn")
        if holder is not None and ts:
            holder["end"] = ts
        if kind == "assistant":
            self.on_assistant(line, ts)
        elif is_tool_result_line(line):
            self.on_tool_results(line, ts)
        elif self.kind == "agent" and is_prompt_line(line):
            self.flush_message()
            self.p["last_input"] = truncate(text_of(content_of(line)))
        if ts:
            self.p["last_ts"] = ts
        return True

    def resolve_spawn(self) -> Optional[Dict[str, Any]]:
        tool_id = self.agent_meta.get("toolUseId") or self.session["agent_tools"].get(str(self.agent_id))
        if not tool_id:
            return None
        return self.session["spawns"].get(str(tool_id))


# --------------------------------------------------------------------------- #
# Reading files incrementally
# --------------------------------------------------------------------------- #


def read_new_lines(path: Path, offset: int, max_bytes: int) -> Tuple[List[Tuple[int, Dict[str, Any]]], int, int]:
    """Complete lines after ``offset`` (up to ``max_bytes``).

    Returns ([(end offset of line, parsed line)], bytes read, file size).
    A trailing partial line (still being written) is left for the next run.
    """
    try:
        size = path.stat().st_size
    except OSError:
        return [], 0, 0
    if size < offset:
        offset = 0  # file was replaced
    if size == offset:
        return [], 0, size
    with open(path, "rb") as f:
        f.seek(offset)
        data = f.read(max_bytes)
    if not data:
        return [], 0, size
    out: List[Tuple[int, Dict[str, Any]]] = []
    pos = 0
    while True:
        nl = data.find(b"\n", pos)
        if nl < 0:
            break
        raw = data[pos:nl]
        pos = nl + 1
        if raw.strip():
            try:
                parsed = json.loads(raw.decode("utf-8"))
                if isinstance(parsed, dict):
                    out.append((offset + pos, parsed))
                    continue
            except (ValueError, UnicodeDecodeError):
                pass
        out.append((offset + pos, {}))
    if pos == 0 and len(data) == max_bytes:
        # One line larger than the chunk: read it whole.
        with open(path, "rb") as f:
            f.seek(offset)
            line = f.readline()
        if line.endswith(b"\n"):
            try:
                parsed = json.loads(line.decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                parsed = {}
            return [(offset + len(line), parsed if isinstance(parsed, dict) else {})], len(line), size
    return out, len(data), size


# --------------------------------------------------------------------------- #
# Sending
# --------------------------------------------------------------------------- #


class SendError(Exception):
    pass


def payload_for(spans: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "resourceSpans": [
            {
                "resource": {"attributes": otlp_attributes({"service.name": "claude-code"})},
                "scopeSpans": [{"scope": {"name": "respan-claude-code-hook", "version": HOOK_VERSION}, "spans": spans}],
            }
        ]
    }


def batches(spans: List[Dict[str, Any]]) -> Iterator[List[Dict[str, Any]]]:
    batch: List[Dict[str, Any]] = []
    size = 0
    for span in spans:
        span_size = len(json.dumps(span, ensure_ascii=False))
        if batch and (len(batch) >= MAX_SPANS_PER_REQUEST or size + span_size > MAX_BYTES_PER_REQUEST):
            yield batch
            batch, size = [], 0
        batch.append(span)
        size += span_size
    if batch:
        yield batch


def _ssl_context() -> ssl.SSLContext:
    """System CAs, or certifi's bundle when installed (python.org macOS builds ship
    without system CAs until 'Install Certificates' is run)."""
    try:
        import certifi  # noqa: PLC0415 - optional

        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def http_post(url: str, body: bytes, headers: Dict[str, str], timeout: float) -> Tuple[int, str]:
    """POST: (status, body text). ``requests`` when installed, else the standard library."""
    if requests is not None:
        response = requests.post(url, data=body, headers=headers, timeout=timeout)
        return response.status_code, response.text[:2000]
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=_ssl_context()) as response:  # nosec B310 - https URL from config
            return response.status, response.read(2000).decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read(2000).decode("utf-8", "replace")


def send_spans(spans: List[Dict[str, Any]], api_key: str, base_url: str) -> None:
    """POST every span; raises SendError unless Respan accepted all of them."""
    if not spans:
        return
    url = base_url.rstrip("/") + "/v2/traces"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    for batch in batches(spans):
        body = json.dumps(payload_for(batch), ensure_ascii=False)
        last_error = ""
        for attempt in range(SEND_ATTEMPTS):
            try:
                status, text = http_post(url, body.encode("utf-8"), headers, SEND_TIMEOUT_SECONDS)
            except Exception as exc:  # network errors are retried
                last_error = str(exc)
            else:
                if status < 300:
                    last_error = ""
                    break
                last_error = f"HTTP {status}: {text[:200]}"
                if 400 <= status < 500 and status not in (408, 429):
                    raise SendError(last_error)
            touch_lock()
            time.sleep(min(2 ** attempt, 8))
        if last_error:
            raise SendError(last_error)
        debug(f"sent {len(batch)} spans")


# --------------------------------------------------------------------------- #
# Session processing
# --------------------------------------------------------------------------- #


def subagent_files(transcript: Path, session_id: str) -> List[Tuple[str, Path, Dict[str, Any]]]:
    folder = transcript.parent / session_id / "subagents"
    out = []
    if not folder.is_dir():
        return out
    for path in sorted(folder.glob("agent-*.jsonl")):
        agent_id = path.stem[len("agent-"):]
        meta: Dict[str, Any] = {}
        meta_path = path.with_name(path.stem + ".meta.json")
        with contextlib.suppress(OSError, ValueError):
            loaded = json.loads(meta_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                meta = loaded
        out.append((agent_id, path, meta))
    out.sort(key=lambda item: (int(item[2].get("spawnDepth") or 1), item[0]))
    return out


def process_file(
    *,
    session_id: str,
    session: Dict[str, Any],
    state: Dict[str, Any],
    path: Path,
    kind: str,
    api_key: str,
    base_url: str,
    agent_id: Optional[str] = None,
    agent_meta: Optional[Dict[str, Any]] = None,
    close: bool = False,
    close_at: Optional[float] = None,
    seen: Optional[SeenLines] = None,
) -> Tuple[bool, int]:
    """Export the new lines of one file, chunk by chunk. Returns (progress made, bytes read)."""
    files = session.setdefault("files", {})
    key = str(path)
    total_read = 0
    progressed = False
    while True:
        entry = files.get(key) or {"offset": 0, "parser": new_parser()}
        snapshot = json.dumps(session)  # restored if the send fails
        builder = SpanBuilder(session_id, seen)
        processor = FileProcessor(
            session_id=session_id,
            session=session,
            builder=builder,
            kind=kind,
            parser=entry["parser"],
            agent_id=agent_id,
            agent_meta=agent_meta,
            seen=seen,
        )
        lines, read, size = read_new_lines(path, int(entry["offset"]), MAX_CHUNK_BYTES)
        total_read += read
        offset = int(entry["offset"])
        blocked = False
        for end_offset, line in lines:
            if line and not processor.feed(line):
                blocked = True
                break
            offset = end_offset
        at_end = offset >= size and not blocked
        if close and at_end:
            if kind == "main":
                turn = processor.p.get("turn")
                # Close only the turn the Stop belongs to, not one a newer prompt opened.
                if turn and (close_at is None or turn.get("start") is None or turn["start"] <= close_at):
                    processor.close_turn()
            else:
                processor.close_agent()
        if offset == int(entry["offset"]) and not builder.spans:
            files[key] = entry
            return progressed, total_read
        entry["offset"] = offset
        files[key] = entry
        try:
            send_spans(builder.spans, api_key, base_url)
        except SendError as exc:
            log("ERROR", f"session {session_id}: send failed, will retry: {exc}")
            if seen is not None:
                seen.rollback()
            restored = json.loads(snapshot)
            session.clear()
            session.update(restored)
            raise
        session["updated"] = time.time()
        save_state(state)
        if seen is not None:
            seen.commit()
        touch_lock()
        progressed = True
        if at_end or blocked or not lines:
            return progressed, total_read


def process_session(
    *,
    state: Dict[str, Any],
    session_id: str,
    transcript: Path,
    api_key: str,
    base_url: str,
    events: List[Dict[str, Any]],
) -> int:
    sessions = state.setdefault("sessions", {})
    session = sessions.setdefault(session_id, new_session_state())
    session_events = [e for e in events if e.get("session_id") == session_id]
    stop_times = [float(e.get("at") or 0) for e in session_events if e.get("hook_event_name") in ("Stop", "SessionEnd")]
    turn_done = bool(stop_times)
    session_end = any(e.get("hook_event_name") == "SessionEnd" for e in session_events)
    for event in session_events:
        if event.get("hook_event_name") == "SubagentStop" and event.get("agent_id"):
            requests_list = session.setdefault("close_requests", [])
            if event["agent_id"] not in requests_list:
                requests_list.append(event["agent_id"])

    total_read = 0
    seen = SeenLines(session_id)
    _, read = process_file(
        session_id=session_id, session=session, state=state, path=transcript, kind="main",
        api_key=api_key, base_url=base_url, close=turn_done, seen=seen,
        close_at=max(stop_times) if stop_times else None,
    )
    total_read += read
    # Sub-agents: repeat while a pass makes progress, so a sub-agent whose spawning
    # Agent call appears in another sub-agent's file is picked up in the same run.
    for _ in range(8):
        progressed_any = False
        now = time.time()
        for agent_id, path, meta in subagent_files(transcript, session_id):
            # Closing an already-closed sub-agent is a no-op; a continued one (new lines
            # after it finished) reopens while its file is read, so decide regardless.
            idle = now - (path.stat().st_mtime if path.exists() else now)
            close = (
                session_end
                or agent_id in session.get("close_requests", [])
                or (turn_done and idle > SUBAGENT_IDLE_CLOSE_SECONDS)
                or idle > SUBAGENT_STALE_CLOSE_SECONDS
            )
            progressed, read = process_file(
                session_id=session_id, session=session, state=state, path=path, kind="agent",
                api_key=api_key, base_url=base_url, agent_id=agent_id, agent_meta=meta, close=close,
                seen=seen,
            )
            total_read += read
            progressed_any = progressed_any or progressed
        if not progressed_any:
            break
    # SubagentStop also fires for agents that never get a transcript here: keep only
    # requests for sub-agents this session knows and has not closed yet.
    known = {Path(f).stem[len("agent-"):] for f in session.get("files", {}) if "/subagents/" in f}
    known |= set(session.get("agent_tools", {}))
    session["close_requests"] = [
        a for a in session.get("close_requests", []) if a in known and a not in session.get("closed_agents", [])
    ][-500:]
    session["updated"] = time.time()
    save_state(state)
    return total_read


# --------------------------------------------------------------------------- #
# Entry points
# --------------------------------------------------------------------------- #


def read_payload() -> Dict[str, Any]:
    if sys.stdin is None or sys.stdin.isatty():
        return {}
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw) if raw.strip() else {}
        return payload if isinstance(payload, dict) else {}
    except (OSError, ValueError):
        return {}


def append_event(payload: Dict[str, Any]) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    event = {
        "hook_event_name": payload.get("hook_event_name") or "Stop",
        "session_id": payload.get("session_id"),
        "transcript_path": payload.get("transcript_path"),
        "agent_id": payload.get("agent_id"),
        "at": time.time(),
    }
    with open(EVENTS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")


def take_events() -> List[Dict[str, Any]]:
    try:
        tmp = EVENTS_FILE.with_suffix(".processing")
        os.replace(str(EVENTS_FILE), str(tmp))
    except OSError:
        return []
    events = []
    with contextlib.suppress(OSError):
        for raw in tmp.read_text(encoding="utf-8").splitlines():
            with contextlib.suppress(ValueError):
                events.append(json.loads(raw))
        tmp.unlink()
    # While Respan is unreachable events pile up (PostToolUse fires constantly):
    # one per (session, event, agent) is enough, keeping the latest.
    latest: Dict[Tuple[Any, Any, Any], Dict[str, Any]] = {}
    for event in events:
        key = (event.get("session_id"), event.get("hook_event_name"), event.get("agent_id"))
        if key not in latest or float(event.get("at") or 0) >= float(latest[key].get("at") or 0):
            latest[key] = event
    return sorted(latest.values(), key=lambda e: float(e.get("at") or 0))


def has_stale_open_agent(session: Dict[str, Any]) -> bool:
    now = time.time()
    for path, entry in session.get("files", {}).items():
        agent = (entry.get("parser") or {}).get("agent")
        if not agent or agent.get("closed"):
            continue
        try:
            if now - os.path.getmtime(path) > SUBAGENT_STALE_CLOSE_SECONDS:
                return True
        except OSError:
            return True
    return False


def run_worker(api_key: str, base_url: str) -> int:
    """Drain queued hook events. Exactly one worker runs at a time; an event that
    arrives while it runs marks the queue dirty and the worker runs another pass."""
    with worker_lock() as acquired:
        if not acquired:
            DIRTY_FILE.touch()
            return 0
        total = 0
        for _ in range(50):
            with contextlib.suppress(OSError):
                DIRTY_FILE.unlink()
            events = take_events()
            if not events:
                break
            state = load_state()
            prune_state(state, time.time())
            by_session: Dict[str, Path] = {}
            for event in events:
                if event.get("session_id") and event.get("transcript_path"):
                    by_session[event["session_id"]] = Path(event["transcript_path"])
            failed = False
            # Sessions with an open sub-agent whose file went quiet get a pass too, so a
            # missed SubagentStop (crash, background agent outliving its parent's last
            # event) still closes that sub-agent on a later hook run of any session.
            for other_id, other in state.get("sessions", {}).items():
                if other_id in by_session:
                    continue
                main = [f for f in other.get("files", {}) if "/subagents/" not in f]
                if main and has_stale_open_agent(other):
                    by_session[other_id] = Path(main[0])
            for session_id, transcript in by_session.items():
                if not transcript.exists():
                    continue
                try:
                    total += process_session(
                        state=state, session_id=session_id, transcript=transcript,
                        api_key=api_key, base_url=base_url, events=events,
                    )
                except SendError:
                    # Keep the events so the next hook run retries this session.
                    for event in events:
                        if event.get("session_id") == session_id:
                            append_event(event)
                    failed = True
                except Exception as exc:  # never break Claude Code
                    log("ERROR", f"session {session_id}: {type(exc).__name__}: {exc}")
            if failed:
                break  # Respan is unreachable: the next hook run retries.
            if not DIRTY_FILE.exists() and not EVENTS_FILE.exists():
                break
        return total


def main() -> None:
    if os.environ.get("TRACE_TO_RESPAN", "").lower() != "true":
        return
    api_key = os.environ.get("RESPAN_API_KEY")
    base_url = os.environ.get("RESPAN_BASE_URL", "https://api.respan.ai/api")
    if not api_key:
        log("ERROR", "RESPAN_API_KEY is not set")
        return
    if len(sys.argv) > 1 and sys.argv[1] == "--worker":
        started = time.monotonic()
        read = run_worker(api_key, base_url)
        debug(f"worker done: {read} bytes read in {time.monotonic() - started:.1f}s")
        return
    payload = read_payload()
    if not payload.get("session_id") or not payload.get("transcript_path"):
        debug("hook payload without session_id/transcript_path, ignored")
        return
    transcript = Path(str(payload["transcript_path"])).expanduser()
    try:
        inside_state = transcript.resolve().is_relative_to(STATE_DIR.resolve())  # type: ignore[attr-defined]
    except AttributeError:  # Python < 3.9
        inside_state = str(transcript.resolve()).startswith(str(STATE_DIR.resolve()))
    if transcript.suffix != ".jsonl" or inside_state:
        debug(f"ignored transcript_path {transcript}")
        return
    debug(f"{payload.get('hook_event_name')} session={payload.get('session_id')} agent={payload.get('agent_id')}")
    append_event(payload)
    if os.environ.get("CC_RESPAN_FOREGROUND", "").lower() == "true":
        run_worker(api_key, base_url)
        return
    # Detach so Claude Code is never slowed down by the export.
    kwargs: Dict[str, Any] = {
        "stdin": subprocess.DEVNULL,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
        "close_fds": True,
    }
    if os.name == "nt":
        kwargs["creationflags"] = 0x00000008 | 0x00000200  # DETACHED_PROCESS | NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True
    try:
        subprocess.Popen([sys.executable, os.path.abspath(__file__), "--worker"], **kwargs)
    except OSError as exc:
        log("ERROR", f"could not start the export worker: {exc}")


if __name__ == "__main__":
    # Claude Code reads a hook's stdout (and exit code 2 blocks Stop): print nothing,
    # swallow everything, always exit 0.
    with contextlib.suppress(Exception):
        sys.stdout = open(os.devnull, "w")
    try:
        main()
    except BaseException as exc:  # the hook must never fail Claude Code
        with contextlib.suppress(Exception):
            log("ERROR", f"{type(exc).__name__}: {exc}")
    os._exit(0)
