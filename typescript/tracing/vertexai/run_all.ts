import { spawn } from "node:child_process";
const scripts = [
  "01_generate_content.ts",
  "02_generate_content_stream.ts",
  "03_chat_tool_call.ts",
  "04_error_capture.ts",
  "05_automatic_function_calls.ts",
  "06_embeddings.ts",
  "07_image_video.ts",
  "08_content_opt_out.ts",
  "09_legacy_vertex.ts",
  "10_current_features.ts",
  "11_image_inference.ts",
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
