import { MODEL, LIVE, createRuntime, runCase, log } from "./_shared.js";
const caseId = "count_tokens_and_batches";
const runtime = await createRuntime();
try {
  const result = await runCase(runtime.respan, caseId, async () => {
    const messages = [
      { role: "user" as const, content: "Count this actual native request." },
    ];
    const stable = await runtime.client.messages.countTokens({
      model: MODEL,
      messages,
    });
    const beta = await runtime.client.beta.messages.countTokens({
      model: MODEL,
      messages,
    });
    if (LIVE)
      return {
        stable: stable.input_tokens,
        beta: beta.input_tokens,
        batchFixtureSkipped: true,
      };
    const request = {
      requests: [
        {
          custom_id: "row_success",
          params: { model: MODEL, max_tokens: 512, messages },
        },
        {
          custom_id: "row_error",
          params: { model: MODEL, max_tokens: 512, messages },
        },
      ],
    };
    const batch = await runtime.client.messages.batches.create(request);
    const betaBatch =
      await runtime.client.beta.messages.batches.create(request);
    const rows = [];
    for await (const row of await runtime.client.messages.batches.results(
      batch.id,
    ))
      rows.push({ customId: row.custom_id, result: row.result.type });
    const betaRows = [];
    for await (const row of await runtime.client.beta.messages.batches.results(
      betaBatch.id,
    ))
      betaRows.push({ customId: row.custom_id, result: row.result.type });
    return {
      stable: stable.input_tokens,
      beta: beta.input_tokens,
      rows,
      betaRows,
    };
  });
  log(caseId, result);
} finally {
  await runtime.close(caseId);
}
