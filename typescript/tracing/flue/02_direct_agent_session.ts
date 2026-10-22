import assert from "node:assert/strict";
import { runNativeExample, shutdownNativeExamples } from "./_shared.js";

await runNativeExample(
  "Flue Native Session Continuation",
  { tool: true },
  async (native) => {
    assert.equal(
      (await native.prompt("Use the actual native tool.")).text,
      "native answer",
    );
    assert.equal(
      (await native.prompt("Continue with existing history.")).text,
      "native answer",
    );
    assert.equal(native.requests.length, 3);
    assert.ok(
      native.requests[2].messages.some(
        (message: any) => message.role === "tool",
      ),
    );
    assert.equal(native.calls.length, 1);
  },
);

await runNativeExample(
  "Flue Native Delegated Task",
  { delegate: true },
  async (native) => {
    assert.equal((await native.prompt()).text, "native answer");
    assert.equal(native.requests.length, 3);
    assert.ok(native.events.some((event: any) => event.type === "task_start"));
  },
);
await runNativeExample(
  "Flue Native Explicit Compaction",
  { compaction: true },
  async (native) => {
    await native.prompt("Create actual native history.");
    await native.prompt("Continue actual native history.");
    await native.session.compact();
    assert.ok(
      native.events.some((event: any) => event.type === "compaction_start"),
    );
  },
);

await shutdownNativeExamples();
