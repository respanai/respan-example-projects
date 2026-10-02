import {
  createRuntime,
  logResult,
  runWorkflow,
  shutdownRuntime,
} from "./_shared.js";

const workflowName = "helicone_ts_custom_events";
const runtime = await createRuntime();

try {
  await runWorkflow(runtime, workflowName, async () => {
    await runtime.logger.logRequest(
      { _type: "tool", toolName: "lookup_order", input: { orderId: "H-2048" } },
      async (recorder) => {
        const result = { eta: "2026-09-01" };
        recorder.appendResults(result);
        return result;
      },
    );

    await runtime.logger.logRequest(
      {
        _type: "vector_db",
        operation: "search",
        text: "Helicone instrumentation",
        vector: [0.11, 0.22, 0.33],
        topK: 2,
        filter: { language: "typescript" },
        databaseName: "respan-docs",
      },
      async (recorder) => {
        const result = { matches: [{ id: "doc-1", score: 0.99 }] };
        recorder.appendResults(result);
        return result;
      },
    );

    await runtime.logger.logRequest(
      {
        _type: "data",
        name: "quality_score",
        meta: {
          score: 0.98,
          evaluator: "deterministic",
          redactionProbe: {
            authToken: "sentinel-auth-value",
            bearerToken: "sentinel-bearer-value",
            idToken: "sentinel-id-value",
            sessionToken: "sentinel-session-value",
            privateKey: "sentinel-private-value",
            clientSecret: "sentinel-client-value",
            credential: "sentinel-credential-value",
            credentials: "sentinel-credentials-value",
            heliconeAuth: "sentinel-helicone-auth-value",
          },
          tokenMetrics: {
            promptTokens: 12,
            completionTokens: 4,
            tokenCount: 16,
            tokenizer: "sentinel-tokenizer",
          },
          serializedPayload: JSON.stringify({
            privateKey: "serialized-private-sentinel",
            authToken: "serialized-auth-sentinel",
            credential: "serialized-credential-sentinel",
            promptTokens: 21,
            completionTokens: 6,
            tokenCount: 27,
            tokenizer: "serialized-tokenizer",
          }),
        },
      },
      async (recorder) => {
        const result = { accepted: true };
        recorder.appendResults(result);
        return result;
      },
    );
  });

  logResult(workflowName, {
    customEventTypes: ["tool", "vector_db", "data"],
    structuredRedactionProbe: true,
    heliconeLogs: runtime.mock.logs.length,
  });
} finally {
  await shutdownRuntime(runtime);
}
