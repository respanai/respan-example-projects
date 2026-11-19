/**
 * Tool Use - trace agent tool calls through Respan.
 *
 * Run:
 *   npx tsx tool_use_test.ts
 */

import "dotenv/config";
import { queryForResult } from "./_sdk_runtime.js";

if (!process.env.RESPAN_API_KEY) {
  throw new Error("Set RESPAN_API_KEY to run this example.");
}

console.log("Running query with tools (Read, Glob, Grep)...\n");

const { result, sessionId } = await queryForResult({
  prompt: "List the files in the current directory. Just show filenames.",
  options: { permissionMode: "bypassPermissions", maxTurns: 3, allowedTools: ["Read", "Glob", "Grep"] },
  onMessage: (message) => console.log(`  ${String(message.type ?? "unknown")}`),
});

console.log(`  Result: subtype=${String(result.subtype)}, turns=${String(result.num_turns)}`);
console.log(`\nSession: ${sessionId}`);
console.log("Check Respan traces to see tool spans (Read, Glob, etc.)");
