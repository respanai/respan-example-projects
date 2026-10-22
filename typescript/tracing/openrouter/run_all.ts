import assert from "node:assert/strict";
import { RUN_ID, LIVE, createRespan, shutdownRespan } from "./_shared.js";
import { runChatCompletion } from "./01_chat_completion.js";
import { runToolCalling } from "./02_tool_calling.js";
import { runStreaming } from "./03_streaming.js";
import { runEmbeddings } from "./04_embeddings.js";
import { runResponses } from "./05_responses.js";
import { runCallModel } from "./06_call_model.js";
import { runNativeOutcomes } from "./07_native_outcomes.js";
const respan = createRespan();
try {
  await runChatCompletion(respan);
  await runToolCalling(respan);
  await runStreaming(respan);
  await runEmbeddings(respan);
  await runResponses(respan);
  await runCallModel(respan);
  await runNativeOutcomes(respan);
  const spans = respan.capture.getFinishedSpans();
  if (!LIVE) {
    assert.equal(spans.length, 18);
    const modelSpans = spans.filter(
      (s) => s.attributes["respan.entity.log_type"] !== "workflow",
    );
    assert.equal(modelSpans.length, 11);
    assert.ok(modelSpans.every((s) => s.parentSpanContext));
  }
  console.log(
    JSON.stringify({
      runId: RUN_ID,
      entrypoints: 7,
      fixture: !LIVE,
      spans: spans.length,
      liveProviderSkipped: !LIVE,
    }),
  );
} finally {
  await shutdownRespan(respan);
}
