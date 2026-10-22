import type { Respan } from "@respan/respan";
import { withSpan, getLLMAttributes } from "@arizeai/openinference-core";
import { OpenInferenceSpanKind } from "@arizeai/openinference-semantic-conventions";
import { workflow } from "./_shared.js";
export async function run(respan: Respan) {
  const inputMessages = Array.from({ length: 80 }, (_, index) => ({
    role: "user",
    content: `fixture input ${index}`,
  }));
  const tools = Array.from({ length: 75 }, (_, index) => ({
    jsonSchema: {
      type: "function",
      function: {
        name: `lookup_${index}`,
        parameters: {
          type: "object",
          properties: { query: { type: "string" } },
        },
      },
    },
  }));
  const full = withSpan(() => ({ ok: false, count: 0, value: null }), {
    name: "full-llm",
    kind: OpenInferenceSpanKind.LLM,
    processOutput: () =>
      getLLMAttributes({
        modelName: "fixture-requested",
        requestModelName: "fixture-requested",
        responseModelName: "fixture-actual",
        provider: "openai",
        inputMessages,
        tools,
        outputMessages: [
          {
            role: "assistant",
            content: "",
            toolCalls: [
              {
                id: "fixture-call",
                function: {
                  name: "lookup_74",
                  arguments: '{"query":"fixture"}',
                },
              },
            ],
          },
        ],
        tokenCount: { prompt: 0, completion: 0, total: 0 },
        invocationParameters: { temperature: 0, top_p: 0, max_tokens: 0 },
      }),
  });
  const multimodal = withSpan(() => false, {
    name: "multimodal-llm",
    kind: OpenInferenceSpanKind.LLM,
    processOutput: () =>
      getLLMAttributes({
        modelName: "fixture-multimodal",
        inputMessages: [
          {
            role: "assistant",
            toolCalls: [
              {
                id: "history-call",
                function: { name: "old", arguments: "{}" },
              },
            ],
          },
          {
            role: "tool",
            toolCallId: "history-call",
            content: "historical result",
          },
          {
            role: "user",
            contents: [
              { type: "text", text: "Describe this image" },
              {
                type: "image",
                image: { url: "https://example.invalid/fixture.png" },
              },
            ],
          },
        ],
        outputMessages: [
          { role: "assistant", content: "fixture image answer" },
        ],
      }),
  });
  return workflow(respan, "full-llm", () => ({
    full: full(),
    multimodal: multimodal(),
  }));
}
