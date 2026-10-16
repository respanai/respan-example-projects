import {
  createRespan,
  createWriterClient,
  DEFAULT_CHAT_MODEL,
  logExampleResult,
  runWithWriterWorkflow,
  shutdownRespan,
} from "./_shared.js";
const respan = createRespan("writer-capture-policy-examples", false),
  writer = createWriterClient(),
  workflowName = "writer.capture_policy.workflow";
try {
  await runWithWriterWorkflow(respan, workflowName, async () => {
    const result = await writer.chat.chat({
      model: DEFAULT_CHAT_MODEL,
      messages: [
        {
          role: "user",
          content:
            "Controlled content withheld by WriterInstrumentor traceContent false.",
        },
      ],
    });
    logExampleResult(workflowName, {
      expected:
        "Writer span keeps model, status and usage with content withheld",
      model: result.model,
    });
  });
} finally {
  await shutdownRespan(respan);
}
