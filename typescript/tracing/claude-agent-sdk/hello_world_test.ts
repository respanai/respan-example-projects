/**
 * Hello World - Claude Agent SDK + Respan tracing.
 *
 * The simplest possible example: ask Claude a question, see the trace in Respan.
 *
 * Run:
 *   npx tsx hello_world_test.ts
 */

import "dotenv/config";
import { queryForResult } from "./_sdk_runtime.js";

if (!process.env.RESPAN_API_KEY) {
  throw new Error("Set RESPAN_API_KEY to run this example.");
}

console.log("Asking Claude a question...\n");

const { result, sessionId } = await queryForResult({
  prompt: "What is 2 + 2? Reply in one word.",
  options: { permissionMode: "bypassPermissions", maxTurns: 1 },
  onMessage: (message) => console.log(`  ${String(message.type ?? "unknown")}`),
});

console.log(`  Result: subtype=${String(result.subtype)}, turns=${String(result.num_turns)}`);
console.log(`\nSession: ${sessionId}`);
console.log("View trace at: https://platform.respan.ai/platform/traces");
