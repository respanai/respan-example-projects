import { MODEL, LIVE, createRuntime, runCase, log } from "./_shared.js";
const caseId = "basic";
const runtime = await createRuntime();
try {
  const result = await runCase(runtime.respan, caseId, async () => {
    const messages = LIVE
      ? [{ role: "user" as const, content: "Reply with a concise greeting." }]
      : Array.from({ length: 76 }, (_, i) => ({
          role: "user" as const,
          content:
            i === 75
              ? [
                  {
                    type: "text" as const,
                    text: "",
                    cache_control: { type: "ephemeral" as const },
                  },
                  {
                    type: "image" as const,
                    source: {
                      type: "base64" as const,
                      media_type: "image/png" as const,
                      data: "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aNG0AAAAASUVORK5CYII=",
                    },
                  },
                  {
                    type: "document" as const,
                    source: {
                      type: "text" as const,
                      media_type: "text/plain" as const,
                      data: "fixture document",
                    },
                    title: "Fixture",
                    context: "",
                    citations: { enabled: true },
                  },
                ]
              : `Context ${i}`,
        }));
    const tools = Array.from({ length: 76 }, (_, i) => ({
      name: `lookup_${i}`,
      description: "",
      input_schema: {
        type: "object" as const,
        properties: {
          enabled: { type: "boolean", default: false },
          count: { type: "number", default: 0 },
        },
        required: [],
      },
    }));
    const pending = runtime.client.messages.create({
      model: MODEL,
      max_tokens: LIVE ? 512 : 2048,
      messages,
      ...(LIVE
        ? {}
        : {
            system: [
              {
                type: "text" as const,
                text: "Use the supplied document.",
                cache_control: { type: "ephemeral" as const },
              },
            ],
            thinking: { type: "enabled" as const, budget_tokens: 1024 },
            tools,
            temperature: 0,
          }),
    });
    const { data, response } = await pending.withResponse();
    const raw = await runtime.client.messages
      .create({
        model: MODEL,
        max_tokens: 512,
        messages: [
          { role: "user", content: "Read only this raw response header." },
        ],
      })
      .asResponse();
    const rawOnlyStatus = raw.status;
    await raw.body?.cancel();
    return {
      rawOnlyStatus,
      status: response.status,
      contentBlocks: data.content.length,
      inputTokens: data.usage.input_tokens,
      outputTokens: data.usage.output_tokens,
    };
  });
  log(caseId, result);
} finally {
  await runtime.close(caseId);
}
