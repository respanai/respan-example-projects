import { createServer, type IncomingMessage, type ServerResponse } from "node:http";
import path from "node:path";
import { fileURLToPath } from "node:url";
import dotenv from "dotenv";
import { Respan } from "@respan/respan";
import { DifyInstrumentor } from "@respan/instrumentation-dify";
import * as DifySdk from "dify-client";

const exampleDir = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(exampleDir, "../../..");
dotenv.config({ path: path.join(repoRoot, ".env") });
dotenv.config({ path: path.join(exampleDir, ".env") });

export const RUN_ID = process.env.RESPAN_EXAMPLE_RUN_ID || `dify-ts-${Date.now()}`;

type JsonRecord = Record<string, any>;

function envValue(name: string): string | undefined {
  const direct = process.env[name];
  if (direct?.trim()) return direct.trim();
  const spaced = process.env[`${name} `];
  return spaced?.trim() || undefined;
}

export interface DifyRuntime {
  baseUrl: string;
  isLocal: boolean;
  key(name: string): string;
  setResult(value: unknown): void;
}

export async function withDifyRuntime<T>(
  workflowName: string,
  fn: (runtime: DifyRuntime) => Promise<T>,
): Promise<T> {
  const respanKey = envValue("RESPAN_API_KEY");
  const noExport = envValue("RESPAN_EXAMPLE_NO_EXPORT") === "true";
  if (!respanKey && !noExport) {
    throw new Error("Set RESPAN_API_KEY in respan-example-projects/.env.");
  }

  const liveBaseUrl = envValue("DIFY_BASE_URL");
  const local = liveBaseUrl ? undefined : await startLocalDifyServer();
  const localRespanSink = noExport ? await startLocalRespanSink() : undefined;
  const baseUrl = liveBaseUrl ?? local!.baseUrl;
  let result: unknown;
  const respan = new Respan({
    apiKey: noExport ? "local-no-export" : respanKey,
    baseURL: localRespanSink?.baseUrl ?? envValue("RESPAN_BASE_URL"),
    appName: workflowName,
    instrumentations: [new DifyInstrumentor({ sdkModule: DifySdk })],
    silenceInitializationMessage: true,
  });

  await respan.initialize();
  try {
    return await respan.propagateAttributes(
      {
        custom_identifier: RUN_ID,
        trace_group_identifier: workflowName,
        metadata: {
          integration: "dify",
          language: "typescript",
          run_id: RUN_ID,
          workflow_name: workflowName,
          dify_example_mode: local ? "loopback" : "live",
        },
      },
      async () => await respan.withWorkflow({ name: workflowName.replace(/\.workflow$/, "") }, async () => {
        const runtime: DifyRuntime = {
          baseUrl,
          isLocal: Boolean(local),
          key(name) {
            return envValue(name) ?? envValue("DIFY_API_KEY") ?? "local-dify-key";
          },
          setResult(value) {
            result = value;
          },
        };
        return await fn(runtime);
      }),
    );
  } finally {
    await respan.shutdown();
    await local?.close();
    await localRespanSink?.close();
    if (result !== undefined) {
      console.log(JSON.stringify({ workflowName, runId: RUN_ID, result }, null, 2));
    }
  }
}

interface LocalServer {
  baseUrl: string;
  close(): Promise<void>;
}

async function startLocalRespanSink(): Promise<LocalServer> {
  const server = createServer((request, response) => {
    request.resume();
    request.once("end", () => {
      response.statusCode = 200;
      response.end();
    });
  });
  await new Promise<void>((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", () => resolve());
  });
  const address = server.address();
  if (!address || typeof address === "string") {
    throw new Error("Failed to bind loopback Respan sink");
  }
  return {
    baseUrl: `http://127.0.0.1:${address.port}`,
    close: () => new Promise<void>((resolve, reject) => {
      server.close((error) => error ? reject(error) : resolve());
    }),
  };
}

async function startLocalDifyServer(): Promise<LocalServer> {
  const server = createServer(async (request, response) => {
    try {
      await handleRequest(request, response);
    } catch (error) {
      sendJson(response, { message: error instanceof Error ? error.message : String(error) }, 500);
    }
  });
  await new Promise<void>((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", () => resolve());
  });
  const address = server.address();
  if (!address || typeof address === "string") throw new Error("Failed to bind loopback Dify server");
  return {
    baseUrl: `http://127.0.0.1:${address.port}`,
    close: () => new Promise<void>((resolve, reject) => {
      server.close((error) => error ? reject(error) : resolve());
    }),
  };
}

async function handleRequest(request: IncomingMessage, response: ServerResponse): Promise<void> {
  const url = new URL(request.url ?? "/", "http://127.0.0.1");
  const body = await readBody(request);
  const json = parseJson(body);

  if (request.method === "POST" && url.pathname === "/chat-messages") {
    if (String(json.query ?? "").toLowerCase().includes("expected error")) {
      sendJson(response, { message: "Deterministic Dify example error" }, 429);
      return;
    }
    if (json.response_mode === "streaming") {
      sendSse(response, [
        { event: "message", task_id: "task-chat-stream", message_id: "msg-chat-stream", conversation_id: "conv-chat-stream", answer: "Streaming " },
        { event: "message", task_id: "task-chat-stream", message_id: "msg-chat-stream", conversation_id: "conv-chat-stream", answer: "Dify response." },
        { event: "message_end", task_id: "task-chat-stream", message_id: "msg-chat-stream", conversation_id: "conv-chat-stream", metadata: { usage: usage(7, 4) } },
      ]);
      return;
    }
    sendJson(response, {
      event: "message",
      task_id: "task-chat-blocking",
      message_id: "msg-chat-blocking",
      conversation_id: "conv-chat-blocking",
      mode: "chat",
      answer: `Hello ${json.user ?? "local-user"}. Dify TypeScript tracing is active.`,
      metadata: { usage: usage(8, 6) },
    });
    return;
  }

  if (request.method === "POST" && url.pathname === "/completion-messages") {
    sendJson(response, {
      event: "message",
      task_id: "task-completion",
      message_id: "msg-completion",
      mode: "completion",
      answer: "Dify completion tracing is active.",
      metadata: { usage: usage(6, 5) },
    });
    return;
  }

  if (request.method === "POST" && url.pathname === "/workflows/run") {
    if (json.response_mode === "streaming") {
      sendSse(response, [
        { event: "workflow_started", task_id: "task-workflow", workflow_run_id: "workflow-run-local" },
        { event: "workflow_finished", task_id: "task-workflow", workflow_run_id: "workflow-run-local", data: { status: "succeeded", outputs: { result: "Workflow stream finished." }, total_tokens: 12, total_steps: 3 } },
      ]);
      return;
    }
    sendJson(response, {
      task_id: "task-workflow",
      workflow_run_id: "workflow-run-local",
      data: { status: "succeeded", outputs: { result: "Workflow blocking result." }, total_tokens: 12, total_steps: 3 },
    });
    return;
  }

  if (request.method === "POST" && url.pathname.endsWith("/pipeline/run")) {
    if (json.response_mode === "streaming") {
      sendSse(response, [
        { event: "workflow_started", task_id: "task-rag", workflow_run_id: "rag-run-local" },
        { event: "workflow_finished", task_id: "task-rag", workflow_run_id: "rag-run-local", data: { status: "succeeded", outputs: { documents: 1 }, total_steps: 2 } },
      ]);
      return;
    }
    sendJson(response, {
      task_id: "task-rag",
      workflow_run_id: "rag-run-local",
      data: { status: "succeeded", outputs: { documents: 1 }, total_steps: 2 },
    });
    return;
  }

  if (request.method === "GET" && url.pathname === "/datasets") {
    sendJson(response, { data: [{ id: "dataset-local", name: "Local tracing knowledge base" }], page: 1, limit: 20, total: 1 });
    return;
  }
  if (request.method === "GET" && url.pathname.startsWith("/workspaces/current/models/model-types/")) {
    sendJson(response, { data: [{ provider: "local", model: "dify/local-test-model", model_type: "llm" }] });
    return;
  }
  if (request.method === "GET" && url.pathname === "/parameters") {
    sendJson(response, { opening_statement: "Local Dify app ready.", user_input_form: [] });
    return;
  }
  if (request.method === "POST" && url.pathname === "/files/upload") {
    sendJson(response, { id: "upload-local", name: "sample.txt", size: body.length, extension: "txt", mime_type: "text/plain" });
    return;
  }

  sendJson(response, { message: `Unhandled ${request.method} ${url.pathname}` }, 404);
}

function usage(promptTokens: number, completionTokens: number): JsonRecord {
  return {
    model: "dify/local-test-model",
    prompt_tokens: promptTokens,
    completion_tokens: completionTokens,
    total_tokens: promptTokens + completionTokens,
    latency: 0.01,
  };
}

async function readBody(request: IncomingMessage): Promise<Buffer> {
  const chunks: Buffer[] = [];
  for await (const chunk of request) chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
  return Buffer.concat(chunks);
}

function parseJson(body: Buffer): JsonRecord {
  if (!body.length) return {};
  try {
    return JSON.parse(body.toString("utf8"));
  } catch {
    return {};
  }
}

function sendJson(response: ServerResponse, body: unknown, status = 200): void {
  const payload = Buffer.from(JSON.stringify(body));
  response.writeHead(status, {
    "content-type": "application/json",
    "content-length": payload.length,
    connection: "close",
  });
  response.end(payload);
}

function sendSse(response: ServerResponse, events: unknown[]): void {
  response.writeHead(200, {
    "content-type": "text/event-stream",
    "cache-control": "no-cache",
    connection: "close",
  });
  for (const event of events) response.write(`data: ${JSON.stringify(event)}\n\n`);
  response.end();
}
