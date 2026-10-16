import { assert, runScenario } from "./_shared.js";

await runScenario("task-tool-and-vector", async (logger) =>
  logger.traced(
    async (parent) => {
      const tool = await parent.traced(
        async (span) => {
          const result = { city: "Kyoto", value: 0 };
          span.log({
            output: result,
            scores: { useful: 0 },
            tags: ["tool", "fixture"],
          });
          return result;
        },
        {
          name: "lookup_city_notes",
          type: "tool",
          event: {
            input: { city: "Kyoto", value: 0 },
            metadata: { tool_call_id: "call_fixture" },
          },
        },
      );
      assert.equal(tool.value, 0);
      const vector = Array.from({ length: 5001 }, (_, index) => index / 10);
      await parent.traced(async (span) => span.log({ output: vector }), {
        name: "native-embedding",
        spanAttributes: { type: "embedding" },
        event: {
          input: ["Kyoto"],
          metadata: { model: "fixture-embedding" },
          metrics: { prompt_tokens: 0, tokens: 0 },
        },
      });
      for (const value of [false, 0, "", null, [], {}])
        await parent.traced(
          async (span) => span.log({ input: value, output: value }),
          { name: "native-scalar", type: "task" },
        );
      return { tool, vectorLength: vector.length, scalarCases: 6 };
    },
    {
      name: "city-agent",
      spanAttributes: { type: "agent" },
      event: {
        input: { city: "Kyoto" },
        metadata: { feature: "native-agent" },
      },
    },
  ),
);
