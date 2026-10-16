import assert from "node:assert/strict";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";
import {
  CreateMessageRequestSchema,
  ElicitRequestSchema,
  ListRootsRequestSchema,
  LoggingMessageNotificationSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { createRespan, finish, runWithExampleTrace } from "./_shared.js";
const name = "TypeScript MCP Protocol Callbacks Example";
const respan = await createRespan("typescript-mcp-protocol");
await respan.initialize();
try {
  await runWithExampleTrace(respan, name, async () => {
    const server = new Server(
      { name: "native-protocol-server", version: "1" },
      { capabilities: { logging: {} } },
    );
    const client = new Client(
      { name: "native-protocol-client", version: "1" },
      {
        capabilities: {
          sampling: {},
          elicitation: { form: {} },
          roots: { listChanged: true },
        },
      },
    );
    client.setRequestHandler(CreateMessageRequestSchema, async () => ({
      role: "assistant",
      model: "client-controlled-model",
      content: { type: "text", text: "Native client sampling response" },
    }));
    client.setRequestHandler(ElicitRequestSchema, async () => ({
      action: "accept",
      content: { approved: false, count: 0 },
    }));
    client.setRequestHandler(ListRootsRequestSchema, async () => ({
      roots: [
        { uri: "file:///controlled-fixture", name: "controlled fixture" },
      ],
    }));
    let loggingCount = 0;
    client.setNotificationHandler(LoggingMessageNotificationSchema, () => {
      loggingCount++;
    });
    const [a, b] = InMemoryTransport.createLinkedPair();
    await server.connect(b);
    await client.connect(a);
    try {
      const sampling = await server.createMessage({
        messages: [
          {
            role: "user",
            content: { type: "text", text: "Controlled MCP sampling request" },
          },
        ],
        maxTokens: 10,
      });
      assert.equal(sampling.model, "client-controlled-model");
      const elicitation = await server.elicitInput({
        message: "Controlled MCP elicitation",
        requestedSchema: {
          type: "object",
          properties: {
            approved: { type: "boolean" },
            count: { type: "number" },
          },
        },
      });
      assert.equal(elicitation.content?.approved, false);
      assert.equal((await server.listRoots()).roots.length, 1);
      await server.sendLoggingMessage({
        level: "info",
        data: { count: 0, flag: false },
      });
      await new Promise((resolve) => setImmediate(resolve));
      assert.equal(loggingCount, 1);
    } finally {
      await client.close();
      await server.close();
    }
  });
} finally {
  await finish(respan, name);
}
