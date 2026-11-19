import Together from "together-ai";
import { TogetherAIInstrumentor } from "@respan/instrumentation-together-ai";
import { setup, actualTool, assert, live } from "./_runtime.js";
const usage = {
  prompt_tokens: 4,
  completion_tokens: 5,
  total_tokens: 17,
  prompt_tokens_details: { cached_tokens: 3 },
  completion_tokens_details: { reasoning_tokens: 2 },
};
const completion = (body: any) => ({
  id: "actual-fixture-response",
  model: body.model,
  choices: [
    {
      index: 0,
      finish_reason: "stop",
      message: {
        role: "assistant",
        content: "Fixture answer",
        reasoning: "Separate fixture reasoning",
        reasoning_content: "Separate current reasoning content",
      },
    },
  ],
  usage,
});
const fetchFixture: typeof fetch = async (url, options) => {
  const pathname = String(url);
  let body: any = {};
  if (typeof options?.body === "string") body = JSON.parse(options.body);
  else if (options?.body instanceof FormData)
    body = Object.fromEntries(options.body.entries());
  if (body.model === "fixture-error")
    return Response.json(
      { error: { message: "Controlled Together error", type: "fixture" } },
      { status: 429 },
    );
  if (pathname.includes("/chat/completions")) {
    if (body.stream) {
      const chunks = [
        {
          model: body.model,
          choices: [
            {
              index: 0,
              delta: {
                role: "assistant",
                content: "first ",
                reasoning: "reason ",
              },
            },
            { index: 1, delta: { content: "other " } },
          ],
        },
        {
          choices: [
            {
              index: 0,
              delta: { content: "answer", reasoning_content: "reason2" },
              finish_reason: "stop",
            },
            { index: 1, delta: { content: "choice" }, finish_reason: "stop" },
          ],
          usage,
        },
      ];
      return new Response(
        chunks.map((chunk) => `data: ${JSON.stringify(chunk)}\n\n`).join("") +
          "data: [DONE]\n\n",
        { headers: { "content-type": "text/event-stream" } },
      );
    }
    const value = completion(body);
    if (
      body.tools?.length &&
      !body.messages?.some((message: any) => message.role === "tool")
    )
      value.choices[0] = {
        index: 0,
        finish_reason: "tool_calls",
        message: {
          role: "assistant",
          content: null,
          tool_calls: [
            {
              id: "actual-weather-call",
              type: "function",
              function: {
                name: body.tools[0].function.name,
                arguments: '{"city":"Tokyo"}',
              },
            },
          ],
        },
      } as any;
    return Response.json(value);
  }
  if (pathname.includes("/embeddings"))
    return Response.json({
      model: body.model,
      data: [
        {
          index: 0,
          embedding: Array.from({ length: 5001 }, (_, i) => i / 5001),
        },
      ],
      usage: { prompt_tokens: 7, total_tokens: 7 },
    });
  if (pathname.includes("/completions"))
    return Response.json({
      model: body.model,
      choices: [
        { index: 0, text: "native text answer", finish_reason: "stop" },
      ],
      usage,
    });
  if (pathname.includes("/images"))
    return Response.json({
      model: body.model,
      data: [{ type: "b64_json", b64_json: "fixture-image" }],
    });
  if (pathname.includes("/rerank"))
    return Response.json({
      model: body.model,
      results: [
        {
          index: 0,
          relevance_score: 0.99,
          document: { text: "fixture document" },
        },
      ],
      usage: { prompt_tokens: 7, total_tokens: 7 },
    });
  if (pathname.includes("/audio/speech"))
    return new Response(new Uint8Array([0, 1, 2, 3]), {
      headers: { "content-type": "audio/mpeg" },
    });
  if (
    pathname.includes("/audio/transcriptions") ||
    pathname.includes("/audio/translations")
  )
    return Response.json({
      text: "native fixture audio text",
      model: body.model,
    });
  throw new Error("Unexpected native fixture route");
};
export async function runExample(scenario: number) {
  const privateContent = scenario === 8;
  const plugin = new TogetherAIInstrumentor({ traceContent: !privateContent });
  const runtime = await setup(plugin, privateContent);
  const client = new Together(
    live
      ? {
          apiKey: process.env.TOGETHER_API_KEY,
          baseURL: process.env.TOGETHER_BASE_URL,
          maxRetries: 0,
        }
      : { apiKey: "fixture-only", fetch: fetchFixture, maxRetries: 0 },
  );
  const chat = process.env.TOGETHER_CHAT_MODEL ?? "fixture-chat";
  try {
    await runtime.run(`together-${scenario}`, async () => {
      if (scenario === 1) {
        const response = await client.chat.completions.create({
          model: chat,
          messages: [
            {
              role: "user",
              content: [
                { type: "text", text: "Fixture multimodal prompt" },
                {
                  type: "image_url",
                  image_url: { url: "data:image/png;base64,fixture" },
                },
              ],
            },
          ],
          temperature: 0,
          max_tokens: 64,
        });
        assert.ok(response.choices.length);
      }
      if (scenario === 2) {
        const stream = await client.chat.completions.create({
          model: chat,
          messages: [{ role: "user", content: "Stream fixture answer" }],
          stream: true,
        });
        assert.ok(stream.controller);
        let count = 0;
        for await (const chunk of stream) {
          assert.ok(chunk);
          count++;
        }
        assert.ok(count > 0);
        const early = await client.chat.completions.create({
          model: chat,
          messages: [{ role: "user", content: "Early stream return" }],
          stream: true,
        });
        for await (const chunk of early) {
          assert.ok(chunk);
          break;
        }
      }
      if (scenario === 3) {
        const tools = [
          {
            type: "function" as const,
            function: {
              name: "weather",
              parameters: {
                type: "object",
                properties: { city: { type: "string" } },
                required: ["city"],
              },
            },
          },
        ];
        const messages: any[] = [
          { role: "user", content: "Use weather for Tokyo" },
        ];
        const first = await client.chat.completions.create({
          model: chat,
          messages,
          tools,
        });
        const call = first.choices[0]?.message?.tool_calls?.[0];
        assert.ok(
          call,
          "Native response must provide the call; no fabricated fallback.",
        );
        const result = await actualTool(
          runtime.respan,
          call.id,
          call.function.name,
          JSON.parse(call.function.arguments),
          async () => ({ temperature: 0, city: "Tokyo" }),
        );
        messages.push(first.choices[0].message, {
          role: "tool",
          tool_call_id: call.id,
          content: JSON.stringify(result),
        });
        await client.chat.completions.create({ model: chat, messages });
      }
      if (scenario === 4) {
        await client.completions.create({
          model: process.env.TOGETHER_COMPLETION_MODEL ?? "fixture-text",
          prompt: "Fixture completion",
          temperature: 0,
          max_tokens: 32,
        });
        const embedding = await client.embeddings.create({
          model: process.env.TOGETHER_EMBEDDING_MODEL ?? "fixture-embedding",
          input: ["Fixture embedding"],
        });
        if (!live) assert.equal(embedding.data[0]?.embedding?.length, 5001);
      }
      if (scenario === 5) {
        await client.images.generate({
          model: process.env.TOGETHER_IMAGE_MODEL ?? "fixture-image",
          prompt: "Fixture image",
          n: 1,
          response_format: "base64",
        });
        await client.rerank.create({
          model: process.env.TOGETHER_RERANK_MODEL ?? "fixture-rerank",
          query: "fixture",
          documents: ["fixture document"],
          top_n: 1,
          return_documents: true,
        });
      }
      if (scenario === 6) {
        const speech = await client.audio.speech.create({
          model: process.env.TOGETHER_SPEECH_MODEL ?? "fixture-speech",
          voice: "fixture",
          input: "Fixture speech",
          response_format: "mp3",
        });
        assert.ok((await speech.arrayBuffer()).byteLength > 0);
        const file = await Together.toFile(
          new Uint8Array([0, 1, 2, 3]),
          "fixture.wav",
        );
        await client.audio.transcriptions.create({
          model: "whisper-large-v3" as any,
          file,
          response_format: "json",
        });
        await client.audio.translations.create({
          model: "whisper-large-v3" as any,
          file: await Together.toFile(
            new Uint8Array([0, 1, 2, 3]),
            "fixture.wav",
          ),
          response_format: "json",
        });
      }
      if (scenario === 7) {
        await assert.rejects(
          client.chat.completions.create({
            model: "fixture-error",
            messages: [{ role: "user", content: "Controlled native error" }],
          }),
        );
      }
      if (scenario === 8) {
        await client.chat.completions.create({
          model: chat,
          messages: [{ role: "user", content: "PRIVATE_SENTINEL" }],
        });
      }
      if (scenario === 9) {
        const tools = Array.from({ length: 80 }, (_, i) => ({
          type: "function" as const,
          function: {
            name: `tool_${i}`,
            strict: true,
            parameters: {
              type: "object",
              properties: { x: { type: "integer" } },
              additionalProperties: false,
            },
          },
        }));
        await client.chat.completions.create({
          model: chat,
          messages: Array.from({ length: 80 }, (_, i) => ({
            role: "user" as const,
            content: `fixture history ${i}`,
          })),
          tools,
        });
        const pending = client.chat.completions.create({
          model: chat,
          messages: [{ role: "user", content: "Native response helpers" }],
        });
        const response = await pending.withResponse();
        assert.ok(response.response instanceof Response);
        await pending;
        const raw = await client.chat.completions
          .create({
            model: chat,
            messages: [{ role: "user", content: "Raw response" }],
          })
          .asResponse();
        assert.equal(raw.bodyUsed, false);
        await raw.json();
      }
    });
  } finally {
    await runtime.close();
  }
  if (privateContent)
    for (const span of runtime.spans)
      assert.ok(!JSON.stringify(span.attributes).includes("PRIVATE_SENTINEL"));
  const children = runtime.spans.filter(
    (span) => span.attributes["traceloop.span.kind"] !== "workflow",
  );
  if (!live)
    assert.equal(children.length, [0, 1, 2, 3, 2, 2, 3, 1, 1, 3][scenario]);
}
