import { spawn } from "node:child_process";

const scripts = [
  "01_core.ts",
  "02_streaming.ts",
  "03_agent_research_tools.ts",
  "04_expected_error.ts",
];
const runId =
  process.env.RESPAN_EXAMPLE_RUN_ID ??
  `otel2-exa-typescript-${new Date().toISOString().replaceAll(/[-:.]/g, "")}`;
console.log(`RESPAN_EXAMPLE_RUN_ID=${runId}`);

for (const script of scripts) {
  await new Promise<void>((resolve, reject) => {
    const child = spawn(process.execPath, ["--import", "tsx", script], {
      cwd: import.meta.dirname,
      env: { ...process.env, RESPAN_EXAMPLE_RUN_ID: runId },
      stdio: "inherit",
    });
    child.once("error", reject);
    child.once("exit", (code) =>
      code === 0 ? resolve() : reject(new Error(`${script} exited with ${code}`)),
    );
  });
}
