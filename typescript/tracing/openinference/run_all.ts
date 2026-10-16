import { createRuntime, RUN_ID } from "./_shared.js";
import * as helpers from "./01_native_helpers.js";
import * as llm from "./02_full_llm_attributes.js";
import * as retrieval from "./03_retrieval_embeddings.js";
import * as openai from "./04_native_openai.js";
import * as privacy from "./05_privacy.js";
import * as kinds from "./06_kinds_errors.js";
const scenarios = [helpers, llm, retrieval, openai, privacy, kinds];
const selected = process.argv[2]
  ? [scenarios[Number(process.argv[2]) - 1]]
  : scenarios;
if (selected.some((scenario) => !scenario))
  throw new Error("Choose a scenario number from 1 to 6.");
const runtime = await createRuntime();
let count = 0;
try {
  for (const scenario of selected) {
    await scenario.run(runtime.respan);
    count++;
  }
} finally {
  const spans = await runtime.finish();
  console.log(
    JSON.stringify({
      runId: RUN_ID,
      scenarios: count,
      spans: spans.length,
      traceIds: [...new Set(spans.map((span) => span.traceId))],
    }),
  );
}
