import assert from "node:assert/strict";
import { context } from "@opentelemetry/api";
import { suppressTracing } from "@opentelemetry/core";
import { CONTEXT_KEY_ALLOW_TRACE_CONTENT } from "@traceloop/ai-semantic-conventions";
import { chatSend } from "@openrouter/sdk/funcs/chatSend.js";
import {
  CHAT_MODEL,
  LIVE,
  createOpenRouterClient,
  createRespan,
  runWithOpenRouterWorkflow,
  shutdownRespan,
  logExampleResult,
} from "./_shared.js";
export async function runNativeOutcomes(
  respan = createRespan(),
): Promise<void> {
  const own = arguments.length === 0;
  try {
    await runWithOpenRouterWorkflow(
      respan,
      "openrouter_ts_native_outcomes",
      async () => {
        if (LIVE) {
          logExampleResult("openrouter_ts_native_outcomes", {
            skipped:
              "controlled error/privacy/large fixtures require fixture mode",
          });
          return;
        }
        const client = createOpenRouterClient();
        const messages = Array.from({ length: 75 }, (_, i) => ({
          role: "user" as const,
          content: `controlled-history-${i}`,
        }));
        const request = { chatRequest: { model: CHAT_MODEL, messages } };
        const promise = chatSend(client, request);
        const inspected = promise.$inspect();
        assert.equal(promise.$inspect(), inspected);
        const [result, meta] = await inspected;
        assert.ok(result.ok);
        assert.equal(meta.status, "complete");
        await assert.rejects(
          client.chat.send({
            chatRequest: { ...request.chatRequest, model: "controlled/error" },
          }),
        );
        const stream = await client.chat.send({
          chatRequest: { ...request.chatRequest, stream: true },
        });
        assert.ok(stream instanceof ReadableStream);
        const reader = stream.getReader();
        await reader.read();
        await reader.cancel();
        await context.with(
          context.active().setValue(CONTEXT_KEY_ALLOW_TRACE_CONTENT, false),
          () => client.chat.send(request),
        );
        await context.with(suppressTracing(context.active()), () =>
          client.chat.send(request),
        );
        logExampleResult("openrouter_ts_native_outcomes", {
          history: messages.length,
          scenarios: 5,
        });
      },
    );
  } finally {
    if (own) await shutdownRespan(respan);
  }
}
if (import.meta.url === `file://${process.argv[1]}`) await runNativeOutcomes();
