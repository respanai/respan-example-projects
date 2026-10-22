import { MODEL, LIVE, createRuntime, runCase, log } from "./_shared.js";
const caseId = "legacy_completion";
const runtime = await createRuntime();
try {
  const result = await runCase(runtime.respan, caseId, async () => {
    if (LIVE) return { fixtureOnly: true };
    const params = {
      model: MODEL,
      max_tokens_to_sample: 64,
      prompt: "\n\nHuman: Legacy compatibility.\n\nAssistant:",
    };
    const response = await runtime.client.completions.create(params);
    let streamed = "";
    for await (const chunk of await runtime.client.completions.create({
      ...params,
      stream: true,
    }))
      streamed += chunk.completion;
    return { completion: response.completion, streamed };
  });
  log(caseId, result);
} finally {
  await runtime.close(caseId);
}
