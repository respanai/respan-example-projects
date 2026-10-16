import assert from "node:assert/strict";
import fs from "node:fs/promises";
import { context, trace } from "@opentelemetry/api";
import * as LiveKit from "@livekit/agents";
import * as LiveKitOpenAI from "@livekit/agents-plugin-openai";
import { OpenAI } from "openai";
import { RespanTelemetry, propagateAttributes } from "@respan/tracing";
import {
  LiveKitInstrumentor,
  type LiveKitInstrumentorOptions,
} from "@respan/instrumentation-livekit";
import type { SpanExporter } from "@opentelemetry/sdk-trace-base";

LiveKit.initializeLogger({ pretty: false, level: "silent" });
export const RUN_ID =
  process.env.RESPAN_EXAMPLE_RUN_ID || `livekit-native-${Date.now()}`;
const exportEnabled = process.env.RESPAN_EXAMPLE_EXPORT === "1";
if (!exportEnabled) {
  process.env.OTEL_METRICS_EXPORTER = "none";
  process.env.OTEL_LOGS_EXPORTER = "none";
}
export const captured: Array<Record<string, unknown>> = [];
const exporter: SpanExporter = {
  export(spans, callback) {
    for (const span of spans)
      captured.push({
        name: span.name,
        spanId: span.spanContext().spanId,
        traceId: span.spanContext().traceId,
        parentSpanId: span.parentSpanContext?.spanId,
        attributes: { ...span.attributes },
        events: span.events,
        status: span.status,
      });
    callback({ code: 0 });
  },
  async shutdown() {},
};

/** Genuine released provider SDK; only its HTTP fetch transport is deterministic. */
export function nativeModel({
  tool,
  error = false,
  content = "The native transport completed this turn.",
}: { tool?: string; error?: boolean; content?: string } = {}) {
  const requests: Array<Record<string, any>> = [];
  const client = new OpenAI({
    apiKey: "fixture-only",
    baseURL: "http://fixture.invalid/v1",
    maxRetries: 0,
    fetch: async (_url, init) => {
      const body = init?.body ? JSON.parse(String(init.body)) : {};
      requests.push(body);
      if (!body.messages)
        return new Response(JSON.stringify({ object: "list", data: [] }), {
          headers: { "content-type": "application/json" },
        });
      if (error)
        return new Response(
          JSON.stringify({
            error: {
              message: "Controlled native transport failure",
              type: "server_error",
            },
          }),
          { status: 400, headers: { "content-type": "application/json" } },
        );
      const useTool =
        tool && !body.messages.some((message: any) => message.role === "tool");
      const base = {
        id: "native-fixture-response",
        object: "chat.completion.chunk",
        created: 1,
        model: "native-fixture-model",
      };
      const frames = [
        {
          ...base,
          choices: [
            {
              index: 0,
              delta: useTool
                ? {
                    role: "assistant",
                    tool_calls: [
                      {
                        index: 0,
                        id: "native-fixture-call",
                        type: "function",
                        function: { name: tool, arguments: '{"city":"Tokyo"}' },
                      },
                    ],
                  }
                : { role: "assistant", content },
              finish_reason: null,
            },
          ],
        },
        {
          ...base,
          choices: [
            {
              index: 0,
              delta: {},
              finish_reason: useTool ? "tool_calls" : "stop",
            },
          ],
        },
        {
          ...base,
          choices: [],
          usage: {
            prompt_tokens: 7,
            completion_tokens: 5,
            total_tokens: 12,
            prompt_tokens_details: { cached_tokens: 0 },
          },
        },
      ];
      return new Response(
        frames.map((frame) => `data: ${JSON.stringify(frame)}\n\n`).join("") +
          "data: [DONE]\n\n",
        { headers: { "content-type": "text/event-stream" } },
      );
    },
  });
  return {
    model: new LiveKitOpenAI.LLM({ model: "native-fixture-model", client }),
    requests,
  };
}

export async function runExample<T>(
  workflowName: string,
  fn: (runtime: RespanTelemetry) => Promise<T>,
  options: LiveKitInstrumentorOptions = {},
): Promise<T> {
  if (exportEnabled && !process.env.RESPAN_API_KEY)
    throw new Error("RESPAN_API_KEY is required when RESPAN_EXAMPLE_EXPORT=1.");
  const runtime = new RespanTelemetry({
    apiKey: exportEnabled ? process.env.RESPAN_API_KEY : "fixture-only",
    baseURL: exportEnabled ? process.env.RESPAN_BASE_URL : "http://127.0.0.1:1",
    appName: "typescript-livekit-native",
    traceContent: options.traceContent,
    exporter: exportEnabled ? undefined : exporter,
    disableBatch: true,
    silenceInitializationMessage: true,
    logLevel: "error",
    disabledInstrumentations: [
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
  await runtime.initialize();
  if (exportEnabled)
    runtime.addProcessor({
      name: "example-capture",
      exporter,
      disableBatch: true,
      filter: () => true,
    });
  const instrumentor = new LiveKitInstrumentor({
    livekitModule: LiveKit,
    ...options,
  });
  await instrumentor.activate();
  const traceIds: string[] = [];
  try {
    const result = await propagateAttributes(
      {
        custom_identifier: RUN_ID,
        trace_group_identifier: workflowName,
        metadata: {
          run_id: RUN_ID,
          example: "typescript-livekit",
          workflow_name: workflowName,
        },
      },
      () =>
        runtime.withWorkflow({ name: workflowName }, async () => {
          const id = trace.getSpan(context.active())?.spanContext().traceId;
          if (id) traceIds.push(id);
          return fn(runtime);
        }),
    );
    await runtime.flush();
    if (!exportEnabled && options.traceContent === false)
      assert.ok(
        captured.every(
          (span: any) =>
            span.attributes["traceloop.entity.input"] === undefined &&
            span.attributes["traceloop.entity.output"] === undefined,
        ),
      );
    console.log(
      JSON.stringify({
        workflowName,
        runId: RUN_ID,
        traceIds,
        result,
        capturedSpanCount: captured.length,
      }),
    );
    if (process.env.RESPAN_EXAMPLE_CAPTURE_PATH)
      await fs.writeFile(
        process.env.RESPAN_EXAMPLE_CAPTURE_PATH,
        JSON.stringify(
          { runId: RUN_ID, workflowName, traceIds, result, spans: captured },
          null,
          2,
        ),
      );
    return result;
  } finally {
    instrumentor.deactivate();
    await runtime.shutdown();
  }
}

export async function agentTurn({
  tools,
  chatCtx,
  tool,
  content,
}: {
  tools?: ConstructorParameters<typeof LiveKit.voice.Agent>[0]["tools"];
  chatCtx?: LiveKit.llm.ChatContext;
  tool?: string;
  content?: string;
} = {}) {
  const fixture = nativeModel({ tool, content });
  const session = new LiveKit.voice.AgentSession({ llm: fixture.model });
  try {
    await session.start({
      agent: new LiveKit.voice.Agent({
        id: "native-example-agent",
        instructions: "Answer using the configured native transport.",
        tools,
        chatCtx,
      }),
      record: false,
    });
    const run = session.run({ userInput: "Show the native LiveKit turn." });
    assert.equal(await run.wait(), run);
    return {
      requests: fixture.requests.filter((request) => request.messages).length,
      events: run.events.map((event) =>
        event.type === "agent_handoff"
          ? { type: event.type, newAgent: event.newAgent.id }
          : { type: event.type, item: event.item.toJSON() },
      ),
    };
  } finally {
    await session.close();
  }
}

export function assertCaptured(
  predicate: (span: Record<string, any>) => boolean,
): void {
  if (!exportEnabled) assert.ok(captured.some(predicate));
}
