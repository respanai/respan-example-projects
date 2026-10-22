import { spawn } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const exampleDir = path.dirname(fileURLToPath(import.meta.url));
const tsxBin = path.join(
  exampleDir,
  "node_modules",
  ".bin",
  process.platform === "win32" ? "tsx.cmd" : "tsx",
);
const examples = [
  "01_log_request_chat_tools.ts",
  "02_log_stream.ts",
  "03_log_single_stream.ts",
  "04_single_request_builder.ts",
  "05_custom_events.ts",
  "06_expected_error.ts",
  "07_anthropic_direct.ts",
  "08_delayed_builder.ts",
  "09_privacy_constructor_headers.ts",
  "10_provider_stream_shapes.ts",
];
const runId = process.env.RESPAN_EXAMPLE_RUN_ID ?? `helicone-ts-${Date.now()}`;
const requestedTimeout = Number(process.env.RESPAN_EXAMPLE_TIMEOUT_MS ?? 120_000);
const timeoutMs = Number.isFinite(requestedTimeout)
  ? Math.min(300_000, Math.max(5_000, requestedTimeout))
  : 120_000;
const results: Array<{
  fileName: string;
  status: "passed" | "failed";
  error?: string;
}> = [];

console.log(JSON.stringify({
  runId,
  exampleRunId: runId,
  exampleSet: "typescript/tracing/helicone",
  scenarioCount: examples.length,
  timeoutMs,
}, null, 2));

for (const fileName of examples) {
  console.log(`\n=== ${fileName.replace(/\.ts$/, "")} ===`);
  try {
    await runExample(fileName);
    results.push({ fileName, status: "passed" });
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    results.push({ fileName, status: "failed", error: message });
    console.error(JSON.stringify({ fileName, status: "failed", error: message }));
  }
}

console.log(JSON.stringify({
  runId,
  exampleRunId: runId,
  exampleSet: "typescript/tracing/helicone",
  examples,
  results,
}, null, 2));

if (results.some((result) => result.status === "failed")) {
  process.exitCode = 1;
}

async function runExample(fileName: string): Promise<void> {
  await new Promise<void>((resolve, reject) => {
    const child = spawn(tsxBin, [fileName], {
      cwd: exampleDir,
      env: { ...process.env, RESPAN_EXAMPLE_RUN_ID: runId },
      stdio: "inherit",
    });
    let settled = false;
    const settle = (fn: () => void) => {
      if (settled) return;
      settled = true;
      clearTimeout(timeout);
      fn();
    };
    const timeout = setTimeout(() => {
      child.kill("SIGTERM");
      settle(() => reject(new Error(`${fileName} timed out after ${timeoutMs}ms`)));
    }, timeoutMs);

    child.on("error", (error) => settle(() => reject(error)));
    child.on("exit", (code, signal) => settle(() => {
      if (code === 0) resolve();
      else reject(new Error(
        `${fileName} exited with status ${code ?? "unknown"}` +
        (signal ? ` (${signal})` : ""),
      ));
    }));
  });
}
