import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import assert from "node:assert/strict";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import {
  createRespan,
  finish,
  runWithExampleTrace,
  attributes,
  exportedSpans,
} from "./_shared.js";
const name = "TypeScript MCP Full Content Example";
const respan = await createRespan("typescript-mcp-full-content");
await respan.initialize();
const text = "native-full-content-".repeat(2500);
try {
  await runWithExampleTrace(respan, name, async () => {
    const server = new Server(
      { name: "native-content-server", version: "1" },
      { capabilities: { tools: {} } },
    );
    server.setRequestHandler(ListToolsRequestSchema, async (request) => ({
      tools: Array.from({ length: 80 }, (_, i) => ({
        name: `native_tool_${i}`,
        description: `Native definition ${i}`,
        inputSchema: { type: "object" as const },
      })),
      nextCursor: request.params?.cursor ? undefined : "native-next-page",
    }));
    server.setRequestHandler(CallToolRequestSchema, async () => ({
      content: [
        { type: "text", text },
        { type: "image", data: "YmluYXJ5", mimeType: "image/png" },
      ],
      structuredContent: {
        flag: false,
        zero: 0,
        empty: "",
        null: null,
        nested: { a: { b: { c: { d: { e: { f: { g: "native deep" } } } } } } },
      },
      _meta: { controlled: true },
    }));
    const client = new Client({ name: "native-content-client", version: "1" });
    const [a, b] = InMemoryTransport.createLinkedPair();
    await server.connect(b);
    await client.connect(a);
    try {
      assert.equal(
        (await client.listTools({ cursor: "native-page-1" })).tools.length,
        80,
      );
      const result = await client.callTool({
        name: "native_full",
        arguments: {
          messages: Array.from({ length: 80 }, (_, i) => ({
            role: "user",
            content: `Native message ${i}`,
          })),
          vector: Array.from({ length: 5001 }, (_, i) => i),
          flag: false,
          zero: 0,
          empty: "",
          null: null,
        },
      });
      assert.equal(
        ((result as CallToolResult).content[0] as { text: string }).text,
        text,
      );
    } finally {
      await client.close();
      await server.close();
    }
  });
} finally {
  await finish(respan, name);
}
if (
  process.env.RESPAN_EXPORT !== "true" &&
  process.env.RESPAN_EXAMPLE_EXPORT !== "true"
) {
  const tool = exportedSpans()
    .map(attributes)
    .find((attrs) => attrs["mcp.operation"] === "client.tools/call")!;
  assert.equal(
    JSON.parse(tool["traceloop.entity.input"]).arguments.vector.length,
    5001,
  );
  assert.equal(
    JSON.parse(tool["traceloop.entity.input"]).arguments.messages.length,
    80,
  );
  assert.equal(
    JSON.parse(tool["traceloop.entity.output"]).content[0].text,
    text,
  );
  assert.equal(tool["gen_ai.tool.call.id"], undefined);
}
