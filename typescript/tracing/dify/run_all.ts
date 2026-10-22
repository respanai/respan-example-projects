#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import { randomUUID } from "node:crypto";
import path from "node:path";
import { fileURLToPath } from "node:url";

const exampleDir = path.dirname(fileURLToPath(import.meta.url));
const scripts = [
  "01_chat_blocking.ts",
  "02_chat_streaming.ts",
  "03_completion_workflow.ts",
  "04_knowledge_workspace.ts",
  "05_file_and_error.ts",
];
const runId = process.env.RESPAN_EXAMPLE_RUN_ID ?? `dify-ts-${randomUUID().slice(0, 12)}`;
const childEnv = { ...process.env, RESPAN_EXAMPLE_RUN_ID: runId };

console.log(`example_run_id=${runId}`);

for (const script of scripts) {
  console.log(`\n### Running ${script}`);
  const result = spawnSync(process.execPath, ["--import", "tsx", script], {
    cwd: exampleDir,
    env: childEnv,
    stdio: "inherit",
  });
  if (result.error) throw result.error;
  if (result.status !== 0) process.exit(result.status ?? 1);
}
