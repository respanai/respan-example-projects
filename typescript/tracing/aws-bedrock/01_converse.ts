import { ConverseCommand } from "@aws-sdk/client-bedrock-runtime";
import {
  createBedrockClient,
  createRespan,
  DEFAULT_CONVERSE_MODEL,
  logExampleResult,
  runWithBedrockWorkflow,
  shutdownRespan,
  textFromConverseResponse,
  withTimeout,
} from "./_shared.js";

const workflowName = "aws_bedrock.converse.workflow";
const respan = createRespan();
const bedrock = createBedrockClient();

try {
  const result = await withTimeout(
    runWithBedrockWorkflow(respan, workflowName, async () => {
      const response = await bedrock.send(
        new ConverseCommand({
          modelId: DEFAULT_CONVERSE_MODEL,
          system: [{ text: "Answer with one concise sentence." }],
          messages: [
            {
              role: "user",
              content: [{ text: "What does the Bedrock Converse API do?" }],
            },
          ],
          toolConfig: {
            tools: [
              {
                toolSpec: {
                  name: "get_city_weather",
                  description: "Return a deterministic city weather summary.",
                  inputSchema: {
                    json: {
                      type: "object",
                      properties: { city: { type: "string" } },
                      required: ["city"],
                    },
                  },
                },
              },
            ],
          },
        }),
      );
      return {
        output: textFromConverseResponse(response),
        statusCode: response.$metadata?.httpStatusCode,
      };
    }),
    workflowName,
  );

  logExampleResult(workflowName, {
    expected:
      "one chat span with Converse input messages, tool definitions, output, tool_calls, and usage tokens",
    actual: result,
  });
} finally {
  bedrock.destroy();
  await shutdownRespan(respan);
}
