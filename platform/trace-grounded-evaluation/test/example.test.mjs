import assert from "node:assert/strict";
import { execFileSync, spawnSync } from "node:child_process";
import { readFileSync, rmSync } from "node:fs";
import test from "node:test";
import { fileURLToPath } from "node:url";

import {
  fetchJudgment,
  gatewayRequest,
  parseReply,
  replay,
} from "../example.ts";

const cases = JSON.parse(
  readFileSync(new URL("../fixtures/cases.json", import.meta.url), "utf8"),
);
const snapshot = JSON.parse(
  readFileSync(new URL("../fixtures/recorded.json", import.meta.url), "utf8"),
);
const evidence = cases[0];
const valid = JSON.stringify({
  verdict: "fail",
  responseGrounded: "no",
  failureCategory: "tool_failure",
  evidenceSpanIds: [evidence.events[0].id],
  reason: "A test verdict.",
});

test("recorded replies replay offline with preserved format flags and code-scored references", () => {
  const results = replay(cases, snapshot);
  assert.equal(results.length, 6);
  assert.ok(
    results.every((r) => r.parsed.ok && r.parsed.format === "markdown_fence"),
  );
  assert.ok(results.every((r) => r.parsed.unknownEvidenceIds.length === 0));
  assert.ok(results.every((r) => r.taskMatchesReference));
});

test("only a complete outer Markdown fence is accepted", () => {
  const fenced = "```json\n" + valid + "\n```";
  assert.equal(parseReply(valid, evidence).format, "raw_json");
  assert.equal(parseReply(fenced, evidence).format, "markdown_fence");
  for (const input of [
    "Here is the answer:\n" + fenced,
    fenced + "\nExtra text",
    fenced + "\n" + fenced,
    fenced.slice(0, -3),
    '```json\n{"verdict":\n```',
  ]) {
    assert.deepEqual(parseReply(input, evidence), {
      ok: false,
      error: "invalid_json",
    });
  }
  assert.deepEqual(parseReply("{}", evidence), {
    ok: false,
    error: "invalid_schema",
  });
});

test("unknown, duplicate, and missing evidence IDs remain visible", () => {
  const unknown = parseReply(
    valid.replace(evidence.events[0].id, "invented-span"),
    evidence,
  );
  assert.equal(unknown.ok, true);
  assert.deepEqual(unknown.unknownEvidenceIds, ["invented-span"]);
  assert.deepEqual(
    parseReply(
      valid.replace(JSON.stringify(evidence.events[0].id), ""),
      evidence,
    ),
    { ok: false, error: "missing_evidence_id" },
  );
  const duplicate = JSON.parse(valid);
  duplicate.evidenceSpanIds.push(duplicate.evidenceSpanIds[0]);
  assert.deepEqual(parseReply(JSON.stringify(duplicate), evidence), {
    ok: false,
    error: "duplicate_evidence_id",
  });
});

test("judge requests exclude reference labels and author annotations", () => {
  const input = structuredClone(evidence);
  input.expectedTaskPassed = "private-label";
  input.authorNote = "private-author-note";
  input.events[0].details.expectedAnswer = "private-answer";
  const request = gatewayRequest(
    input,
    "grounded",
    snapshot.rubrics.grounded,
    snapshot.model,
    "run-marker",
  );
  const encoded = JSON.stringify(request);
  for (const hidden of [
    "private-label",
    "private-author-note",
    "private-answer",
  ])
    assert.ok(!encoded.includes(hidden));
  assert.equal(request.metadata.run_id, "run-marker");
  assert.ok(request.custom_identifier.includes(evidence.caseId));
});

test("live client retains raw model output and Respan log ID without returning credentials", async () => {
  const rawOutput = "```json\n" + valid + "\n```";
  const request = gatewayRequest(
    evidence,
    "baseline",
    snapshot.rubrics.baseline,
    snapshot.model,
    "test",
  );
  let calls = 0;
  const result = await fetchJudgment(request, {
    apiKey: "respan-test-secret",
    anthropicKey: "provider-test-secret",
    transport: async (url, init) => {
      calls++;
      assert.equal(url, "https://api.respan.ai/api/chat/completions");
      assert.equal(init.headers.Authorization, "Bearer respan-test-secret");
      assert.equal(
        JSON.parse(init.body).customer_credentials.anthropic.api_key,
        "provider-test-secret",
      );
      return new Response(
        JSON.stringify({
          id: "response-1",
          choices: [{ message: { content: rawOutput }, finish_reason: "stop" }],
          usage: { prompt_tokens: 10, completion_tokens: 20 },
        }),
        { status: 200, headers: { "x-respan-log-id": "log-1" } },
      );
    },
  });
  assert.equal(calls, 1);
  assert.equal(result.rawOutput, rawOutput);
  assert.equal(result.logId, "log-1");
  assert.equal(result.finishReason, "stop");
  assert.ok(!JSON.stringify(result).includes("test-secret"));
});

test("gateway errors retain the explanation and redact both keys", async () => {
  const error = fetchJudgment(
    {},
    {
      apiKey: "respan-secret",
      anthropicKey: "provider-secret",
      transport: async () =>
        new Response(
          JSON.stringify({
            code: "activation_required",
            detail: "respan-secret provider-secret",
          }),
          { status: 401 },
        ),
    },
  );
  await assert.rejects(
    error,
    (e) =>
      e.message.includes("activation_required") &&
      !e.message.includes("respan-secret") &&
      !e.message.includes("provider-secret"),
  );
});

test("default CLI works without credentials and makes no inference calls", () => {
  const stdout = execFileSync(
    process.execPath,
    [fileURLToPath(new URL("../example.ts", import.meta.url))],
    {
      encoding: "utf8",
      env: { ...process.env, RESPAN_API_KEY: "", ANTHROPIC_API_KEY: "" },
    },
  );
  const summary = JSON.parse(stdout.trim().split("\n").at(-1));
  assert.equal(summary.mode, "recorded replay");
  assert.equal(summary.inferenceCalls, 0);
  assert.equal(summary.replies, 6);
});

test("live CLI retains a malformed reply and stops after one mocked inference call", () => {
  const marker = `offline-format-failure-${process.pid}`;
  const output = new URL(`../.out/${marker}.jsonl`, import.meta.url);
  const preload = `let calls=0;globalThis.fetch=async()=>{if(++calls>1)throw Error('unexpected second call');return new Response(JSON.stringify({id:'mock-response',choices:[{message:{content:'not json'},finish_reason:'stop'}]}),{status:200});};`;
  try {
    const result = spawnSync(
      process.execPath,
      [
        "--import",
        `data:text/javascript,${encodeURIComponent(preload)}`,
        fileURLToPath(new URL("../example.ts", import.meta.url)),
        "--live",
        "--max-calls",
        "6",
      ],
      {
        encoding: "utf8",
        env: {
          ...process.env,
          RESPAN_API_KEY: "offline-test-key",
          RESPAN_EXAMPLE_RUN_ID: marker,
        },
      },
    );
    assert.equal(result.status, 1);
    assert.match(result.stderr, /No further calls made/);
    const rows = readFileSync(output, "utf8")
      .trim()
      .split("\n")
      .map(JSON.parse);
    assert.equal(rows.length, 1);
    assert.equal(rows[0].rawOutput, "not json");
    assert.deepEqual(rows[0].parsed, { ok: false, error: "invalid_json" });
  } finally {
    rmSync(output, { force: true });
  }
});
