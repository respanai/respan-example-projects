import * as Cursor from "@cursor/sdk";
import { Respan } from "@respan/respan";
import { CursorSDKInstrumentor } from "@respan/instrumentation-cursor";
import { nativeFixture } from "./_native_fixture.mjs";
import { writeFile } from "node:fs/promises";
export { Cursor };
export const RUN_ID =
  process.env.RESPAN_EXAMPLE_RUN_ID ?? `cursor-sdk-${Date.now()}`;
export async function scenario(
  name: string,
  fn: (sdk: typeof Cursor, fixture: any, respan: Respan) => Promise<unknown>,
  traceContent = true,
) {
  const fixture = await nativeFixture();
  const spans: any[] = [];
  const exporting = process.env.RESPAN_EXAMPLE_EXPORT === "1";
  const plugin = new CursorSDKInstrumentor({
    sdkModule: { ...Cursor },
    agentName: "cursor-example",
    traceContent,
  });
  const respan = new Respan({
    appName: "cursor-sdk-example",
    apiKey: exporting ? process.env.RESPAN_API_KEY : "cursor-fixture-key",
    baseURL: exporting ? process.env.RESPAN_BASE_URL : fixture.baseURL,
    instrumentations: [plugin],
    traceContent,
    silenceInitializationMessage: true,
  });
  try {
    await respan.initialize();
    respan.addProcessor({
      name: "example-capture",
      filter: () => true,
      disableBatch: true,
      exporter: {
        export(values: any[], cb: any) {
          spans.push(...values);
          cb({ code: 0 });
        },
        async shutdown() {},
      },
    });
    const result = await respan.propagateAttributes(
      {
        custom_identifier: RUN_ID,
        metadata: {
          run_id: RUN_ID,
          example: "typescript-cursor-sdk",
          scenario: name,
        },
      },
      () =>
        respan.withWorkflow({ name: `cursor-${name}` }, () =>
          fn(Cursor, fixture, respan),
        ),
    );
    await respan.flush();
    if (
      !traceContent &&
      spans
        .filter((span) =>
          ["agent", "tool"].includes(span.attributes["respan.entity.log_type"]),
        )
        .some((span) =>
          Object.keys(span.attributes).some((key) =>
            ["traceloop.entity.input", "traceloop.entity.output"].includes(key),
          ),
        )
    )
      throw new Error("Private example captured content");
    const normalized = spans.map((span) => ({
      name: span.name,
      spanId: span.spanContext().spanId,
      traceId: span.spanContext().traceId,
      parentSpanId: span.parentSpanContext?.spanId,
      attributes: span.attributes,
      status: span.status,
    }));
    if (process.env.RESPAN_EXAMPLE_CAPTURE_PATH)
      await writeFile(
        process.env.RESPAN_EXAMPLE_CAPTURE_PATH,
        JSON.stringify(
          { runId: RUN_ID, scenario: name, spans: normalized },
          null,
          2,
        ),
      );
    console.log(
      JSON.stringify({
        runId: RUN_ID,
        scenario: name,
        spans: spans.length,
        result,
      }),
    );
  } finally {
    plugin.deactivate();
    await respan.shutdown();
    await fixture.close();
  }
}
