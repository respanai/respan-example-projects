import { createServer } from "node:http";
import { gunzipSync } from "node:zlib";
import type { AddressInfo } from "node:net";

/** A controlled provider HTTP endpoint; every client call uses the released SDK. */
export async function startFixture() {
  const captured: unknown[] = [];
  const server = createServer(async (request, response) => {
    const parts: Buffer[] = [];
    for await (const part of request) parts.push(Buffer.from(part));
    let body = Buffer.concat(parts);
    if (request.headers["content-encoding"] === "gzip") body = gunzipSync(body);
    let input: any = {};
    try {
      input = JSON.parse(body.toString("utf8"));
    } catch {}
    response.setHeader("content-type", "application/json");
    if (request.url?.includes("traces")) {
      captured.push(input);
      response.end("{}");
      return;
    }
    const text = JSON.stringify(input.messages ?? input.input ?? "");
    if (text.includes("CONTROLLED_FAILURE")) {
      response.statusCode = 422;
      response.end(
        JSON.stringify({
          error: {
            message: "controlled native provider failure",
            type: "invalid_request_error",
          },
        }),
      );
      return;
    }
    if (request.url?.endsWith("/embeddings")) {
      const values = Array.from({ length: 5001 }, (_, index) =>
        index === 0 ? 0 : index / 5001,
      );
      const embedding =
        input.encoding_format === "base64"
          ? Buffer.from(new Float32Array(values).buffer).toString("base64")
          : values;
      response.end(
        JSON.stringify({
          object: "list",
          data: input.input.map((_: unknown, index: number) => ({
            object: "embedding",
            index,
            embedding,
          })),
          usage: { prompt_tokens: 3, total_tokens: 3 },
        }),
      );
      return;
    }
    if (request.url?.endsWith("/responses")) {
      response.end(
        JSON.stringify({
          id: "native-response",
          object: "response",
          model: input.model,
          status: "completed",
          output: [
            {
              type: "message",
              id: "native-message",
              role: "assistant",
              content: [
                {
                  type: "output_text",
                  text: "Native Responses answer",
                  annotations: [],
                },
              ],
            },
          ],
          usage: { input_tokens: 4, output_tokens: 2, total_tokens: 6 },
        }),
      );
      return;
    }
    if (input.stream) {
      response.setHeader("content-type", "text/event-stream");
      for (const chunk of [
        {
          choices: [
            {
              index: 0,
              delta: { role: "assistant", content: "Native " },
              finish_reason: null,
            },
          ],
        },
        {
          choices: [
            { index: 0, delta: { content: "stream" }, finish_reason: "stop" },
          ],
        },
        {
          choices: [],
          usage: { prompt_tokens: 0, completion_tokens: 2, total_tokens: 2 },
        },
      ])
        response.write(
          `data: ${JSON.stringify({ id: "native-stream", model: input.model, ...chunk })}\n\n`,
        );
      response.end("data: [DONE]\n\n");
      return;
    }
    const alreadyUsedTool = input.messages?.some(
      (message: any) => message.role === "tool",
    );
    const useTool =
      text.includes("USE_NATIVE_TOOL") &&
      input.tools?.length &&
      !alreadyUsedTool;
    const message = useTool
      ? {
          role: "assistant",
          content: null,
          tool_calls: [
            {
              id: "native-lookup-call",
              type: "function",
              function: { name: "lookup", arguments: '{"topic":"Respan"}' },
            },
          ],
        }
      : { role: "assistant", content: "Respan traces native AI applications." };
    response.end(
      JSON.stringify({
        id: "native-chat",
        object: "chat.completion",
        model: input.model,
        choices: [
          { index: 0, message, finish_reason: useTool ? "tool_calls" : "stop" },
        ],
        usage: {
          prompt_tokens: 0,
          completion_tokens: 5,
          total_tokens: 5,
          prompt_tokens_details: { cached_tokens: 0 },
        },
      }),
    );
  });
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  return {
    baseURL: `http://127.0.0.1:${(server.address() as AddressInfo).port}`,
    captured,
    close: () =>
      new Promise<void>((resolve, reject) =>
        server.close((error) => (error ? reject(error) : resolve())),
      ),
  };
}
