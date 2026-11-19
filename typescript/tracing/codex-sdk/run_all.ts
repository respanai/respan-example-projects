import { spawnSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";
const dir = path.dirname(fileURLToPath(import.meta.url));
const scripts = [
  "01_basic_turn.ts",
  "02_streamed_turn.ts",
  "03_structured_output.ts",
  "04_image_input.ts",
  "05_resume_thread.ts",
  "06_workspace_file_change.ts",
  "07_expected_error.ts",
  "08_privacy_and_lifecycle.ts",
  "09_current_sdk_options.ts",
];
for (const script of scripts) {
  const result = spawnSync(
    process.execPath,
    ["--import", "tsx", path.join(dir, script)],
    {
      stdio: "inherit",
      env: {
        ...process.env,
        OTEL_METRICS_EXPORTER: "none",
        OTEL_LOGS_EXPORTER: "none",
      },
    },
  );
  if (result.status !== 0) process.exit(result.status ?? 1);
}
