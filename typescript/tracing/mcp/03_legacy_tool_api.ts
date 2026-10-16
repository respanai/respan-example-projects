import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import assert from "node:assert/strict";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { createRespan, finish, runWithExampleTrace } from "./_shared.js";
const name = "TypeScript MCP Legacy Tool API Example";
const respan = await createRespan("typescript-mcp-legacy");
await respan.initialize();
try {
  await runWithExampleTrace(respan, name, async () => {
    const server = new McpServer({
      name: "native-legacy-server",
      version: "1",
    });
    server.tool("legacy_echo", async () => ({
      content: [{ type: "text", text: "native legacy echo" }],
    }));
    const client = new Client({ name: "native-legacy-client", version: "1" });
    const [a, b] = InMemoryTransport.createLinkedPair();
    await server.connect(b);
    await client.connect(a);
    try {
      assert.equal(
        (
          (await client.callTool({
            name: "legacy_echo",
            arguments: {},
          })) as CallToolResult
        ).content[0].type,
        "text",
      );
    } finally {
      await client.close();
      await server.close();
    }
  });
} finally {
  await finish(respan, name);
}
