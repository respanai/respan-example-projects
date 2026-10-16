import assert from "node:assert/strict";
import { runExample, MODEL } from "./_shared.js";
await runExample("redact", async ({ client, fixture }) => {
  if (fixture) fixture.plan.redact = true;
  const result = await client.redact({
    input: "controlled email person@example.invalid",
    model: MODEL,
    rewrite: false,
    entities: ["email addresses"],
  });
  if (fixture) assert.equal(result.redacted, "controlled contact removed");
  return result;
});
