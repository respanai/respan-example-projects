import {
  createRuntime,
  logResult,
  runWorkflow,
  shutdownRuntime,
} from "./_shared.js";

const workflowName = "helicone_ts_log_request_chat_tools";
const runtime = await createRuntime();

try {
  const result = await runWorkflow(runtime, workflowName, async () => {
    return await runtime.logger.logRequest(
      {
        model: "gpt-4o-mini",
        messages: [
          { role: "system", content: "Use the shipping tool." },
          { role: "user", content: "When will order H-2048 arrive?" },
        ],
        tools: [
          {
            type: "function",
            function: {
              name: "get_shipping_eta",
              description: "Return the shipping ETA for an order.",
              parameters: {
                type: "object",
                properties: { order_id: { type: "string" } },
                required: ["order_id"],
              },
            },
          },
        ],
      },
      async (recorder) => {
        const response = {
          id: "chatcmpl-helicone-example",
          model: "gpt-4o-mini-2026-08-01",
          choices: [
            {
              message: {
                role: "assistant",
                content: "I will check the shipping ETA.",
                tool_calls: [
                  {
                    id: "call_shipping_eta",
                    type: "function",
                    function: {
                      name: "get_shipping_eta",
                      arguments: JSON.stringify({ order_id: "H-2048" }),
                    },
                  },
                ],
              },
            },
          ],
          usage: { prompt_tokens: 18, completion_tokens: 9, total_tokens: 27 },
        };
        recorder.appendResults(response);
        return response;
      },
      {
        "Helicone-User-Id": "helicone-example-user",
        "Helicone-Session-Id": "helicone-example-session",
        "Helicone-Property-scenario": "log-request-chat-tools",
      },
      "openai",
    );
  });

  logResult(workflowName, {
    model: result.model,
    toolCall: result.choices[0]?.message.tool_calls?.[0]?.function.name,
    heliconeLogs: runtime.mock.logs.length,
  });
} finally {
  await shutdownRuntime(runtime);
}
