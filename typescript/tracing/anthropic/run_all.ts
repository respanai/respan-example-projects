import { spawn } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";
const cwd = path.dirname(fileURLToPath(import.meta.url));
const scripts = [
  "01_basic.ts",
  "02_streaming.ts",
  "03_tool_call.ts",
  "04_expected_error.ts",
  "05_parse_and_stream_helpers.ts",
  "06_native_tool_runner.ts",
  "07_count_tokens_and_batches.ts",
  "08_legacy_completion.ts",
];
const runId =
  process.env.RESPAN_EXAMPLE_RUN_ID || `typescript-anthropic-${Date.now()}`;
for (const script of scripts)
  await new Promise<void>((resolve, reject) => {
    const child = spawn(
      process.execPath,
      ["node_modules/tsx/dist/cli.mjs", script],
      {
        cwd,
        env: { ...process.env, RESPAN_EXAMPLE_RUN_ID: runId },
        stdio: "inherit",
      },
    );
    child.on("error", reject);
    child.on("exit", (code) =>
      code === 0 ? resolve() : reject(Error(`${script} failed with ${code}`)),
    );
  });
console.log(JSON.stringify({ runId, scripts }));
