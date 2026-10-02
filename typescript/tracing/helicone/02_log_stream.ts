import {
  createRuntime,
  jsonLineStream,
  logResult,
  runWorkflow,
  shutdownRuntime,
} from "./_shared.js";

const workflowName = "helicone_ts_log_stream";
const runtime = await createRuntime();

try {
  const result = await runWorkflow(runtime, workflowName, async () => {
    return await runtime.logger.logStream(
      {
        model: "gpt-4o-mini",
        messages: [{ role: "user", content: "Stream one traced sentence." }],
      },
      async (recorder) => {
        const chunks = [
          { choices: [{ delta: { role: "assistant", content: "Streaming " } }] },
          { choices: [{ delta: { content: "through Helicone." } }] },
          {
            choices: [{ delta: {}, finish_reason: "stop" }],
            usage: { prompt_tokens: 7, completion_tokens: 4, total_tokens: 11 },
          },
        ];
        recorder.attachStream(jsonLineStream(chunks));
        return { chunkCount: chunks.length };
      },
      { "Helicone-Property-scenario": "log-stream" },
    );
  });

  logResult(workflowName, {
    chunkCount: result.chunkCount,
    heliconeLogs: runtime.mock.logs.length,
  });
} finally {
  await shutdownRuntime(runtime);
}
