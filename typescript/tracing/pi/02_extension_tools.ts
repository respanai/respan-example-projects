import { finish, isDirect } from "./_shared.ts";
import { assert, scenario, byType } from "./_shared.ts";
export async function main() {
  const vector = Array.from({ length: 5001 }, (_, index) => index / 5001);
  const output = {
    content: [{ type: "text", text: "native tool output" }],
    details: { vector, enabled: false, count: 0, empty: "", nullable: null },
    structuredContent: { accepted: false },
  };
  const tool = {
    name: "inspect",
    label: "Inspect",
    description: "Complete schema",
    parameters: {
      type: "object",
      properties: {
        value: { type: "integer", description: "schema".repeat(5000) },
      },
      required: ["value"],
    },
    async execute() {
      return output;
    },
  };
  const history = Array.from({ length: 75 }, (_, index) => ({
    role: "user",
    content: `native history ${index}`,
    timestamp: index + 1,
  }));
  const result = await scenario("extension-tools", {
    extension: true,
    tools: [tool],
    history,
    responses: [
      {
        tools: [
          { id: "native-call-1", name: "inspect", arguments: { value: 0 } },
        ],
      },
      { text: "tool completed" },
    ],
  });
  const execution = byType(result.spans, "tool")[0];
  assert.equal(execution.attributes["gen_ai.tool.call.id"], "native-call-1");
  assert.deepEqual(
    JSON.parse(execution.attributes["traceloop.entity.output"]),
    output,
  );
  assert.equal(result.spans.length, 4);
}

if (isDirect(import.meta.url)) {
  try {
    await main();
  } finally {
    await finish();
  }
}
