"""End-to-end: run the scripted call, then check what Respan stored, via the API.

  python e2e.py            run a new call, then check it
  python e2e.py <session>  check an earlier call only

Checks, against GET /api/sessions/<session>/?view=turns:
  - the call is one session, and every span the SDK sent carries that session id
  - one trace per caller turn, each with voice timings (wait, STT, LLM time to
    first token, TTS time to first audio)
  - the turn the caller talked over is flagged interrupted, and only that one
  - the whole-call voice_summary counts the turns and the interruption

Writes out/session_turns.json (the API's answer) and prints PASS/FAIL per check.
Exit code 0 only if every check passes.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time

import requests

from voice_demo import EXPECTED_INTERRUPTED_TURN, EXPECTED_TURNS, OUT, run_call

VOICE_TIMINGS = ("wait_ms", "stt_ms", "llm_ttft_ms", "tts_ttfa_ms")
READ_TIMEOUT_S = 180
RESULTS: list[bool] = []


def check(label: str, passed: bool, detail: object = "") -> None:
    RESULTS.append(bool(passed))
    print(f"{'PASS' if passed else 'FAIL'} {label}" + (f": {detail}" if detail != "" else ""), flush=True)


def read_session(session_id: str) -> dict:
    """The session's turns page, once every turn has been ingested."""
    base = os.environ.get("RESPAN_BASE_URL", "https://api.respan.ai/api").rstrip("/")
    headers = {"Authorization": f"Bearer {os.environ['RESPAN_API_KEY']}"}
    deadline = time.monotonic() + READ_TIMEOUT_S
    page: dict = {}
    while time.monotonic() < deadline:
        response = requests.get(f"{base}/sessions/{session_id}/", params={"view": "turns"},
                                headers=headers, timeout=60)
        if response.ok:
            page = response.json()
            voice_turns = [t for t in page.get("results", []) if t.get("voice")]
            if len(voice_turns) >= EXPECTED_TURNS and page.get("voice_summary"):
                break
        time.sleep(5)
    (OUT / "session_turns.json").write_text(json.dumps(page, indent=2))
    return page


def main() -> int:
    if len(sys.argv) > 1:
        session_id = sys.argv[1]
        spans = json.loads((OUT / "spans.json").read_text())
    else:
        call = asyncio.run(run_call())
        session_id = call["session_id"]
        spans = json.loads((OUT / "spans.json").read_text())
        check("the call was cut off once by the caller", call["agent_cut_off"] == 1, call["agent_cut_off"])

    session_ids = {s["session_id"] for s in spans}
    check("one session: every exported span carries the same session id",
          isinstance(session_id, str) and session_ids == {session_id}, sorted(map(str, session_ids)))

    page = read_session(str(session_id))
    traces = page.get("results", [])
    voice_turns = sorted((t for t in traces if t.get("voice")),
                         key=lambda t: int(t["voice"].get("turn_index") or 0))
    other = [t for t in traces if not t.get("voice")]
    print(f"\nsession {session_id}: {len(traces)} traces, {len(voice_turns)} voice turns")
    for turn in voice_turns:
        v = turn["voice"]
        print(f"  turn {v.get('turn_index')}: trace {turn['id']}  wait {v.get('wait_ms')} ms, "
              f"stt {v.get('stt_ms')} ms, llm ttft {v.get('llm_ttft_ms')} ms, "
              f"tts ttfa {v.get('tts_ttfa_ms')} ms{'  INTERRUPTED' if v.get('is_interrupted') else ''}{'  slow' if v.get('is_slow') else ''}")
    print(f"  voice_summary: {page.get('voice_summary')}\n")

    check(f"one trace per turn: {EXPECTED_TURNS} voice turns", len(voice_turns) == EXPECTED_TURNS, len(voice_turns))
    check("each turn is its own trace", len({t["id"] for t in voice_turns}) == len(voice_turns))
    check("the only other trace is the call itself (its id is the session id)",
          all(t["id"] == session_id for t in other) and len(other) <= 1, [t["id"] for t in other])
    missing = {t["voice"].get("turn_index"): [k for k in VOICE_TIMINGS
                                             if not isinstance(t["voice"].get(k), (int, float))]
               for t in voice_turns}
    check("every turn has wait, STT, LLM TTFT and TTS TTFA timings",
          bool(voice_turns) and not any(missing.values()), {k: v for k, v in missing.items() if v})
    interrupted = [i + 1 for i, t in enumerate(voice_turns) if t["voice"].get("is_interrupted")]
    check(f"turn {EXPECTED_INTERRUPTED_TURN} (talked over) is flagged interrupted, and only it",
          interrupted == [EXPECTED_INTERRUPTED_TURN], interrupted)
    summary = page.get("voice_summary") or {}
    check("voice_summary counts the turns and the interruption",
          summary.get("turn_count") == EXPECTED_TURNS and summary.get("interruption_count") == 1, summary)

    passed = all(RESULTS)
    print(f"\n{'PASS' if passed else 'FAIL'}: {sum(RESULTS)}/{len(RESULTS)} checks")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
