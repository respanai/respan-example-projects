import { ChatOpenAI, OpenAI } from "@langchain/openai";

export interface FixtureCall {
  id: string;
  name: string;
  args: Record<string, unknown>;
}
export type FixtureReply =
  | string
  | {
      toolCalls?: FixtureCall[];
      structured?: Record<string, unknown>;
      content?: string;
      error?: string;
    };

/** A controlled provider transport. The model, messages, callbacks and streams are released LangChain SDK objects. */
function fixtureFetch(replies: FixtureReply[]): typeof fetch {
  let index = 0;
  return async (url, init) => {
    const body = JSON.parse(String(init?.body ?? "{}"));
    const reply =
      replies[Math.min(index++, replies.length - 1)] ?? "Fixture response.";
    if (typeof reply === "object" && reply.error) {
      return new Response(
        JSON.stringify({
          error: { message: reply.error, type: "invalid_request_error" },
        }),
        { status: 429, headers: { "content-type": "application/json" } },
      );
    }
    const text =
      typeof reply === "string"
        ? reply
        : reply.structured
          ? JSON.stringify(reply.structured)
          : (reply.content ?? "");
    const calls =
      typeof reply === "object"
        ? (reply.toolCalls ??
          (reply.structured && body.tools?.length
            ? [
                {
                  id: "call_fixture_structured",
                  name: body.tools[0].function.name,
                  args: reply.structured,
                },
              ]
            : undefined))
        : undefined;
    const toolCalls = calls?.map((call) => ({
      id: call.id,
      type: "function",
      function: { name: call.name, arguments: JSON.stringify(call.args) },
    }));
    const completion =
      String(url).includes("/completions") &&
      !String(url).includes("/chat/completions");
    const base = {
      id: `fixture-${index}`,
      created: 0,
      model: body.model,
      usage: { prompt_tokens: 4, completion_tokens: 2, total_tokens: 6 },
    };
    const message = {
      role: "assistant",
      content: toolCalls ? "" : text,
      ...(toolCalls ? { tool_calls: toolCalls } : {}),
    };
    if (body.stream) {
      const delta = completion
        ? { text }
        : {
            delta: {
              ...message,
              ...(toolCalls
                ? {
                    tool_calls: toolCalls.map((call, i) => ({
                      index: i,
                      ...call,
                    })),
                  }
                : {}),
            },
          };
      const chunks = [
        {
          ...base,
          object: completion ? "text_completion" : "chat.completion.chunk",
          choices: [{ index: 0, ...delta, finish_reason: null }],
        },
        {
          ...base,
          object: completion ? "text_completion" : "chat.completion.chunk",
          choices: [
            {
              index: 0,
              ...(completion ? { text: "" } : { delta: {} }),
              finish_reason: toolCalls ? "tool_calls" : "stop",
            },
          ],
        },
        { ...base, object: "chat.completion.chunk", choices: [] },
      ];
      return new Response(
        chunks.map((chunk) => `data: ${JSON.stringify(chunk)}\n\n`).join("") +
          "data: [DONE]\n\n",
        { headers: { "content-type": "text/event-stream" } },
      );
    }
    return new Response(
      JSON.stringify({
        ...base,
        object: completion ? "text_completion" : "chat.completion",
        choices: [
          {
            index: 0,
            ...(completion ? { text } : { message }),
            finish_reason: toolCalls ? "tool_calls" : "stop",
          },
        ],
      }),
      { headers: { "content-type": "application/json" } },
    );
  };
}
export function chatModel(
  replies: FixtureReply[] = ["Fixture response."],
): ChatOpenAI {
  return new ChatOpenAI({
    model: "fixture-chat",
    apiKey: "fixture-local-only",
    maxRetries: 0,
    configuration: {
      baseURL: "http://fixture.invalid/v1",
      fetch: fixtureFetch(replies),
    },
  });
}
export function textModel(response: string): OpenAI {
  return new OpenAI({
    model: "fixture-text",
    apiKey: "fixture-local-only",
    maxRetries: 0,
    configuration: {
      baseURL: "http://fixture.invalid/v1",
      fetch: fixtureFetch([response]),
    },
  });
}
