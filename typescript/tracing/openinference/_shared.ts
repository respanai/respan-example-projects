import { createServer } from "node:http";
import { writeFile } from "node:fs/promises";
import { Respan } from "@respan/respan";
import { InMemorySpanExporter } from "@opentelemetry/sdk-trace-base";
import { OpenInferenceInstrumentor } from "@respan/instrumentation-openinference";
import { OpenAIInstrumentation } from "@arizeai/openinference-instrumentation-openai";
import * as OpenAI from "openai";

export const RUN_ID =
  process.env.RESPAN_EXAMPLE_RUN_ID ?? `openinference-ts-${Date.now()}`;
export async function createRuntime() {
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
  const baseURL = exportEnabled
    ? process.env.RESPAN_BASE_URL
    : `http://127.0.0.1:${typeof address === "object" && address ? address.port : 0}`;
  const plugin = new OpenInferenceInstrumentor(OpenAIInstrumentation, OpenAI, {
    traceContent: process.env.RESPAN_EXAMPLE_TRACE_CONTENT !== "false",
  });
  const respan = new Respan({
    apiKey: exportEnabled ? process.env.RESPAN_API_KEY : "local-fixture-only",
    baseURL,
    appName: "openinference-typescript-examples",
    traceContent: process.env.RESPAN_EXAMPLE_TRACE_CONTENT !== "false",
    instrumentations: [plugin],
    silenceInitializationMessage: true,
  });
  const exporter = new InMemorySpanExporter();
  await respan.initialize();
  respan.addProcessor({
    name: "example-capture",
    exporter,
    filter: () => true,
    disableBatch: true,
  });
  return {
    respan,
    async finish() {
      await respan.flush();
      const spans = exporter.getFinishedSpans().map((span) => ({
        name: span.name,
        spanId: span.spanContext().spanId,
        traceId: span.spanContext().traceId,
        parentSpanId: span.parentSpanContext?.spanId,
        status: span.status,
        attributes: span.attributes,
        events: span.events,
      }));
      if (process.env.RESPAN_EXAMPLE_CAPTURE_PATH)
        await writeFile(
          process.env.RESPAN_EXAMPLE_CAPTURE_PATH,
          JSON.stringify({ runId: RUN_ID, spans }, null, 2),
        );
      await respan.shutdown();
      if (!exportEnabled)
        await new Promise<void>((resolve) => collector.close(() => resolve()));
      return spans;
    },
  };
}
export async function workflow<T>(
  respan: Respan,
  scenario: string,
  fn: () => Promise<T> | T,
) {
  return respan.propagateAttributes(
    {
      metadata: {
        run_id: RUN_ID,
        scenario,
        example: "typescript-openinference",
      },
      custom_identifier: RUN_ID,
    },
    () =>
      respan.withWorkflow(
        { name: `openinference-${scenario}.workflow` },
        async () => fn(),
      ),
  );
}
