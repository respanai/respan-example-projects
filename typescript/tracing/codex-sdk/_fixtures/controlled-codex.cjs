#!/usr/bin/env node
// Deterministic CLI JSONL transport for the actual released Codex SDK.
// This does not execute Codex model inference or the native Codex CLI.
const fs = require("node:fs");
const args = process.argv.slice(2);
let input = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", (chunk) => (input += chunk));
process.stdin.on("end", async () => {
  if (process.env.CODEX_FIXTURE_REQUEST_PATH) {
    const schemaIndex = args.indexOf("--output-schema");
    fs.writeFileSync(
      process.env.CODEX_FIXTURE_REQUEST_PATH,
      JSON.stringify({
        args,
        input,
        schema:
          schemaIndex >= 0
            ? JSON.parse(fs.readFileSync(args[schemaIndex + 1], "utf8"))
            : null,
      }),
    );
  }
  const emit = (e) => process.stdout.write(JSON.stringify(e) + "\n");
  const scenario = process.env.CODEX_FIXTURE_SCENARIO || "all";
  if (scenario === "invalid-json") {
    process.stdout.write("{broken\n");
    return;
  }
  if (scenario === "process-error") {
    process.stderr.write("controlled process failure");
    process.exitCode = 7;
    return;
  }
  emit({
    type: "thread.started",
    thread_id: process.env.CODEX_FIXTURE_THREAD_ID || "controlled-codex-thread",
  });
  emit({ type: "turn.started" });
  if (scenario === "wait") {
    setTimeout(() => {}, 10000);
    return;
  }
  const items = [
    { id: "reason-1", type: "reasoning", text: "controlled reasoning summary" },
    {
      id: "command-1",
      type: "command_execution",
      command: "pwd",
      aggregated_output: "controlled workspace\n",
      exit_code: 0,
      status: "completed",
    },
    {
      id: "mcp-1",
      type: "mcp_tool_call",
      server: "fixture",
      tool: "lookup",
      arguments: {
        query: "controlled",
        false: false,
        zero: 0,
        empty: "",
        nullable: null,
        definitions: Array.from({ length: 82 }, (_, i) => ({
          name: `tool_${i}`,
          parameters: {
            type: "object",
            properties: { value: { type: "string" } },
          },
        })),
      },
      result: {
        content: [
          { type: "text", text: "controlled MCP result" },
          { type: "image", data: "AA==", mimeType: "image/png" },
        ],
        structured_content: {
          ok: true,
          vector: Array.from({ length: 5001 }, (_, i) => i / 5001),
        },
        ...(process.env.CODEX_FIXTURE_CACHE_WRITE === "1"
          ? { _meta: { controlled: true } }
          : {}),
      },
      status: "completed",
    },
    { id: "web-1", type: "web_search", query: "controlled search" },
    {
      id: "file-1",
      type: "file_change",
      changes: [{ path: "controlled.txt", kind: "update" }],
      status: "completed",
    },
    {
      id: "todo-1",
      type: "todo_list",
      items: [{ text: "controlled task", completed: true }],
    },
    { id: "error-1", type: "error", message: "controlled nonfatal error" },
    {
      id: "message-1",
      type: "agent_message",
      text:
        scenario === "structured"
          ? '{"ok":true,"value":0}'
          : scenario === "empty"
            ? ""
            : "controlled native result",
    },
  ];
  for (const item of items) {
    if (scenario === "failure" && item.id !== "command-1") continue;
    emit({
      type: "item.started",
      item: { ...item, ...(item.status ? { status: "in_progress" } : {}) },
    });
    emit({ type: "item.updated", item });
    emit({ type: "item.completed", item });
  }
  if (scenario === "failure")
    emit({
      type: "turn.failed",
      error: { message: "controlled turn failure" },
    });
  else if (scenario === "stream-error")
    emit({ type: "error", message: "controlled stream error" });
  else {
    const usage = {
      input_tokens: 31,
      cached_input_tokens: 4,
      output_tokens: 9,
      reasoning_output_tokens: 3,
    };
    if (process.env.CODEX_FIXTURE_CACHE_WRITE === "1")
      usage.cache_write_input_tokens = 2;
    emit({ type: "turn.completed", usage });
  }
});
