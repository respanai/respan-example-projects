import { tool } from "@langchain/core/tools";
import { z } from "zod";
import { Document } from "@langchain/core/documents";
import { BaseRetriever } from "@langchain/core/retrievers";
import type { RunnableConfig } from "@langchain/core/runnables";
import { RespanTelemetry } from "@respan/tracing";
import type { ReadableSpan, SpanExporter } from "@opentelemetry/sdk-trace-base";
import { writeFile } from "node:fs/promises";
export { chatModel, textModel } from "./_fixture";
import { LangChainInstrumentor } from "@respan/instrumentation-langchain";
import { Respan } from "@respan/respan";
export interface ExampleRuntime {
  enabled: boolean;
  instrumentor: LangChainInstrumentor;
  respan?: Respan;
  telemetry?: RespanTelemetry;
  spans: ReadableSpan[];
}

export async function initRespan(appName: string): Promise<ExampleRuntime> {
  const instrumentor = new LangChainInstrumentor();
  const spans: ReadableSpan[] = [];
  const exporter: SpanExporter = {
    export(batch, done) {
      spans.push(...batch);
      done({ code: 0 });
    },
    shutdown: async () => {},
  };
  if (process.env.RESPAN_EXPORT === "1") {
    const apiKey = process.env.RESPAN_API_KEY;
    if (!apiKey) throw new Error("RESPAN_EXPORT=1 requires RESPAN_API_KEY.");
    const respan = new Respan({
      apiKey,
      baseURL: process.env.RESPAN_BASE_URL,
      appName,
      instrumentations: [instrumentor],
      logLevel: "error",
      silenceInitializationMessage: true,
    });
    await respan.initialize();
    respan.addProcessor({
      name: "example-capture",
      exporter,
      filter: () => true,
      disableBatch: true,
    });
    return { enabled: true, instrumentor, respan, spans };
  }
  const telemetry = new RespanTelemetry({
    appName,
    apiKey: "fixture-local-only",
    exporter,
    disableBatch: true,
    disabledInstrumentations: [
      "http",
      "openAI",
      "anthropic",
      "azureOpenAI",
      "cohere",
      "bedrock",
      "googleVertexAI",
      "googleAIPlatform",
      "pinecone",
      "together",
      "langChain",
      "llamaIndex",
      "chromaDB",
      "qdrant",
    ],
    logLevel: "error",
    silenceInitializationMessage: true,
  });
  await telemetry.initialize();
  instrumentor.activate();
  return { enabled: true, instrumentor, telemetry, spans };
}

export function tracingConfig(
  runtime: ExampleRuntime,
  name: string,
  metadata: Record<string, unknown> = {},
): RunnableConfig {
  const config: RunnableConfig = {
    runName: name,
    tags: ["respan-langchain-example", name],
    metadata: {
      example: name,
      custom_identifier: process.env.RESPAN_EXAMPLE_RUN_ID,
      ...metadata,
    },
  };
  return runtime.instrumentor
    ? runtime.instrumentor.addCallback(config)
    : config;
}

export async function shutdown(runtime: ExampleRuntime): Promise<void> {
  runtime.instrumentor.deactivate();
  if (runtime.respan) await runtime.respan.shutdown();
  else await runtime.telemetry?.shutdown();
  if (runtime.spans.length === 0)
    throw new Error("The native example produced no spans.");
  if (process.env.RESPAN_CAPTURE_PATH) {
    await writeFile(
      process.env.RESPAN_CAPTURE_PATH,
      JSON.stringify(
        runtime.spans.map((span) => ({
          name: span.name,
          traceId: span.spanContext().traceId,
          spanId: span.spanContext().spanId,
          parentId: span.parentSpanContext?.spanId,
          attributes: span.attributes,
          status: span.status,
        })),
        null,
        2,
      ),
    );
  }
  console.log(
    `Captured ${runtime.spans.length} native callback spans through the Respan pipeline.`,
  );
}

export function messageText(value: unknown): string {
  if (typeof value === "string") return value;
  if (value && typeof value === "object" && "content" in value) {
    const content = (value as { content: unknown }).content;
    return typeof content === "string" ? content : JSON.stringify(content);
  }
  return JSON.stringify(value);
}

export const getWeather = tool(
  ({ city }: { city: string }) => `It is sunny in ${city}.`,
  {
    name: "get_weather",
    description: "Get deterministic weather for a city.",
    schema: z.object({
      city: z.string().describe("City name"),
    }),
  },
);

export const addNumbers = tool(
  ({ left, right }: { left: number; right: number }) => left + right,
  {
    name: "add_numbers",
    description: "Add two numbers.",
    schema: z.object({
      left: z.number(),
      right: z.number(),
    }),
  },
);

export class StaticRetriever extends BaseRetriever {
  lc_namespace = ["respan", "examples", "langchain"];

  async _getRelevantDocuments(query: string): Promise<Document[]> {
    return [
      new Document({
        pageContent: `Respan tracing captures LangChain callbacks for ${query}.`,
        metadata: { source: "static-retriever" },
      }),
    ];
  }
}
