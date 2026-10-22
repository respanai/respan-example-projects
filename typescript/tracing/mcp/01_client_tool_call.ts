import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import assert from "node:assert/strict";
import {
  createDemoMcpEnvironment,
  createRespan,
  finish,
  runWithExampleTrace,
} from "./_shared.js";
const name = "TypeScript MCP Client Tool Example";
const respan = await createRespan("typescript-mcp-tools");
await respan.initialize();
try {
  await runWithExampleTrace(respan, name, async () => {
    const env = await createDemoMcpEnvironment();
    try {
      assert.equal(
        (await env.client.listTools()).tools[0].name,
        "summarize_city",
      );
      const result = (await env.client.callTool({
        name: "summarize_city",
        arguments: { city: "Paris" },
      })) as CallToolResult;
      assert.equal(result.structuredContent?.zero, 0);
      assert.equal(result.structuredContent?.flag, false);
    } finally {
      await env.close();
    }
  });
} finally {
  await finish(respan, name);
}
