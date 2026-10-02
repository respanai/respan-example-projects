#!/usr/bin/env node
import { ChatClient } from "dify-client";
import { withDifyRuntime } from "./_shared.js";

const workflowName = "dify_typescript_chat_blocking.workflow";

await withDifyRuntime(workflowName, async (runtime) => {
  const client = new ChatClient({
    apiKey: runtime.key("DIFY_CHAT_API_KEY"),
    baseUrl: runtime.baseUrl,
  });
  const response = await client.createChatMessage({
    inputs: { city: "Paris" },
    query: "Reply with one sentence about observability.",
    user: "respan-dify-ts-chat",
    response_mode: "blocking",
  });
  if (Symbol.asyncIterator in response) throw new Error("Expected blocking chat response");
  const data = response.data as Record<string, unknown>;
  const result = {
    status: response.status,
    answer: data.answer,
    conversationId: data.conversation_id,
  };
  runtime.setResult(result);
  return result;
});
