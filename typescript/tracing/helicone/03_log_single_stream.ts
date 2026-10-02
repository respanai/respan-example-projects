import {
  createRuntime,
  jsonLineStream,
  logResult,
  runWorkflow,
  shutdownRuntime,
} from "./_shared.js";

const workflowName = "helicone_ts_log_single_stream";
const runtime = await createRuntime();

try {
  const chunks = [
    { choices: [{ delta: { role: "assistant", content: "Single " } }] },
    { choices: [{ delta: { content: "stream captured." } }] },
    {
      choices: [{ delta: {}, finish_reason: "stop" }],
      usage: { prompt_tokens: 6, completion_tokens: 3, total_tokens: 9 },
    },
  ];

  await runWorkflow(runtime, workflowName, async () => {
    await runtime.logger.logSingleStream(
      {
        model: "gpt-4o-mini",
        messages: [{ role: "user", content: "Exercise logSingleStream." }],
      },
      jsonLineStream(chunks),
      { "Helicone-Property-scenario": "log-single-stream" },
    );
  });

  logResult(workflowName, {
    chunkCount: chunks.length,
    heliconeLogs: runtime.mock.logs.length,
  });
} finally {
  await shutdownRuntime(runtime);
}
