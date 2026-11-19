import * as genai from "@google/genai";
import * as legacy from "@google-cloud/vertexai";
import { VertexAIInstrumentor } from "@respan/instrumentation-vertexai";
import { setup, actualTool, assert, live } from "./_runtime.js";
function requireLiveProject(): string {
  const project = process.env.GOOGLE_CLOUD_PROJECT;
  if (!project)
    throw new Error("Live Vertex examples require GOOGLE_CLOUD_PROJECT.");
  return project;
}
const authClient = {
  async getAccessToken() {
    return { token: "fixture-only" };
  },
  async getRequestHeaders() {
    return new Headers({ Authorization: "Bearer fixture-only" });
  },
};
const response = (parts: any[] = [{ text: "Fixture answer" }]) => ({
  responseId: "native-fixture-response",
  modelVersion: "fixture-response-model",
  candidates: [
    { index: 0, finishReason: "STOP", content: { role: "model", parts } },
  ],
  usageMetadata: {
    promptTokenCount: 4,
    candidatesTokenCount: 5,
    totalTokenCount: 17,
    thoughtsTokenCount: 2,
    cachedContentTokenCount: 3,
  },
});
export async function runExample(scenario: number) {
  const privateContent = scenario === 8;
  const runtime = await setup(
    new VertexAIInstrumentor({
      sdkModule: legacy,
      genaiModule: genai,
      traceContent: !privateContent,
    }),
    privateContent,
  );
  const originalFetch = globalThis.fetch;
  let requests = 0;
  if (!live)
    globalThis.fetch = async (url, options) => {
      const path = String(url);
      const body =
        typeof options?.body === "string" ? JSON.parse(options.body) : {};
      requests++;
      if (path.includes("fixture-error"))
        return Response.json(
          {
            error: {
              code: 429,
              message: "Controlled Vertex error",
              status: "RESOURCE_EXHAUSTED",
            },
          },
          { status: 429 },
        );
      if (path.includes(":predictLongRunning"))
        return Response.json({
          name: "projects/fixture/locations/us-central1/publishers/google/models/veo/operations/native-operation",
          done: false,
        });
      if (path.includes("text-embedding"))
        return Response.json({
          predictions: [
            {
              embeddings: {
                values: Array.from({ length: 5001 }, (_, i) => i / 5001),
                statistics: { token_count: 7, truncated: false },
              },
            },
          ],
        });
      if (path.includes(":predict"))
        return Response.json({
          predictions: [
            { bytesBase64Encoded: "fixture-image", mimeType: "image/png" },
          ],
        });
      if (path.includes(":streamGenerateContent"))
        return new Response(
          [
            response([{ text: "first " }]),
            response([
              { text: "answer", thoughtSignature: "native-signature" },
            ]),
          ]
            .map((chunk) => `data: ${JSON.stringify(chunk)}\n\n`)
            .join(""),
          { headers: { "content-type": "text/event-stream" } },
        );
      const parts =
        body.contents?.flatMap((content: any) => content.parts ?? []) ?? [];
      const functions =
        body.tools?.flatMap((tool: any) => tool.functionDeclarations ?? []) ??
        [];
      if (functions.length && !parts.some((part: any) => part.functionResponse))
        return Response.json(
          response([
            {
              functionCall: {
                id: "native-weather-call",
                name: functions[0].name,
                args: { city: "Tokyo" },
              },
            },
          ]),
        );
      return Response.json(
        response([
          {
            text: "Fixture reasoning",
            thought: true,
            thoughtSignature: "native-thought-signature",
          },
          { text: "Fixture answer" },
          {
            inlineData: { mimeType: "image/png", data: "fixture-output-image" },
          },
        ]),
      );
    };
  const client = new genai.GoogleGenAI(
    live
      ? {
          vertexai: true,
          project: requireLiveProject(),
          location: process.env.GOOGLE_CLOUD_LOCATION ?? "us-central1",
        }
      : {
          vertexai: true,
          project: "fixture-project",
          location: "us-central1",
          googleAuthOptions: { authClient: authClient as any },
        },
  );
  const model = process.env.VERTEXAI_MODEL ?? "gemini-fixture";
  try {
    await runtime.run(`vertexai-${scenario}`, async () => {
      if (scenario === 1) {
        const result = await client.models.generateContent({
          model,
          contents: [
            {
              role: "user",
              parts: [
                { text: "Fixture multimodal prompt" },
                {
                  inlineData: {
                    mimeType: "image/png",
                    data: "fixture-input-image",
                  },
                },
              ],
            },
          ],
          config: {
            systemInstruction: "Fixture system instruction",
            temperature: 0,
            maxOutputTokens: 64,
          },
        });
        assert.ok(result.candidates?.length);
      }
      if (scenario === 2) {
        const stream = await client.models.generateContentStream({
          model,
          contents: "Fixture streaming",
        });
        let count = 0;
        for await (const chunk of stream) {
          assert.ok(chunk);
          count++;
        }
        assert.ok(count);
        const early = await client.models.generateContentStream({
          model,
          contents: "Early return",
        });
        for await (const chunk of early) {
          assert.ok(chunk);
          break;
        }
      }
      if (scenario === 3) {
        const chat = client.chats.create({
          model,
          config: {
            tools: [
              {
                functionDeclarations: [
                  {
                    name: "weather",
                    parameters: {
                      type: genai.Type.OBJECT,
                      properties: { city: { type: genai.Type.STRING } },
                    },
                  },
                ],
              },
            ],
          },
        });
        const first = await chat.sendMessage({ message: "Weather Tokyo" });
        const call = first.functionCalls?.[0];
        assert.ok(call, "Native response must supply the function call.");
        const result = { temperature: 0, city: "Tokyo" };
        await chat.sendMessage({
          message: [
            {
              functionResponse: {
                id: call.id,
                name: call.name,
                response: result,
              },
            },
          ],
        });
      }
      if (scenario === 4) {
        await assert.rejects(
          client.models.generateContent({
            model: "fixture-error",
            contents: "Controlled native provider error",
          }),
        );
      }
      if (scenario === 5) {
        let callbacks = 0;
        const callable = {
          async tool() {
            return {
              functionDeclarations: [
                {
                  name: "weather",
                  parameters: {
                    type: genai.Type.OBJECT,
                    properties: { city: { type: genai.Type.STRING } },
                  },
                },
              ],
            };
          },
          async callTool(calls: any[]) {
            callbacks++;
            assert.ok(calls[0].id);
            const result = await actualTool(
              runtime.respan,
              calls[0].id,
              calls[0].name,
              calls[0].args,
              async () => ({ city: "Tokyo", temperature: 0 }),
            );
            return [
              {
                functionResponse: {
                  id: calls[0].id,
                  name: calls[0].name,
                  response: result,
                },
              },
            ];
          },
        };
        await client.models.generateContent({
          model,
          contents: "Native AFC Weather",
          config: { tools: [callable] },
        });
        if (!live) assert.equal(callbacks, 1);
      }
      if (scenario === 6) {
        const result = await client.models.embedContent({
          model: process.env.VERTEXAI_EMBEDDING_MODEL ?? "text-embedding-005",
          contents: ["Fixture embedding"],
        });
        if (!live) assert.equal(result.embeddings?.[0].values?.length, 5001);
      }
      if (scenario === 7) {
        await client.models.generateImages({
          model: "imagen-4.0-generate-001",
          prompt: "Fixture image",
        });
        const operation = await client.models.generateVideos({
          model: "veo-3.0-generate-001",
          source: { prompt: "Fixture video" },
        });
        if (!live) assert.equal(operation.done, false);
      }
      if (scenario === 8) {
        await client.models.generateContent({
          model,
          contents: "PRIVATE_SENTINEL",
        });
      }
      if (scenario === 9) {
        const vertex = new legacy.VertexAI(
          live
            ? {
                project: requireLiveProject(),
                location: process.env.GOOGLE_CLOUD_LOCATION ?? "us-central1",
              }
            : {
                project: "fixture-project",
                location: "us-central1",
                googleAuthOptions: { authClient: authClient as any },
              },
        );
        await vertex
          .getGenerativeModel({ model })
          .generateContent("Legacy GA retained");
        await vertex.preview
          .getGenerativeModel({ model })
          .generateContent("Legacy preview retained");
        const chat = vertex.getGenerativeModel({ model }).startChat();
        await chat.sendMessage("Legacy chat");
        const stream = await chat.sendMessageStream("Legacy chat stream");
        for await (const chunk of stream.stream) assert.ok(chunk);
        await stream.response;
      }
      if (scenario === 10) {
        await client.models.generateContent({
          model,
          contents: Array.from({ length: 80 }, (_, i) => ({
            role: "user",
            parts:
              i === 0
                ? [
                    {
                      functionCall: {
                        id: "native-history-call",
                        name: "tool_0",
                        args: { x: 0 },
                      },
                      thoughtSignature: "native-history-signature",
                    },
                  ]
                : i === 1
                  ? [
                      {
                        functionResponse: {
                          id: "native-history-call",
                          name: "tool_0",
                          response: { x: 0 },
                          parts: [
                            {
                              inlineData: {
                                mimeType: "image/png",
                                data: "fixture-tool-image",
                              },
                            },
                          ],
                        },
                      },
                    ]
                  : [{ text: `Fixture history ${i}` }],
          })),
          config: {
            tools: [
              {
                functionDeclarations: Array.from({ length: 80 }, (_, i) => ({
                  name: `tool_${i}`,
                  parametersJsonSchema: {
                    type: "object",
                    properties: { x: { type: "integer" } },
                    required: ["x"],
                  },
                  responseJsonSchema: {
                    type: "object",
                    properties: { x: { type: "integer" } },
                  },
                })),
              },
            ],
          },
        });
      }
      if (scenario === 11) {
        await client.models.editImage({
          model: "imagen-3.0-capability-001",
          prompt: "Edit fixture",
          referenceImages: [],
        });
        await client.models.upscaleImage({
          model: "imagen-4.0-upscale-preview",
          image: { imageBytes: "fixture", mimeType: "image/png" },
          upscaleFactor: "x2",
        });
        await client.models.recontextImage({
          model: "imagen-product-recontext-preview-06-30",
          source: {
            productImages: [
              {
                productImage: { imageBytes: "fixture", mimeType: "image/png" },
              },
            ],
          },
        });
        await client.models.segmentImage({
          model: "image-segmentation-001",
          source: { image: { imageBytes: "fixture", mimeType: "image/png" } },
          config: { mode: genai.SegmentMode.FOREGROUND },
        });
      }
    });
  } finally {
    globalThis.fetch = originalFetch;
    await runtime.close();
  }
  if (privateContent)
    for (const span of runtime.spans)
      assert.ok(!JSON.stringify(span.attributes).includes("PRIVATE_SENTINEL"));
  const children = runtime.spans.filter(
    (span) => span.attributes["traceloop.span.kind"] !== "workflow",
  );
  if (!live)
    assert.equal(
      children.length,
      [0, 1, 2, 2, 1, 3, 1, 2, 1, 4, 1, 4][scenario],
    );
}
