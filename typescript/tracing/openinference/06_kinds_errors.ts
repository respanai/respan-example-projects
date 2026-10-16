import type { Respan } from "@respan/respan";
import assert from "node:assert/strict";
import { withSpan } from "@arizeai/openinference-core";
import { OpenInferenceSpanKind } from "@arizeai/openinference-semantic-conventions";
import { workflow } from "./_shared.js";
export async function run(respan: Respan) {
  return workflow(respan, "kinds-errors", async () => {
    const result = [];
    for (const kind of [
      OpenInferenceSpanKind.RERANKER,
      OpenInferenceSpanKind.GUARDRAIL,
      OpenInferenceSpanKind.EVALUATOR,
      OpenInferenceSpanKind.PROMPT,
      OpenInferenceSpanKind.DECISION,
    ])
      result.push(
        withSpan(
          () => ({ accepted: false, score: 0, empty: "", nullable: null }),
          { name: `kind-${kind.toLowerCase()}`, kind },
        )(),
      );
    const error = Error("controlled helper failure");
    await assert.rejects(
      withSpan(
        async () => {
          throw error;
        },
        { name: "helper-failure", kind: OpenInferenceSpanKind.LLM },
      )(),
      (caught) => caught === error,
    );
    return { kindCount: result.length, controlledFailure: true };
  });
}
