import {
  createRuntime,
  logResult,
  runWorkflow,
  shutdownRuntime,
} from "./_shared.js";

const workflowName = "helicone_ts_anthropic_direct";
const runtime = await createRuntime();

try {
  await runWorkflow(runtime, workflowName, async () => {
    await runtime.logger.sendLog(
      {
        model: "claude-sonnet-4-20250514",
        system: "Use tools when they help.",
        messages: [
          {
            role: "user",
            content: [{ type: "text", text: "Find order H-2048." }],
          },
          {
            role: "assistant",
            content: [{
              type: "tool_use",
              id: "toolu_history",
              name: "lookup_order",
              input: { order_id: "H-1024" },
            }],
          },
          {
            role: "user",
            content: [{
              type: "tool_result",
              tool_use_id: "toolu_history",
              content: "Order H-1024 was delivered.",
            }],
          },
        ],
        tools: [{
          name: "lookup_order",
          description: "Look up an order by id.",
          input_schema: {
            type: "object",
            properties: { order_id: { type: "string" } },
            required: ["order_id"],
          },
        }],
      },
      {
        id: "msg_helicone_anthropic",
        type: "message",
        role: "assistant",
        model: "claude-sonnet-4-20250514-rev1",
        content: [
          { type: "text", text: "I will check that order." },
          {
            type: "tool_use",
            id: "toolu_current",
            name: "lookup_order",
            input: { order_id: "H-2048" },
          },
        ],
        usage: {
          input_tokens: 21,
          output_tokens: 8,
          cache_read_input_tokens: 13,
        },
      },
      {
        startTime: Date.now() - 15,
        endTime: Date.now(),
        status: 200,
        provider: "anthropic",
        additionalHeaders: {
          "Helicone-Property-scenario": "anthropic-direct",
        },
      },
    );
  });

  logResult(workflowName, {
    provider: "anthropic",
    requestModel: "claude-sonnet-4-20250514",
    responseModel: "claude-sonnet-4-20250514-rev1",
    cacheReadInputTokens: 13,
    heliconeLogs: runtime.mock.logs.length,
  });
} finally {
  await shutdownRuntime(runtime);
}
