import { InvokeModelCommand } from "@aws-sdk/client-bedrock-runtime";
import {
  createBedrockClient,
  createRespan,
  decodeBody,
  DEFAULT_INVOKE_MODEL,
  logExampleResult,
  runWithBedrockWorkflow,
  shutdownRespan,
  withTimeout,
} from "./_shared.js";

const workflowName = "aws_bedrock.invoke_model.workflow";
const respan = createRespan();
const bedrock = createBedrockClient();

try {
  const result = await withTimeout(
    runWithBedrockWorkflow(respan, workflowName, async () => {
      const response = await bedrock.send(
        new InvokeModelCommand({
          modelId: DEFAULT_INVOKE_MODEL,
          contentType: "application/json",
          accept: "application/json",
          body: JSON.stringify({
            anthropic_version: "bedrock-2023-05-31",
            max_tokens: 128,
            system: "Answer with one sentence.",
            messages: [
              {
                role: "user",
                content: "Trace a Bedrock InvokeModel request.",
              },
            ],
          }),
        }),
      );
      const bodyText = decodeBody(response.body);
      return {
        statusCode: response.$metadata?.httpStatusCode,
        bodyPreview: bodyText.slice(0, 160),
      };
    }),
    workflowName,
  );

  logExampleResult(workflowName, {
    expected:
      "one chat span with InvokeModel request body, parsed response body, and usage tokens",
    actual: result,
  });
} finally {
  bedrock.destroy();
  await shutdownRespan(respan);
}
