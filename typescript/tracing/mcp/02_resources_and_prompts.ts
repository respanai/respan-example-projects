import assert from "node:assert/strict";
import {
  createDemoMcpEnvironment,
  createRespan,
  finish,
  runWithExampleTrace,
} from "./_shared.js";
const name = "TypeScript MCP Resources And Prompts Example";
const respan = await createRespan("typescript-mcp-resources-prompts");
await respan.initialize();
try {
  await runWithExampleTrace(respan, name, async () => {
    const env = await createDemoMcpEnvironment();
    try {
      assert.equal((await env.client.listResources()).resources.length, 1);
      assert.equal(
        (await env.client.listResourceTemplates()).resourceTemplates.length,
        1,
      );
      assert.equal(
        (await env.client.readResource({ uri: "demo://city/paris" })).contents
          .length,
        1,
      );
      assert.equal((await env.client.listPrompts()).prompts.length, 1);
      assert.equal(
        (
          await env.client.getPrompt({
            name: "city_brief",
            arguments: { city: "Paris" },
          })
        ).messages[0].role,
        "user",
      );
    } finally {
      await env.close();
    }
  });
} finally {
  await finish(respan, name);
}
