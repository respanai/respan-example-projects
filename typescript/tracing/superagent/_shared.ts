import { context } from "@opentelemetry/api";
import {
  RespanTelemetry,
  propagateAttributes,
  INSTRUMENTATION_INFO,
  type InstrumentationName,
} from "@respan/tracing";
import { InMemorySpanExporter } from "@opentelemetry/sdk-trace-base";
import { SuperagentInstrumentor } from "@respan/instrumentation-superagent";
import { CONTEXT_KEY_ALLOW_TRACE_CONTENT } from "@traceloop/ai-semantic-conventions";
import * as sdk from "safety-agent";
import type { SupportedModel } from "safety-agent";
import dotenv from "dotenv";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { providerFixture } from "./_fixtures.js";
export { context, CONTEXT_KEY_ALLOW_TRACE_CONTENT };
const liveMode = process.env.SUPERAGENT_EXAMPLE_PROVIDER === "live";
if (liveMode || process.env.RESPAN_EXAMPLE_EXPORT === "1")
  dotenv.config({
    path: resolve(dirname(fileURLToPath(import.meta.url)), "../../../.env"),
    override: false,
    quiet: true,
  });
export const RUN_ID =
  process.env.RESPAN_EXAMPLE_RUN_ID ?? `superagent-ts-${Date.now()}`;
export const MODEL = (
  liveMode
    ? (process.env.SUPERAGENT_MODEL ?? "openai/gpt-4o-mini")
    : "openai-compatible/controlled"
) as SupportedModel;
export async function runExample(
  scenario: string,
  fn: (env: {
    runtime: RespanTelemetry;
    client: sdk.SafetyClient;
    fixture: ReturnType<typeof providerFixture> | undefined;
  }) => Promise<unknown>,
) {
  const exporting = process.env.RESPAN_EXAMPLE_EXPORT === "1";
  const live = process.env.SUPERAGENT_EXAMPLE_PROVIDER === "live";
  if (exporting || live)
    dotenv.config({
      path: resolve(dirname(fileURLToPath(import.meta.url)), "../../../.env"),
      override: false,
      quiet: true,
    });
  if (exporting && !process.env.RESPAN_API_KEY)
    throw new Error("RESPAN_API_KEY is required for explicit export");
  for (const method of ["debug", "info", "log"] as const) {
    const original = console[method].bind(console);
    console[method] = (...args: unknown[]) => {
      if (
        typeof args[0] === "string" &&
        /^(\[Respan|Respan tracing)/.test(args[0])
      )
        return;
      original(...args);
    };
  }
  const local = new InMemorySpanExporter();
  const captures: any[] = [];
  const runtime = new RespanTelemetry({
    apiKey: exporting ? process.env.RESPAN_API_KEY! : "controlled-local-only",
    baseURL: process.env.RESPAN_BASE_URL,
    exporter: exporting ? undefined : local,
    disableBatch: true,
    silenceInitializationMessage: true,
    disabledInstrumentations: Object.keys(
      INSTRUMENTATION_INFO,
    ) as InstrumentationName[],
    spanPostprocessCallback: (span) => {
      captures.push({
        name: span.name,
        traceId: span.spanContext().traceId,
        spanId: span.spanContext().spanId,
        parentSpanId: span.parentSpanContext?.spanId,
        attributes: span.attributes,
        status: span.status,
      });
    },
  });
  await runtime.initialize();
  const instrumentor = new SuperagentInstrumentor({ safetyAgentModule: sdk });
  await instrumentor.activate();
  const fixture = live ? undefined : providerFixture();
  const client = sdk.createClient({
    apiKey: live ? process.env.SUPERAGENT_API_KEY : "controlled-client",
    enableFallback: false,
  });
  try {
    await propagateAttributes(
      {
        custom_identifier: RUN_ID,
        metadata: {
          run_id: RUN_ID,
          example: "typescript-superagent",
          scenario,
        },
      },
      () =>
        runtime.withWorkflow({ name: `superagent-${scenario}` }, () =>
          fn({ runtime, client, fixture }),
        ),
    );
  } finally {
    instrumentor.deactivate();
    fixture?.close();
    await runtime.shutdown();
    if (process.env.SUPERAGENT_CAPTURE_DIR) {
      mkdirSync(process.env.SUPERAGENT_CAPTURE_DIR, { recursive: true });
      writeFileSync(
        resolve(process.env.SUPERAGENT_CAPTURE_DIR, scenario + ".json"),
        JSON.stringify({ runId: RUN_ID, captures }, null, 2),
      );
    }
  }
  console.log(
    JSON.stringify({
      runId: RUN_ID,
      scenario,
      spanCount: captures.length,
      requests: fixture?.requests.length,
      exporting,
      live,
    }),
  );
  return captures;
}
