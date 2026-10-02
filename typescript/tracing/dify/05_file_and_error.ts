#!/usr/bin/env node
import { ChatClient, DifyClient } from "dify-client";
import { withDifyRuntime } from "./_shared.js";

const workflowName = "dify_typescript_file_and_error.workflow";

await withDifyRuntime(workflowName, async (runtime) => {
  const client = new DifyClient({
    apiKey: runtime.key("DIFY_CHAT_API_KEY"),
    baseUrl: runtime.baseUrl,
    maxRetries: 0,
  });
  const form = new FormData();
  form.append("file", new Blob(["Dify file upload tracing sample.\n"], { type: "text/plain" }), "sample.txt");
  const upload = await client.fileUpload(form, "respan-dify-ts-file");

  const chat = new ChatClient({
    apiKey: runtime.key("DIFY_CHAT_API_KEY"),
    baseUrl: runtime.baseUrl,
    maxRetries: 0,
  });
  let expectedError = "";
  try {
    await chat.createChatMessage({
      inputs: {},
      query: "Trigger the expected error.",
      user: "respan-dify-ts-error",
      response_mode: "blocking",
    });
  } catch (error) {
    expectedError = error instanceof Error ? error.message : String(error);
  }
  if (!expectedError) throw new Error("Expected the deterministic Dify error");

  const result = { uploadId: upload.data.id, expectedError };
  runtime.setResult(result);
  return result;
});
