import { appendFileSync } from "node:fs";
import type { SpanExporter } from "@opentelemetry/sdk-trace-base";
function sanitized(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(sanitized);
  if (value && typeof value === "object")
    return Object.fromEntries(
      Object.entries(value)
        .filter(
          ([key]) =>
            !/(?:auth|credential|organization|\borg\b|account|storage|store_id|signed|limit|credit|budget|customer|email|cost|price|meter|markup|discount)/i.test(
              key,
            ),
        )
        .map(([key, item]) => [key, sanitized(item)]),
    );
  if (typeof value === "string" && /^[\[{]/.test(value)) {
    try {
      return JSON.stringify(sanitized(JSON.parse(value)));
    } catch {}
  }
  return value;
}
export function withCapture(exporter: SpanExporter): SpanExporter {
  return {
    export(spans, callback) {
      const path = process.env.RESPAN_EXAMPLE_CAPTURE_PATH;
      if (path)
        for (const span of spans)
          appendFileSync(
            path,
            JSON.stringify(
              sanitized({
                name: span.name,
                context: span.spanContext(),
                parent: span.parentSpanContext,
                attributes: span.attributes,
                status: span.status,
                events: span.events,
                links: span.links,
              }),
            ) + "\n",
          );
      exporter.export(spans, callback);
    },
    forceFlush: () => exporter.forceFlush?.() ?? Promise.resolve(),
    shutdown: () => exporter.shutdown(),
  };
}
