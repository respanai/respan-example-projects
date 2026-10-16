import { context } from "@opentelemetry/api";
import { CONTEXT_KEY_ALLOW_TRACE_CONTENT } from "@traceloop/ai-semantic-conventions";
import {
  createAzureClient,
  createRespan,
  runWithExampleTrace,
  logExampleResult,
} from "./_shared.js";
const workflowName = "TypeScript Azure OpenAI Privacy and Error Example";
const respan = await createRespan(
  "typescript-azure-openai-privacy-error-example",
);
await respan.initialize();
try {
  await runWithExampleTrace(respan, workflowName, async () => {
    await context.with(
      context.active().setValue(CONTEXT_KEY_ALLOW_TRACE_CONTENT, false),
      () =>
        createAzureClient().chat.completions.create({
          model: "deployment",
          messages: [
            {
              role: "user",
              content: "Private prompt omitted from the model span",
            },
          ],
        }),
    );
    if (process.env.RESPAN_AZURE_LIVE !== "1") {
      try {
        await createAzureClient().chat.completions.create({
          model: "fixture-error",
          messages: [{ role: "user", content: "Controlled error" }],
        });
      } catch (error) {
        if (!(error instanceof Error)) throw error;
        logExampleResult(workflowName, { controlledError: error.name });
      }
    }
  });
} finally {
  await respan.shutdown();
}
