import assert from "node:assert/strict";
import { BODY } from "./_native.mjs";
import { runNativeExample, shutdownNativeExamples } from "./_shared.js";

await runNativeExample(
  "Flue Native Tools and Full Payload",
  { tool: true, large: true },
  async (native) => {
    const handle = native.prompt();
    assert.equal(typeof handle.abort, "function");
    assert.ok(handle.signal instanceof AbortSignal);
    assert.equal((await handle).text, BODY);
    assert.deepEqual(native.calls[0].data, {
      flag: false,
      count: 0,
      empty: "",
    });
    assert.equal(native.calls.length, 1);
  },
);

await shutdownNativeExamples();
