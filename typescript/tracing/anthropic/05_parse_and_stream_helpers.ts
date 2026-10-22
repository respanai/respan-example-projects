import { jsonSchemaOutputFormat } from "@anthropic-ai/sdk/helpers/json-schema";
import { MODEL, createRuntime, runCase, log } from "./_shared.js";
const caseId = "parse_and_stream_helpers";
const runtime = await createRuntime();
try {
  const result = await runCase(runtime.respan, caseId, async () => {
    const format = jsonSchemaOutputFormat({
      type: "object",
      properties: {
        enabled: { type: "boolean" },
        count: { type: "number" },
        empty: { type: "string" },
        nil: { type: "null" },
      },
      required: ["enabled", "count", "empty", "nil"],
      additionalProperties: false,
    } as const);
    const params = {
      model: MODEL,
      max_tokens: 2048,
      messages: [
        { role: "user" as const, content: "Return structured scalar values." },
      ],
      output_config: { format },
    };
    const stable = await runtime.client.messages.parse(params);
    const beta = await runtime.client.beta.messages.parse(params);
    let callbacks = 0;
    const stream = runtime.client.messages.stream({
      ...params,
      metadata: { user_id: "helper-stream" },
    });
    stream.on("text", () => {
      callbacks++;
    });
    const streamed = await stream.finalMessage();
    const betaStream = runtime.client.beta.messages.stream({
      ...params,
      metadata: { user_id: "helper-beta-stream" },
    });
    const betaFinal = await betaStream.finalMessage();
    return {
      stable: stable.parsed_output,
      beta: beta.parsed_output,
      streamed: streamed.parsed_output,
      betaStreamed: betaFinal.parsed_output,
      callbacks,
      compaction: betaFinal.content.find(
        (block) => block.type === "compaction",
      ),
    };
  });
  log(caseId, result);
} finally {
  await runtime.close(caseId);
}
