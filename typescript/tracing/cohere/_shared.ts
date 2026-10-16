import dotenv from "dotenv";
import path from "node:path";
import { fileURLToPath } from "node:url";
import * as Cohere from "cohere-ai";
import { CohereClient, CohereClientV2 } from "cohere-ai";
import { CohereInstrumentor } from "@respan/instrumentation-cohere";
import { Respan } from "@respan/respan";
import {
  startMockCohereServer,
  type MockCohereServer,
} from "./_mock_server.js";
import { startLocalCollector } from "./_collector.js";

const exampleDir = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(exampleDir, "../../..");
if (
  process.env.RESPAN_EXPORT === "true" ||
  process.env.COHERE_USE_REAL_API === "true"
)
  dotenv.config({ path: path.join(repoRoot, ".env"), quiet: true } as any);

export const RUN_ID =
  process.env.RESPAN_EXAMPLE_RUN_ID || `cohere-ts-${Date.now()}`;

function envValue(name: string): string | undefined {
  const direct = process.env[name];
  if (direct && direct.trim()) return direct.trim();
  const spaced = process.env[`${name} `];
  if (spaced && spaced.trim()) return spaced.trim();
  return undefined;
}

export interface CohereRuntime {
  client: CohereClient;
  clientV2: CohereClientV2;
  mode: "mock" | "real";
  close: () => Promise<void>;
}

async function createCohereRuntime(): Promise<CohereRuntime> {
  const useReal = envValue("COHERE_USE_REAL_API") === "true";
  let mockServer: MockCohereServer | undefined;
  const token = useReal ? envValue("COHERE_API_KEY") : "mock-cohere-token";
  if (!token) {
    throw new Error(
      "Set COHERE_API_KEY or leave COHERE_USE_REAL_API unset to use the local mock server.",
    );
  }

  const environment = useReal
    ? envValue("COHERE_BASE_URL")
    : (mockServer = await startMockCohereServer()).baseUrl;

  const options = {
    token,
    environment,
    maxRetries: 0,
    clientName: "respan-cohere-typescript-example",
  };

  return {
    client: new CohereClient(options),
    clientV2: new CohereClientV2(options),
    mode: useReal ? "real" : "mock",
    close: async () => {
      await mockServer?.close();
    },
  };
}

export async function runCohereWorkflow<T>(
  workflowName: string,
  fn: (runtime: CohereRuntime) => Promise<T>,
  capture: { traceContent?: boolean } = {},
): Promise<T> {
  const exportToRespan = process.env.RESPAN_EXPORT === "true";
  const collectorOverride = process.env.RESPAN_COLLECTOR_URL;
  const collector =
    !exportToRespan && !collectorOverride
      ? await startLocalCollector()
      : undefined;
  const apiKey = exportToRespan ? envValue("RESPAN_API_KEY") : "local-fixture";
  if (!apiKey) throw new Error("RESPAN_EXPORT=true requires RESPAN_API_KEY.");

  const respan = new Respan({
    apiKey,
    baseURL: collectorOverride ?? collector?.url ?? envValue("RESPAN_BASE_URL"),
    appName: "cohere-typescript-examples",
    traceContent: capture.traceContent !== false,
    silenceInitializationMessage: true,
    instrumentations: [
      new CohereInstrumentor({
        sdkModule: Cohere,
        traceContent: capture.traceContent !== false,
      }),
    ],
  });

  let runtime: CohereRuntime | undefined;
  await respan.initialize();
  try {
    runtime = await createCohereRuntime();
    const activeRuntime = runtime;
    return await respan.propagateAttributes(
      {
        trace_group_identifier: workflowName,
        custom_identifier: RUN_ID,
        metadata: {
          example_set: "typescript/tracing/cohere",
          workflow_name: workflowName,
          run_id: RUN_ID,
          cohere_mode: activeRuntime.mode,
        },
      },
      () =>
        respan.withWorkflow(
          {
            name: workflowName,
            associationProperties: {
              example_set: "typescript/tracing/cohere",
              provider: "cohere",
              language: "typescript",
            },
          },
          () => fn(activeRuntime),
        ),
    );
  } finally {
    await respan.shutdown();
    await runtime?.close();
    await collector?.close(workflowName, RUN_ID);
  }
}

export function logExampleResult(
  workflowName: string,
  details: Record<string, unknown>,
): void {
  console.log(
    JSON.stringify({ workflowName, runId: RUN_ID, ...details }, null, 2),
  );
}
