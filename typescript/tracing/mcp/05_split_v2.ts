import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import assert from "node:assert/strict";
import * as clientModule from "@modelcontextprotocol/client";
import * as serverModule from "@modelcontextprotocol/server";
import { createRespan, finish, runWithExampleTrace } from "./_shared.js";
const name = "TypeScript MCP Split V2 Example";
const respan = await createRespan("typescript-mcp-v2", {
  clientModule,
  serverModule,
});
await respan.initialize();
try {
  await runWithExampleTrace(respan, name, async () => {
    const server = new serverModule.McpServer({
      name: "native-v2-server",
      version: "1",
    });
    server.registerTool(
      "v2_tool",
      { description: "Native v2 structured output" },
      async () => ({
        content: [{ type: "text", text: "Native v2 result" }],
        structuredContent: { flag: false, zero: 0 },
      }),
    );
    const client = new clientModule.Client({
      name: "native-v2-client",
      version: "1",
    });
    const [a, b] = clientModule.InMemoryTransport.createLinkedPair();
    await server.connect(b);
    await client.connect(a);
    try {
      assert.equal((await client.listTools()).tools[0].name, "v2_tool");
      const result = (await client.callTool({
        name: "v2_tool",
        arguments: {},
      })) as CallToolResult;
      assert.equal(result.structuredContent?.zero, 0);
    } finally {
      await client.close();
      await server.close();
    }
  });
} finally {
  await finish(respan, name);
}
