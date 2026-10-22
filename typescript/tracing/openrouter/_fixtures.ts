export function chatFixture(body: any) {
  const tools = body.tools?.length;
  return {
    id: "controlled-chat-id",
    object: "chat.completion",
    created: 1,
    system_fingerprint: "controlled",
    model: "controlled/resolved-chat",
    choices: [
      {
        index: 0,
        message: tools
          ? {
              role: "assistant",
              content: null,
              tool_calls: [
                {
                  id: "controlled-tool-id",
                  type: "function",
                  function: {
                    name: body.tools[0].function.name,
                    arguments: '{"order_id":"OR-2048","destination":"Austin"}',
                  },
                },
              ],
            }
          : { role: "assistant", content: "Controlled OpenRouter response." },
        finish_reason: tools ? "tool_calls" : "stop",
      },
    ],
    usage: { prompt_tokens: 0, completion_tokens: 0, total_tokens: 0 },
  };
}
export function responseFixture(
  output: any[] = [
    {
      type: "message",
      id: "controlled-message",
      status: "completed",
      role: "assistant",
      content: [
        {
          type: "output_text",
          text: "Controlled Responses output.",
          annotations: [],
          logprobs: [],
        },
      ],
    },
  ],
  id = "controlled-response-id",
) {
  return {
    id,
    object: "response",
    created_at: 1,
    completed_at: 2,
    error: null,
    frequency_penalty: null,
    incomplete_details: null,
    instructions: null,
    metadata: null,
    model: "controlled/resolved-responses",
    output,
    parallel_tool_calls: false,
    presence_penalty: null,
    status: "completed",
    temperature: null,
    tool_choice: "auto",
    tools: [],
    top_p: null,
    usage: {
      input_tokens: 2,
      input_tokens_details: { cached_tokens: 0 },
      output_tokens: 1,
      output_tokens_details: { reasoning_tokens: 0 },
      total_tokens: 3,
    },
  };
}
export const fixtureFetch: typeof fetch = async (input, init) => {
  const request = input instanceof Request ? input : new Request(input, init);
  const body = await request.json();
  const endpoint = new URL(request.url).pathname;
  if (body.model === "controlled/error")
    return Response.json(
      { error: { code: 401, message: "Controlled authorization failure" } },
      { status: 401 },
    );
  if (endpoint.endsWith("/embeddings"))
    return Response.json({
      object: "list",
      model: "controlled/resolved-embedding",
      data: (Array.isArray(body.input) ? body.input : [body.input]).map(
        (_: unknown, index: number) => ({
          object: "embedding",
          index,
          embedding: Array.from({ length: 5001 }, (__, i) => i / 5001),
        }),
      ),
      usage: { prompt_tokens: 2, total_tokens: 2 },
    });
  if (endpoint.endsWith("/responses")) {
    const priorToolOutput =
      Array.isArray(body.input) &&
      body.input.some((item: any) => item.type === "function_call_output");
    return Response.json(
      body.tools?.length && !priorToolOutput
        ? responseFixture([
            {
              type: "function_call",
              id: "controlled-item",
              call_id: "controlled-call",
              name: "lookup",
              arguments: '{"q":"x"}',
              status: "completed",
            },
          ])
        : responseFixture(),
    );
  }
  if (body.stream) {
    const values = [
      { role: "assistant", content: "Controlled " },
      { content: "stream." },
      {},
    ].map((delta, index) => ({
      id: "controlled-stream-id",
      object: "chat.completion.chunk",
      created: 1,
      model: "controlled/resolved-stream",
      choices: [
        { index: 0, delta, finish_reason: index === 2 ? "stop" : null },
      ],
      ...(index === 2
        ? { usage: { prompt_tokens: 2, completion_tokens: 1, total_tokens: 3 } }
        : {}),
    }));
    let index = 0;
    const encoder = new TextEncoder();
    return new Response(
      new ReadableStream({
        pull(controller) {
          if (index < values.length)
            controller.enqueue(
              encoder.encode(`data: ${JSON.stringify(values[index++])}\n\n`),
            );
          else controller.close();
        },
      }),
      { headers: { "content-type": "text/event-stream" } },
    );
  }
  return Response.json(chatFixture(body));
};
