import { withCapture } from "./capture.js";
import { EveInstrumentor, withEveLineage } from "@respan/instrumentation-eve";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-http";
import { RespanTelemetry } from "@respan/tracing";
import { defineInstrumentation } from "eve/instrumentation";
import { EXAMPLE_RUN_ID, RESPAN_API_KEY, RESPAN_BASE_URL } from "../_env.js";

const instrumentor = new EveInstrumentor();
const exporter = new OTLPTraceExporter({
  url:
    (RESPAN_BASE_URL ?? "https://api.respan.ai")
      .replace(/\/$/, "")
      .replace(/\/api$/, "") + "/api/v2/traces",
  headers: { Authorization: "Bearer " + RESPAN_API_KEY },
});
const respan = new RespanTelemetry({
  apiKey: RESPAN_API_KEY,
  baseURL: RESPAN_BASE_URL,
  appName: "eve-typescript-examples",
  disabledInstrumentations: [
    "openAI",
    "anthropic",
    "azureOpenAI",
    "cohere",
    "bedrock",
    "googleVertexAI",
    "googleAIPlatform",
    "pinecone",
    "together",
    "langChain",
    "llamaIndex",
    "chromaDB",
    "qdrant",
  ],
  exporter: instrumentor.wrapExporter(withCapture(exporter)),
  // These examples use only deterministic synthetic content, so keep capture
  // enabled and verify the actual chat/tool payloads on the platform.
  traceContent: true,
  silenceInitializationMessage: true,
});

await respan.initialize();
instrumentor.activate();

export default withEveLineage(
  defineInstrumentation({
    functionId: "eve_typescript_" + EXAMPLE_RUN_ID,
    recordInputs: true,
    recordOutputs: true,
    events: {
      "step.started"(input) {
        return {
          runtimeContext: {
            "example.framework": "eve",
            "example.run_id": EXAMPLE_RUN_ID,
            "example.step_index": input.step.index,
          },
        };
      },
    },
  }),
);
