import { finish, isDirect } from "./_shared.ts";
import { assert, scenario, byType } from "./_shared.ts";
export async function main() {
  let start!: () => void;
  const started = new Promise<void>((resolve) => {
    start = resolve;
  });
  let release!: () => void;
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  const tool = {
    name: "wait",
    label: "Wait",
    description: "Controlled boundary",
    parameters: { type: "object", properties: {} },
    async execute() {
      start();
      await gate;
      return { content: [{ type: "text", text: "ready" }], details: {} };
    },
  };
  await scenario(
    "native-steering",
    {
      tools: [tool],
      responses: [
        { tools: [{ id: "steer-call", name: "wait", arguments: {} }] },
        { text: "steered answer" },
      ],
    },
    {},
    async (fixture, spans) => {
      const pending = fixture.session.prompt("start native steering");
      await started;
      await fixture.session.steer("controlled steered message");
      release();
      await pending;
      assert.ok(
        byType(spans, "task").some((span) => span.name.includes("steer")),
      );
      assert.equal(byType(spans, "agent").length, 1);
    },
  );
}

if (isDirect(import.meta.url)) {
  try {
    await main();
  } finally {
    await finish();
  }
}
