import { pathToFileURL } from "node:url";
import assert from "node:assert/strict";
import { context, trace } from "@opentelemetry/api";
import { BasicTracerProvider } from "@opentelemetry/sdk-trace-base";
import { AsyncLocalStorageContextManager } from "@opentelemetry/context-async-hooks";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-http";
import { PiInstrumentor } from "@respan/instrumentation-pi";
import { transformReadableSpanBatch } from "@respan/tracing";
import { nativeFixture } from "./_fixture.mjs";

export { assert, context, trace, nativeFixture, PiInstrumentor };
export const runId =
  process.env.RESPAN_EXAMPLE_RUN_ID ?? `pi-local-${Date.now()}`;
export const captured: any[] = [];
export const results: any[] = [];
let activeScenario: any[] | undefined;
const provider = new BasicTracerProvider({
  spanProcessors: [
    {
      onStart() {},
      onEnd(span: any) {
        if (span.instrumentationScope?.name === "@respan/instrumentation-pi") {
          captured.push(span);
          activeScenario?.push(span);
        }
      },
      async forceFlush() {},
      async shutdown() {},
    },
  ],
});
trace.setGlobalTracerProvider(provider);
const manager = new AsyncLocalStorageContextManager().enable();
context.setGlobalContextManager(manager);

export async function scenario(
  name: string,
  plan: any = {},
  options: any = {},
  callback?: (
    fixture: any,
    spans: any[],
    instrumentor: PiInstrumentor,
  ) => Promise<void>,
) {
  const spans: any[] = [];
  const instrumentor = new PiInstrumentor({
    traceScope: "run",
    ...options,
    metadata: { run_id: runId, scenario: name },
  });
  activeScenario = spans;
  instrumentor.activate();
  const fixture = await nativeFixture({ instrumentor, ...plan });
  try {
    if (callback) await callback(fixture, spans, instrumentor);
    else await fixture.session.prompt(`Controlled Pi example: ${name}`);
    const result = {
      scenario: name,
      spans: spans.length,
      requests: fixture.requests.length,
      trace_ids: [
        ...new Set(spans.map((span: any) => span.spanContext().traceId)),
      ],
    };
    results.push(result);
    return { spans, fixture, output: fixture.session.getLastAssistantText() };
  } finally {
    await fixture.close();
    instrumentor.deactivate();
    activeScenario = undefined;
  }
}
export const byType = (spans: any[], kind: string) =>
  spans.filter((span) => span.attributes["respan.entity.log_type"] === kind);
export async function finish() {
  const exported = transformReadableSpanBatch(captured, "semantic");
  assert.equal(exported.length, captured.length);
  for (const span of exported) {
    assert.ok(
      !Object.keys(span.attributes).some((key) =>
        key.startsWith("respan.internal."),
      ),
      "Internal SDK hints must not cross the wire",
    );
  }
  if (process.env.RESPAN_EXAMPLE_EXPORT === "1") {
    const base = (process.env.RESPAN_BASE_URL ?? "https://api.respan.ai")
      .replace(/\/+$/, "")
      .replace(/\/api$/, "");
    const exporter = new OTLPTraceExporter({
      url: process.env.RESPAN_EXAMPLE_TRACE_URL ?? `${base}/api/v2/traces`,
      headers: process.env.RESPAN_API_KEY
        ? { Authorization: `Bearer ${process.env.RESPAN_API_KEY}` }
        : {},
      timeoutMillis: 60000,
    });
    await new Promise<void>((resolve, reject) =>
      exporter.export(exported, (result) =>
        result.code === 0
          ? resolve()
          : reject(result.error ?? new Error("Trace export failed")),
      ),
    );
    await exporter.shutdown();
  }
  console.log(
    JSON.stringify({
      run_id: runId,
      scenarios: results,
      spans: captured.length,
      live_opt_in: process.env.RESPAN_PI_LIVE === "1",
    }),
  );
  trace.disable();
  context.disable();
  manager.disable();
  await provider.shutdown();
}

export function isDirect(url: string): boolean {
  return !!process.argv[1] && pathToFileURL(process.argv[1]).href === url;
}
