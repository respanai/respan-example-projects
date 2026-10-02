import { createServer, type IncomingMessage, type Server, type ServerResponse } from "node:http";

async function body(request: IncomingMessage): Promise<Record<string, unknown>> {
  const chunks: Buffer[] = [];
  for await (const chunk of request) chunks.push(Buffer.from(chunk));
  if (chunks.length === 0) return {};
  return JSON.parse(Buffer.concat(chunks).toString("utf8"));
}

function json(response: ServerResponse, status: number, payload: unknown): void {
  const encoded = JSON.stringify(payload);
  response.writeHead(status, {
    "content-type": "application/json",
    "content-length": Buffer.byteLength(encoded),
  });
  response.end(encoded);
}

function sse(response: ServerResponse, chunks: unknown[]): void {
  const encoded = `${chunks.map((chunk) => `data: ${JSON.stringify(chunk)}\n\n`).join("")}data: [DONE]\n\n`;
  response.writeHead(200, {
    "content-type": "text/event-stream",
    "content-length": Buffer.byteLength(encoded),
  });
  response.end(encoded);
}

function agentRun(status: "queued" | "completed", request?: unknown): Record<string, unknown> {
  return {
    id: "run-loopback",
    object: "agent.run",
    status,
    request,
    output: status === "completed" ? { text: "Deterministic agent result." } : undefined,
    usage: status === "completed" ? { agentComputeUnits: 1, searches: 1 } : undefined,
    costDollars:
      status === "completed"
        ? { total: 0.012, agentCompute: 0.005, search: 0.007 }
        : undefined,
  };
}

async function handle(request: IncomingMessage, response: ServerResponse): Promise<void> {
  const url = new URL(request.url ?? "/", "http://127.0.0.1");
  const payload = request.method === "POST" ? await body(request) : {};
  if (payload.query === "expected Exa provider error") {
    json(response, 429, { error: "deterministic Exa rate limit" });
    return;
  }

  if (request.method === "POST" && url.pathname === "/search") {
    if (payload.stream) {
      sse(response, [
        { choices: [{ delta: { content: "loopback " } }] },
        {
          choices: [{ delta: { content: "search" } }],
          citations: [
            {
              id: "source-1",
              url: "https://example.com/search",
              title: "Loopback source",
            },
          ],
        },
      ]);
      return;
    }
    json(response, 200, {
      results: [
        {
          id: "https://example.com/search",
          url: "https://example.com/search",
          title: "Loopback search result",
          text: "Deterministic Exa search content.",
          highlights: ["Deterministic Exa search content."],
        },
      ],
      requestId: "loopback-search-request",
      resolvedSearchType: payload.type ?? "auto",
      costDollars: { total: 0.007, search: { neural: 0.007 } },
    });
    return;
  }

  if (request.method === "POST" && url.pathname === "/contents") {
    const urls = Array.isArray(payload.urls) ? payload.urls : [];
    json(response, 200, {
      results: urls.map((item) => ({
        id: item,
        url: item,
        title: "Loopback page",
        text: "Deterministic page contents for instrumentation.",
        highlights: ["Deterministic page contents."],
      })),
      requestId: "loopback-contents-request",
      costDollars: { total: 0.001, contents: { text: 0.001 } },
    });
    return;
  }

  if (request.method === "POST" && url.pathname === "/answer") {
    if (payload.stream) {
      sse(response, [
        { choices: [{ delta: { content: "loopback " } }] },
        {
          choices: [{ delta: { content: "answer" } }],
          citations: [
            {
              id: "answer-source",
              url: "https://example.com/answer",
              title: "Answer source",
            },
          ],
        },
      ]);
      return;
    }
    json(response, 200, {
      answer: "A deterministic grounded answer.",
      citations: [
        {
          id: "answer-source",
          url: "https://example.com/answer",
          title: "Answer source",
        },
      ],
      costDollars: { total: 0.005 },
    });
    return;
  }

  if (request.method === "POST" && url.pathname === "/agent/runs") {
    if (request.headers.accept === "text/event-stream") {
      sse(response, [
        { id: "event-1", event: "run.started", data: { id: "run-loopback" } },
        {
          id: "event-2",
          event: "run.completed",
          data: { id: "run-loopback", output: { text: "agent result" } },
        },
      ]);
      return;
    }
    json(response, 200, agentRun("queued", payload));
    return;
  }

  if (request.method === "GET" && url.pathname === "/agent/runs/run-loopback") {
    json(response, 200, agentRun("completed"));
    return;
  }

  if (request.method === "POST" && url.pathname === "/research/v1") {
    json(response, 200, {
      researchId: "research-loopback",
      createdAt: Date.now(),
      model: payload.model ?? "exa-research-fast",
      instructions: payload.instructions ?? "loopback research",
      status: "pending",
    });
    return;
  }

  if (request.method === "GET" && url.pathname === "/research/v1/research-loopback") {
    json(response, 200, {
      researchId: "research-loopback",
      createdAt: Date.now(),
      model: "exa-research-fast",
      instructions: "Create a deterministic research brief.",
      status: "completed",
      output: { content: "Deterministic legacy research output." },
      costDollars: {
        total: 0.02,
        numPages: 1,
        numSearches: 1,
        reasoningTokens: 32,
      },
    });
    return;
  }

  json(response, 404, { error: `Unhandled ${request.method} ${url.pathname}` });
}

export interface MockExaServer {
  baseURL: string;
  close: () => Promise<void>;
}

export async function startMockExaServer(): Promise<MockExaServer> {
  const server: Server = createServer((request, response) => {
    void handle(request, response).catch((error) => {
      json(response, 500, { error: error instanceof Error ? error.message : String(error) });
    });
  });
  await new Promise<void>((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", () => resolve());
  });
  const address = server.address();
  if (!address || typeof address === "string") throw new Error("No mock Exa address");
  return {
    baseURL: `http://127.0.0.1:${address.port}`,
    close: () => new Promise<void>((resolve, reject) => server.close((error) => (error ? reject(error) : resolve()))),
  };
}
