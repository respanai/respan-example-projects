import { spawnSync } from "node:child_process";
for (const file of [
  "01_agent_generate.ts",
  "02_agent_tool_call.ts",
  "03_agent_stream.ts",
  "04_agent_failure.ts",
  "05_workflow.ts",
  "06_native_shapes.ts",
  "07_privacy.ts",
]) {
  const result = spawnSync(process.execPath, ["--import", "tsx", file], {
    stdio: "inherit",
    env: process.env,
  });
  if (result.status !== 0) process.exit(result.status ?? 1);
}
