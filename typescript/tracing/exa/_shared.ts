import dotenv from "dotenv";
import { Exa } from "exa-js";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { ExaInstrumentor } from "@respan/instrumentation-exa";
import { Respan } from "@respan/respan";
import { startMockExaServer, type MockExaServer } from "./_mock_server.js";

const exampleDir = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(exampleDir, "../../..");
dotenv.config({ path: path.join(repoRoot, ".env"), override: false, quiet: true });

export const RUN_ID =
  process.env.RESPAN_EXAMPLE_RUN_ID ?? `otel2-exa-typescript-${Date.now()}`;

export interface ExaRuntime {
  client: Exa;
  mode: "live" | "loopback";
  close: () => Promise<void>;
}

function requireEnv(name: string): string {
  const value = process.env[name];
  if (!value) throw new Error(`${name} is required in respan-example-projects/.env`);
  return value;
}

async function createRuntime(): Promise<ExaRuntime> {
  if (["1", "true", "yes"].includes((process.env.RESPAN_EXA_LIVE ?? "0").toLowerCase())) {
    return {
      client: new Exa(requireEnv("EXA_API_KEY")),
      mode: "live",
      close: async () => {},
    };
  }
  const server: MockExaServer = await startMockExaServer();
  return {
    client: new Exa("loopback-exa-key", server.baseURL),
    mode: "loopback",
    close: server.close,
  };
}

export async function runExaExample<T>(params: {
  example: string;
  fn: (runtime: ExaRuntime) => Promise<T>;
}): Promise<T> {
  const respan = new Respan({
    apiKey: requireEnv("RESPAN_API_KEY"),
    baseURL: process.env.RESPAN_BASE_URL,
    appName: "exa-typescript-examples",
    traceContent: true,
    silenceInitializationMessage: true,
    instrumentations: [new ExaInstrumentor()],
  });
  await respan.initialize();
  const runtime = await createRuntime();
  const workflowName = `exa_typescript_${params.example.replaceAll("-", "_")}`;
  try {
    return await respan.propagateAttributes(
      {
        custom_identifier: `exa-${params.example}-${RUN_ID}`,
        trace_group_identifier: workflowName,
        metadata: {
          example: params.example,
          example_set: "typescript/tracing/exa",
          run_id: RUN_ID,
          workflow_name: workflowName,
          exa_mode: runtime.mode,
        },
      },
      () =>
        respan.withWorkflow(
          {
            name: workflowName,
            associationProperties: {
              integration: "exa",
              language: "typescript",
            },
          },
          () => params.fn(runtime),
        ),
    );
  } finally {
    await respan.shutdown();
    await runtime.close();
  }
}

export function printResult(example: string, mode: string, result: unknown): void {
  console.log(JSON.stringify({ example, mode, runId: RUN_ID, result }, null, 2));
}
