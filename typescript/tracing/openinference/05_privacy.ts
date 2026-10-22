import type { Respan } from "@respan/respan";
import { context, trace } from "@opentelemetry/api";
import { OITracer, withSpan } from "@arizeai/openinference-core";
import {
  SemanticConventions,
  OpenInferenceSpanKind,
} from "@arizeai/openinference-semantic-conventions";
import { CONTEXT_KEY_ALLOW_TRACE_CONTENT } from "@traceloop/ai-semantic-conventions";
import { workflow } from "./_shared.js";
export async function run(respan: Respan) {
  return workflow(respan, "privacy", () => {
    const tracer = new OITracer({ tracer: trace.getTracer("native-privacy") });
    tracer.startActiveSpan(
      "late-veto",
      {
        attributes: {
          [SemanticConventions.OPENINFERENCE_SPAN_KIND]:
            OpenInferenceSpanKind.LLM,
          [SemanticConventions.LLM_MODEL_NAME]: "safe-fixture-model",
        },
      },
      (span) => {
        span.setAttribute(
          SemanticConventions.INPUT_VALUE,
          "PRIVATE_FIXTURE_INPUT",
        );
        const actual = trace.getSpan(context.active())!;
        actual.setAttribute("allow_trace_content", false);
        actual.setAttribute("allow_trace_content", true);
        span.setAttribute(
          SemanticConventions.OUTPUT_VALUE,
          "PRIVATE_FIXTURE_OUTPUT",
        );
        span.recordException(Error("PRIVATE_FIXTURE_ERROR"));
        span.setStatus({ code: 2, message: "PRIVATE_FIXTURE_STATUS" });
        span.end();
      },
    );
    const redacted = new OITracer({
      tracer: trace.getTracer("native-redaction"),
      traceConfig: {
        hideInputs: true,
        hideOutputs: true,
        hideEmbeddingVectors: true,
        hideLLMTools: true,
      },
    });
    withSpan((text: string) => text, {
      name: "native-redaction",
      tracer: redacted,
      kind: OpenInferenceSpanKind.LLM,
    })("PRIVATE_FIXTURE_REDACTED");
    context.with(
      context
        .active()
        .setValue(CONTEXT_KEY_ALLOW_TRACE_CONTENT as never, false),
      () =>
        withSpan((_input: string) => "PRIVATE_FIXTURE_CONTEXT_OUTPUT", {
          name: "context-veto",
        })("PRIVATE_FIXTURE_CONTEXT_INPUT"),
    );
    return { lateVeto: true, nativeRedaction: true, contextVeto: true };
  });
}
