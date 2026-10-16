import { spawnSync } from "node:child_process";
const files = [
  "01_guard.ts",
  "02_redact.ts",
  "03_workflow.ts",
  "04_scan.ts",
  "05_fallback.ts",
  "06_privacy.ts",
  "07_provider_error.ts",
  "08_large_payload.ts",
];
for (const file of files) {
  const result = spawnSync(process.execPath, ["--import", "tsx", file], {
    stdio: "inherit",
    env: {
      ...process.env,
      RESPAN_EXAMPLE_RUN_ID: `${process.env.RESPAN_EXAMPLE_RUN_ID ?? "superagent-ts-" + Date.now()}-${file.slice(0, 2)}`,
    },
  });
  if (result.status !== 0) process.exit(result.status ?? 1);
}
