import { defineAgent } from "eve";
import { mockModel } from "eve/evals";

export default defineAgent({
  modelContextWindowTokens: 1_000_000,
  model: mockModel({
    provider: "respan-example",
    modelId: "eve-deterministic-root",
    respond({ lastUserMessage, toolResults, messages }) {
      if (
        messages.some((message) =>
          message.text.includes("RESEARCH_MARKER=eve-lineage-ok"),
        )
      ) {
        return {
          text: "Delegated result: RESEARCH_MARKER=eve-lineage-ok",
          usage: { inputTokens: 41, outputTokens: 15 },
        };
      }
      if (toolResults.at(-1)?.name === "profile__save_memory")
        return {
          text: "Memory saved",
          usage: { inputTokens: 5, outputTokens: 2 },
        };
      if (lastUserMessage?.includes("RESPAN_EVE_MEMORY_SAVE"))
        return {
          toolCalls: [
            {
              id: "memory-call-1",
              name: "profile__save_memory",
              input: { text: "EVE_MEMORY_NOTE=synthetic-recall-ok" },
            },
          ],
          usage: { inputTokens: 5, outputTokens: 1 },
        };
      if (lastUserMessage?.includes("RESPAN_EVE_MEMORY_RECALL"))
        return {
          text:
            "Memory recall verified: " +
            messages.some((message) =>
              message.text.includes("EVE_MEMORY_NOTE=synthetic-recall-ok"),
            ),
          usage: { inputTokens: 8, outputTokens: 2 },
        };
      if (toolResults.at(-1)?.name === "echo_value") {
        return {
          text: "Value: " + JSON.stringify(toolResults.at(-1)?.output),
          usage: { inputTokens: 0, outputTokens: 3 },
        };
      }
      if (toolResults.at(-1)?.name === "fail_tool") {
        return {
          text: "Synthetic error observed",
          usage: { inputTokens: 11, outputTokens: 4 },
        };
      }
      if (lastUserMessage?.includes("RESPAN_EVE_VALUE_")) {
        const value = lastUserMessage.includes("FALSE")
          ? false
          : lastUserMessage.includes("ZERO")
            ? 0
            : "";
        return {
          toolCalls: [
            {
              id: "value-call-" + typeof value,
              name: "echo_value",
              input: { value },
            },
          ],
          usage: { inputTokens: 0, outputTokens: 1 },
        };
      }
      if (lastUserMessage?.includes("RESPAN_EVE_ERROR")) {
        return {
          toolCalls: [{ id: "error-call-1", name: "fail_tool", input: {} }],
          usage: { inputTokens: 7, outputTokens: 2 },
        };
      }
      if (lastUserMessage?.includes("RESPAN_EVE_LARGE")) {
        return {
          text: "LARGE_BEGIN_" + "x".repeat(80000) + "_LARGE_END",
          usage: { inputTokens: 12, outputTokens: 0 },
        };
      }
      if (lastUserMessage?.includes("RESPAN_EVE_CONTINUE")) {
        return {
          text: "Continuation preserved history",
          usage: { inputTokens: 17, outputTokens: 4 },
        };
      }

      if (toolResults.length > 0) {
        const result = toolResults.at(-1);
        if (result?.name === "get_weather") {
          return {
            text: "Weather result: " + JSON.stringify(result.output),
            usage: { inputTokens: 31, outputTokens: 11 },
          };
        }
        if (result?.name === "researcher") {
          return {
            text: "Delegated result: " + JSON.stringify(result.output),
            usage: { inputTokens: 37, outputTokens: 13 },
          };
        }
      }

      if (lastUserMessage?.includes("RESPAN_EVE_TOOL")) {
        return {
          toolCalls: [
            {
              id: "weather-call-1",
              name: "get_weather",
              input: { city: "Paris" },
            },
          ],
          usage: { inputTokens: 23, outputTokens: 7 },
        };
      }

      if (lastUserMessage?.includes("RESPAN_EVE_SUBAGENT")) {
        return {
          toolCalls: [
            {
              id: "research-call-1",
              name: "researcher",
              input: {
                message: "Return the deterministic instrumentation marker.",
              },
            },
          ],
          usage: { inputTokens: 29, outputTokens: 8 },
        };
      }

      return {
        text: "Eve basic instrumentation example completed.",
        usage: { inputTokens: 17, outputTokens: 9 },
      };
    },
  }),
});
