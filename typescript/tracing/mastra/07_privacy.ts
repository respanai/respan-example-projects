import { context } from "@opentelemetry/api";
import { CONTEXT_KEY_ALLOW_TRACE_CONTENT } from "@traceloop/ai-semantic-conventions";
import { SpanType } from "@mastra/core/observability";
import {
  createRuntime,
  EXAMPLE_RUN_ID,
  runWithRespanWorkflow,
} from "./_shared.js";
const { mastra, respan, observability } = createRuntime({});
await runWithRespanWorkflow(mastra, respan, "Mastra Privacy", async () => {
  const span = context.with(
    context.active().setValue(CONTEXT_KEY_ALLOW_TRACE_CONTENT, false),
    () =>
      observability.getDefaultInstance()!.startSpan({
        name: "native.private",
        type: SpanType.GENERIC,
        input: { private: "must not export" },
      }),
  );
  span.end({ output: { private: "must not export" } });
});
console.log(
  JSON.stringify({
    runId: EXAMPLE_RUN_ID,
    scenario: "privacy",
    expectedContent: false,
  }),
);
