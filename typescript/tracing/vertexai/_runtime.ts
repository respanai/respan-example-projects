import { createServer } from "node:http";
import { gunzipSync } from "node:zlib";
import { writeFile } from "node:fs/promises";
import { context, trace } from "@opentelemetry/api";
import { ATTR_GEN_AI_TOOL_CALL_ID } from "@opentelemetry/semantic-conventions/incubating";
import { SpanAttributes } from "@traceloop/ai-semantic-conventions";
import { Respan } from "@respan/respan";
import assert from "node:assert/strict";
console.debug = () => {};
console.info = () => {};
const log = console.log.bind(console);
console.log = (...args: unknown[]) => {
  if (
    typeof args[0] !== "string" ||
    (!args[0].startsWith("[Respan]") && !args[0].startsWith("Respan tracing"))
  )
    log(...args);
};
export const RUN_ID =
  process.env.RESPAN_EXAMPLE_RUN_ID ?? `vertexai-ts-${Date.now()}`;
export const live = process.env.VERTEXAI_EXAMPLE_LIVE === "1";
export const exported = process.env.RESPAN_EXAMPLE_EXPORT === "1";
export async function setup(plugin: any, privateContent = false) {
  if (privateContent) process.env.RESPAN_TRACE_CONTENT = "false";
  const wire: any[] = [];
  const spans: any[] = [];
  let collector: ReturnType<typeof createServer> | undefined;
  let baseURL = process.env.RESPAN_BASE_URL;
  if (!exported) {
    collector = createServer(async (req, res) => {
      const chunks: Buffer[] = [];
      for await (const chunk of req) chunks.push(Buffer.from(chunk));
      let body = Buffer.concat(chunks);
      if (req.headers["content-encoding"] === "gzip") body = gunzipSync(body);
      wire.push(JSON.parse(body.toString()));
      res.writeHead(200, { "content-type": "application/json" });
      res.end("{}");
    });
    await new Promise<void>((resolve) =>
      collector!.listen(0, "127.0.0.1", resolve),
    );
    const address = collector.address();
    assert.ok(address && typeof address === "object");
    baseURL = `http://127.0.0.1:${address.port}/api`;
  }
  if (exported && !process.env.RESPAN_API_KEY)
    throw new Error("Export mode requires RESPAN_API_KEY.");
  const respan = new Respan({
    apiKey: exported ? process.env.RESPAN_API_KEY : "fixture-local-only",
    baseURL,
    appName: "vertexai-examples",
    traceContent: !privateContent,
    instrumentations: [plugin],
    silenceInitializationMessage: true,
  });
  await respan.initialize();
  respan.addProcessor({
    name: "example-capture",
    filter: () => true,
    disableBatch: true,
    exporter: {
      export(batch: any[], cb: any) {
        spans.push(...batch);
        cb({ code: 0 });
      },
      async shutdown() {},
      async forceFlush() {},
    },
  });
  return {
    respan,
    spans,
    async run(name: string, fn: () => Promise<any>) {
      return respan.propagateAttributes(
        {
          custom_identifier: RUN_ID,
          trace_group_identifier: name,
          metadata: {
            run_id: RUN_ID,
            example: "typescript-vertexai",
            scenario: name,
          },
        },
        () => respan.withWorkflow({ name }, fn),
      );
    },
    async close() {
      await respan.shutdown();
      await new Promise<void>((resolve, reject) => {
        if (!collector) return resolve();
        collector.close((error) => (error ? reject(error) : resolve()));
      });
      const records = spans.map((span) => ({
        name: span.name,
        spanId: span.spanContext().spanId,
        traceId: span.spanContext().traceId,
        parentSpanId: span.parentSpanContext?.spanId,
        attributes: span.attributes,
        status: span.status,
      }));
      if (process.env.RESPAN_EXAMPLE_CAPTURE_PATH)
        await writeFile(
          process.env.RESPAN_EXAMPLE_CAPTURE_PATH,
          JSON.stringify({ runId: RUN_ID, spans: records, wire }, null, 2),
        );
      for (const span of records)
        assert.ok(
          !Object.keys(span.attributes).some((key) =>
            key.startsWith("respan.internal."),
          ),
        );
      console.log(
        JSON.stringify({
          package: "vertexai",
          runId: RUN_ID,
          mode: live ? "live" : "native SDK transport fixture",
          spans: records.length,
          errors: records.filter((span) => span.status.code === 2).length,
        }),
      );
    },
  };
}
export async function actualTool<T>(
  respan: Respan,
  id: string,
  name: string,
  args: any,
  fn: () => Promise<T>,
): Promise<T> {
  return respan.withTool({ name }, async () => {
    const span = trace.getSpan(context.active());
    span?.setAttribute(ATTR_GEN_AI_TOOL_CALL_ID, id);
    span?.setAttribute(
      SpanAttributes.TRACELOOP_ENTITY_INPUT,
      JSON.stringify({ name, arguments: args }),
    );
    return fn();
  });
}
export { assert };
