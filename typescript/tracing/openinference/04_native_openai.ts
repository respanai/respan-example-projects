import type { Respan } from "@respan/respan";
import assert from "node:assert/strict";
import OpenAI from "openai";
import { workflow } from "./_shared.js";
export async function run(respan: Respan) {
  const client = new OpenAI({
    apiKey: "local-provider-fixture",
    baseURL: "http://127.0.0.1:1/v1",
    maxRetries: 0,
    fetch: async (_url, options) => {
      const body = JSON.parse(String(options?.body));
      if (body.model === "fixture-failure")
        return new Response(
          JSON.stringify({
            error: {
              message: "controlled fixture failure",
              type: "invalid_request_error",
            },
          }),
          { status: 400, headers: { "content-type": "application/json" } },
        );
      if (body.stream) {
        const chunk = {
          id: "fixture-stream",
          object: "chat.completion.chunk",
          created: 0,
          model: "fixture-stream",
          choices: [
            {
              index: 0,
              delta: { role: "assistant", content: "streamed fixture" },
              finish_reason: "stop",
            },
          ],
          usage: { prompt_tokens: 0, completion_tokens: 0, total_tokens: 0 },
        };
        return new Response(
          `data: ${JSON.stringify(chunk)}\n\ndata: [DONE]\n\n`,
          { headers: { "content-type": "text/event-stream" } },
        );
      }
      return new Response(
        JSON.stringify({
          id: "fixture-completion",
          object: "chat.completion",
          created: 0,
          model: "fixture-model",
          choices: [
            {
              index: 0,
              message: { role: "assistant", content: "fixture native answer" },
              finish_reason: "stop",
            },
          ],
          usage: { prompt_tokens: 0, completion_tokens: 0, total_tokens: 0 },
        }),
        { headers: { "content-type": "application/json" } },
      );
    },
  });
  return workflow(respan, "native-openai", async () => {
    const promise = client.chat.completions.create({
      model: "fixture-model",
      messages: [{ role: "user", content: "native fixture prompt" }],
    });
    assert.equal(typeof promise.withResponse, "function");
    assert.equal(typeof promise.asResponse, "function");
    const result = await promise.withResponse();
    const stream = await client.chat.completions.create({
      model: "fixture-stream",
      messages: [{ role: "user", content: "stream fixture prompt" }],
      stream: true,
    });
    let chunks = 0;
    for await (const chunk of stream) {
      assert.equal(chunk.object, "chat.completion.chunk");
      chunks++;
    }
    await assert.rejects(
      client.chat.completions.create({
        model: "fixture-failure",
        messages: [{ role: "user", content: "controlled failure" }],
      }),
      (error) => error instanceof OpenAI.APIError && error.status === 400,
    );
    return {
      answer: result.data.choices[0].message.content,
      chunks,
      controlledFailure: true,
    };
  });
}
