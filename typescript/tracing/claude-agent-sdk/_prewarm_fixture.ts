// Deterministic CLI wire protocol for the real Claude Agent SDK.
// No repository files or provider services are read by this fixture.
import { EventEmitter } from "node:events";
import { PassThrough, Writable } from "node:stream";
import type { SpawnedProcess } from "@anthropic-ai/claude-agent-sdk";

export function createPrewarmFixture(toolFailure: boolean): SpawnedProcess {
  const process = new EventEmitter() as EventEmitter & SpawnedProcess;
  const stdout = new PassThrough();
  process.stdout = stdout;
  Object.defineProperty(process, "killed", { value: false, writable: true });
  Object.defineProperty(process, "exitCode", { value: null, writable: true });

  let hooks: Record<string, Array<{ hookCallbackIds?: string[] }>> | undefined;
  let hookId = 0;
  const pendingHooks = new Map<string, () => void>();
  const send = (message: Record<string, unknown>) => stdout.write(`${JSON.stringify(message)}\n`);
  const hook = async (event: string, input: Record<string, unknown>) => {
    for (const matcher of hooks?.[event] ?? []) {
      for (const callbackId of matcher.hookCallbackIds ?? []) {
        const requestId = `hook-${hookId++}`;
        const completed = new Promise<void>(resolve => pendingHooks.set(requestId, resolve));
        send({ type: "control_request", request_id: requestId, request: {
          subtype: "hook_callback", callback_id: callbackId, tool_use_id: "prewarm-tool",
          input: { hook_event_name: event, session_id: "prewarm-session", ...input },
        } });
        await completed;
      }
    }
  };
  process.stdin = new Writable({ write(chunk, _encoding, done) {
    for (const line of chunk.toString().trim().split("\n")) {
      const message = JSON.parse(line);

      if (message.type === "control_request") {
        if (message.request.subtype === "initialize") hooks = message.request.hooks;
        send({ type: "control_response", response: { subtype: "success", request_id: message.request_id,
          response: message.request.subtype === "initialize"
            ? { commands: [], agents: [], models: [], capabilities: {} }
            : { cwd: "/private/tmp", session_id: "prewarm-session" },
        } });
      } else if (message.type === "control_response") {
        pendingHooks.get(message.response.request_id)?.();
      } else if (message.type === "user") {
        (async () => {
          await hook("UserPromptSubmit", { prompt: "claim fixture" });
          await hook("PreToolUse", { tool_name: "Read", tool_input: { file_path: "fixture.txt" } });
          await hook(toolFailure ? "PostToolUseFailure" : "PostToolUse", {
            tool_name: "Read", tool_input: { file_path: "fixture.txt" },
            ...(toolFailure ? { error: "fixture rejected" } : { tool_response: "fixture contents" }),
          });
          send({ type: "assistant", session_id: "prewarm-session", message: {
            id: "prewarm-message", model: "claude-sonnet-4-6", role: "assistant",
            content: [{ type: "text", text: "claim fixture completed" }],
            usage: { input_tokens: 4, output_tokens: 3 },
          } });
          send({ type: "result", subtype: "success", session_id: "prewarm-session",
            result: "claim fixture completed", duration_ms: 1, duration_api_ms: 1,
            num_turns: 1, is_error: false, usage: { input_tokens: 4, output_tokens: 3 },
          });
        })().catch(error => process.emit("error", error));
      }
    }
    done();
  } });
  process.kill = () => {
    if (process.killed) return true;
    Object.defineProperty(process, "killed", { value: true });
    Object.defineProperty(process, "exitCode", { value: 0 });
    stdout.end();
    process.emit("exit", 0, null);
    return true;
  };
  return process;
}
