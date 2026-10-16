import { createServer, type Server } from "node:http";
import { writeFileSync } from "node:fs";
import assert from "node:assert/strict";
import * as MCPClientModule from "@modelcontextprotocol/sdk/client/index.js";
import * as MCPServerModule from "@modelcontextprotocol/sdk/server/index.js";
import * as MCPHighServerModule from "@modelcontextprotocol/sdk/server/mcp.js";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";
import {
  McpServer,
  ResourceTemplate,
} from "@modelcontextprotocol/sdk/server/mcp.js";
import { Respan } from "@respan/respan";
import {
  MCPInstrumentor,
  type MCPInstrumentorOptions,
} from "@respan/instrumentation-mcp";
import * as z from "zod/v4";

export const RUN_ID =
  process.env.RESPAN_EXAMPLE_RUN_ID ?? `mcp-ts-${Date.now()}`;
export const capture: Array<Record<string, any>> = [];
let collector: Server | undefined;

export async function createRespan(
  appName: string,
  options: MCPInstrumentorOptions = {},
): Promise<Respan> {
  const remote =
    process.env.RESPAN_EXPORT === "true" ||
    process.env.RESPAN_EXAMPLE_EXPORT === "true";
  let baseURL: string;
  if (remote) {
    if (!process.env.RESPAN_API_KEY)
      throw new Error("Explicit export requires RESPAN_API_KEY.");
    baseURL = process.env.RESPAN_BASE_URL ?? "https://api.respan.ai";
  } else {
    collector = createServer(async (request, response) => {
      const chunks: Buffer[] = [];
      for await (const chunk of request) chunks.push(Buffer.from(chunk));
      const body = JSON.parse(Buffer.concat(chunks).toString("utf8"));
      capture.push(body);
      response.writeHead(200, { "content-type": "application/json" });
      response.end("{}");
    });
    await new Promise<void>((resolve) =>
      collector!.listen(0, "127.0.0.1", resolve),
    );
    const address = collector.address();
    if (!address || typeof address === "string")
      throw new Error("Local collector did not bind.");
    baseURL = `http://127.0.0.1:${address.port}`;
  }
  return new Respan({
    apiKey: remote ? process.env.RESPAN_API_KEY : "local-mcp-validation",
    baseURL,
    appName,
    instrumentations: [
      new MCPInstrumentor({
        clientModule: MCPClientModule,
        serverModule: { ...MCPServerModule, ...MCPHighServerModule },
        ...options,
      }),
    ],
    silenceInitializationMessage: true,
  });
}

export async function runWithExampleTrace<T>(
  respan: Respan,
  workflowName: string,
  fn: () => Promise<T>,
): Promise<T> {
  return respan.propagateAttributes(
    {
      custom_identifier: RUN_ID,
      thread_identifier: `mcp-thread-${RUN_ID}`,
      trace_group_identifier: workflowName,
      metadata: { example: "typescript-mcp", run_id: RUN_ID },
    },
    () => respan.withWorkflow({ name: workflowName }, fn),
  );
}
export function exportedSpans(): Array<Record<string, any>> {
  return capture.flatMap((body) =>
    (body.resourceSpans ?? []).flatMap((resource: any) =>
      (resource.scopeSpans ?? []).flatMap((scope: any) => scope.spans ?? []),
    ),
  );
}
export function attributes(span: Record<string, any>): Record<string, any> {
  return Object.fromEntries(
    (span.attributes ?? []).map((attribute: any) => [
      attribute.key,
      attribute.value?.stringValue ??
        attribute.value?.intValue ??
        attribute.value?.boolValue ??
        attribute.value?.doubleValue,
    ]),
  );
}
export async function finish(
  respan: Respan,
  workflowName: string,
): Promise<void> {
  await respan.shutdown();
  if (collector) {
    const spans = exportedSpans();
    assert.ok(
      spans.length > 0,
      "Released public runtime must export native spans to local collector",
    );
    for (const span of spans)
      assert.ok(
        !Object.keys(attributes(span)).some((key) =>
          key.startsWith("respan.internal."),
        ),
      );
    if (process.env.RESPAN_EXAMPLE_CAPTURE_PATH)
      writeFileSync(
        process.env.RESPAN_EXAMPLE_CAPTURE_PATH,
        JSON.stringify(
          { runId: RUN_ID, workflowName, payloads: capture },
          null,
          2,
        ),
      );
    console.log(
      JSON.stringify({
        workflowName,
        runId: RUN_ID,
        spans: spans.length,
        nativeTraceIds: [...new Set(spans.map((span) => span.traceId))],
      }),
    );
    await new Promise<void>((resolve, reject) =>
      collector!.close((error) => (error ? reject(error) : resolve())),
    );
  } else
    console.log(
      JSON.stringify({ workflowName, runId: RUN_ID, exported: true }),
    );
}
export function logExampleResult(
  workflowName: string,
  details: Record<string, unknown>,
): void {
  console.log(JSON.stringify({ workflowName, runId: RUN_ID, ...details }));
}

export async function createDemoMcpEnvironment() {
  const server = new McpServer({
    name: "respan-demo-mcp-server",
    version: "1.0.0",
  });
  server.registerTool(
    "summarize_city",
    { description: "Return a city summary", inputSchema: { city: z.string() } },
    async ({ city }) => ({
      content: [{ type: "text", text: `${city}: museums and transit.` }],
      structuredContent: { city, zero: 0, flag: false, empty: "" },
    }),
  );
  server.registerResource(
    "city_notes",
    "demo://city/paris",
    { mimeType: "text/plain" },
    async (uri) => ({
      contents: [
        { uri: uri.href, mimeType: "text/plain", text: "Native resource text" },
      ],
    }),
  );
  server.registerResource(
    "city_template",
    new ResourceTemplate("demo://city/{city}", { list: undefined }),
    { mimeType: "text/plain" },
    async (uri) => ({
      contents: [{ uri: uri.href, text: "Native dynamic resource" }],
    }),
  );
  server.registerPrompt(
    "city_brief",
    { argsSchema: { city: z.string() } },
    ({ city }) => ({
      messages: [
        { role: "user", content: { type: "text", text: `Brief for ${city}` } },
      ],
    }),
  );
  const client = new Client({
    name: "respan-demo-mcp-client",
    version: "1.0.0",
  });
  const [a, b] = InMemoryTransport.createLinkedPair();
  await server.connect(b);
  await client.connect(a);
  return {
    client,
    server,
    async close() {
      await client.close();
      await server.close();
    },
  };
}
