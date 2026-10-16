import assert from "node:assert/strict";
import { llm } from "@livekit/agents";
import { trace, context } from "@opentelemetry/api";
import { z } from "zod";
import { agentTurn, nativeModel, runExample } from "./_shared.js";
await runExample("TypeScript LiveKit Native Privacy and Errors", async () => {
  const toolError = await agentTurn({
    tool: "native_error",
    tools: {
      native_error: llm.tool({
        description: "Controlled native error.",
        parameters: z.object({ city: z.string() }),
        execute: async () => {
          throw new llm.ToolError("Controlled tool failure.");
        },
      }),
    },
  });
  const lateVeto = await agentTurn({
    tool: "native_private",
    tools: {
      native_private: llm.tool({
        description: "Native content veto.",
        parameters: z.object({ city: z.string() }),
        execute: async () => {
          const span = trace.getSpan(context.active());
          span?.setAttribute("allow_trace_content", false);
          span?.setAttribute("allow_trace_content", true);
          return { hidden: "native payload" };
        },
      }),
    },
  });
  const fixture = nativeModel({ error: true });
  const errors: unknown[] = [];
  fixture.model.on("error", (error) => errors.push(error));
  const unhandled: unknown[] = [];
  const observeRejection = (error: unknown) => {
    unhandled.push(error);
  };
  process.on("unhandledRejection", observeRejection);
  const stream = fixture.model.chat({
    chatCtx: llm.ChatContext.empty(),
    connOptions: { maxRetry: 0, retryIntervalMs: 0, timeoutMs: 1000 },
  });
  let chunks = 0;
  for await (const _chunk of stream) chunks++;
  stream.close();
  await new Promise((resolve) => setTimeout(resolve, 30));
  process.removeListener("unhandledRejection", observeRejection);
  assert.equal(chunks, 0);
  assert.ok(errors.length);
  return {
    toolError,
    lateVeto,
    controlledProviderErrors: errors.length,
    observedNativeRejections: unhandled.length,
  };
});
