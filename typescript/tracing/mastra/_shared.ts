import type { Agent } from "@mastra/core/agent";
import { Mastra } from "@mastra/core/mastra";
import { SpanType } from "@mastra/core/observability";
import type { AnyWorkflow } from "@mastra/core/workflows";
import {
  createMockModel,
  MastraLanguageModelV2Mock,
} from "@mastra/core/test-utils/llm-mock";
import { Observability, SamplingStrategyType } from "@mastra/observability";
import { MastraInstrumentor } from "@respan/instrumentation-mastra";
import { RespanTelemetry, propagateAttributes } from "@respan/tracing";
import { InMemorySpanExporter } from "@opentelemetry/sdk-trace-base";
import { writeFileSync } from "node:fs";
import dotenv from "dotenv";
import { existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

export const EXAMPLE_RUN_ID =
  process.env.RESPAN_EXAMPLE_RUN_ID ?? `mastra-ts-${Date.now()}`;

let rootEnvLoaded = false;
let respanLogsSuppressed = false;
const originalConsoleDebug = console.debug.bind(console);
const originalConsoleInfo = console.info.bind(console);
const originalConsoleLog = console.log.bind(console);

function suppressExampleRespanLogs(): void {
  if (respanLogsSuppressed || process.env.RESPAN_EXAMPLE_DEBUG === "true") {
    return;
  }

  console.debug = (...args: unknown[]) => {
    const firstArg = typeof args[0] === "string" ? args[0] : "";
    if (
      firstArg.startsWith("[Respan]") ||
      firstArg.startsWith("[Respan Debug]")
    ) {
      return;
    }
    originalConsoleDebug(...args);
  };

  console.info = (...args: unknown[]) => {
    const firstArg = typeof args[0] === "string" ? args[0] : "";
    if (firstArg.startsWith("[Respan]")) {
      return;
    }
    originalConsoleInfo(...args);
  };

  console.log = (...args: unknown[]) => {
    const firstArg = typeof args[0] === "string" ? args[0] : "";
    if (
      firstArg.startsWith("[Respan]") ||
      firstArg.startsWith("Respan tracing")
    ) {
      return;
    }
    originalConsoleLog(...args);
  };

  respanLogsSuppressed = true;
}

export function loadRootEnv(): void {
  if (rootEnvLoaded) {
    return;
  }

  const startDir = dirname(fileURLToPath(import.meta.url));
  let currentDir = startDir;

  for (let depth = 0; depth < 8; depth += 1) {
    const envPath = join(currentDir, ".env");
    if (existsSync(envPath)) {
      dotenv.config({ path: envPath, override: false, quiet: true });
      rootEnvLoaded = true;
      return;
    }
    const parentDir = dirname(currentDir);
    if (parentDir === currentDir) {
      break;
    }
    currentDir = parentDir;
  }

  dotenv.config({ override: false, quiet: true });
  rootEnvLoaded = true;
}

export function requireEnv(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(
      `${name} is required. Add it to respan-example-projects/.env.`,
    );
  }
  return value;
}

export function createDeterministicModel(text: string) {
  return createMockModel({ mockText: text });
}

export function createToolCallModel() {
  let callCount = 0;
  return new MastraLanguageModelV2Mock({
    provider: "respan-example",
    modelId: "deterministic-tool-model",
    doGenerate: async () => {
      callCount += 1;
      return {
        rawCall: { rawPrompt: null, rawSettings: {} },
        finishReason: callCount === 1 ? "tool-calls" : "stop",
        usage: { inputTokens: 10, outputTokens: 6, totalTokens: 16 },
        content:
          callCount === 1
            ? [
                {
                  type: "tool-call",
                  toolCallId: "call_weather_tokyo",
                  toolName: "getWeather",
                  input: JSON.stringify({ city: "Tokyo" }),
                },
              ]
            : [{ type: "text", text: "Tokyo is sunny and 72 F." }],
        warnings: [],
      };
    },
  });
}

export function createFailingModel() {
  const fail = async () => {
    throw new Error("Intentional deterministic provider failure");
  };
  return new MastraLanguageModelV2Mock({
    provider: "respan-example",
    modelId: "deterministic-failure-model",
    doGenerate: fail,
    doStream: fail,
  });
}

export function createRuntime<
  TAgents extends Record<string, Agent<any>>,
  TWorkflows extends Record<string, AnyWorkflow> = Record<string, AnyWorkflow>,
>(
  agents: TAgents,
  workflows?: TWorkflows,
): {
  mastra: Mastra<TAgents, TWorkflows>;
  respan: RespanTelemetry;
  observability: Observability;
  instrumentor: MastraInstrumentor;
} {
  loadRootEnv();
  suppressExampleRespanLogs();
  const instrumentor = new MastraInstrumentor();
  const exporting = process.env.RESPAN_EXPORT === "1";
  const captures: unknown[] = [];
  const localExporter = new InMemorySpanExporter();
  const respan = new RespanTelemetry({
    apiKey: exporting
      ? requireEnv("RESPAN_API_KEY")
      : "local-only-mastra-example",
    exporter: exporting ? undefined : localExporter,
    disableBatch: true,
    disabledInstrumentations: [
      "openAI",
      "anthropic",
      "azureOpenAI",
      "cohere",
      "bedrock",
      "googleVertexAI",
      "googleAIPlatform",
      "pinecone",
      "together",
      "langChain",
      "llamaIndex",
      "chromaDB",
      "qdrant",
    ],
    spanPostprocessCallback: (span) => {
      captures.push({
        name: span.name,
        traceId: span.spanContext().traceId,
        spanId: span.spanContext().spanId,
        parentSpanId: span.parentSpanContext?.spanId,
        attributes: span.attributes,
        status: span.status,
      });
      if (process.env.MASTRA_CAPTURE_PATH)
        writeFileSync(
          process.env.MASTRA_CAPTURE_PATH,
          JSON.stringify({ runId: EXAMPLE_RUN_ID, captures }, null, 2),
        );
    },
    baseURL: process.env.RESPAN_BASE_URL,
    appName: "mastra-typescript-examples",
    silenceInitializationMessage: true,
  });

  const observability = new Observability({
    configs: {
      default: {
        serviceName: "respan-mastra-typescript-examples",
        sampling: { type: SamplingStrategyType.ALWAYS },
        exporters: [instrumentor],
        // Native Mastra defaults bound arrays to 50 entries. These controlled
        // fidelity examples deliberately request larger native payloads.
        serializationOptions: {
          maxArrayLength: 100000,
          maxObjectKeys: 100000,
          maxDepth: 100,
          maxStringLength: 10000000,
        },
      },
    },
    sensitiveDataFilter: false,
  });
  const mastra = new Mastra<TAgents, TWorkflows>({
    agents,
    workflows,
    observability,
  });

  return { mastra, respan, instrumentor, observability };
}

export function getTraceWorkflowName(workflowName: string): string {
  return normalizeWorkflowName(workflowName).traceWorkflowName;
}

export async function runWithRespanWorkflow<T>(
  mastra: Mastra<any>,
  respan: RespanTelemetry,
  workflowName: string,
  fn: () => Promise<T>,
): Promise<T> {
  const { mastraWorkflowName, traceWorkflowName } =
    normalizeWorkflowName(workflowName);
  await respan.initialize();
  try {
    return await propagateAttributes(
      {
        custom_identifier: EXAMPLE_RUN_ID,
        trace_group_identifier: traceWorkflowName,
        metadata: {
          example: "mastra-typescript",
          run_id: EXAMPLE_RUN_ID,
          workflow_name: traceWorkflowName,
        },
      },
      () => respan.withWorkflow({ name: mastraWorkflowName }, fn),
    );
  } finally {
    try {
      await mastra.shutdown();
    } finally {
      await respan.shutdown();
    }
  }
}

function normalizeWorkflowName(workflowName: string): {
  mastraWorkflowName: string;
  traceWorkflowName: string;
} {
  const suffix = ".workflow";
  const mastraWorkflowName = workflowName.endsWith(suffix)
    ? workflowName.slice(0, -suffix.length)
    : workflowName;
  return {
    mastraWorkflowName,
    traceWorkflowName: `${mastraWorkflowName}${suffix}`,
  };
}
