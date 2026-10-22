import { spawn } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const exampleDir = path.dirname(fileURLToPath(import.meta.url));
const scripts = [
  "01_converse.ts",
  "02_invoke_model.ts",
  "03_streaming.ts",
  "04_expected_error.ts",
  "05_native_features.ts",
];

for (const script of scripts) {
  await runScript(script);
}

function runScript(script: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const child = spawn(
      process.execPath,
      ["--import", "tsx", path.join(exampleDir, script)],
      {
        cwd: exampleDir,
        env: process.env,
        stdio: "inherit",
      },
    );
    child.on("error", reject);
    child.on("exit", (code) => {
      if (code === 0) resolve();
      else reject(new Error(`${script} exited with code ${code}`));
    });
  });
}
