import {
  Agent,
  Graph,
  McpClient,
  Swarm,
  tool,
  type AgentResult,
  type ContentBlock,
  type ContentBlockData,
} from "@strands-agents/sdk";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StrandsAgentsInstrumentor } from "@respan/instrumentation-strands-agents";
import { Respan } from "@respan/respan";
import { OpenAIModel } from "@strands-agents/sdk/models/openai";
import {
  RespanTelemetry,
  PROPAGATED_ATTRIBUTES_KEY,
  INSTRUMENTATION_INFO,
  type InstrumentationName,
} from "@respan/tracing";
import { InMemorySpanExporter } from "@opentelemetry/sdk-trace-base";
import { context } from "@opentelemetry/api";
import { mkdirSync, writeFileSync } from "node:fs";
import dotenv from "dotenv";
import { existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { z } from "zod";

const DEFAULT_BASE_URL = "https://api.respan.ai/api";
const STRUCTURED_OUTPUT_TOOL_NAME = "strands_structured_output";

export const EXAMPLE_RUN_ID =
  process.env.RESPAN_EXAMPLE_RUN_ID ?? `strands-agents-ts-${Date.now()}`;

let rootEnvLoaded = false;
let respanLogsSuppressed = false;
const originalConsoleDebug = console.debug.bind(console);
const originalConsoleInfo = console.info.bind(console);
const originalConsoleLog = console.log.bind(console);

export type DemoMode =
  | "basic"
  | "tool"
  | "streaming"
  | "structured"
  | "graph-researcher"
  | "graph-writer"
  | "swarm-researcher"
  | "swarm-writer"
  | "mcp"
  | "error"
  | "large";

export interface DemoMcpEnvironment {
  client: McpClient;
  close: () => Promise<void>;
  server: McpServer;
}

export const cityBriefSchema = z.object({
  city: z.string(),
  score: z.number(),
  rationale: z.string(),
});

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

export async function runStrandsExample<T>(params: {
  appName: string;
  workflowName: string;
  fn: () => Promise<T>;
}): Promise<T> {
  const exportEnabled = process.env.RESPAN_EXAMPLE_EXPORT === "true";
  if (exportEnabled || process.env.STRANDS_EXAMPLE_PROVIDER === "live")
    loadRootEnv();
  suppressExampleRespanLogs();
  const plugin = new StrandsAgentsInstrumentor({
    traceContent: process.env.RESPAN_TRACE_CONTENT !== "false",
  });
  const localExporter = new InMemorySpanExporter();
  const respan = exportEnabled
    ? new Respan({
        apiKey: requireEnv("RESPAN_API_KEY"),
        baseURL: process.env.RESPAN_BASE_URL ?? DEFAULT_BASE_URL,
        appName: params.appName,
        instrumentations: [plugin],
        silenceInitializationMessage: true,
      })
    : new RespanTelemetry({
        apiKey: "controlled-local-capture",
        appName: params.appName,
        exporter: localExporter,
        disableBatch: true,
        disabledInstrumentations: Object.keys(
          INSTRUMENTATION_INFO,
        ) as InstrumentationName[],
        silenceInitializationMessage: true,
      });
  const previousMetricsExporter = process.env.OTEL_METRICS_EXPORTER;
  process.env.OTEL_METRICS_EXPORTER = "none";
  await respan.initialize();
  if (!exportEnabled) plugin.activate();
  const attrs = {
    custom_identifier: EXAMPLE_RUN_ID,
    thread_identifier: `strands-agents-ts-thread-${EXAMPLE_RUN_ID}`,
    trace_group_identifier: params.workflowName,
    metadata: {
      example: "strands-agents-typescript",
      run_id: EXAMPLE_RUN_ID,
      workflow_name: params.workflowName,
    },
  };
  try {
    const execute = async () =>
      await respan.withWorkflow({ name: params.workflowName }, params.fn);
    return await context.with(
      context.active().setValue(PROPAGATED_ATTRIBUTES_KEY, attrs),
      execute,
    );
  } finally {
    await respan.flush();
    if (!exportEnabled && process.env.RESPAN_EXAMPLE_CAPTURE_DIR) {
      mkdirSync(process.env.RESPAN_EXAMPLE_CAPTURE_DIR, { recursive: true });
      const spans = localExporter.getFinishedSpans().map((span) => ({
        name: span.name,
        attributes: span.attributes,
        events: span.events,
        status: span.status,
        spanContext: span.spanContext(),
        parentSpanContext: span.parentSpanContext,
      }));
      writeFileSync(
        join(
          process.env.RESPAN_EXAMPLE_CAPTURE_DIR,
          `${params.workflowName.replace(/[^a-zA-Z0-9]+/g, "-")}.json`,
        ),
        JSON.stringify({ runId: EXAMPLE_RUN_ID, spans }, null, 2),
      );
    }
    plugin.deactivate();
    await respan.shutdown();
    if (previousMetricsExporter === undefined)
      delete process.env.OTEL_METRICS_EXPORTER;
    else process.env.OTEL_METRICS_EXPORTER = previousMetricsExporter;
  }
}

/** Exercise the released provider's request mapper, SSE parser and agent loop. */
export function createNativeFixtureModel(mode: DemoMode): OpenAIModel {
  if (process.env.STRANDS_EXAMPLE_PROVIDER === "live" && mode !== "error") {
    loadRootEnv();
    return new OpenAIModel({
      api: "chat",
      apiKey: requireEnv("OPENAI_API_KEY"),
      modelId: process.env.STRANDS_EXAMPLE_MODEL ?? "gpt-4.1-nano",
    });
  }
  let calls = 0;
  return new OpenAIModel({
    api: "chat",
    apiKey: "controlled-fixture",
    modelId: "gpt-4.1-nano",
    clientConfig: {
      maxRetries: 0,
      fetch: async (_url, init) => {
        calls++;
        if (mode === "error")
          return new Response(
            JSON.stringify({
              error: {
                message: "Controlled Strands provider error",
                type: "fixture_error",
              },
            }),
            { status: 400, headers: { "content-type": "application/json" } },
          );
        const body = JSON.parse(String(init?.body));
        const hasResult = body.messages.some(
          (message: { role: string }) => message.role === "tool",
        );
        const tools = body.tools ?? [];
        let selected: string | undefined;
        let args: Record<string, unknown> = {};
        if (
          tools.some(
            (item: any) => item.function.name === STRUCTURED_OUTPUT_TOOL_NAME,
          )
        ) {
          selected = STRUCTURED_OUTPUT_TOOL_NAME;
          args =
            mode === "swarm-researcher"
              ? {
                  agentId: "swarm-writer",
                  message: "Write a Lisbon brief.",
                  context: { city: "Lisbon" },
                }
              : mode === "swarm-writer"
                ? {
                    message: "Lisbon brief: trams, riverfront walks, tilework.",
                  }
                : {
                    city: "Tokyo",
                    score: 92,
                    rationale: "Reliable transit and compact neighborhoods.",
                  };
        } else if (!hasResult && mode === "tool") {
          selected = "get_weather";
          args = { city: "Tokyo" };
        } else if (!hasResult && mode === "mcp") {
          selected = "summarize_city";
          args = { city: "Lisbon" };
        }
        const text =
          mode === "large"
            ? JSON.stringify({
                vector: Array.from({ length: 5001 }, (_, i) => i / 5001),
                zero: 0,
                falsy: false,
                empty: "",
                nothing: null,
              })
            : mode === "streaming"
              ? "Streaming native Strands provider output through Respan."
              : mode === "graph-researcher"
                ? "Kyoto research: temples, rail access, gardens."
                : mode === "graph-writer"
                  ? "Kyoto brief: temples, reliable rail, gardens."
                  : mode === "tool"
                    ? "The Tokyo forecast is sunny with light wind."
                    : mode === "mcp"
                      ? "Lisbon MCP summary received."
                      : "Hello from Strands Agents TypeScript instrumentation.";
        const delta = selected
          ? {
              role: "assistant",
              tool_calls: [
                {
                  index: 0,
                  id: `native-${mode}-${calls}`,
                  type: "function",
                  function: { name: selected, arguments: JSON.stringify(args) },
                },
              ],
            }
          : { role: "assistant", content: text };
        const chunks = [
          { choices: [{ index: 0, delta, finish_reason: null }] },
          {
            choices: [
              {
                index: 0,
                delta: {},
                finish_reason: selected ? "tool_calls" : "stop",
              },
            ],
          },
          {
            choices: [],
            usage: {
              prompt_tokens: 20,
              completion_tokens: 8,
              total_tokens: 28,
            },
          },
        ];
        const payload =
          chunks
            .map(
              (chunk) =>
                `data: ${JSON.stringify({ id: "controlled", object: "chat.completion.chunk", created: 1, model: "gpt-4.1-nano", ...chunk })}\n\n`,
            )
            .join("") + "data: [DONE]\n\n";
        return new Response(payload, {
          headers: { "content-type": "text/event-stream" },
        });
      },
    },
  });
}

export function createAgent(
  mode: DemoMode,
  options: Partial<ConstructorParameters<typeof Agent>[0]> = {},
): Agent {
  return new Agent({
    id: options.id ?? mode,
    name: options.name ?? readableAgentName(mode),
    description:
      options.description ?? `Native provider ${mode} Strands demo agent`,
    model: options.model ?? createNativeFixtureModel(mode),
    systemPrompt:
      options.systemPrompt ??
      "Return concise demo responses for Respan tracing examples.",
    printer: false,
    tools: options.tools ?? (mode === "tool" ? [getWeatherTool] : []),
    structuredOutputSchema: options.structuredOutputSchema,
    traceAttributes: options.traceAttributes,
  });
}

export function createGraph(): Graph {
  const researcher = createAgent("graph-researcher", {
    id: "graph-researcher",
    name: "Graph Researcher",
  });
  const writer = createAgent("graph-writer", {
    id: "graph-writer",
    name: "Graph Writer",
  });

  return new Graph({
    id: "strands-demo-graph",
    nodes: [researcher, writer],
    edges: [["graph-researcher", "graph-writer"]],
    maxSteps: 4,
  });
}

export function createSwarm(): Swarm {
  const researcher = createAgent("swarm-researcher", {
    id: "swarm-researcher",
    name: "Swarm Researcher",
    description: "Collects city notes and hands off to the writer.",
  });
  const writer = createAgent("swarm-writer", {
    id: "swarm-writer",
    name: "Swarm Writer",
    description: "Writes the final city brief.",
  });

  return new Swarm({
    id: "strands-demo-swarm",
    nodes: [researcher, writer],
    start: "swarm-researcher",
    maxSteps: 3,
  });
}

export async function createDemoMcpEnvironment(): Promise<DemoMcpEnvironment> {
  const server = new McpServer({
    name: "respan-strands-demo-mcp-server",
    version: "1.0.0",
  });

  server.registerTool(
    "summarize_city",
    {
      title: "Summarize city",
      description: "Return a concise city summary for Strands MCP examples.",
      inputSchema: {
        city: z.string().describe("City name"),
      },
    },
    async ({ city }) => ({
      content: [
        {
          type: "text",
          text: `${city} has river walks, compact neighborhoods, and strong public spaces.`,
        },
      ],
      structuredContent: {
        city,
        summary: `${city} has river walks and compact neighborhoods.`,
      },
    }),
  );

  const [clientTransport, serverTransport] =
    InMemoryTransport.createLinkedPair();
  await server.connect(serverTransport);

  const client = new McpClient({
    transport: clientTransport,
    applicationName: "respan-strands-mcp-client",
    applicationVersion: "1.0.0",
  });
  await client.connect();

  return {
    client,
    server,
    close: async () => {
      await client.disconnect();
      await server.close();
    },
  };
}

export function resultText(result: AgentResult): string {
  return result.toString();
}

export function multiAgentText(result: {
  content: readonly ContentBlock[];
}): string {
  return result.content.map(contentBlockText).filter(Boolean).join(" ");
}

export function logExampleResult(
  workflowName: string,
  details: Record<string, unknown>,
): void {
  console.log(
    JSON.stringify(
      { workflowName, runId: EXAMPLE_RUN_ID, ...details },
      null,
      2,
    ),
  );
}

const getWeatherTool = tool({
  name: "get_weather",
  description: "Return a deterministic weather forecast.",
  inputSchema: z.object({
    city: z.string().describe("City name"),
  }),
  callback: ({ city }) => ({
    city,
    forecast: city === "Tokyo" ? "sunny with light wind" : "clear",
  }),
});

function readableAgentName(mode: DemoMode): string {
  return mode
    .split("-")
    .map((part) => part[0].toUpperCase() + part.slice(1))
    .join(" ");
}

function contentBlockText(block: ContentBlock): string {
  const data = block.toJSON() as ContentBlockData;
  if ("text" in data) {
    return data.text;
  }
  if ("toolResult" in data) {
    return data.toolResult.content
      .map((item) => JSON.stringify(item))
      .join(" ");
  }
  if ("toolUse" in data) {
    return `${data.toolUse.name}(${JSON.stringify(data.toolUse.input)})`;
  }
  return "";
}
