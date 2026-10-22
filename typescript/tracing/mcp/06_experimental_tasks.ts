import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import assert from "node:assert/strict";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  CallToolResultSchema,
} from "@modelcontextprotocol/sdk/types.js";
import {
  InMemoryTaskStore,
  InMemoryTaskMessageQueue,
} from "@modelcontextprotocol/sdk/experimental/tasks/stores/in-memory.js";
import { createRespan, finish, runWithExampleTrace } from "./_shared.js";
const name = "TypeScript MCP Native Experimental Tasks Example";
const respan = await createRespan("typescript-mcp-tasks");
await respan.initialize();
const store = new InMemoryTaskStore();
try {
  await runWithExampleTrace(respan, name, async () => {
    const server = new Server(
      { name: "native-task-server", version: "1" },
      {
        capabilities: {
          tools: {},
          tasks: { list: {}, cancel: {}, requests: { tools: { call: {} } } },
        },
        taskStore: store,
        taskMessageQueue: new InMemoryTaskMessageQueue(),
      },
    );
    server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: "native_task",
          inputSchema: { type: "object" },
          execution: { taskSupport: "required" },
        },
      ],
    }));
    server.setRequestHandler(CallToolRequestSchema, async (_request, extra) => {
      const task = await extra.taskStore!.createTask({
        ttl: 60_000,
        pollInterval: 1,
      });
      await extra.taskStore!.storeTaskResult(task.taskId, "completed", {
        content: [{ type: "text", text: "Native task completed" }],
        structuredContent: { zero: 0 },
      });
      return { task };
    });
    const client = new Client({ name: "native-task-client", version: "1" });
    const [a, b] = InMemoryTransport.createLinkedPair();
    await server.connect(b);
    await client.connect(a);
    try {
      await client.listTools();
      const stream = client.experimental.tasks.callToolStream({
        name: "native_task",
        arguments: { flag: false },
      });
      const originalNext = stream.next;
      let taskId = "";
      for await (const message of stream) {
        if (message.type === "error") throw message.error;
        if (message.type === "taskCreated") taskId = message.task.taskId;
        if (message.type === "result")
          assert.equal(
            (message.result as CallToolResult).structuredContent?.zero,
            0,
          );
      }
      assert.equal(stream.next, originalNext);
      assert.equal(
        (await client.experimental.tasks.getTask(taskId)).status,
        "completed",
      );
      assert.equal(
        (
          await client.experimental.tasks.getTaskResult(
            taskId,
            CallToolResultSchema,
          )
        ).content[0].type,
        "text",
      );
      assert.equal(
        (await client.experimental.tasks.listTasks()).tasks.length,
        1,
      );
      const pending = await store.createTask({ ttl: 60_000 }, 9000, {
        method: "tools/call",
        params: { name: "native_task" },
      });
      assert.equal(
        (await client.experimental.tasks.cancelTask(pending.taskId)).status,
        "cancelled",
      );
    } finally {
      await client.close();
      await server.close();
    }
  });
} finally {
  store.cleanup();
  await finish(respan, name);
}
