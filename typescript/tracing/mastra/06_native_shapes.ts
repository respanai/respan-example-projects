import assert from "node:assert/strict";
import { SpanType } from "@mastra/core/observability";
import {
  createRuntime,
  EXAMPLE_RUN_ID,
  runWithRespanWorkflow,
} from "./_shared.js";
const { mastra, respan, observability } = createRuntime({});
await runWithRespanWorkflow(
  mastra,
  respan,
  "Mastra Native Fidelity",
  async () => {
    const instance = observability.getDefaultInstance()!;
    const messages = Array.from({ length: 80 }, (_, i) => ({
      role: "assistant" as const,
      content: [
        { type: "text" as const, text: `history ${i}` },
        {
          type: "tool-call" as const,
          toolCallId: `history-${i}`,
          toolName: "weather",
          input: { city: "Tokyo" },
        },
      ],
    }));
    const parameters = {
      type: "object",
      properties: Object.fromEntries(
        Array.from({ length: 80 }, (_, i) => [`field${i}`, { type: "string" }]),
      ),
    };
    const model = instance.startSpan({
      name: "native.fidelity",
      type: SpanType.MODEL_GENERATION,
      input: { messages },
      attributes: {
        model: "controlled-model",
        provider: "controlled",
        tools: [
          {
            type: "function",
            name: "weather",
            description: "Full native JSON schema",
            parameters,
          },
        ],
      },
    });
    model.end({
      output: {
        text: "",
        object: { empty: "", nil: null, no: false, zero: 0 },
        toolCalls: [
          {
            toolCallId: "native-call",
            toolName: "weather",
            input: { city: "Tokyo" },
          },
        ],
      },
    });
    const vector = Array.from({ length: 5003 }, (_, i) => i / 5003);
    const embedding = instance.startSpan({
      name: "native.embedding",
      type: SpanType.RAG_EMBEDDING,
      input: ["controlled"],
      attributes: {
        model: "controlled-embedding",
        provider: "controlled",
        dimensions: 5003,
      },
    });
    embedding.end({ output: { vectors: [vector] } });
    assert.equal(vector.length, 5003);
  },
);
console.log(
  JSON.stringify({
    runId: EXAMPLE_RUN_ID,
    scenario: "fidelity",
    messages: 80,
    schemaFields: 80,
    dimensions: 5003,
  }),
);
