import type { Event, RunConfig } from "@google/adk";
import { InMemorySpanExporter } from "@opentelemetry/sdk-trace-base";
import type { ReadableSpan, SpanExporter } from "@opentelemetry/sdk-trace-base";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-http";
import { GoogleADKInstrumentor } from "@respan/instrumentation-google-adk";
import { propagateAttributes, RespanTelemetry } from "@respan/tracing";
import dotenv from "dotenv";
import { appendFileSync, existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { z } from "zod/v4";

export const EXAMPLE_RUN_ID =
  process.env.RESPAN_EXAMPLE_RUN_ID ?? `google-adk-ts-${Date.now()}`;
export type DemoMode =
  "hello" | "tool" | "stream" | "graph" | "privacy" | "error";

function loadEnv(): void {
  let directory = dirname(fileURLToPath(import.meta.url));
  for (let depth = 0; depth < 8; depth += 1) {
    const candidate = join(directory, ".env");
    if (existsSync(candidate)) {
      dotenv.config({ path: candidate, quiet: true });
      return;
    }
    directory = dirname(directory);
  }
}

function createExporter(workflowName: string): SpanExporter {
  const memory = new InMemorySpanExporter();
  if (process.env.RESPAN_EXAMPLE_EXPORT !== "1") return memory;
  if (!process.env.RESPAN_API_KEY)
    throw new Error("RESPAN_EXAMPLE_EXPORT=1 requires RESPAN_API_KEY.");
  const base = (process.env.RESPAN_BASE_URL ?? "https://api.respan.ai")
    .replace(/\/api\/?$/, "")
    .replace(/\/$/, "");
  const remote = new OTLPTraceExporter({
    url: process.env.RESPAN_EXAMPLE_TRACE_URL ?? `${base}/api/v2/traces`,
    headers: { Authorization: `Bearer ${process.env.RESPAN_API_KEY}` },
  });
  return {
    export(spans, callback) {
      const captured = spans.map((span) => ({
        workflowName,
        runId: EXAMPLE_RUN_ID,
        name: span.name,
        traceId: span.spanContext().traceId,
        spanId: span.spanContext().spanId,
        parentSpanId: span.parentSpanContext?.spanId,
        attributes: span.attributes,
        status: span.status,
      }));
      if (process.env.RESPAN_CAPTURE_FILE)
        appendFileSync(
          process.env.RESPAN_CAPTURE_FILE,
          JSON.stringify({ type: "spans", spans: captured }) + "\n",
        );
      remote.export(spans, (receipt) => {
        if (process.env.RESPAN_CAPTURE_FILE)
          appendFileSync(
            process.env.RESPAN_CAPTURE_FILE,
            JSON.stringify({
              type: "receipt",
              workflowName,
              runId: EXAMPLE_RUN_ID,
              code: receipt.code,
              spanIds: captured.map((span) => span.spanId),
            }) + "\n",
          );
        callback(receipt);
      });
    },
    forceFlush: () => remote.forceFlush(),
    shutdown: () => remote.shutdown(),
  };
}

function installTransport(mode: DemoMode): () => void {
  if (process.env.GOOGLE_ADK_LIVE === "1" && mode !== "error") return () => {};
  const original = globalThis.fetch;
  globalThis.fetch = async (input, options) => {
    const url =
      typeof input === "string"
        ? input
        : input instanceof URL
          ? input.href
          : input.url;
    if (!url.startsWith("https://generativelanguage.googleapis.com/"))
      throw new Error(`Unexpected controlled provider transport: ${url}`);
    const request = JSON.parse(String(options?.body ?? "{}"));
    if (mode === "error")
      return new Response(
        JSON.stringify({
          error: {
            code: 429,
            status: "RESOURCE_EXHAUSTED",
            message: "Controlled ADK provider failure",
          },
        }),
        { status: 429, headers: { "content-type": "application/json" } },
      );
    const hasResult = request.contents?.some(
      (content: { parts?: Array<{ functionResponse?: unknown }> }) =>
        content.parts?.some((part) => part.functionResponse),
    );
    const parts =
      mode === "tool" && !hasResult
        ? [
            {
              functionCall: {
                id: "example_weather_call_tokyo",
                name: "get_weather",
                args: { city: "Tokyo" },
              },
            },
            {
              functionCall: {
                id: "example_weather_call_paris",
                name: "get_weather",
                args: { city: "Paris" },
              },
            },
          ]
        : [
            {
              text:
                mode === "tool"
                  ? "Tokyo is sunny with light wind; Paris is cloudy."
                  : "Hello from native Google ADK TypeScript.",
            },
          ];
    const usageMetadata = {
      promptTokenCount: 14,
      candidatesTokenCount: 7,
      thoughtsTokenCount: 2,
      totalTokenCount: 23,
    };
    const frames =
      mode === "stream"
        ? [
            {
              candidates: [
                {
                  index: 0,
                  content: {
                    role: "model",
                    parts: [{ text: "Streaming ADK " }],
                  },
                },
              ],
            },
            {
              candidates: [
                {
                  index: 0,
                  content: {
                    role: "model",
                    parts: [{ text: "telemetry complete." }],
                  },
                  finishReason: "STOP",
                },
              ],
            },
            { usageMetadata },
          ]
        : [
            {
              candidates: [
                {
                  index: 0,
                  content: { role: "model", parts },
                  finishReason: "STOP",
                },
              ],
              usageMetadata,
            },
          ];
    return mode === "stream"
      ? new Response(
          frames.map((frame) => `data: ${JSON.stringify(frame)}\n\n`).join(""),
          { headers: { "content-type": "text/event-stream" } },
        )
      : new Response(JSON.stringify(frames[0]), {
          headers: { "content-type": "application/json" },
        });
  };
  return () => {
    globalThis.fetch = original;
  };
}

export async function runADKExample(params: {
  appName: string;
  workflowName: string;
  mode: DemoMode;
  prompt: string;
  runConfig?: RunConfig;
  streaming?: boolean;
}): Promise<{ events: Event[]; output: string; respan: RespanTelemetry }> {
  loadEnv();
  const exporter = createExporter(params.workflowName);
  const previousMetricsExporter = process.env.OTEL_METRICS_EXPORTER;
  process.env.OTEL_METRICS_EXPORTER = "none";
  const respan = new RespanTelemetry({
    appName: params.appName,
    apiKey: "local-controlled-example",
    exporter,
    disableBatch: true,
    silenceInitializationMessage: true,
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
  });
  await respan.initialize();
  const instrumentor = new GoogleADKInstrumentor({
    traceContent: params.mode !== "privacy",
  });
  instrumentor.activate();
  const restore = installTransport(params.mode);
  const events: Event[] = [];
  try {
    const adk = await import("@google/adk");
    const tool = new adk.FunctionTool({
      name: "get_weather",
      description: "Return a deterministic local forecast.",
      parameters: z.object({ city: z.string() }),
      execute: ({ city }) => ({
        city,
        forecast: city === "Paris" ? "cloudy" : "sunny with light wind",
      }),
    });
    const agent =
      params.mode === "graph"
        ? new adk.Workflow({
            name: "forecast_workflow",
            edges: [
              [
                "START",
                new adk.FunctionNode("format_forecast", () => ({
                  forecast: "sunny",
                  city: "Tokyo",
                })),
              ],
            ],
          })
        : new adk.LlmAgent({
            name: `${params.mode}_agent`,
            model: new adk.Gemini({
              model: "gemini-2.5-flash",
              apiKey:
                process.env.GOOGLE_ADK_LIVE === "1" && params.mode !== "error"
                  ? process.env.GOOGLE_GENAI_API_KEY
                  : "controlled-local-provider",
            }),
            instruction: "Answer concisely. Use tools when needed.",
            tools: params.mode === "tool" ? [tool] : [],
          });
    const runner = new adk.InMemoryRunner({ appName: params.appName, agent });
    await propagateAttributes(
      {
        custom_identifier: EXAMPLE_RUN_ID,
        metadata: {
          run_id: EXAMPLE_RUN_ID,
          profile: process.env.RESPAN_EXAMPLE_PROFILE ?? "current",
          source_frozen_hash: process.env.RESPAN_EXAMPLE_SOURCE_HASH ?? "local",
          workflow_name: params.workflowName,
          example: "google-adk-typescript",
        },
      },
      async () => {
        await respan.withWorkflow({ name: params.workflowName }, async () => {
          for await (const event of runner.runEphemeral({
            userId: "example-user",
            newMessage: { role: "user", parts: [{ text: params.prompt }] },
            runConfig:
              params.runConfig ??
              (params.streaming
                ? { streamingMode: adk.StreamingMode.SSE }
                : undefined),
          }))
            events.push(event);
        });
      },
    );
    await respan.flush();
    const localSpans: ReadableSpan[] =
      exporter instanceof InMemorySpanExporter
        ? exporter.getFinishedSpans()
        : [];
    if (
      params.mode === "privacy" &&
      JSON.stringify(localSpans.map((span) => span.attributes)).includes(
        params.prompt,
      )
    )
      throw new Error("Privacy example exported prompt content.");
    if (params.mode === "error" && !events.some((event) => event.errorCode))
      throw new Error("Expected native ADK error event.");
    const output = events
      .filter((event) => !event.partial)
      .flatMap((event) => event.content?.parts ?? [])
      .map((part) => part.text ?? "")
      .join("");
    return { events, output, respan };
  } finally {
    restore();
    instrumentor.deactivate();
    await respan.shutdown();
    if (previousMetricsExporter === undefined)
      delete process.env.OTEL_METRICS_EXPORTER;
    else process.env.OTEL_METRICS_EXPORTER = previousMetricsExporter;
  }
}

export function logExampleResult(
  workflowName: string,
  details: Record<string, unknown>,
): void {
  console.log(
    JSON.stringify(
      { workflowName, runId: EXAMPLE_RUN_ID, ...details },
      null,
      2,
    ),
  );
}
