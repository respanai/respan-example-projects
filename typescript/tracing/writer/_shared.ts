import dotenv from "dotenv";
import { Respan } from "@respan/respan";
import { WriterInstrumentor } from "@respan/instrumentation-writer";
import Writer from "writer-sdk";
import * as WriterSDKModule from "writer-sdk";
import path from "node:path";
import { fileURLToPath } from "node:url";

const exampleDir = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(exampleDir, "../../..");
dotenv.config({ path: path.join(repoRoot, ".env") });

export const RUN_ID =
  process.env.RESPAN_EXAMPLE_RUN_ID || `writer-ts-${Date.now()}`;
export const DEFAULT_CHAT_MODEL = process.env.WRITER_MODEL || "palmyra-x5";
export const DEFAULT_COMPLETION_MODEL =
  process.env.WRITER_COMPLETION_MODEL || "palmyra-x-003-instruct";

function envValue(name: string): string | undefined {
  const direct = process.env[name];
  if (direct && direct.trim()) return direct.trim();
  const spaced = process.env[`${name} `];
  if (spaced && spaced.trim()) return spaced.trim();
  return undefined;
}

export function createRespan(
  appName = "writer-typescript-examples",
  traceContent = true,
): Respan {
  const apiKey = envValue("RESPAN_API_KEY");
  if (!apiKey) {
    throw new Error(
      "Set RESPAN_API_KEY in the respan-example-projects repo root .env file.",
    );
  }

  return new Respan({
    apiKey,
    baseURL: envValue("RESPAN_BASE_URL"),
    appName,
    instrumentations: [
      new WriterInstrumentor({ sdkModule: WriterSDKModule, traceContent }),
    ],
    silenceInitializationMessage: true,
  });
}

export function createWriterClient(): Writer {
  const liveMode = process.env.WRITER_EXAMPLE_MODE === "live";
  const apiKey = envValue("WRITER_API_KEY");

  if (liveMode && !apiKey) {
    throw new Error(
      "Set WRITER_API_KEY in respan-example-projects/.env for live Writer examples.",
    );
  }

  return new Writer({
    apiKey: apiKey || "respan-writer-mock-key",
    maxRetries: 0,
    timeout: 30_000,
    ...(liveMode ? {} : { fetch: createWriterMockFetch() }),
  });
}

export async function runWithWriterWorkflow<T>(
  respan: Respan,
  workflowName: string,
  fn: () => Promise<T>,
): Promise<T> {
  await respan.initialize();
  return await respan.propagateAttributes(
    {
      trace_group_identifier: workflowName,
      custom_identifier: RUN_ID,
      metadata: {
        example: "typescript-writer",
        run_id: RUN_ID,
        workflow_name: workflowName,
        writer_example_mode:
          process.env.WRITER_EXAMPLE_MODE === "live" ? "live" : "mock",
      },
    },
    async () =>
      await respan.withWorkflow({ name: workflowSpanName(workflowName) }, fn),
  );
}

function workflowSpanName(workflowName: string): string {
  return workflowName.endsWith(".workflow")
    ? workflowName.slice(0, -".workflow".length)
    : workflowName;
}

export async function shutdownRespan(respan: Respan): Promise<void> {
  await respan.shutdown();
}

export function logExampleResult(
  workflowName: string,
  details: Record<string, unknown>,
): void {
  console.log(
    JSON.stringify({ workflowName, runId: RUN_ID, ...details }, null, 2),
  );
}

export async function withTimeout<T>(
  promise: Promise<T>,
  label: string,
): Promise<T> {
  let timeout: NodeJS.Timeout | undefined;
  const timeoutPromise = new Promise<never>((_, reject) => {
    timeout = setTimeout(
      () => reject(new Error(`${label} timed out after 60s`)),
      60_000,
    );
  });
  try {
    return await Promise.race([promise, timeoutPromise]);
  } finally {
    if (timeout) clearTimeout(timeout);
  }
}

export function createWriterMockFetch(): typeof fetch {
  return async (
    input: RequestInfo | URL,
    init?: RequestInit,
  ): Promise<Response> => {
    const request =
      input instanceof Request ? input.clone() : new Request(input, init);
    const url = new URL(request.url);
    const body = await readJsonBody(request);

    if (url.pathname === "/v1/chat") {
      if (body.stream === true) {
        return sseResponse(chatStreamEvents(body));
      }
      if (hasUserText(body, "expected error")) {
        return jsonResponse(
          {
            error: {
              message: "Deterministic Writer example error",
              type: "rate_limit_error",
            },
          },
          429,
        );
      }
      if (Array.isArray(body.tools) && !hasToolResult(body)) {
        return jsonResponse(toolCallChatResponse(body));
      }
      if (hasToolResult(body)) {
        return jsonResponse(finalToolChatResponse(body));
      }
      if (body.response_format?.type === "json_schema") {
        return jsonResponse(structuredChatResponse(body));
      }
      return jsonResponse(basicChatResponse(body));
    }

    if (url.pathname === "/v1/completions") {
      if (body.stream === true) {
        return sseResponse(completionStreamEvents());
      }
      return jsonResponse({
        model: body.model || DEFAULT_COMPLETION_MODEL,
        choices: [
          {
            text: "Writer text completions are captured as Respan text spans.",
          },
        ],
        usage: { prompt_tokens: 15, completion_tokens: 19, total_tokens: 34 },
      });
    }

    return jsonResponse(
      { error: { message: `Unhandled mock Writer path: ${url.pathname}` } },
      404,
    );
  };
}

async function readJsonBody(request: Request): Promise<Record<string, any>> {
  const text = await request.text();
  if (!text.trim()) return {};
  try {
    return JSON.parse(text);
  } catch {
    return {};
  }
}

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

function sseResponse(events: unknown[]): Response {
  const encoder = new TextEncoder();
  const stream = new ReadableStream({
    start(controller) {
      for (const event of events) {
        controller.enqueue(
          encoder.encode(`data: ${JSON.stringify(event)}\n\n`),
        );
      }
      controller.enqueue(encoder.encode("data: [DONE]\n\n"));
      controller.close();
    },
  });

  return new Response(stream, {
    status: 200,
    headers: { "content-type": "text/event-stream" },
  });
}

function hasUserText(body: Record<string, any>, text: string): boolean {
  return (body.messages || []).some((message: any) => {
    if (message?.role !== "user") return false;
    return String(message.content ?? "")
      .toLowerCase()
      .includes(text.toLowerCase());
  });
}

function hasToolResult(body: Record<string, any>): boolean {
  return (body.messages || []).some((message: any) => message?.role === "tool");
}

function basicChatResponse(body: Record<string, any>): Record<string, any> {
  return {
    id: "chatcmpl_writer_basic",
    object: "chat.completion",
    created: Math.floor(Date.now() / 1000),
    model: body.model || DEFAULT_CHAT_MODEL,
    choices: [
      {
        index: 0,
        finish_reason: "stop",
        message: {
          role: "assistant",
          content: "Writer instrumentation is active and producing chat spans.",
          refusal: null,
        },
      },
    ],
    usage: { prompt_tokens: 21, completion_tokens: 8, total_tokens: 29 },
  };
}

function structuredChatResponse(
  body: Record<string, any>,
): Record<string, any> {
  return {
    ...basicChatResponse(body),
    id: "chatcmpl_writer_structured",
    choices: [
      {
        index: 0,
        finish_reason: "stop",
        message: {
          role: "assistant",
          content: JSON.stringify({
            title: "Writer tracing",
            priority: "medium",
            tags: ["instrumentation", "typescript"],
          }),
          refusal: null,
        },
      },
    ],
    usage: { prompt_tokens: 34, completion_tokens: 15, total_tokens: 49 },
  };
}

function toolCallChatResponse(body: Record<string, any>): Record<string, any> {
  return {
    ...basicChatResponse(body),
    id: "chatcmpl_writer_tool_call",
    choices: [
      {
        index: 0,
        finish_reason: "tool_calls",
        message: {
          role: "assistant",
          content: "",
          refusal: null,
          tool_calls: [
            {
              id: "call_weather_1",
              type: "function",
              function: {
                name: "get_weather",
                arguments: JSON.stringify({ city: "Tokyo" }),
              },
            },
          ],
        },
      },
    ],
    usage: { prompt_tokens: 42, completion_tokens: 9, total_tokens: 51 },
  };
}

function finalToolChatResponse(body: Record<string, any>): Record<string, any> {
  return {
    ...basicChatResponse(body),
    id: "chatcmpl_writer_tool_final",
    choices: [
      {
        index: 0,
        finish_reason: "stop",
        message: {
          role: "assistant",
          content: "Tokyo is clear and 23 C, based on the local tool result.",
          refusal: null,
        },
      },
    ],
    usage: { prompt_tokens: 55, completion_tokens: 13, total_tokens: 68 },
  };
}

function chatStreamEvents(body: Record<string, any>): unknown[] {
  const model = body.model || DEFAULT_CHAT_MODEL;
  return [
    {
      id: "chatcmpl_writer_stream",
      object: "chat.completion.chunk",
      created: Math.floor(Date.now() / 1000),
      model,
      choices: [
        {
          index: 0,
          finish_reason: null,
          delta: { role: "assistant", content: "Streaming " },
        },
      ],
    },
    {
      id: "chatcmpl_writer_stream",
      object: "chat.completion.chunk",
      created: Math.floor(Date.now() / 1000),
      model,
      choices: [
        { index: 0, finish_reason: null, delta: { content: "Writer output." } },
      ],
      usage: { prompt_tokens: 18, completion_tokens: 4, total_tokens: 22 },
    },
    {
      id: "chatcmpl_writer_stream",
      object: "chat.completion.chunk",
      created: Math.floor(Date.now() / 1000),
      model,
      choices: [{ index: 0, finish_reason: "stop", delta: {} }],
    },
  ];
}

function completionStreamEvents(): unknown[] {
  return [{ value: "streamed " }, { value: "completion" }];
}
