import { FlueInstrumentor } from "@respan/instrumentation-flue";
import { Respan } from "@respan/respan";
import dotenv from "dotenv";
import { existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { nativeRuntime, current, runtime } from "./_native.mjs";

export const EXAMPLE_RUN_ID =
  process.env.RESPAN_EXAMPLE_RUN_ID ?? `flue-ts-native-${Date.now()}`;
for (const method of ["debug", "info", "log"] as const) {
  const original = console[method].bind(console);
  console[method] = (...args: unknown[]) => {
    const label = typeof args[0] === "string" ? args[0] : "";
    if (label.startsWith("[Respan") || label.startsWith("Respan tracing"))
      return;
    original(...args);
  };
}
let root = dirname(fileURLToPath(import.meta.url));
for (let depth = 0; depth < 8; depth++) {
  const path = join(root, ".env");
  if (existsSync(path)) {
    dotenv.config({ path, quiet: true });
    break;
  }
  root = dirname(root);
}

process.env.OTEL_METRICS_EXPORTER ??= "none";
const instrumentor = new FlueInstrumentor({ runtimeModule: runtime });
const respan = new Respan({
  apiKey: process.env.RESPAN_API_KEY,
  baseURL: process.env.RESPAN_BASE_URL ?? "https://api.respan.ai/api",
  appName: "flue-native-typescript",
  instrumentations: [instrumentor],
  silenceInitializationMessage: true,
});
let initialized: Promise<void> | undefined;

export async function runNativeExample(
  name: string,
  options: any,
  execute: (native: any) => Promise<unknown>,
): Promise<void> {
  if (!process.env.RESPAN_API_KEY)
    throw new Error(
      "RESPAN_API_KEY is required in respan-example-projects/.env",
    );
  initialized ??= respan.initialize();
  await initialized;
  let native: any;
  try {
    await respan.propagateAttributes(
      {
        custom_identifier: EXAMPLE_RUN_ID,
        metadata: {
          run_id: EXAMPLE_RUN_ID,
          example: "flue-typescript-native",
          scenario: name,
          profile: current ? "2.2.2" : "1.0.0-beta.1",
        },
      },
      () =>
        respan.withWorkflow({ name }, async () => {
          native = await nativeRuntime(options);
          await execute(native);
        }),
    );
    console.log(
      JSON.stringify({
        runId: EXAMPLE_RUN_ID,
        scenario: name,
        profile: current ? "2.2.2" : "1.0.0-beta.1",
        nativeRequests: native?.requests.length,
        nativeToolCalls: native?.calls.length,
      }),
    );
  } finally {
    await native?.close();
  }
}

export async function shutdownNativeExamples(): Promise<void> {
  await instrumentor.deactivate();
  await respan.shutdown();
}
