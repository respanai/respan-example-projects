/** Trace-based task judging through Respan. Replay recorded replies by default. */
import { appendFileSync, mkdirSync, readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

export type Rubric = "baseline" | "grounded";
export interface Evidence {
  caseId: string;
  instruction: string;
  answerContract: string;
  observationLimits: string;
  events: Array<{
    id: string;
    kind: string;
    agent: string | null;
    details: Record<string, unknown>;
  }>;
  finalResponse: string | null;
}
interface Judgment {
  verdict: "pass" | "fail" | "insufficient_evidence";
  responseGrounded: "yes" | "no" | "insufficient_evidence";
  failureCategory: string;
  evidenceSpanIds: string[];
  reason: string;
}
export type ParsedReply =
  | {
      ok: true;
      format: "raw_json" | "markdown_fence";
      value: Judgment;
      unknownEvidenceIds: string[];
    }
  | { ok: false; error: string };
export interface Snapshot {
  model: string;
  labels: Record<string, boolean>;
  rubrics: Record<Rubric, string>;
  replies: Array<{
    caseId: string;
    rubric: Rubric;
    rawOutput: string;
    finishReason: string | null;
  }>;
}

function object(value: unknown): Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value)
    ? (value as Record<string, unknown>)
    : {};
}

/** Accept one complete outer fence; never repair broken JSON or extract from prose. */
export function parseReply(text: string, evidence: Evidence): ParsedReply {
  let value: unknown;
  let format: "raw_json" | "markdown_fence" = "raw_json";
  try {
    value = JSON.parse(text);
  } catch {
    const fence = /^```(?:json)?[ \t]*\r?\n([\s\S]*?)\r?\n```$/i.exec(
      text.trim(),
    );
    if (!fence) return { ok: false, error: "invalid_json" };
    try {
      value = JSON.parse(fence[1]!);
      format = "markdown_fence";
    } catch {
      return { ok: false, error: "invalid_json" };
    }
  }
  const r = object(value);
  const keys = [
    "verdict",
    "responseGrounded",
    "failureCategory",
    "evidenceSpanIds",
    "reason",
  ];
  if (
    Object.keys(r).length !== keys.length ||
    !keys.every((key) => key in r) ||
    !["pass", "fail", "insufficient_evidence"].includes(String(r.verdict)) ||
    !["yes", "no", "insufficient_evidence"].includes(
      String(r.responseGrounded),
    ) ||
    ![
      "none",
      "tool_failure",
      "missing_capability",
      "unsupported_claim",
      "answer_failure",
      "other",
      "unknown",
    ].includes(String(r.failureCategory)) ||
    typeof r.reason !== "string" ||
    r.reason.length === 0 ||
    r.reason.length > 1500 ||
    !Array.isArray(r.evidenceSpanIds) ||
    r.evidenceSpanIds.length > 12 ||
    !r.evidenceSpanIds.every((id) => typeof id === "string")
  ) {
    return { ok: false, error: "invalid_schema" };
  }
  const judgment = r as unknown as Judgment;
  if (
    new Set(judgment.evidenceSpanIds).size !== judgment.evidenceSpanIds.length
  ) {
    return { ok: false, error: "duplicate_evidence_id" };
  }
  if (
    judgment.verdict !== "insufficient_evidence" &&
    judgment.evidenceSpanIds.length === 0
  ) {
    return { ok: false, error: "missing_evidence_id" };
  }
  const ids = new Set(evidence.events.map((event) => event.id));
  return {
    ok: true,
    format,
    value: judgment,
    unknownEvidenceIds: judgment.evidenceSpanIds.filter((id) => !ids.has(id)),
  };
}

const OBSERVED = [
  "llm.assistant_text",
  "llm.stop_reason",
  "tool.name",
  "tool.input",
  "tool.output",
  "tool.ok",
  "tool.error.kind",
  "delegate.worker_tools",
  "delegate.worker_answer",
  "delegate.worker_final_text",
  "delegate.worker_halt_reason",
];

/** Explicit projection prevents labels or author annotations leaking into judge input. */
export function gatewayRequest(
  evidence: Evidence,
  rubric: Rubric,
  systemPrompt: string,
  model: string,
  runId: string,
): Record<string, unknown> {
  const visible = {
    caseId: evidence.caseId,
    instruction: evidence.instruction,
    answerContract: evidence.answerContract,
    observationLimits: evidence.observationLimits,
    events: evidence.events.map((event) => ({
      id: event.id,
      kind: event.kind,
      agent: event.agent,
      details: Object.fromEntries(
        Object.entries(event.details).filter(([key]) => OBSERVED.includes(key)),
      ),
    })),
    finalResponse: evidence.finalResponse,
  };
  return {
    model,
    temperature: 0,
    max_tokens: 512,
    messages: [
      { role: "system", content: systemPrompt },
      { role: "user", content: JSON.stringify(visible) },
    ],
    custom_identifier: `${runId}:${evidence.caseId}:${rubric}`,
    metadata: {
      example: "trace-grounded-evaluation",
      run_id: runId,
      case_id: evidence.caseId,
      rubric,
    },
  };
}

export async function fetchJudgment(
  request: Record<string, unknown>,
  options: {
    apiKey: string;
    anthropicKey?: string;
    transport?: typeof fetch;
  },
): Promise<{
  rawOutput: string;
  responseId: string | null;
  logId: string | null;
  finishReason: string | null;
  usage: unknown;
}> {
  if (!options.apiKey)
    throw new Error("RESPAN_API_KEY is required for live calls");
  const response = await (options.transport ?? fetch)(
    "https://api.respan.ai/api/chat/completions",
    {
      method: "POST",
      redirect: "error",
      signal: AbortSignal.timeout(30_000),
      headers: {
        Authorization: `Bearer ${options.apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        ...request,
        ...(options.anthropicKey
          ? {
              customer_credentials: {
                anthropic: { api_key: options.anthropicKey },
              },
            }
          : {}),
      }),
    },
  );
  const raw = await response.text();
  if (!response.ok) {
    let detail = raw;
    for (const secret of [options.apiKey, options.anthropicKey]) {
      if (secret) detail = detail.split(secret).join("[redacted]");
    }
    throw new Error(
      `Respan HTTP ${response.status}: ${detail.replace(/sk-[a-zA-Z0-9_-]+/g, "[redacted]").slice(0, 1000)}`,
    );
  }
  const result = object(JSON.parse(raw));
  const first = Array.isArray(result.choices) ? object(result.choices[0]) : {};
  const content = object(first.message).content;
  if (typeof content !== "string")
    throw new Error("Gateway response has no text content");
  return {
    rawOutput: content,
    responseId: typeof result.id === "string" ? result.id : null,
    logId: response.headers.get("x-respan-log-id"),
    finishReason:
      typeof first.finish_reason === "string" ? first.finish_reason : null,
    usage: result.usage ?? null,
  };
}

export function replay(cases: Evidence[], snapshot: Snapshot) {
  return cases.flatMap((evidence) =>
    (["baseline", "grounded"] as const).map((rubric) => {
      const captured = snapshot.replies.find(
        (r) => r.caseId === evidence.caseId && r.rubric === rubric,
      );
      if (!captured)
        throw new Error(`Missing recorded reply: ${evidence.caseId}/${rubric}`);
      const parsed = parseReply(captured.rawOutput, evidence);
      const comparable =
        parsed.ok &&
        parsed.unknownEvidenceIds.length === 0 &&
        parsed.value.verdict !== "insufficient_evidence";
      return {
        caseId: evidence.caseId,
        rubric,
        rawOutput: captured.rawOutput,
        parsed,
        taskMatchesReference: comparable
          ? (parsed.value.verdict === "pass") ===
            snapshot.labels[evidence.caseId]
          : null,
      };
    }),
  );
}

async function main(): Promise<void> {
  const args = process.argv.slice(2);
  const live = args.includes("--live");
  const byok = args.includes("--byok");
  const at = args.indexOf("--max-calls");
  const maxCalls = Number(at < 0 ? 1 : args[at + 1]);
  if (
    args.some(
      (arg, i) =>
        !["--live", "--byok", "--max-calls"].includes(arg) &&
        i !== (at < 0 ? -1 : at + 1),
    ) ||
    !Number.isInteger(maxCalls) ||
    maxCalls < 1 ||
    maxCalls > 6
  ) {
    throw new Error(
      "Usage: node example.ts [--live] [--max-calls 1..6] [--byok]",
    );
  }
  const here = dirname(fileURLToPath(import.meta.url));
  const cases = JSON.parse(
    readFileSync(resolve(here, "fixtures/cases.json"), "utf8"),
  ) as Evidence[];
  const snapshot = JSON.parse(
    readFileSync(resolve(here, "fixtures/recorded.json"), "utf8"),
  ) as Snapshot;
  if (!live) {
    const results = replay(cases, snapshot);
    for (const result of results)
      console.log(
        JSON.stringify({
          caseId: result.caseId,
          rubric: result.rubric,
          parsed: result.parsed,
          taskMatchesReference: result.taskMatchesReference,
        }),
      );
    console.log(
      JSON.stringify({
        mode: "recorded replay",
        inferenceCalls: 0,
        replies: results.length,
        caveat:
          "Three curated synthetic cases. Task labels do not label explanation or response-grounding quality.",
      }),
    );
    return;
  }
  const apiKey = process.env.RESPAN_API_KEY;
  if (!apiKey) throw new Error("RESPAN_API_KEY is required");
  const anthropicKey = byok ? process.env.ANTHROPIC_API_KEY : undefined;
  if (byok && !anthropicKey)
    throw new Error("--byok requires ANTHROPIC_API_KEY");
  const model = process.env.RESPAN_JUDGE_MODEL ?? snapshot.model;
  if (byok && !model.includes("claude"))
    throw new Error("--byok supports Anthropic models in this example");
  const runId =
    process.env.RESPAN_EXAMPLE_RUN_ID ??
    `trace-judge-${new Date().toISOString()}`;
  const output = resolve(
    here,
    ".out",
    `${runId.replace(/[^a-zA-Z0-9._-]/g, "_")}.jsonl`,
  );
  mkdirSync(dirname(output), { recursive: true });
  // Exclusive first write prevents accidental replacement of a previous run.
  appendFileSync(output, "", { flag: "wx" });
  const plan = cases.flatMap((evidence) =>
    (["baseline", "grounded"] as const).map((rubric) => ({ evidence, rubric })),
  );
  for (const { evidence, rubric } of plan.slice(0, maxCalls)) {
    const request = gatewayRequest(
      evidence,
      rubric,
      snapshot.rubrics[rubric],
      model,
      runId,
    );
    const reply = await fetchJudgment(request, {
      apiKey,
      ...(anthropicKey ? { anthropicKey } : {}),
    });
    const parsed = parseReply(reply.rawOutput, evidence);
    const comparable =
      parsed.ok &&
      parsed.unknownEvidenceIds.length === 0 &&
      parsed.value.verdict !== "insufficient_evidence";
    const taskMatchesReference = comparable
      ? (parsed.value.verdict === "pass") === snapshot.labels[evidence.caseId]
      : null;
    appendFileSync(
      output,
      JSON.stringify({
        caseId: evidence.caseId,
        rubric,
        model,
        ...reply,
        parsed,
        taskMatchesReference,
      }) + "\n",
    );
    console.log(
      JSON.stringify({
        caseId: evidence.caseId,
        rubric,
        parsed,
        taskMatchesReference,
        logId: reply.logId,
      }),
    );
    if (!parsed.ok || parsed.unknownEvidenceIds.length > 0) {
      throw new Error(
        `Judge output needs inspection; raw reply retained at ${output}. No further calls made.`,
      );
    }
  }
  console.log(`Saved live replies to ${output}`);
}

if (
  process.argv[1] &&
  import.meta.url === pathToFileURL(resolve(process.argv[1])).href
) {
  await main();
}
