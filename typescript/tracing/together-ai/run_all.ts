import { spawn } from "node:child_process";
const scripts = [
  "01_chat_completion.ts",
  "02_chat_streaming.ts",
  "03_tool_calls.ts",
  "04_text_completion_embedding.ts",
  "05_image_rerank.ts",
  "06_audio_transcription_translation.ts",
  "07_expected_error.ts",
  "08_content_opt_out.ts",
  "09_current_features.ts",
];
for (const script of scripts)
  await new Promise<void>((resolve, reject) => {
    const child = spawn(process.execPath, ["--import", "tsx", script], {
      stdio: "inherit",
      env: {
        ...process.env,
        OTEL_METRICS_EXPORTER: "none",
        OTEL_LOGS_EXPORTER: "none",
      },
    });
    child.once("error", reject);
    child.once("exit", (code) =>
      code === 0 ? resolve() : reject(new Error(`${script} exited ${code}`)),
    );
  });
