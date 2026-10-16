import { EventStreamCodec } from "@smithy/eventstream-codec";
import { fromUtf8, toUtf8 } from "@smithy/util-utf8";

const encode = (value: unknown): Uint8Array =>
  new TextEncoder().encode(JSON.stringify(value));
const converseEvents = [
  { messageStart: { role: "assistant" } },
  {
    contentBlockStart: {
      contentBlockIndex: 1,
      start: {
        toolUse: { toolUseId: "fixture-tool", name: "get_city_weather" },
      },
    },
  },
  {
    contentBlockDelta: {
      contentBlockIndex: 1,
      delta: { toolUse: { input: '{"city":' } },
    },
  },
  {
    contentBlockDelta: {
      contentBlockIndex: 1,
      delta: { toolUse: { input: '"Paris"}' } },
    },
  },
  {
    contentBlockDelta: {
      contentBlockIndex: 0,
      delta: { text: "Paris stream response" },
    },
  },
  { messageStop: { stopReason: "tool_use" } },
  {
    metadata: { usage: { inputTokens: 18, outputTokens: 4, totalTokens: 22 } },
  },
];
const invokeEvents = [
  {
    type: "message_start",
    message: { role: "assistant", usage: { input_tokens: 18 } },
  },
  {
    type: "content_block_delta",
    index: 0,
    delta: { type: "text_delta", text: "Invoke stream response" },
  },
  {
    type: "message_delta",
    delta: { stop_reason: "end_turn" },
    usage: { output_tokens: 4 },
  },
];
function eventBody(invoke: boolean): AsyncIterable<Uint8Array> {
  const codec = new EventStreamCodec(toUtf8, fromUtf8);
  return (async function* () {
    for (const event of invoke ? invokeEvents : converseEvents) {
      const type = invoke ? "chunk" : Object.keys(event)[0];
      const payload = invoke
        ? { bytes: Buffer.from(encode(event)).toString("base64") }
        : (event as Record<string, unknown>)[type];
      yield codec.encode({
        headers: {
          ":message-type": { type: "string", value: "event" },
          ":event-type": { type: "string", value: type },
          ":content-type": { type: "string", value: "application/json" },
        },
        body: encode(payload),
      });
    }
  })();
}
/** Controlled wire transport for the real AWS serializer and deserializer. */
export const fixtureHandler = {
  async handle(request: { path: string; body?: unknown }) {
    const bodyText =
      request.body instanceof Uint8Array
        ? new TextDecoder().decode(request.body)
        : request.body;
    const body = typeof bodyText === "string" ? JSON.parse(bodyText) : {};
    const expectedError = JSON.stringify(body).includes("expected error");
    const stream =
      request.path.endsWith("converse-stream") ||
      request.path.endsWith("invoke-with-response-stream");
    const invoke = request.path.includes("/invoke");
    const embedding = request.path.includes("titan-embed");
    const payload = expectedError
      ? {
          __type: "ThrottlingException",
          message: "Deterministic Bedrock fixture error",
        }
      : embedding
        ? {
            embedding: Array.from({ length: 5001 }, (_, index) => index / 5001),
            inputTextTokenCount: 0,
          }
        : invoke
          ? {
              role: "assistant",
              content: [
                { type: "text", text: "Native InvokeModel fixture response" },
              ],
              usage: { input_tokens: 24, output_tokens: 9 },
            }
          : {
              output: {
                message: {
                  role: "assistant",
                  content: [
                    { text: "Native Converse fixture response" },
                    {
                      toolUse: {
                        toolUseId: "fixture-tool",
                        name: "get_city_weather",
                        input: {
                          city: "Tokyo",
                          enabled: false,
                          count: 0,
                          empty: "",
                          nil: null,
                        },
                      },
                    },
                  ],
                },
              },
              usage: { inputTokens: 31, outputTokens: 18, totalTokens: 49 },
              stopReason: "tool_use",
            };
    return {
      response: {
        statusCode: expectedError ? 429 : 200,
        headers: {
          "content-type": stream
            ? "application/vnd.amazon.eventstream"
            : "application/json",
          "x-amzn-requestid": "native-fixture-request",
        },
        body: stream ? eventBody(invoke) : encode(payload),
      },
    };
  },
};
