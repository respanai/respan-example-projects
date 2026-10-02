import {
  createRuntime,
  logResult,
  runWorkflow,
  shutdownRuntime,
} from "./_shared.js";

const workflowName = "helicone_ts_expected_error";
const runtime = await createRuntime();

try {
  const message = await runWorkflow(runtime, workflowName, async () => {
    try {
      await runtime.logger.logRequest(
        {
          model: "controlled-error-model",
          messages: [{ role: "user", content: "Trigger the controlled failure." }],
        },
        async () => {
          throw new Error("controlled provider failure before sendLog");
        },
        { "Helicone-Property-scenario": "expected-error" },
        "openai",
      );
      throw new Error("Expected the controlled provider call to fail.");
    } catch (error) {
      const caught = error instanceof Error ? error.message : String(error);
      if (!caught.includes("controlled provider failure")) throw error;
      return caught;
    }
  });

  logResult(workflowName, {
    expectedError: true,
    message,
    heliconeLogs: runtime.mock.logs.length,
  });
} finally {
  await shutdownRuntime(runtime);
}
