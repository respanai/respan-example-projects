import {
  createRuntime,
  logResult,
  runWorkflow,
  shutdownRuntime,
} from "./_shared.js";

const workflowName = "helicone_ts_provider_stream_shapes";
const runtime = await createRuntime();

try {
  await runWorkflow(runtime, workflowName, async () => {
    const now = Date.now();
    const anthropicChunks = [
      {
        type: "message_start",
        message: {
          role: "assistant",
          model: "claude-sonnet-4-stream-rev",
          content: [],
          usage: { input_tokens: 12, cache_read_input_tokens: 4 },
        },
      },
      {
        type: "content_block_start",
        index: 0,
        content_block: { type: "text", text: "" },
      },
      {
        type: "content_block_delta",
        index: 0,
        delta: { type: "text_delta", text: "Anthropic streamed." },
      },
      {
        type: "content_block_start",
        index: 1,
        content_block: {
          type: "tool_use",
          id: "toolu_stream",
          name: "lookup_order",
          input: {},
        },
      },
      {
        type: "content_block_delta",
        index: 1,
        delta: { type: "input_json_delta", partial_json: '{"order_id":"H-2048"}' },
      },
      { type: "message_delta", usage: { output_tokens: 7 } },
    ];
    await runtime.logger.sendLog(
      {
        model: "claude-sonnet-4-stream",
        messages: [{ role: "user", content: "Stream an Anthropic tool call." }],
        tools: [{ name: "lookup_order", input_schema: { type: "object" } }],
      },
      anthropicChunks.map((chunk) => `data: ${JSON.stringify(chunk)}`).join("\n"),
      {
        startTime: now - 30,
        endTime: now - 20,
        status: 200,
        timeToFirstToken: 2,
        provider: "anthropic",
        additionalHeaders: {
          "Helicone-Property-stream-shape": "anthropic-sse",
        },
      },
    );

    const googleChunks = [
      {
        modelVersion: "gemini-2.5-flash-stream-rev",
        candidates: [{
          content: { role: "model", parts: [{ text: "Google streamed." }] },
        }],
      },
      {
        candidates: [{
          content: {
            role: "model",
            parts: [{
              functionCall: { name: "lookup_order", args: { order_id: "G-42" } },
            }],
          },
        }],
        usageMetadata: {
          promptTokenCount: 10,
          candidatesTokenCount: 5,
          totalTokenCount: 15,
          cachedContentTokenCount: 3,
        },
      },
    ];
    await runtime.logger.sendLog(
      {
        model: "gemini-2.5-flash",
        contents: [{ role: "user", parts: [{ text: "Stream a Google tool call." }] }],
        tools: [{ functionDeclarations: [{
          name: "lookup_order",
          parameters: { type: "object" },
        }] }],
      },
      googleChunks.map((chunk) => JSON.stringify(chunk)).join("\n"),
      {
        startTime: now - 20,
        endTime: now - 10,
        status: 200,
        timeToFirstToken: 3,
        provider: "google",
        additionalHeaders: {
          "Helicone-Property-stream-shape": "google-candidates",
        },
      },
    );

    const openAiChunks = [
      {
        model: "gpt-4o-mini-stream-rev",
        choices: [{ delta: {
          role: "assistant",
          tool_calls: [{
            index: 0,
            id: "call_stream",
            type: "function",
            function: { name: "lookup_order", arguments: "" },
          }],
        } }],
      },
      {
        choices: [{ delta: {
          tool_calls: [{ index: 0, function: { arguments: '{"order_id":' } }],
        } }],
      },
      {
        choices: [{ delta: {
          tool_calls: [{ index: 0, function: { arguments: '"O-42"}' } }],
        } }],
        usage: { prompt_tokens: 9, completion_tokens: 4, total_tokens: 13 },
      },
    ];
    await runtime.logger.sendLog(
      {
        model: "gpt-4o-mini",
        messages: [{ role: "user", content: "Stream a fragmented OpenAI tool call." }],
      },
      openAiChunks.map((chunk) => `data: ${JSON.stringify(chunk)}`).join("\n"),
      {
        startTime: now - 10,
        endTime: now,
        status: 200,
        timeToFirstToken: 1,
        provider: "openai",
        additionalHeaders: {
          "Helicone-Property-stream-shape": "openai-fragmented-tool",
        },
      },
    );
  });

  logResult(workflowName, {
    expectedSpans: 3,
    streamShapes: [
      "anthropic-sse",
      "google-candidates",
      "openai-fragmented-tool",
    ],
    expectedToolCalls: ["toolu_stream", "lookup_order", "call_stream"],
    heliconeLogs: runtime.mock.logs.length,
  });
} finally {
  await shutdownRuntime(runtime);
}
