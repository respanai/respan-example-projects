import assert from "node:assert/strict";
import { context, trace } from "@opentelemetry/api";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";
import { CallToolRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import { CONTEXT_KEY_ALLOW_TRACE_CONTENT } from "@traceloop/ai-semantic-conventions";
import {
  createRespan,
  finish,
  runWithExampleTrace,
  attributes,
  exportedSpans,
} from "./_shared.js";
const name = "TypeScript MCP Privacy And Controlled Errors Example";
const respan = await createRespan("typescript-mcp-privacy");
await respan.initialize();
try {
  await runWithExampleTrace(respan, name, async () => {
    const server = new Server(
      { name: "native-private-server", version: "1" },
      { capabilities: { tools: {} } },
    );
    server.setRequestHandler(CallToolRequestSchema, async (request, extra) => {
      trace
        .getSpan(context.active())
        ?.setAttribute("private.payload", "controlled secret");
      if (request.params.name === "reject")
        throw new Error("controlled private native error");
      if (request.params.name === "cancel")
        return new Promise((_resolve, reject) =>
          extra.signal.addEventListener(
            "abort",
            () => reject(new Error("controlled native abort")),
            { once: true },
          ),
        );
      return { content: [{ type: "text", text: "controlled private output" }] };
    });
    const client = new Client({ name: "native-private-client", version: "1" });
    const [a, b] = InMemoryTransport.createLinkedPair();
    await server.connect(b);
    await client.connect(a);
    try {
      await context.with(
        context.active().setValue(CONTEXT_KEY_ALLOW_TRACE_CONTENT, false),
        async () => {
          await client.callTool({
            name: "private",
            arguments: { secret: "controlled private input" },
          });
          await assert.rejects(
            client.callTool({ name: "reject", arguments: {} }),
            /controlled private native error/,
          );
          const controller = new AbortController();
          const pending = client.callTool(
            { name: "cancel", arguments: {} },
            undefined,
            { signal: controller.signal },
          );
          controller.abort(new Error("controlled native cancellation"));
          await assert.rejects(pending, /controlled native cancellation/);
          await new Promise((resolve) => setImmediate(resolve));
        },
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
)
  for (const span of exportedSpans()) {
    const attrs = attributes(span);
    if (attrs["mcp.method"] !== "tools/call") continue;
    assert.equal(attrs["traceloop.entity.input"], undefined);
    assert.equal(attrs["traceloop.entity.output"], undefined);
    assert.equal(attrs["private.payload"], undefined);
    assert.equal(span.status?.message, undefined);
    assert.ok(!span.events?.length);
  }
