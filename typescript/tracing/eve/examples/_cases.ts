import { type Client } from "eve/client";
import assert from "node:assert/strict";
import { EXAMPLE_RUN_ID } from "../_env.js";
import { createSession, runCase, type ExampleResult } from "./_shared.js";

export function runBasicTurn(client: Client): Promise<ExampleResult> {
  return runCase(
    client,
    "basic-turn",
    "RESPAN_EVE_BASIC: return the deterministic basic response.",
    {
      eventTypes: ["message.completed", "session.waiting"],
      message: /Eve basic instrumentation example completed/,
    },
  );
}

export function runToolCall(client: Client): Promise<ExampleResult> {
  return runCase(
    client,
    "tool-call",
    "RESPAN_EVE_TOOL: call get_weather and report its deterministic result.",
    {
      eventTypes: ["actions.requested", "action.result", "session.waiting"],
      message: /Sunny/,
    },
  );
}

export function runSubagentLineage(client: Client): Promise<ExampleResult> {
  return runCase(
    client,
    "subagent-lineage",
    "RESPAN_EVE_SUBAGENT: call researcher and include its exact marker.",
    {
      eventTypes:
        "sessions" in client
          ? ["agent.started", "task.settled", "session.waiting"]
          : ["subagent.called", "subagent.completed", "session.waiting"],
      message: /RESEARCH_MARKER=eve-lineage-ok/,
      needsChildSession: true,
    },
  );
}

export async function runValuesAndError(
  client: Client,
): Promise<ExampleResult[]> {
  const results = [];
  for (const [suffix, expected] of [
    ["FALSE", /^Value: false$/],
    ["ZERO", /^Value: 0$/],
    ["EMPTY", /^Value: ""$/],
  ] as const) {
    results.push(
      await runCase(
        client,
        "value-" + suffix.toLowerCase(),
        "RESPAN_EVE_VALUE_" + suffix,
        {
          eventTypes: ["actions.requested", "action.result", "session.waiting"],
          message: expected,
        },
      ),
    );
  }
  results.push(
    await runCase(client, "tool-error", "RESPAN_EVE_ERROR", {
      eventTypes: ["actions.requested", "action.result", "session.waiting"],
      message: /Synthetic error observed/,
    }),
  );
  return results;
}
export async function runContinuation(client: Client): Promise<ExampleResult> {
  const session = await createSession(client);
  await (await session.send("RESPAN_EVE_BASIC")).result();
  const result = await (await session.send("RESPAN_EVE_CONTINUE")).result();
  assert.match(result.message, /Continuation preserved history/);
  return {
    caseId: "continuation",
    childSessionIds: [],
    eventTypes: result.events.map((event: { type: string }) => event.type),
    message: result.message,
    runId: EXAMPLE_RUN_ID,
    sessionId: result.sessionId,
    status: result.status,
  };
}
export async function runStreamAndLarge(
  client: Client,
): Promise<ExampleResult> {
  const session = await createSession(client),
    response = await session.send("RESPAN_EVE_LARGE");
  const events: { type: string; data?: unknown }[] = [];
  for await (const event of response) events.push(event);
  assert.ok(events.some((event) => event.type === "message.completed"));
  const completed = events.filter(
    (event) => event.type === "message.completed",
  );
  assert.ok(JSON.stringify(completed).includes("_LARGE_END"));
  return {
    caseId: "stream-large",
    childSessionIds: [],
    eventTypes: events.map((event) => event.type),
    message: "native stream retained the 80022-character response",
    runId: EXAMPLE_RUN_ID,
    sessionId: response.sessionId,
    status: "waiting",
  };
}

export async function runMemory(client: Client): Promise<ExampleResult[]> {
  if (!("sessions" in client)) return [];
  const saved = await runCase(client, "memory-save", "RESPAN_EVE_MEMORY_SAVE", {
    eventTypes: ["action.result", "session.waiting"],
    message: /Memory saved/,
  });
  const recalled = await runCase(
    client,
    "memory-recall",
    "RESPAN_EVE_MEMORY_RECALL",
    {
      eventTypes: ["session.waiting"],
      message: /Memory recall verified: true/,
    },
  );
  return [saved, recalled];
}
