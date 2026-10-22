#!/usr/bin/env node
import { ChatClient } from "dify-client";
import { withDifyRuntime } from "./_shared.js";

const workflowName = "dify_typescript_chat_streaming.workflow";

await withDifyRuntime(workflowName, async (runtime) => {
  const client = new ChatClient({
    apiKey: runtime.key("DIFY_CHAT_API_KEY"),
    baseUrl: runtime.baseUrl,
  });
  const stream = await client.createChatMessage({
    inputs: {},
    query: "Stream a short Dify response.",
    user: "respan-dify-ts-stream",
    response_mode: "streaming",
  });
  if (!(Symbol.asyncIterator in stream)) throw new Error("Expected a Dify stream");

  const events: string[] = [];
  let answer = "";
  for await (const event of stream) {
    const data = event.data && typeof event.data === "object" ? event.data : {};
    if (typeof data.event === "string") events.push(data.event);
    if (typeof data.answer === "string") answer += data.answer;
  }
  const result = { answer, events, status: stream.status };
  runtime.setResult(result);
  return result;
});
