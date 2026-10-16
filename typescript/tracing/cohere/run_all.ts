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
  "01_v2_chat_tools.ts",
  "02_v2_streaming_chat.ts",
  "03_embeddings.ts",
  "04_rerank.ts",
  "05_legacy_generate.ts",
  "06_expected_error.ts",
  "07_privacy.ts",
  "08_v1_chat.ts",
  "09_document_parse.ts",
];

const runId = process.env.RESPAN_EXAMPLE_RUN_ID || `cohere-ts-${Date.now()}`;

async function runExample(fileName: string): Promise<void> {
  console.log(`\n=== ${fileName.replace(/\.ts$/, "")} ===`);
  await new Promise<void>((resolve, reject) => {
    const child = spawn(tsxBin, [fileName], {
      cwd: exampleDir,
      env: {
        ...process.env,
        RESPAN_EXAMPLE_RUN_ID: runId,
      },
      stdio: "inherit",
    });

    child.on("error", reject);
    child.on("exit", (code) => {
      if (code === 0) {
        resolve();
        return;
      }
      reject(new Error(`${fileName} exited with status ${code ?? "unknown"}`));
    });
  });
}

for (const example of examples) {
  await runExample(example);
}

console.log(JSON.stringify({ runId, examples }, null, 2));
