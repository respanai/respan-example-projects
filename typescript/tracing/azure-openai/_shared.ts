import * as OpenAIModule from "openai";
import { AzureOpenAI } from "openai";
import { Respan } from "@respan/respan";
import { AzureOpenAIInstrumentor } from "@respan/instrumentation-azure-openai";
import { createServer } from "node:http";
import { appendFile } from "node:fs/promises";
import { context, trace } from "@opentelemetry/api";
import { SpanAttributes } from "@traceloop/ai-semantic-conventions";
import { ATTR_GEN_AI_TOOL_CALL_ID } from "@opentelemetry/semantic-conventions/incubating";

export const RUN_ID =
  process.env.RESPAN_EXAMPLE_RUN_ID || `azure-openai-ts-${Date.now()}`;
const live = process.env.RESPAN_AZURE_LIVE === "1";
const exporting = process.env.RESPAN_EXAMPLE_EXPORT === "1";

export async function createRespan(appName: string): Promise<Respan> {
  if (exporting && !process.env.RESPAN_API_KEY)
    throw new Error("Set RESPAN_API_KEY for explicit trace export.");
  const collector = exporting
    ? undefined
    : createServer(async (request, response) => {
        const chunks: Buffer[] = [];
        for await (const chunk of request) chunks.push(Buffer.from(chunk));
        const payload = JSON.parse(Buffer.concat(chunks).toString());
        if (process.env.RESPAN_EXAMPLE_CAPTURE)
          await appendFile(
            process.env.RESPAN_EXAMPLE_CAPTURE,
            JSON.stringify({ runId: RUN_ID, payload }) + "\n",
          );
        response.writeHead(200, { "content-type": "application/json" });
        response.end("{}");
      });
  if (collector)
    await new Promise<void>((resolve) =>
      collector.listen(0, "127.0.0.1", resolve),
    );
  const address = collector?.address();
  const baseURL = exporting
    ? process.env.RESPAN_BASE_URL
    : (process.env.RESPAN_EXAMPLE_COLLECTOR_URL ??
      `http://127.0.0.1:${typeof address === "object" ? address?.port : 0}`);
  const respan = new Respan({
    apiKey: exporting ? process.env.RESPAN_API_KEY : "local-fixture-no-export",
    baseURL,
    appName,
    instrumentations: [
      new AzureOpenAIInstrumentor({ openAIModule: OpenAIModule }),
    ],
    silenceInitializationMessage: true,
  });
  const shutdown = respan.shutdown.bind(respan);
  respan.shutdown = async () => {
    try {
      await shutdown();
    } finally {
      if (collector)
        await new Promise<void>((resolve, reject) =>
          collector.close((error) => (error ? reject(error) : resolve())),
        );
    }
  };
  return respan;
}
export function createAzureClient(deployment = "deployment"): AzureOpenAI {
  if (
    live &&
    (!process.env.AZURE_OPENAI_API_KEY ||
      !process.env.AZURE_OPENAI_ENDPOINT ||
      !process.env.OPENAI_API_VERSION)
  )
    throw new Error(
      "Live mode requires AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT and OPENAI_API_VERSION.",
    );
  return new AzureOpenAI({
    apiKey: live ? process.env.AZURE_OPENAI_API_KEY : "azure-fixture",
    endpoint: live
      ? process.env.AZURE_OPENAI_ENDPOINT
      : "https://fixture.openai.azure.com",
    apiVersion: process.env.OPENAI_API_VERSION || "2024-10-21",
    deployment,
    maxRetries: 0,
    ...(live ? {} : { fetch: fixtureFetch }),
  });
}
export async function runWithExampleTrace<T>(
  respan: Respan,
  name: string,
  fn: () => Promise<T>,
): Promise<T> {
  return respan.propagateAttributes(
    {
      trace_group_identifier: name,
      custom_identifier: RUN_ID,
      metadata: {
        example: "typescript-azure-openai",
        run_id: RUN_ID,
        workflow_name: name,
      },
    },
    () => respan.withWorkflow({ name }, fn),
  );
}
export function logExampleResult(
  workflowName: string,
  details: Record<string, unknown>,
): void {
  console.log(JSON.stringify({ workflowName, runId: RUN_ID, ...details }));
}
export function stampTool(callID: string, name: string, args: unknown): void {
  const span = trace.getSpan(context.active());
  span?.setAttribute(ATTR_GEN_AI_TOOL_CALL_ID, callID);
  span?.setAttribute(
    SpanAttributes.TRACELOOP_ENTITY_INPUT,
    JSON.stringify({ name, arguments: args }),
  );
}
const completion = (content: string) => ({
  id: "chat-fixture",
  object: "chat.completion",
  created: 1,
  model: "fixture-model",
  choices: [
    {
      index: 0,
      message: { role: "assistant", content },
      finish_reason: "stop",
    },
  ],
  usage: { prompt_tokens: 18, completion_tokens: 11, total_tokens: 29 },
});
const response = () => ({
  id: "resp-fixture",
  object: "response",
  created_at: 1,
  status: "completed",
  model: "fixture-model",
  output: [
    {
      id: "msg-fixture",
      type: "message",
      role: "assistant",
      status: "completed",
      content: [
        { type: "output_text", text: "Responses captured", annotations: [] },
      ],
    },
  ],
  usage: { input_tokens: 2, output_tokens: 3, total_tokens: 5 },
});
const json = (value: unknown, status = 201) =>
  new Response(JSON.stringify(value), {
    status,
    headers: {
      "content-type": "application/json",
      "x-request-id": "fixture-request",
    },
  });
const sse = (values: unknown[]) =>
  new Response(
    values.map((value) => `data: ${JSON.stringify(value)}\n\n`).join("") +
      "data: [DONE]\n\n",
    { status: 202, headers: { "content-type": "text/event-stream" } },
  );
export const fixtureFetch: typeof fetch = async (url, init) => {
  const body = JSON.parse(String(init?.body));
  if (body.model === "fixture-error")
    return json(
      {
        error: {
          message: "Controlled fixture error",
          type: "invalid_request_error",
        },
      },
      429,
    );
  if (String(url).includes("/embeddings"))
    return json({
      object: "list",
      model: "fixture-embedding",
      data: [
        {
          index: 0,
          object: "embedding",
          embedding: Array.from({ length: 5001 }, (_, i) => i / 10000),
        },
        { index: 1, object: "embedding", embedding: [0, 0, 0] },
      ],
      usage: { prompt_tokens: 7, total_tokens: 7 },
    });
  if (String(url).includes("/responses")) {
    const result = response();
    return body.stream
      ? sse([
          { type: "response.created", response: { ...result, output: [] } },
          {
            type: "response.output_item.added",
            output_index: 0,
            item: {
              id: "msg-fixture",
              type: "message",
              role: "assistant",
              content: [],
            },
          },
          {
            type: "response.content_part.added",
            output_index: 0,
            content_index: 0,
            item_id: "msg-fixture",
            part: { type: "output_text", text: "", annotations: [] },
          },
          {
            type: "response.output_text.delta",
            output_index: 0,
            content_index: 0,
            item_id: "msg-fixture",
            delta: "Responses captured",
          },
          { type: "response.completed", response: result },
        ])
      : json(result);
  }
  if (String(url).includes("/chat/completions")) {
    if (body.stream)
      return sse([
        {
          id: "chat-fixture",
          object: "chat.completion.chunk",
          created: 1,
          model: "fixture-model",
          choices: [
            {
              index: 0,
              delta: {
                role: "assistant",
                content: "Looking up ",
                tool_calls: [
                  {
                    index: 0,
                    id: "call_city",
                    type: "function",
                    function: { name: "lookup_city", arguments: '{"city"' },
                  },
                ],
              },
              finish_reason: null,
            },
          ],
        },
        {
          id: "chat-fixture",
          object: "chat.completion.chunk",
          created: 1,
          model: "fixture-model",
          choices: [
            {
              index: 0,
              delta: {
                content: "city notes.",
                tool_calls: [
                  { index: 0, function: { arguments: ':"Seattle"}' } },
                ],
              },
              finish_reason: "tool_calls",
            },
          ],
          usage: { prompt_tokens: 22, completion_tokens: 6, total_tokens: 28 },
        },
      ]);
    return json(
      completion(
        body.messages.some((m: { role: string }) => m.role === "tool")
          ? "Seattle has active waterfront neighborhoods and frequent ferry traffic."
          : "Azure OpenAI native SDK tracing is active.",
      ),
    );
  }
  return json({
    id: "text-fixture",
    object: "text_completion",
    created: 1,
    model: "fixture-text",
    choices: [
      { index: 0, text: "Text completions captured", finish_reason: "stop" },
    ],
    usage: { prompt_tokens: 9, completion_tokens: 10, total_tokens: 19 },
  });
};
