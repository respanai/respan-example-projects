import {
  createRuntime,
  heliconeValueStream,
  logResult,
  runWorkflow,
  shutdownRuntime,
} from "./_shared.js";

const workflowName = "helicone_ts_single_request_builder";
const runtime = await createRuntime();

try {
  await runWorkflow(runtime, workflowName, async () => {
    await runtime.logger.logSingleRequest(
      { model: "text-model", prompt: "Write a short release note." },
      JSON.stringify({
        model: "text-model",
        choices: [{ text: "Added deterministic Helicone tracing." }],
        usage: { prompt_tokens: 6, completion_tokens: 5, total_tokens: 11 },
      }),
      {
        latencyMs: 25,
        additionalHeaders: { "Helicone-Property-scenario": "single-request" },
      },
    );

    const responseBuilder = runtime.logger.logBuilder(
      {
        model: "builder-model",
        messages: [{ role: "user", content: "Exercise the response builder." }],
      },
      { "Helicone-Property-scenario": "builder-response" },
    );
    responseBuilder.addAdditionalHeaders({
      "Helicone-Property-builder-header": "added-after-creation",
    });
    responseBuilder.setResponse(JSON.stringify({
      choices: [{ message: { role: "assistant", content: "Builder response captured." } }],
      usage: { prompt_tokens: 5, completion_tokens: 4, total_tokens: 9 },
    }));
    await responseBuilder.sendLog();

    const streamBuilder = runtime.logger.logBuilder(
      {
        model: "builder-stream-model",
        messages: [{ role: "user", content: "Exercise the stream builder." }],
      },
      { "Helicone-Property-scenario": "builder-stream" },
    );
    const builderReadable = streamBuilder.toReadableStream(heliconeValueStream([
      { choices: [{ delta: { role: "assistant", content: "Builder stream." } }] },
      { choices: [{ delta: {} }], usage: { prompt_tokens: 4, completion_tokens: 2 } },
    ]));
    const reader = builderReadable.getReader();
    while (!(await reader.read()).done) {
      // Consume the public toReadableStream path so the builder records chunks.
    }
    await streamBuilder.sendLog();

    const attachedStreamBuilder = runtime.logger.logBuilder(
      {
        model: "builder-attached-stream-model",
        messages: [{ role: "user", content: "Exercise builder attachStream." }],
      },
      { "Helicone-Property-scenario": "builder-attach-stream" },
    );
    await attachedStreamBuilder.attachStream(heliconeValueStream([
      { choices: [{ delta: { role: "assistant", content: "Attached stream." } }] },
      { choices: [{ delta: {} }], usage: { prompt_tokens: 4, completion_tokens: 2 } },
    ]));
    await attachedStreamBuilder.sendLog();

    const errorBuilder = runtime.logger.logBuilder(
      {
        model: "builder-error-model",
        messages: [{ role: "user", content: "Record a controlled builder failure." }],
      },
      { "Helicone-Property-scenario": "builder-error" },
    );
    errorBuilder.setError(new Error("controlled builder failure"));
    await errorBuilder.sendLog();

    await runtime.logger.sendLog(
      {
        model: "direct-send-model",
        messages: [{ role: "user", content: "Exercise direct sendLog." }],
      },
      {
        choices: [{ message: { role: "assistant", content: "Direct send captured." } }],
        usage: { prompt_tokens: 3, completion_tokens: 3, total_tokens: 6 },
      },
      {
        startTime: Date.now() - 10,
        endTime: Date.now(),
        status: 200,
        additionalHeaders: { "Helicone-Property-scenario": "direct-send" },
      },
    );
  });

  logResult(workflowName, {
    expectedSpans: 6,
    builderErrorIncluded: true,
    builderToReadableStreamIncluded: true,
    builderAttachStreamIncluded: true,
    builderAddAdditionalHeadersIncluded: true,
    heliconeLogs: runtime.mock.logs.length,
  });
} finally {
  await shutdownRuntime(runtime);
}
