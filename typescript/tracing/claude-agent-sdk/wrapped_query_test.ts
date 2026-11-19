/**
 * Auto-Instrumented Query - the simplest integration pattern.
 *
 * Respan auto-patches query() via ClaudeAgentSDKInstrumentor.
 *
 * Run:
 *   npx tsx wrapped_query_test.ts
 */

import "dotenv/config";
import { queryForResult } from "./_sdk_runtime.js";

if (!process.env.RESPAN_API_KEY) {
  throw new Error("Set RESPAN_API_KEY to run this example.");
}

console.log("Running auto-instrumented query...\n");

const { messageTypes, result } = await queryForResult({
  prompt: "Name three primary colors. One word each, comma separated.",
  options: { permissionMode: "bypassPermissions", maxTurns: 1 },
  onMessage: (message) => console.log(`  ${String(message.type ?? "unknown")}`),
});

console.log(`\nMessage flow: ${messageTypes.join(" -> ")}`);
console.log(`Result: subtype=${String(result.subtype)}, turns=${String(result.num_turns)}`);
console.log("All traces exported automatically via auto-instrumented query()");
