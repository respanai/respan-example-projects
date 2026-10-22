import { llm } from "@livekit/agents";
import { z } from "zod";
import { agentTurn, assertCaptured, runExample } from "./_shared.js";
await runExample("TypeScript LiveKit Native Tool Results", async () => {
  const results = [];
  for (const [label, value] of Object.entries({
    structured: {
      city: "Tokyo",
      forecast: "clear",
      zero: 0,
      disabled: false,
      empty: "",
      nil: null,
    },
    zero: 0,
    disabled: false,
    empty: "",
    nil: null,
  })) {
    results.push({
      label,
      result: await agentTurn({
        tool: "native_weather",
        tools: {
          native_weather: llm.tool({
            description: "Return a native tool result.",
            parameters: z.object({ city: z.string() }),
            execute: async () => value,
          }),
        },
      }),
    });
  }
  assertCaptured(
    (span) =>
      span.attributes["respan.entity.log_type"] === "tool" &&
      span.attributes["traceloop.entity.input"].includes('"city":"Tokyo"'),
  );
  return results;
});
