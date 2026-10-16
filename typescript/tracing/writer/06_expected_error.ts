import {
  createRespan,
  createWriterClient,
  DEFAULT_CHAT_MODEL,
  logExampleResult,
  runWithWriterWorkflow,
  shutdownRespan,
  withTimeout,
} from "./_shared.js";

const workflowName = "writer.expected_error.workflow";
const respan = createRespan();
const writer = createWriterClient();

try {
  let errorMessage = "";
  await withTimeout(
    runWithWriterWorkflow(respan, workflowName, async () => {
      try {
        await writer.chat.chat({
          model: DEFAULT_CHAT_MODEL,
          messages: [
            { role: "user", content: "Trigger the expected error path." },
          ],
        });
      } catch (error) {
        errorMessage = error instanceof Error ? error.message : String(error);
      }
    }),
    workflowName,
  );

  logExampleResult(workflowName, {
    expected: "one failed chat span with status_code and error.message",
    actual: errorMessage,
  });
} finally {
  await shutdownRespan(respan);
}
