import {
  ConverseStreamCommand,
  InvokeModelWithResponseStreamCommand,
} from "@aws-sdk/client-bedrock-runtime";
import {
  collectConverseStreamText,
  collectInvokeStreamText,
  createBedrockClient,
  createRespan,
  DEFAULT_CONVERSE_MODEL,
  DEFAULT_INVOKE_MODEL,
  logExampleResult,
  runWithBedrockWorkflow,
  shutdownRespan,
  withTimeout,
} from "./_shared.js";

const workflowName = "aws_bedrock.streaming.workflow";
const respan = createRespan();
const bedrock = createBedrockClient();

try {
  const result = await withTimeout(
    runWithBedrockWorkflow(respan, workflowName, async () => {
      const converseStream = await bedrock.send(
        new ConverseStreamCommand({
          modelId: DEFAULT_CONVERSE_MODEL,
          messages: [
            {
              role: "user",
              content: [{ text: "Stream a short Bedrock response." }],
            },
          ],
          toolConfig: {
            tools: [
              {
                toolSpec: {
                  name: "get_city_weather",
                  inputSchema: { json: { type: "object" } },
                },
              },
            ],
          },
        }),
      );
      const converseText = await collectConverseStreamText(
        converseStream.stream,
      );

      const invokeStream = await bedrock.send(
        new InvokeModelWithResponseStreamCommand({
          modelId: DEFAULT_INVOKE_MODEL,
          contentType: "application/json",
          accept: "application/json",
          body: JSON.stringify({
            anthropic_version: "bedrock-2023-05-31",
            max_tokens: 128,
            messages: [
              {
                role: "user",
                content: "Stream a Bedrock InvokeModel response.",
              },
            ],
          }),
        }),
      );
      const invokeText = await collectInvokeStreamText(invokeStream.body);

      return {
        converseText,
        invokeText,
      };
    }),
    workflowName,
  );

  logExampleResult(workflowName, {
    expected:
      "two chat spans, one for ConverseStream and one for InvokeModelWithResponseStream, emitted after stream consumption",
    actual: result,
  });
} finally {
  bedrock.destroy();
  await shutdownRespan(respan);
}
