import assert from "node:assert/strict";
import { runExample, MODEL } from "./_shared.js";
const vector = Array.from({ length: 5001 }, (_, i) => i / 5001);
const spans = await runExample("large", async ({ client, fixture }) => {
  if (!fixture) throw new Error("The payload assertions require fixture mode");
  fixture.plan.extra = {
    vector,
    tail: { false: false, zero: 0, empty: "", nil: null },
  };
  return client.guard({
    input: "controlled long input ".repeat(6000),
    model: MODEL,
    chunkSize: 0,
  });
});
const chat = spans.find(
  (s) => s.attributes["respan.entity.log_type"] === "chat",
);
const body = JSON.parse(
  JSON.parse(chat.attributes["traceloop.entity.output"])[0].content,
);
assert.deepEqual(body.vector, vector);
assert.deepEqual(body.tail, { false: false, zero: 0, empty: "", nil: null });
