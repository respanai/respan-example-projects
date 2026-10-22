import dotenv from "dotenv";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { OpenRouter } from "@openrouter/sdk";
import { HTTPClient } from "@openrouter/sdk/lib/http.js";
import { NodeTracerProvider } from "@opentelemetry/sdk-trace-node";
import {
  InMemorySpanExporter,
  SimpleSpanProcessor,
} from "@opentelemetry/sdk-trace-base";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-http";
import { trace, SpanStatusCode } from "@opentelemetry/api";
import { RespanSpanAttributes } from "@respan/respan-sdk";
import { SpanAttributes } from "@traceloop/ai-semantic-conventions";
import { OpenRouterInstrumentor } from "@respan/instrumentation-openrouter";
import { fixtureFetch } from "./_fixtures.js";

dotenv.config({
  path: path.resolve(
    path.dirname(fileURLToPath(import.meta.url)),
    "../../../.env",
  ),
});
export const RUN_ID =
  process.env.RESPAN_EXAMPLE_RUN_ID || `openrouter-ts-${Date.now()}`;
export const LIVE = process.env.RESPAN_LIVE_OPENROUTER === "1";
export const CHAT_MODEL =
  process.env.OPENROUTER_CHAT_MODEL || "controlled/chat";
export const EMBEDDING_MODEL =
  process.env.OPENROUTER_EMBEDDING_MODEL || "controlled/embedding";
export function createOpenRouterClient(): OpenRouter {
  if (
    LIVE &&
    (!process.env.OPENROUTER_API_KEY || !process.env.OPENROUTER_CHAT_MODEL)
  )
    throw new Error(
      "Live mode requires OPENROUTER_API_KEY and OPENROUTER_CHAT_MODEL.",
    );
  return new OpenRouter({
    apiKey: LIVE ? process.env.OPENROUTER_API_KEY : "controlled-synthetic-key",
    retryConfig: { strategy: "none" },
    ...(LIVE
      ? {}
      : {
          serverURL: "https://fixture.invalid/api/v1",
          httpClient: new HTTPClient({ fetcher: fixtureFetch }),
        }),
  });
}
export function createRespan() {
  const capture = new InMemorySpanExporter();
  const processors = [new SimpleSpanProcessor(capture)];
  if (process.env.RESPAN_EXPORT_TRACES === "1") {
    if (!process.env.RESPAN_API_KEY)
      throw new Error("Trace export requires RESPAN_API_KEY.");
    const base = (process.env.RESPAN_BASE_URL || "https://api.respan.ai")
      .replace(/\/+$/, "")
      .replace(/\/api$/, "");
    processors.push(
      new SimpleSpanProcessor(
        new OTLPTraceExporter({
          url: `${base}/api/v2/traces`,
          headers: { Authorization: `Bearer ${process.env.RESPAN_API_KEY}` },
          timeoutMillis: 120000,
        }),
      ),
    );
  }
  const provider = new NodeTracerProvider({
    spanProcessors: processors,
    spanLimits: {
      attributeCountLimit: Infinity,
      attributeValueLengthLimit: Infinity,
    },
  });
  const instrumentor = new OpenRouterInstrumentor();
  let initialized = false;
  return {
    capture,
    async initialize() {
      if (!initialized) {
        provider.register();
        await instrumentor.activate();
        initialized = true;
      }
    },
    async shutdown() {
      await instrumentor.deactivate();
      await provider.forceFlush();
      await provider.shutdown();
    },
  };
}
export async function runWithOpenRouterWorkflow<T>(
  respan: ReturnType<typeof createRespan>,
  name: string,
  fn: () => Promise<T>,
): Promise<T> {
  await respan.initialize();
  return trace
    .getTracer("openrouter-examples")
    .startActiveSpan(name, async (span) => {
      span.setAttributes({
        [RespanSpanAttributes.RESPAN_LOG_TYPE]: "workflow",
        [SpanAttributes.TRACELOOP_ENTITY_NAME]: name,
        [RespanSpanAttributes.RESPAN_METADATA]: JSON.stringify({
          run_id: RUN_ID,
          scenario: name,
        }),
      });
      try {
        return await fn();
      } catch (error) {
        span.setStatus({ code: SpanStatusCode.ERROR });
        throw error;
      } finally {
        span.end();
      }
    });
}
export async function shutdownRespan(
  respan: ReturnType<typeof createRespan>,
): Promise<void> {
  await respan.shutdown();
}
export function logExampleResult(
  workflowName: string,
  details: Record<string, unknown>,
): void {
  console.log(
    JSON.stringify({ workflowName, runId: RUN_ID, fixture: !LIVE, ...details }),
  );
}
