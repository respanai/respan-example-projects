import { assert, messages, MODEL, runScenario, tools } from "./_shared.js";

await runScenario("chat-and-stream", async (logger, openai) =>
  logger.traced(
    async () => {
      const response = await openai.chat.completions.create({
        model: MODEL,
        messages,
        tools,
      });
      assert.equal(
        response.choices[0].message.tool_calls?.[0].id,
        "call_fixture",
      );
      assert.equal(response.usage?.total_tokens, 17);
      const stream = await openai.chat.completions.create({
        model: MODEL,
        messages: [{ role: "user", content: "Stream a fixture response" }],
        stream: true,
        stream_options: { include_usage: true },
      });
      assert.equal(typeof stream.controller.abort, "function");
      let text = "";
      for await (const chunk of stream)
        text += chunk.choices[0]?.delta.content ?? "";
      assert.equal(text, "Fixture stream");
      return {
        messages: messages.length,
        tools: tools.length,
        text,
        totalTokens: response.usage?.total_tokens,
      };
    },
    { name: "braintrust-chat", type: "task" },
  ),
);
