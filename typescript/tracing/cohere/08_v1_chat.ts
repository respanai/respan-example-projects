import { logExampleResult, runCohereWorkflow } from "./_shared.js";
const workflowName = "cohere_ts_v1_chat";
const result = await runCohereWorkflow(workflowName, async ({ client }) => {
  const response = await client.chat({
    model: "command",
    message: "Show v1 compatibility.",
    preamble: "Use concise responses.",
    chatHistory: [
      { role: "USER", message: "Earlier input." },
      { role: "CHATBOT", message: "Earlier response." },
    ],
  });
  let streamed = "";
  for await (const event of await client.chatStream({
    model: "command",
    message: "Stream a v1 response.",
  })) {
    if (event.eventType === "text-generation") streamed += event.text;
  }
  return { response, streamed };
});
logExampleResult(workflowName, {
  text: result.response.text,
  streamed: result.streamed,
});
