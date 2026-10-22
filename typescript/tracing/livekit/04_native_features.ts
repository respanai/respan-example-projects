import assert from "node:assert/strict";
import { llm } from "@livekit/agents";
import { z } from "zod";
import { TTS } from "@livekit/agents-plugin-openai";
import { OpenAI } from "openai";
import {
  agentTurn,
  assertCaptured,
  nativeModel,
  runExample,
} from "./_shared.js";
await runExample("TypeScript LiveKit Native Features", async () => {
  const chatCtx = llm.ChatContext.empty();
  for (let index = 0; index < 80; index++)
    chatCtx.addMessage({
      role: index % 2 ? "assistant" : "user",
      content: `history-${index}`,
    });
  const tools = Object.fromEntries(
    Array.from({ length: 75 }, (_, index) => [
      `tool_${index}`,
      llm.tool({
        description: `Definition ${index}`,
        parameters: z.object({ value: z.string() }),
        execute: async () => "ok",
      }),
    ]),
  );
  const long = await agentTurn({ chatCtx, tools });
  assertCaptured(
    (span) =>
      span.attributes["traceloop.entity.input"]?.includes("history-79") &&
      JSON.parse(span.attributes["llm.request.functions"] || "[]").length ===
        75,
  );
  const multimedia = llm.ChatContext.empty();
  multimedia.addMessage({
    role: "user",
    content: [
      "Describe the image URI.",
      llm.createImageContent({
        image: "https://example.invalid/native-fixture.png",
      }),
    ],
  });
  const fixture = nativeModel();
  const stream = fixture.model.chat({ chatCtx: multimedia });
  assert.equal(stream[Symbol.asyncIterator](), stream);
  const chunks = [];
  for await (const chunk of stream) chunks.push(chunk);
  stream.close();
  assert.ok(
    JSON.stringify(
      fixture.requests.find((request) => request.messages),
    ).includes("https://example.invalid/native-fixture.png"),
  );

  const audioClient = new OpenAI({
    apiKey: "fixture-only",
    baseURL: "http://fixture.invalid/v1",
    fetch: async () =>
      new Response(new Uint8Array(4800), {
        headers: { "content-type": "application/octet-stream" },
      }),
  });
  const tts = new TTS({
    client: audioClient,
    model: "native-tts",
    voice: "alloy",
  });
  let audioFrames = 0;
  try {
    for await (const _event of tts.synthesize("Native audio transport."))
      audioFrames++;
  } finally {
    await tts.close();
  }
  assert.ok(audioFrames);
  return {
    long,
    audioFrames,
    multimodalChunks: chunks.length,
    definitions: 75,
    historyMessages: 80,
  };
});
