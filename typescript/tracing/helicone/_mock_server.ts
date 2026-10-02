import { createServer, type IncomingMessage, type ServerResponse } from "node:http";

export interface CapturedHeliconeLog {
  path: string;
  body: Record<string, unknown>;
}

export interface MockHeliconeServer {
  baseUrl: string;
  logs: CapturedHeliconeLog[];
  close(): Promise<void>;
}

export async function startMockHeliconeServer(): Promise<MockHeliconeServer> {
  const logs: CapturedHeliconeLog[] = [];
  const server = createServer(async (request, response) => {
    await handleRequest(request, response, logs);
  });

  await new Promise<void>((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", () => resolve());
  });
  const address = server.address();
  if (!address || typeof address === "string") {
    throw new Error("Mock Helicone server did not expose a TCP address.");
  }

  return {
    baseUrl: `http://127.0.0.1:${address.port}`,
    logs,
    close: async () => {
      await new Promise<void>((resolve, reject) => {
        server.close((error) => error ? reject(error) : resolve());
      });
    },
  };
}

async function handleRequest(
  request: IncomingMessage,
  response: ServerResponse,
  logs: CapturedHeliconeLog[],
): Promise<void> {
  if (request.method !== "POST" || !request.url?.endsWith("/v1/log")) {
    response.writeHead(404).end();
    return;
  }

  const chunks: Buffer[] = [];
  for await (const chunk of request) chunks.push(Buffer.from(chunk));
  const text = Buffer.concat(chunks).toString("utf8");
  logs.push({
    path: request.url,
    body: text ? JSON.parse(text) as Record<string, unknown> : {},
  });
  response.writeHead(204).end();
}
