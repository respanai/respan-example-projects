import assert from "node:assert/strict";
import { tmpdir } from "node:os";
import { mkdtemp, rm } from "node:fs/promises";
import { join } from "node:path";
import { createRuntime, shutdownRuntime } from "./_runtime.js";
import { createPrewarmFixture } from "./_prewarm_fixture.js";

const runtime = await createRuntime("claude-agent-sdk-prewarm");
const directory = await mkdtemp(join(tmpdir(), "respan-prewarm-"));
const live = process.env.CLAUDE_PREWARM_LIVE === "1";

try {
  for (const scenario of live ? ["live"] : ["tool-success", "tool-failure"]) {
    await runtime.respan.withWorkflow({
      name: "claude_agent_sdk_prewarm.workflow",
      associationProperties: { run_id: runtime.runId, scenario, example: "claude-agent-sdk" },
    }, async () => {
      let hooksObserved = 0;
      const fixture = createPrewarmFixture(scenario === "tool-failure");
      const spare = await runtime.prewarm({
        initializeTimeoutMs: 30_000,
        options: {
          ...runtime.options,
          cwd: directory,
          settingSources: [],
          permissionMode: "default",
          tools: [],
          maxTurns: 1,
          persistSession: false,
          ...(live ? {} : { spawnClaudeCodeProcess: () => fixture }),
          hooks: { PreToolUse: [{ hooks: [async () => { hooksObserved++; return {}; }] }] },
        },
      });
      try {
        const query = spare.claim({
          prompt: "Reply with exactly: prewarm tracing works.",
          options: { cwd: directory, model: "claude-sonnet-4-6" },
        });
        assert.equal(typeof query.next, "function");
        assert.equal("then" in query, false);
        await spare.claimed;
        let foundResult = false;
        for await (const message of query) {
          if (message.type === "result") {
            foundResult = true;
            assert.equal(message.is_error, false);
            console.log(JSON.stringify({ runId: runtime.runId, scenario, subtype: message.subtype }));
            break;
          }
        }
        assert.ok(foundResult);
        if (!live) assert.equal(hooksObserved, 1);
      } finally {
        spare.close();
      }
    });
  }
} finally {
  await shutdownRuntime(runtime);
  await rm(directory, { recursive: true, force: true });
}
