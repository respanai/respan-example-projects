import assert from "node:assert/strict";
import http from "node:http";
import { writeFile } from "node:fs/promises";
import { context } from "@opentelemetry/api";
import { CONTEXT_KEY_ALLOW_TRACE_CONTENT } from "@traceloop/ai-semantic-conventions";
import { BraintrustInstrumentor } from "@respan/instrumentation-braintrust";
import { Respan } from "@respan/respan";
import OpenAI from "openai";

// Explicit fixture settings prevent native SDK environment-file discovery.
process.env.BRAINTRUST_ENVIRONMENT_TYPE = "development";
process.env.BRAINTRUST_ENVIRONMENT_NAME = "respan-fixture";
export const bt = await import("braintrust");
export const EXAMPLE_RUN_ID =
  process.env.RESPAN_EXAMPLE_RUN_ID ?? `braintrust-ts-${Date.now()}`;
export const MODEL = "fixture-model";
export const tools = Array.from({ length: 82 }, (_, index) => ({
  type: "function" as const,
  function: {
    name: `tool_${index}`,
    description: `Fixture tool ${index}`,
    parameters: { type: "object", properties: { value: { type: "number" } } },
  },
}));
export const messages: OpenAI.ChatCompletionMessageParam[] = Array.from(
  { length: 80 },
  (_, index) => ({
    role: "user" as const,
    content: [
      { type: "text" as const, text: `Fixture message ${index}` },
      {
        type: "image_url" as const,
        image_url: { url: `data:image/png;base64,fixture${index}` },
      },
    ],
  }),
);

if (process.env.RESPAN_EXAMPLE_DEBUG !== "1") {
  for (const method of ["debug", "info", "log"] as const) {
    const original = console[method].bind(console);
    console[method] = (...args: unknown[]) => {
      if (typeof args[0] === "string" && args[0].startsWith("[Respan")) return;
      original(...args);
    };
  }
}

export async function runScenario(
  name: string,
  fn: (
    logger: ReturnType<typeof bt.initLogger>,
    client: ReturnType<typeof bt.wrapOpenAI<OpenAI>>,
    instrumentor: BraintrustInstrumentor,
  ) => Promise<unknown>,
): Promise<void> {
  const captured: any[] = [];
  let base = "";
  const server = http.createServer(async (req, res) => {
    const chunks: Buffer[] = [];
    for await (const chunk of req) chunks.push(Buffer.from(chunk));
    const body = JSON.parse(Buffer.concat(chunks).toString() || "{}");
    res.setHeader("content-type", "application/json");
    if (Array.isArray(body.resourceSpans)) {
      for (const resource of body.resourceSpans)
        for (const scope of resource.scopeSpans ?? [])
          for (const span of scope.spans ?? [])
            captured.push({ ...span, scope: scope.scope });
      return res.end("{}");
    }
    if (req.url === "/api/apikey/login")
      return res.end(
        JSON.stringify({
          org_info: [{ id: "fixture-org", name: "fixture", api_url: base }],
        }),
      );
    if (req.url?.startsWith("/api/project"))
      return res.end(
        JSON.stringify({ id: "fixture-project", name: "fixture", project: {} }),
      );
    if (req.url !== "/v1/chat/completions") {
      res.statusCode = 404;
      return res.end("{}");
    }
    if (body.model === "fixture-error") {
      res.statusCode = 400;
      return res.end(
        JSON.stringify({
          error: {
            message: "Controlled fixture error",
            type: "invalid_request_error",
          },
        }),
      );
    }
    if (body.stream) {
      res.setHeader("content-type", "text/event-stream");
      for (const [index, content] of ["Fixture", " stream"].entries())
        res.write(
          `data: ${JSON.stringify({ id: "fixture-stream", object: "chat.completion.chunk", created: 1, model: MODEL, choices: [{ index: 0, delta: { ...(index === 0 ? { role: "assistant" } : {}), content }, finish_reason: index === 1 ? "stop" : null }], ...(index === 1 ? { usage: { prompt_tokens: 0, completion_tokens: 2, total_tokens: 9 } } : {}) })}\n\n`,
        );
      return res.end("data: [DONE]\n\n");
    }
    res.end(
      JSON.stringify({
        id: "fixture-chat",
        object: "chat.completion",
        created: 1,
        model: MODEL,
        choices: [
          {
            index: 0,
            message: {
              role: "assistant",
              content: "Fixture answer",
              tool_calls: [
                {
                  id: "call_fixture",
                  type: "function",
                  function: { name: "tool_81", arguments: '{"value":0}' },
                },
              ],
            },
            finish_reason: "tool_calls",
          },
        ],
        usage: { prompt_tokens: 3, completion_tokens: 2, total_tokens: 17 },
      }),
    );
  });
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  base = `http://127.0.0.1:${(server.address() as { port: number }).port}`;
  const instrumentor = new BraintrustInstrumentor();
  const exporting = process.env.RESPAN_EXAMPLE_EXPORT === "1";
  if (exporting && !process.env.RESPAN_API_KEY)
    throw new Error(
      "RESPAN_EXAMPLE_EXPORT=1 requires RESPAN_API_KEY in the process environment",
    );
  const respan = new Respan({
    apiKey: exporting ? process.env.RESPAN_API_KEY : "fixture-only",
    baseURL: exporting ? process.env.RESPAN_BASE_URL : base,
    appName: "braintrust-typescript-examples",
    silenceInitializationMessage: true,
    logLevel: "error",
    instrumentations: [instrumentor],
  });
  try {
    await respan.initialize();
    const logger = bt.initLogger({
      projectId: "00000000-0000-4000-8000-000000000001",
      projectName: "fixture",
      apiKey: "fixture-only",
      appUrl: base,
    });
    const client = bt.wrapOpenAI(
      new OpenAI({
        apiKey: "fixture-only",
        baseURL: `${base}/v1`,
        maxRetries: 0,
      }),
    );
    const result = await respan.propagateAttributes(
      {
        custom_identifier: EXAMPLE_RUN_ID,
        trace_group_identifier: `${EXAMPLE_RUN_ID}.${name}`,
        metadata: {
          run_id: EXAMPLE_RUN_ID,
          example: "braintrust-typescript",
          scenario: name,
        },
      },
      () =>
        respan.withWorkflow({ name: `braintrust-${name}` }, async () => {
          try {
            return await fn(logger, client, instrumentor);
          } finally {
            await logger.flush();
            await instrumentor.flush();
          }
        }),
    );
    await respan.flush();
    if (process.env.RESPAN_EXAMPLE_CAPTURE)
      await writeFile(
        process.env.RESPAN_EXAMPLE_CAPTURE,
        JSON.stringify(
          { runId: EXAMPLE_RUN_ID, scenario: name, spans: captured },
          null,
          2,
        ),
      );
    console.log(
      JSON.stringify({
        runId: EXAMPLE_RUN_ID,
        scenario: name,
        spans: captured.length,
        exporting,
        result,
      }),
    );
  } finally {
    await instrumentor.deactivate();
    await respan.shutdown();
    await new Promise<void>((resolve) => server.close(() => resolve()));
  }
}

export async function withoutContent<T>(fn: () => Promise<T>): Promise<T> {
  return context.with(
    context.active().setValue(CONTEXT_KEY_ALLOW_TRACE_CONTENT, false),
    fn,
  );
}
export { assert };
