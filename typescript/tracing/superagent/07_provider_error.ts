import assert from "node:assert/strict";
import { runExample, MODEL } from "./_shared.js";
await runExample("error", async ({ client, fixture }) => {
  if (!fixture)
    throw new Error("The controlled error example requires fixture mode");
  const original = new Error("controlled native provider failure");
  fixture.plan.fail = original;
  await assert.rejects(
    client.guard({ input: "controlled error", model: MODEL, chunkSize: 0 }),
    (e) => e === original,
  );
  return { handled: true };
});
