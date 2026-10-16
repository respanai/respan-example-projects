import assert from "node:assert/strict";
import {
  ConverseCommand,
  ConverseStreamCommand,
  InvokeModelCommand,
} from "@aws-sdk/client-bedrock-runtime";
import {
  createBedrockClient,
  createRespan,
  DEFAULT_CONVERSE_MODEL,
  exampleMode,
  logExampleResult,
  runWithBedrockWorkflow,
  shutdownRespan,
} from "./_shared.js";

const workflowName = "aws_bedrock.native_features.workflow";
const respan = createRespan();
const bedrock = createBedrockClient();
try {
  const actual = await runWithBedrockWorkflow(
    respan,
    workflowName,
    async () => {
      const response = await bedrock.send(
        new ConverseCommand({
          modelId: DEFAULT_CONVERSE_MODEL,
          ...(exampleMode() === "fixture"
            ? {
                outputConfig: {
                  textFormat: {
                    type: "json_schema" as const,
                    structure: {
                      jsonSchema: {
                        name: "fixture",
                        schema: '{"type":"object"}',
                      },
                    },
                  },
                  effort: "high",
                },
                requestMetadata: { fixture: "native-features" },
              }
            : {}),
          messages: Array.from({ length: 76 }, (_, index) => ({
            role: "user" as const,
            content: [
              { text: `Native message ${index}` },
              ...(exampleMode() === "fixture" && index === 0
                ? [
                    {
                      image: {
                        format: "png" as const,
                        source: { bytes: new Uint8Array([0, 1, 2, 255]) },
                      },
                    },
                    {
                      audio: {
                        format: "wav" as const,
                        source: { bytes: new Uint8Array([0, 2, 0, 3]) },
                      },
                    },
                    {
                      cachePoint: {
                        type: "default" as const,
                        ttl: "1h" as const,
                      },
                    },
                  ]
                : []),
            ],
          })),
          toolConfig: {
            tools: Array.from({ length: 76 }, (_, index) => ({
              toolSpec: {
                name: `tool_${index}`,
                inputSchema: {
                  json: {
                    type: "object",
                    properties: {
                      enabled: { const: false },
                      count: { const: 0 },
                      empty: { const: "" },
                      nil: { const: null },
                    },
                  },
                },
              },
            })),
          },
        }),
      );
      const callbackText = await new Promise<string>((resolve, reject) => {
        const returned = bedrock.send(
          new ConverseCommand({
            modelId: DEFAULT_CONVERSE_MODEL,
            messages: [
              { role: "user", content: [{ text: "Native callback" }] },
            ],
          }),
          (error, result) => {
            if (error) reject(error);
            else resolve(result?.output?.message?.content?.[0]?.text ?? "");
          },
        );
        assert.equal(returned, undefined);
      });
      const stream = await bedrock.send(
        new ConverseStreamCommand({
          modelId: DEFAULT_CONVERSE_MODEL,
          messages: [
            { role: "user", content: [{ text: "Native early stream return" }] },
          ],
        }),
      );
      if (!stream.stream) throw new Error("Missing native stream");
      for await (const _event of stream.stream) break;
      let dimensions: number | undefined;
      if (exampleMode() === "fixture") {
        const vector = await bedrock.send(
          new InvokeModelCommand({
            modelId: "amazon.titan-embed-text-v2:0",
            contentType: "application/json",
            body: '{"inputText":"Native embedding fixture"}',
          }),
        );
        dimensions = JSON.parse(new TextDecoder().decode(vector.body)).embedding
          .length;
        assert.equal(dimensions, 5001);
      }
      return {
        responseRole: response.output?.message?.role,
        callbackText,
        dimensions,
      };
    },
  );
  logExampleResult(workflowName, {
    expected:
      "complete native messages/tools, structured output configuration, multimodal input, callback, early return, and fixture embedding vector",
    actual,
  });
} finally {
  bedrock.destroy();
  await shutdownRespan(respan);
}
