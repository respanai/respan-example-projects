/**
 * Gateway Integration - route through Respan, no Anthropic key needed.
 *
 * Run:
 *   npx tsx gateway_test.ts
 */

import "dotenv/config";
import { queryForResult } from "./_sdk_runtime.js";

const API_KEY = process.env.RESPAN_API_KEY;
const BASE_URL = (process.env.RESPAN_GATEWAY_BASE_URL || process.env.RESPAN_BASE_URL || "https://api.respan.ai/api").replace(/\/+$/, "");
const QUERY_TIMEOUT_SECONDS = Number.parseInt(process.env.RESPAN_GATEWAY_QUERY_TIMEOUT_SECONDS ?? process.env.RESPAN_QUERY_TIMEOUT_SECONDS ?? "90", 10);

if (!API_KEY) {
  throw new Error("Set RESPAN_API_KEY to run this example.");
}

const gatewayUrl = `${BASE_URL}/anthropic`;
console.log(`Gateway: ${BASE_URL}`);
console.log(`API key: ${API_KEY.slice(0, 8)}...\n`);

const { result, sessionId } = await queryForResult({
  prompt: "Reply with exactly: gateway_ok",
  options: {
    permissionMode: "bypassPermissions",
    maxTurns: 1,
    env: { ...process.env, ANTHROPIC_BASE_URL: gatewayUrl, ANTHROPIC_AUTH_TOKEN: API_KEY, ANTHROPIC_API_KEY: API_KEY },
  },
  timeoutSeconds: QUERY_TIMEOUT_SECONDS,
  onMessage: (message) => console.log(`  ${String(message.type ?? "unknown")}`),
});

const usage = result.usage as Record<string, unknown> | undefined;
console.log(`  Result: subtype=${String(result.subtype)}, turns=${String(result.num_turns)}`);
if (usage) console.log(`  Usage: input=${usage.input_tokens}, output=${usage.output_tokens}`);
console.log(`\nSession: ${sessionId}`);
console.log("View trace at: https://platform.respan.ai/platform/traces");
