/**
 * End-to-end: run the scripted call, then check what Respan stored, via the API.
 * The same checks as the Python demo's e2e.py.
 *
 *   npx tsx e2e.ts            run a new call, then check it
 *   npx tsx e2e.ts <session>  check an earlier call only
 *
 * Writes out/session_turns.json (the API's answer); prints PASS/FAIL per check.
 */
import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { EXPECTED_INTERRUPTED_TURN, EXPECTED_TURNS, OUT, runCall } from "./voice_demo.js";

const VOICE_TIMINGS = ["wait_ms", "stt_ms", "llm_ttft_ms", "tts_ttfa_ms"];
const READ_TIMEOUT_MS = 180_000;
const results: boolean[] = [];

type Voice = Record<string, number | boolean | null>;
type Trace = { id: string; voice: Voice | null };
type Page = { results?: Trace[]; voice_summary?: Record<string, number> | null };

function check(label: string, passed: boolean, detail: unknown = ""): void {
  results.push(passed);
  console.log(`${passed ? "PASS" : "FAIL"} ${label}${detail === "" ? "" : `: ${JSON.stringify(detail)}`}`);
}

async function readSession(sessionId: string): Promise<Page> {
  const base = (process.env.RESPAN_BASE_URL ?? "https://api.respan.ai/api").replace(/\/$/, "");
  const deadline = Date.now() + READ_TIMEOUT_MS;
  let page: Page = {};
  while (Date.now() < deadline) {
    const response = await fetch(`${base}/sessions/${sessionId}/?view=turns`, {
      headers: { Authorization: `Bearer ${process.env.RESPAN_API_KEY}` },
    });
    if (response.ok) {
      page = (await response.json()) as Page;
      const voiceTurns = (page.results ?? []).filter((t) => t.voice);
      if (voiceTurns.length >= EXPECTED_TURNS && page.voice_summary) break;
    }
    await new Promise((resolve) => setTimeout(resolve, 5000));
  }
  writeFileSync(join(OUT, "session_turns.json"), JSON.stringify(page, null, 2));
  return page;
}

async function main(): Promise<number> {
  let sessionId: unknown = process.argv[2];
  if (!sessionId) {
    const call = await runCall();
    sessionId = call.session_id;
    check("the call was cut off once by the caller", call.agent_cut_off === 1, call.agent_cut_off);
  }
  const spans = JSON.parse(readFileSync(join(OUT, "spans.json"), "utf8")) as Array<{ session_id: string }>;
  const sessionIds = [...new Set(spans.map((s) => s.session_id))];
  check(
    "one session: every exported span carries the same session id",
    typeof sessionId === "string" && sessionIds.length === 1 && sessionIds[0] === sessionId,
    sessionIds,
  );

  const page = await readSession(String(sessionId));
  const traces = page.results ?? [];
  const voiceTurns = traces
    .filter((t) => t.voice)
    .sort((a, b) => Number(a.voice?.turn_index ?? 0) - Number(b.voice?.turn_index ?? 0));
  const other = traces.filter((t) => !t.voice);
  console.log(`\nsession ${sessionId}: ${traces.length} traces, ${voiceTurns.length} voice turns`);
  for (const turn of voiceTurns) {
    const v = turn.voice as Voice;
    console.log(
      `  turn ${v.turn_index}: trace ${turn.id}  wait ${v.wait_ms} ms, stt ${v.stt_ms} ms, ` +
        `llm ttft ${v.llm_ttft_ms} ms, tts ttfa ${v.tts_ttfa_ms} ms` +
        `${v.is_interrupted ? "  INTERRUPTED" : ""}${v.is_slow ? "  slow" : ""}`,
    );
  }
  console.log(`  voice_summary: ${JSON.stringify(page.voice_summary)}\n`);

  check(`one trace per turn: ${EXPECTED_TURNS} voice turns`, voiceTurns.length === EXPECTED_TURNS, voiceTurns.length);
  check("each turn is its own trace", new Set(voiceTurns.map((t) => t.id)).size === voiceTurns.length);
  check(
    "the only other trace is the call itself (its id is the session id)",
    other.length <= 1 && other.every((t) => t.id === sessionId),
    other.map((t) => t.id),
  );
  const missing = voiceTurns
    .map((t) => [t.voice?.turn_index, VOICE_TIMINGS.filter((k) => typeof t.voice?.[k] !== "number")] as const)
    .filter(([, keys]) => keys.length);
  check("every turn has wait, STT, LLM TTFT and TTS TTFA timings", voiceTurns.length > 0 && !missing.length, missing);
  const interrupted = voiceTurns.flatMap((t, i) => (t.voice?.is_interrupted ? [i + 1] : []));
  check(
    `turn ${EXPECTED_INTERRUPTED_TURN} (talked over) is flagged interrupted, and only it`,
    interrupted.length === 1 && interrupted[0] === EXPECTED_INTERRUPTED_TURN,
    interrupted,
  );
  const summary = page.voice_summary ?? {};
  check(
    "voice_summary counts the turns and the interruption",
    summary.turn_count === EXPECTED_TURNS && summary.interruption_count === 1,
    summary,
  );

  const passed = results.every(Boolean);
  console.log(`\n${passed ? "PASS" : "FAIL"}: ${results.filter(Boolean).length}/${results.length} checks`);
  return passed ? 0 : 1;
}

main().then(
  (code) => process.exit(code),
  (error) => {
    console.error(error);
    process.exit(1);
  },
);
