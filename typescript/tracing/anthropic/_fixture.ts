import type Anthropic from "@anthropic-ai/sdk";
export const FIXTURE_MODEL = "claude-sonnet-5-5";
export const scalarValues = { enabled: false, count: 0, empty: "", nil: null };
const citation = {
  type: "char_location",
  cited_text: "fixture document",
  document_index: 0,
  document_title: "Fixture",
  start_char_index: 0,
  end_char_index: 16,
};
export function fixtureMessage(extra: Record<string, unknown> = {}) {
  return {
    id: "msg_fixture",
    type: "message",
    role: "assistant",
    model: FIXTURE_MODEL,
    content: [
      {
        type: "thinking",
        thinking: "Fixture thinking",
        signature: "fixture-signature",
      },
      { type: "redacted_thinking", data: "fixture-redacted" },
      {
        type: "text",
        text: JSON.stringify(scalarValues),
        citations: [citation],
      },
    ],
    stop_reason: "end_turn",
    stop_sequence: null,
    usage: {
      input_tokens: 0,
      output_tokens: 0,
      cache_read_input_tokens: 0,
      cache_creation_input_tokens: 0,
      cache_creation: {
        ephemeral_5m_input_tokens: 0,
        ephemeral_1h_input_tokens: 0,
      },
    },
    ...extra,
  };
}
export function streamEvents(tool = true, compaction = false) {
  return [
    {
      type: "message_start",
      message: fixtureMessage({ content: [], stop_reason: null }),
    },
    {
      type: "content_block_start",
      index: 0,
      content_block: { type: "thinking", thinking: "", signature: "" },
    },
    {
      type: "content_block_delta",
      index: 0,
      delta: { type: "thinking_delta", thinking: "Fixture thinking" },
    },
    {
      type: "content_block_delta",
      index: 0,
      delta: { type: "signature_delta", signature: "fixture-signature" },
    },
    { type: "content_block_stop", index: 0 },
    ...(tool
      ? [
          {
            type: "content_block_start",
            index: 1,
            content_block: {
              type: "tool_use",
              id: "tool_stream_fixture",
              name: "lookup_weather",
              input: {},
            },
          },
          {
            type: "content_block_delta",
            index: 1,
            delta: {
              type: "input_json_delta",
              partial_json: '{"enabled":false,"count":0,',
            },
          },
          {
            type: "content_block_delta",
            index: 1,
            delta: {
              type: "input_json_delta",
              partial_json: '"empty":"","nil":null}',
            },
          },
          { type: "content_block_stop", index: 1 },
        ]
      : []),
    {
      type: "content_block_start",
      index: tool ? 2 : 1,
      content_block: { type: "text", text: "", citations: [] },
    },
    {
      type: "content_block_delta",
      index: tool ? 2 : 1,
      delta: { type: "text_delta", text: JSON.stringify(scalarValues) },
    },
    {
      type: "content_block_delta",
      index: tool ? 2 : 1,
      delta: { type: "citations_delta", citation },
    },
    { type: "content_block_stop", index: tool ? 2 : 1 },
    {
      type: "content_block_delta",
      index: tool ? 2 : 1,
      delta: {
        type: "future_delta",
        payload: { enabled: false, count: 0, empty: "", nil: null },
      },
    },
    { type: "future_message_event", payload: { keptByTransport: true } },
    ...(compaction
      ? [
          {
            type: "content_block_start",
            index: 2,
            content_block: {
              type: "compaction",
              content: null,
              encrypted_content: null,
            },
          },
          {
            type: "content_block_delta",
            index: 2,
            delta: {
              type: "compaction_delta",
              content: "first compaction state",
              encrypted_content: "encrypted-a",
            },
          },
          {
            type: "content_block_delta",
            index: 2,
            delta: {
              type: "compaction_delta",
              content: "complete compacted context",
              encrypted_content: "encrypted-b",
            },
          },
          { type: "content_block_stop", index: 2 },
        ]
      : []),
    {
      type: "message_delta",
      delta: {
        stop_reason: tool ? "tool_use" : "end_turn",
        stop_sequence: null,
      },
      usage: { output_tokens: 0 },
    },
    { type: "message_stop" },
  ];
}
function sse(events: unknown[]) {
  return new Response(
    events
      .map(
        (event: any) =>
          `event: ${event.type}\ndata: ${JSON.stringify(event)}\n\n`,
      )
      .join(""),
    {
      status: 202,
      headers: {
        "content-type": "text/event-stream",
        "request-id": "fixture-stream",
      },
    },
  );
}
export const fixtureFetch: typeof fetch = async (url, init) => {
  const path = String(url),
    body = init?.body ? JSON.parse(String(init.body)) : {};
  if (body.model === "fixture-error")
    return Response.json(
      {
        type: "error",
        error: {
          type: "rate_limit_error",
          message: "Controlled fixture error",
        },
      },
      { status: 429, headers: { "request-id": "fixture-error" } },
    );
  if (path.includes("/count_tokens"))
    return Response.json(
      { input_tokens: 0 },
      { status: 201, headers: { "request-id": "fixture-count" } },
    );
  if (path.includes("/results.jsonl"))
    return new Response(
      [
        JSON.stringify({
          custom_id: "row_success",
          result: { type: "succeeded", message: fixtureMessage() },
        }),
        JSON.stringify({
          custom_id: "row_error",
          result: {
            type: "errored",
            error: {
              type: "error",
              error: {
                type: "invalid_request_error",
                message: "Controlled batch row error",
              },
            },
          },
        }),
      ].join("\n") + "\n",
      { status: 200, headers: { "content-type": "application/binary" } },
    );
  if (path.includes("/batches"))
    return Response.json(
      {
        id: "msgbatch_fixture",
        type: "message_batch",
        processing_status: "ended",
        request_counts: {
          processing: 0,
          succeeded: 1,
          errored: 1,
          canceled: 0,
          expired: 0,
        },
        results_url: "https://fixture.invalid/results.jsonl",
        created_at: "2026-10-10T00:00:00Z",
        ended_at: "2026-10-10T00:00:01Z",
        expires_at: "2026-10-11T00:00:00Z",
        archived_at: null,
        cancel_initiated_at: null,
      },
      { status: 201, headers: { "request-id": "fixture-batch" } },
    );
  if (path.includes("/complete"))
    return body.stream
      ? sse([
          {
            type: "completion",
            id: "completion-fixture",
            completion: "Legacy ",
            model: FIXTURE_MODEL,
            stop_reason: null,
          },
          {
            type: "completion",
            id: "completion-fixture",
            completion: "fixture",
            model: FIXTURE_MODEL,
            stop_reason: "stop_sequence",
          },
        ])
      : Response.json(
          {
            id: "completion-fixture",
            type: "completion",
            completion: "Legacy fixture",
            model: FIXTURE_MODEL,
            stop_reason: "stop_sequence",
          },
          { status: 201, headers: { "request-id": "fixture-completion" } },
        );
  const priorToolResult = (body.messages ?? []).some(
    (m: any) =>
      Array.isArray(m.content) &&
      m.content.some((block: any) => block.type === "tool_result"),
  );
  const runnable = (body.tools ?? []).some(
    (tool: any) => tool.name === "lookup_native",
  );
  const forced = body.tool_choice?.type === "tool";
  if (body.stream)
    return sse(
      streamEvents(
        !body.metadata?.user_id?.includes("helper"),
        body.metadata?.user_id === "helper-beta-stream",
      ),
    );
  if ((runnable || forced) && !priorToolResult)
    return Response.json(
      fixtureMessage({
        content: [
          {
            type: "tool_use",
            id: runnable ? "tool_native_fixture" : "tool_manual_fixture",
            name: runnable ? "lookup_native" : "lookup_weather",
            input: scalarValues,
          },
        ],
        stop_reason: "tool_use",
      }),
      { status: 201, headers: { "request-id": "fixture-tool" } },
    );
  return Response.json(fixtureMessage(), {
    status: 201,
    headers: { "request-id": "fixture-message" },
  });
};
export const text = (message: Anthropic.Message) =>
  message.content
    .filter((block) => block.type === "text")
    .map((block) => block.text)
    .join("");
