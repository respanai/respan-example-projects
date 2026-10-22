import { ConverseCommand } from "@aws-sdk/client-bedrock-runtime";
import {
  createBedrockClient,
  createRespan,
  DEFAULT_CONVERSE_MODEL,
  logExampleResult,
  runWithBedrockWorkflow,
  shutdownRespan,
  withTimeout,
} from "./_shared.js";

const workflowName = "aws_bedrock.expected_error.workflow";
const respan = createRespan();
const bedrock = createBedrockClient();

try {
  let errorMessage = "";
  await withTimeout(
    runWithBedrockWorkflow(respan, workflowName, async () => {
      try {
        await bedrock.send(
          new ConverseCommand({
            modelId: DEFAULT_CONVERSE_MODEL,
            messages: [
              {
                role: "user",
                content: [{ text: "Trigger the expected error path." }],
              },
            ],
          }),
        );
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
  bedrock.destroy();
  await shutdownRespan(respan);
}
