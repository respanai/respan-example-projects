import { existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import dotenv from "dotenv";

export interface BeeAIExampleEnv {
  respanApiKey: string;
  respanBaseURL: string | undefined;
  gatewayApiKey: string;
  gatewayBaseURL: string;
  openAIEndpoint: string;
  model: string;
}

function trimTrailingSlash(value: string): string {
  return value.replace(/\/+$/, "");
}

function findRootEnv(): string | undefined {
  let current = dirname(fileURLToPath(import.meta.url));
  for (let i = 0; i < 8; i += 1) {
    const candidate = join(current, ".env");
    if (existsSync(candidate)) {
      return candidate;
    }
    current = dirname(current);
  }
  return undefined;
}

function requireEnv(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(
      `Set ${name} in respan-example-projects/.env to run this example.`,
    );
  }
  return value;
}

export function loadBeeAIExampleEnv(): BeeAIExampleEnv {
  const envPath = findRootEnv();
  if (envPath) dotenv.config({ path: envPath });

  const respanApiKey = requireEnv("RESPAN_API_KEY");
  const gatewayApiKey = process.env.RESPAN_GATEWAY_API_KEY || respanApiKey;
  const gatewayBaseURL = trimTrailingSlash(
    process.env.RESPAN_GATEWAY_BASE_URL ||
      process.env.RESPAN_BASE_URL ||
      "https://api.respan.ai/api",
  );
  const openAIEndpoint = gatewayBaseURL;
  const model = process.env.RESPAN_MODEL || "gpt-4o";

  process.env.OPENAI_API_KEY = gatewayApiKey;
  process.env.OPENAI_API_ENDPOINT = openAIEndpoint;
  process.env.OPENAI_BASE_URL = openAIEndpoint;
  process.env.OPENAI_CHAT_MODEL = model;

  return {
    respanApiKey,
    respanBaseURL: process.env.RESPAN_BASE_URL,
    gatewayApiKey,
    gatewayBaseURL,
    openAIEndpoint,
    model,
  };
}
