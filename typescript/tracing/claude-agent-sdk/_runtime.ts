import * as ClaudeAgentSDKExports from "@anthropic-ai/claude-agent-sdk";
import { ClaudeAgentSDKInstrumentor } from "@respan/instrumentation-claude-agent-sdk";
import { Respan } from "@respan/respan";
import dotenv from "dotenv";
import { existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const DEFAULT_RESPAN_BASE_URL = "https://api.respan.ai";
const DEFAULT_GATEWAY_BASE_URL = "https://api.respan.ai/api";

let envLoaded = false;

type QueryMessage = Record<string, unknown>;
type QueryFunction = (args: Record<string, unknown>) => AsyncIterable<unknown> | Promise<AsyncIterable<unknown>>;

export interface Runtime {
  query: QueryFunction;
  prewarm: typeof ClaudeAgentSDKExports.prewarm;
  respan: Respan;
  runId: string;
  options: Record<string, unknown>;
}

type QueryOptions = Record<string, unknown>;

export function loadEnv(): void {
  if (envLoaded) return;
  let current = dirname(fileURLToPath(import.meta.url));
  for (let depth = 0; depth < 8; depth += 1) {
    const envPath = join(current, ".env");
    if (existsSync(envPath)) {
      dotenv.config({ path: envPath, override: false, quiet: true });
      envLoaded = true;
      return;
    }
    const parent = dirname(current);
    if (parent === current) break;
    current = parent;
  }
  dotenv.config({ override: false, quiet: true });
  envLoaded = true;
}

export function requireEnv(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`${name} is required. Add it to respan-example-projects/.env.`);
  }
  return value;
}

export async function createRuntime(appName: string): Promise<Runtime> {
  loadEnv();
  const respanApiKey = requireEnv("RESPAN_API_KEY");
  const gatewayApiKey = process.env.RESPAN_GATEWAY_API_KEY ?? respanApiKey;
  const respanBaseURL = process.env.RESPAN_BASE_URL ?? DEFAULT_RESPAN_BASE_URL;
  const gatewayBaseURL = (
    process.env.RESPAN_GATEWAY_BASE_URL ?? DEFAULT_GATEWAY_BASE_URL
  ).replace(/\/+$/, "");
  const runId = process.env.RESPAN_EXAMPLE_RUN_ID ?? `claude-agent-sdk-ts-${Date.now()}`;
  const sdkModule = { ...ClaudeAgentSDKExports } as Record<string, unknown>;

  const respan = new Respan({
    apiKey: respanApiKey,
    baseURL: respanBaseURL,
    appName,
    instrumentations: [
      new ClaudeAgentSDKInstrumentor({
        sdkModule,
        agentName: appName,
      }),
    ],
    traceContent: true,
    silenceInitializationMessage: true,
  });
  await respan.initialize();

  const options = {
    permissionMode: "bypassPermissions",
    allowDangerouslySkipPermissions: true,
    maxTurns: 1,
    env: {
      ...process.env,
      ANTHROPIC_BASE_URL: `${gatewayBaseURL}/anthropic`,
      ANTHROPIC_AUTH_TOKEN: gatewayApiKey,
      ANTHROPIC_API_KEY: gatewayApiKey,
    },
  };

  console.log(`run_id: ${runId}`);
  console.log(`gateway_base_url: ${gatewayBaseURL}/anthropic`);

  return {
    query: sdkModule.query as QueryFunction,
    prewarm: sdkModule.prewarm as typeof ClaudeAgentSDKExports.prewarm,
    respan,
    runId,
    options,
  };
}

function mergeQueryOptions(base: QueryOptions, overrides: QueryOptions): QueryOptions {
  return {
    ...base,
    ...overrides,
    env: {
      ...(base.env as Record<string, string | undefined> | undefined),
      ...(overrides.env as Record<string, string | undefined> | undefined),
    },
  };
}

export async function queryForResult(
  runtime: Runtime,
  prompt: string,
  optionOverrides: QueryOptions = {},
): Promise<QueryMessage> {
  const stream = await runtime.query({
    prompt,
    options: mergeQueryOptions(runtime.options, optionOverrides),
  });
  let result: QueryMessage | undefined;

  for await (const rawMessage of stream) {
    const message = rawMessage as QueryMessage;
    console.log(`  ${String(message.type ?? "unknown")}`);
    if (message.type === "result") {
      result = message;
    }
  }

  if (!result) {
    throw new Error("Claude Agent SDK query completed without a result message.");
  }
  return result;
}

export async function shutdownRuntime(runtime: Runtime): Promise<void> {
  await runtime.respan.shutdown();
}
