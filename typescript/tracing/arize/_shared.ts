import { Respan } from "@respan/respan";
import { ArizeInstrumentor } from "@respan/instrumentation-arize";
import { InMemorySpanExporter } from "@opentelemetry/sdk-trace-base";
import { createServer } from "node:http";
import { appendFile } from "node:fs/promises";

const exportEnabled = process.env.RESPAN_EXAMPLE_EXPORT === "1";
if (exportEnabled && !process.env.RESPAN_API_KEY)
  throw new Error("RESPAN_EXAMPLE_EXPORT=1 requires RESPAN_API_KEY.");
const collector = createServer((request, response) => {
  request.resume();
  request.on("end", () => {
    response.writeHead(200, { "content-type": "application/json" });
    response.end("{}");
  });
});
if (!exportEnabled)
  await new Promise<void>((resolve) =>
    collector.listen(0, "127.0.0.1", resolve),
  );
const address = collector.address();
const exporters = new WeakMap<Respan, InMemorySpanExporter>();
export const RUN_ID =
  process.env.RESPAN_EXAMPLE_RUN_ID ?? `arize-ts-${Date.now()}`;
export function createRespan(appName = "arize-typescript-examples"): Respan {
  return new Respan({
    apiKey: exportEnabled ? process.env.RESPAN_API_KEY : "local-fixture-only",
    baseURL: exportEnabled
      ? process.env.RESPAN_BASE_URL
      : `http://127.0.0.1:${typeof address === "object" && address ? address.port : 0}`,
    appName,
    instrumentations: [new ArizeInstrumentor()],
    silenceInitializationMessage: true,
  });
}
export async function runWithArizeWorkflow<T>(
  respan: Respan,
  workflowName: string,
  fn: () => Promise<T>,
): Promise<T> {
  await respan.initialize();
  const exporter = new InMemorySpanExporter();
  exporters.set(respan, exporter);
  respan.addProcessor({
    name: "arize-example-capture",
    exporter,
    filter: () => true,
    disableBatch: true,
  });
  return respan.propagateAttributes(
    {
      trace_group_identifier: workflowName,
      custom_identifier: RUN_ID,
      metadata: {
        example: "typescript-arize",
        run_id: RUN_ID,
        workflow_name: workflowName,
      },
    },
    () => respan.withWorkflow({ name: workflowName }, fn),
  );
}
export async function finishRespan(respan: Respan) {
  await respan.flush();
  const spans =
    exporters
      .get(respan)
      ?.getFinishedSpans()
      .map((span) => ({
        name: span.name,
        spanId: span.spanContext().spanId,
        traceId: span.spanContext().traceId,
        parentSpanId: span.parentSpanContext?.spanId,
        status: span.status,
        attributes: span.attributes,
      })) ?? [];
  if (process.env.RESPAN_EXAMPLE_CAPTURE_PATH)
    await appendFile(
      process.env.RESPAN_EXAMPLE_CAPTURE_PATH,
      JSON.stringify({ runId: RUN_ID, spans }) + "\n",
    );
  await respan.shutdown();
  if (!exportEnabled)
    await new Promise<void>((resolve) => collector.close(() => resolve()));
}
export function logExampleResult(
  workflowName: string,
  details: Record<string, unknown>,
): void {
  console.log(JSON.stringify({ workflowName, runId: RUN_ID, ...details }));
}
