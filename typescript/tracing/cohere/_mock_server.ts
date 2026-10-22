import http from "node:http";
import { AddressInfo } from "node:net";

export interface MockCohereServer {
  baseUrl: string;
  close: () => Promise<void>;
}

function jsonResponse(
  res: http.ServerResponse,
  status: number,
  body: unknown,
): void {
  res.writeHead(status, { "content-type": "application/json" });
  res.end(JSON.stringify(body));
}

function jsonStreamResponse(res: http.ServerResponse, events: unknown[]): void {
  res.writeHead(200, { "content-type": "application/json" });
  for (const event of events) {
    res.write(`${JSON.stringify(event)}\n`);
  }
  res.end();
}

function sseResponse(res: http.ServerResponse, events: unknown[]): void {
  res.writeHead(200, { "content-type": "text/event-stream" });
  for (const event of events as Array<Record<string, unknown>>) {
    res.write(`event: ${event.type}\n`);
    res.write(`data: ${JSON.stringify(event)}\n\n`);
  }
  res.write("data: [DONE]\n\n");
  res.end();
}

async function readJson(
  req: http.IncomingMessage,
): Promise<Record<string, any>> {
  const chunks: Buffer[] = [];
  for await (const chunk of req) {
    chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
  }
  const body = Buffer.concat(chunks).toString("utf8");
  return body.trim() ? JSON.parse(body) : {};
}

function v2ChatBody(body: Record<string, any>): Record<string, any> {
  if (body.model === "force-error") {
    return { error: "forced mock Cohere error" };
  }

  return {
    id: "mock-chat-v2",
    finish_reason: "COMPLETE",
    message: {
      role: "assistant",
      content: [{ type: "text", text: "Mock Cohere v2 response." }],
      tool_calls: body.tools?.length
        ? [
            {
              id: "call_mock_1",
              type: "function",
              function: {
                name: body.tools[0].function?.name ?? "lookup_docs",
                arguments: JSON.stringify({ topic: "respan" }),
              },
            },
          ]
        : undefined,
    },
    usage: {
      billed_units: { input_tokens: 5, output_tokens: 6 },
      tokens: { input_tokens: 11, output_tokens: 6 },
      cached_tokens: 1,
    },
  };
}

function v2ChatStreamEvents(): unknown[] {
  return [
    {
      type: "message-start",
      id: "mock-stream-v2",
      delta: { message: { role: "assistant" } },
    },
    {
      type: "content-start",
      index: 0,
      delta: { message: { content: { type: "text", text: "" } } },
    },
    {
      type: "content-delta",
      index: 0,
      delta: { message: { content: { text: "Mock " } } },
    },
    {
      type: "content-delta",
      index: 0,
      delta: { message: { content: { text: "streaming response." } } },
    },
    { type: "content-end", index: 0 },
    {
      type: "tool-call-start",
      index: 0,
      delta: {
        message: {
          tool_calls: {
            id: "stream_call_1",
            type: "function",
            function: { name: "lookup_docs", arguments: "" },
          },
        },
      },
    },
    {
      type: "tool-call-delta",
      index: 0,
      delta: {
        message: { tool_calls: { function: { arguments: '{"topic":' } } },
      },
    },
    {
      type: "tool-call-delta",
      index: 0,
      delta: {
        message: { tool_calls: { function: { arguments: '"respan"}' } } },
      },
    },
    { type: "tool-call-end", index: 0 },
    {
      type: "message-end",
      delta: {
        finish_reason: "COMPLETE",
        usage: {
          billed_units: { input_tokens: 4, output_tokens: 3 },
          tokens: { input_tokens: 9, output_tokens: 3 },
        },
      },
    },
  ];
}

function v1GenerateBody(): Record<string, any> {
  return {
    id: "mock-generate-v1",
    prompt: "Write a concise status.",
    generations: [
      { text: "Mock legacy generation response.", finish_reason: "COMPLETE" },
      { text: "", finish_reason: "COMPLETE" },
    ],
    meta: {
      billed_units: { input_tokens: 4, output_tokens: 5 },
      tokens: { input_tokens: 6, output_tokens: 5 },
    },
  };
}

function v1GenerateStreamEvents(): unknown[] {
  return [
    { event_type: "text-generation", text: "Mock " },
    { event_type: "text-generation", text: "legacy stream response." },
    { event_type: "stream-end", response: v1GenerateBody() },
  ];
}

function embedBody(body: Record<string, any>): Record<string, any> {
  return {
    id: "mock-embed",
    response_type: "embeddings_by_type",
    embeddings: {
      float: [Array.from({ length: 5001 }, (_, i) => i / 5001)],
      int8: [[0, -1, 127]],
      uint8: [[0, 255]],
      binary: [[0, -128]],
      ubinary: [[0, 255]],
    },
    texts: body.texts ?? ["hello"],
    meta: { billed_units: { input_tokens: 3 } },
  };
}

function rerankBody(): Record<string, any> {
  return {
    id: "mock-rerank",
    results: [
      {
        index: 1,
        relevance_score: 0,
        document: { text: "", extra: "preserved" },
      },
    ],
    meta: { billed_units: { search_units: 1 } },
  };
}

export async function startMockCohereServer(): Promise<MockCohereServer> {
  const server = http.createServer(async (req, res) => {
    try {
      const body = await readJson(req);
      const path = new URL(req.url ?? "/", "http://localhost").pathname;

      if (path === "/v2/parse") {
        jsonResponse(res, 200, {
          id: "mock-parse",
          pages: [
            {
              type: "markdown",
              index: 0,
              markdown: { content: "# Parsed document", images: [] },
            },
          ],
        });
        return;
      }
      if (path === "/v1/chat" && body.stream === true) {
        jsonStreamResponse(res, [
          {
            event_type: "text-generation",
            text: "Mock v1 streaming response.",
          },
          {
            event_type: "stream-end",
            response: {
              text: "Mock v1 streaming response.",
              generation_id: "mock-v1-stream",
              meta: { tokens: { input_tokens: 0, output_tokens: 2 } },
            },
          },
        ]);
        return;
      }
      if (path === "/v2/chat" && body.stream === true) {
        sseResponse(res, v2ChatStreamEvents());
        return;
      }
      if (path === "/v2/chat") {
        if (body.model === "force-error") {
          jsonResponse(res, 400, { message: "forced mock Cohere error" });
          return;
        }
        jsonResponse(res, 200, v2ChatBody(body));
        return;
      }
      if (path === "/v2/embed" || path === "/v1/embed") {
        jsonResponse(res, 200, embedBody(body));
        return;
      }
      if (path === "/v2/rerank" || path === "/v1/rerank") {
        jsonResponse(res, 200, rerankBody());
        return;
      }
      if (path === "/v1/generate" && body.stream === true) {
        jsonStreamResponse(res, v1GenerateStreamEvents());
        return;
      }
      if (path === "/v1/generate") {
        jsonResponse(res, 200, v1GenerateBody());
        return;
      }
      if (path === "/v1/chat") {
        jsonResponse(res, 200, {
          text: "Mock Cohere v1 chat response.",
          generation_id: "mock-v1-chat",
          meta: { tokens: { input_tokens: 6, output_tokens: 5 } },
        });
        return;
      }

      jsonResponse(res, 404, { message: `Unhandled mock path: ${path}` });
    } catch (error) {
      jsonResponse(res, 500, {
        message: error instanceof Error ? error.message : String(error),
      });
    }
  });

  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  const address = server.address() as AddressInfo;
  return {
    baseUrl: `http://127.0.0.1:${address.port}`,
    close: () => new Promise((resolve) => server.close(() => resolve())),
  };
}
