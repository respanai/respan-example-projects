import {
  createRuntime,
  logResult,
  runWorkflow,
  shutdownRuntime,
} from "./_shared.js";

const creationWorkflow = "helicone_ts_delayed_builder_creation";
const sendWorkflow = "helicone_ts_delayed_builder_send_context";
const runtime = await createRuntime();

try {
  let builder: ReturnType<typeof runtime.logger.logBuilder> | undefined;
  await runWorkflow(runtime, creationWorkflow, async () => {
    builder = runtime.logger.logBuilder(
      {
        model: "delayed-builder-model",
        messages: [{
          role: "user",
          content: "Keep the creation workflow as this span's parent.",
        }],
      },
      {
        "Helicone-User-Id": "delayed-builder-user",
        "Helicone-Session-Id": "delayed-builder-thread",
        "Helicone-Property-context": "creation",
      },
    );
    return { builderCreated: true };
  });

  const createdBuilder = builder;
  if (!createdBuilder) throw new Error("Delayed builder was not created.");
  createdBuilder.setResponse(JSON.stringify({
    choices: [{
      message: {
        role: "assistant",
        content: "The creation context was retained.",
      },
    }],
    usage: { prompt_tokens: 8, completion_tokens: 6, total_tokens: 14 },
  }));

  await runWorkflow(runtime, sendWorkflow, async () => {
    await createdBuilder.sendLog();
  });

  logResult(creationWorkflow, {
    sendWorkflow,
    expectedCreationChildren: 1,
    expectedSendChildren: 0,
    expectedCapturedWorkflowMetadata: creationWorkflow,
    heliconeLogs: runtime.mock.logs.length,
  });
} finally {
  await shutdownRuntime(runtime);
}
