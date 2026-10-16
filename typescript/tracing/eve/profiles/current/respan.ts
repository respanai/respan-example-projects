import { withCapture } from "../capture.js";
import { EveSpanProcessor, withEveLineage } from "@respan/instrumentation-eve";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-http";
import { otelIntegration } from "eve/instrumentation/otel";
const translator = new EveSpanProcessor();
const exporter = new OTLPTraceExporter({
  url:
    (process.env.RESPAN_BASE_URL ?? "https://api.respan.ai")
      .replace(/\/$/, "")
      .replace(/\/api$/, "") + "/api/v2/traces",
  headers: { Authorization: "Bearer " + process.env.RESPAN_API_KEY },
});
export default withEveLineage(
  otelIntegration({
    spanProcessors: [translator],
    traceExporter: translator.wrapExporter(withCapture(exporter)),
    runtimeContext: () => ({
      "example.run_id": process.env.RESPAN_EXAMPLE_RUN_ID ?? "",
    }),
  }),
);
