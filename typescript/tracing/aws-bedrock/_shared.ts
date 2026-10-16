import {
  BedrockRuntimeClient,
  ConverseCommand,
  ConverseStreamCommand,
  InvokeModelCommand,
  InvokeModelWithResponseStreamCommand,
} from "@aws-sdk/client-bedrock-runtime";
import * as BedrockRuntimeModule from "@aws-sdk/client-bedrock-runtime";
import { AWSBedrockInstrumentor } from "@respan/instrumentation-aws-bedrock";
import { Respan } from "@respan/respan";
import { RespanTelemetry, propagateAttributes } from "@respan/tracing";
import dotenv from "dotenv";
import { fixtureHandler } from "./_fixture.js";
import { writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const exampleDir = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(exampleDir, "../../..");
if (
  process.env.RESPAN_EXAMPLE_EXPORT === "1" ||
  process.env.AWS_BEDROCK_EXAMPLE_MODE === "live"
)
  dotenv.config({ path: path.join(repoRoot, ".env") });

export const RUN_ID =
  process.env.RESPAN_EXAMPLE_RUN_ID || `aws-bedrock-ts-${Date.now()}`;
export const DEFAULT_CONVERSE_MODEL =
  process.env.AWS_BEDROCK_MODEL_ID || "anthropic.claude-3-haiku-20240307-v1:0";
export const DEFAULT_INVOKE_MODEL =
  process.env.AWS_BEDROCK_INVOKE_MODEL_ID || DEFAULT_CONVERSE_MODEL;

function envValue(name: string): string | undefined {
  const direct = process.env[name];
  if (direct && direct.trim()) return direct.trim();
  const spaced = process.env[`${name} `];
  if (spaced && spaced.trim()) return spaced.trim();
  return undefined;
}

export function exampleMode(): "live" | "fixture" {
  return process.env.AWS_BEDROCK_EXAMPLE_MODE === "live" ? "live" : "fixture";
}
const captured: Record<string, unknown>[] = [];

export type ExampleTracing = Pick<
  Respan,
  "initialize" | "withWorkflow" | "propagateAttributes" | "shutdown"
>;
export function createRespan(
  appName = "aws-bedrock-typescript-examples",
): ExampleTracing {
  const exporting = process.env.RESPAN_EXAMPLE_EXPORT === "1";
  const apiKey = exporting ? envValue("RESPAN_API_KEY") : undefined;
  if (exporting && !apiKey)
    throw new Error("RESPAN_EXAMPLE_EXPORT=1 requires RESPAN_API_KEY.");
  const instrumentor = new AWSBedrockInstrumentor({
    sdkModule: BedrockRuntimeModule,
    traceContent: process.env.AWS_BEDROCK_TRACE_CONTENT !== "false",
  });
  const localExporter: NonNullable<
    ConstructorParameters<typeof RespanTelemetry>[0]["exporter"]
  > = {
    export(spans, callback) {
      for (const span of spans)
        captured.push({
          name: span.name,
          traceId: span.spanContext().traceId,
          spanId: span.spanContext().spanId,
          parentSpanId: span.parentSpanContext?.spanId,
          attributes: span.attributes,
          status: span.status,
        });
      callback({ code: 0 });
    },
    async shutdown() {},
  };
  if (exporting) {
    const facade = new Respan({
      apiKey,
      baseURL: envValue("RESPAN_BASE_URL"),
      appName,
      instrumentations: [instrumentor],
      silenceInitializationMessage: true,
    });
    let attached = false;
    return {
      async initialize() {
        await facade.initialize();
        if (!attached && process.env.RESPAN_EXAMPLE_CAPTURE) {
          facade.addProcessor({
            name: "example-capture",
            exporter: localExporter,
            filter: () => true,
          });
          attached = true;
        }
      },
      withWorkflow: facade.withWorkflow,
      propagateAttributes: facade.propagateAttributes.bind(facade),
      shutdown: facade.shutdown.bind(facade),
    };
  }
  const telemetry = new RespanTelemetry({
    apiKey: "local-fixture-no-export",
    appName,
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
    exporter: localExporter,
    silenceInitializationMessage: true,
  });
  return {
    async initialize() {
      await telemetry.initialize();
      await instrumentor.activate();
    },
    withWorkflow: telemetry.withWorkflow,
    propagateAttributes,
    async shutdown() {
      instrumentor.deactivate();
      await telemetry.shutdown();
    },
  };
}

export function createBedrockClient(): BedrockRuntimeClient {
  return new BedrockRuntimeClient({
    region:
      envValue("AWS_REGION") || envValue("AWS_DEFAULT_REGION") || "us-east-1",
    ...(exampleMode() === "fixture"
      ? {
          credentials: { accessKeyId: "fixture", secretAccessKey: "fixture" },
          maxAttempts: 1,
          requestHandler: fixtureHandler,
        }
      : {}),
  });
}

export async function runWithBedrockWorkflow<T>(
  respan: ExampleTracing,
  workflowName: string,
  fn: () => Promise<T>,
): Promise<T> {
  await respan.initialize();
  return await respan.propagateAttributes(
    {
      trace_group_identifier: workflowName,
      custom_identifier: RUN_ID,
      metadata: {
        example: "typescript-aws-bedrock",
        run_id: RUN_ID,
        workflow_name: workflowName,
        aws_bedrock_example_mode: exampleMode(),
      },
    },
    async () => await respan.withWorkflow({ name: workflowName }, fn),
  );
}

export async function shutdownRespan(respan: ExampleTracing): Promise<void> {
  await respan.shutdown();
  const output = process.env.RESPAN_EXAMPLE_CAPTURE;
  if (output)
    await writeFile(
      output.replace("{pid}", String(process.pid)),
      JSON.stringify(
        { runId: RUN_ID, mode: exampleMode(), spans: captured },
        null,
        2,
      ),
    );
}

export function logExampleResult(
  workflowName: string,
  details: Record<string, unknown>,
): void {
  console.log(
    JSON.stringify(
      { workflowName, runId: RUN_ID, mode: exampleMode(), ...details },
      null,
      2,
    ),
  );
}

export async function withTimeout<T>(
  promise: Promise<T>,
  label: string,
): Promise<T> {
  let timeout: NodeJS.Timeout | undefined;
  const timeoutMs = Number.parseInt(
    process.env.AWS_BEDROCK_EXAMPLE_TIMEOUT_MS || "60000",
    10,
  );
  const timeoutPromise = new Promise<never>((_, reject) => {
    timeout = setTimeout(
      () => reject(new Error(`${label} timed out after ${timeoutMs}ms`)),
      timeoutMs,
    );
  });
  try {
    return await Promise.race([promise, timeoutPromise]);
  } finally {
    if (timeout) clearTimeout(timeout);
  }
}

export function textFromConverseResponse(response: any): string {
  const content = response?.output?.message?.content;
  if (!Array.isArray(content)) return "";
  return content
    .map((block) => (typeof block?.text === "string" ? block.text : ""))
    .filter(Boolean)
    .join("\n");
}

export function decodeBody(body: unknown): string {
  if (body instanceof Uint8Array) {
    return new TextDecoder().decode(body);
  }
  if (typeof body === "string") {
    return body;
  }
  return JSON.stringify(body ?? null);
}

export async function collectConverseStreamText(
  stream: AsyncIterable<any> | undefined,
): Promise<string> {
  const parts: string[] = [];
  if (!stream) throw new Error("Native Bedrock SDK returned no stream.");
  for await (const event of stream) {
    const text = event?.contentBlockDelta?.delta?.text;
    if (typeof text === "string") parts.push(text);
  }
  return parts.join("");
}

export async function collectInvokeStreamText(
  stream: AsyncIterable<any> | undefined,
): Promise<string> {
  const parts: string[] = [];
  if (!stream) throw new Error("Native Bedrock SDK returned no stream.");
  for await (const event of stream) {
    const bytes = event?.chunk?.bytes;
    if (!(bytes instanceof Uint8Array)) continue;
    const payload = JSON.parse(new TextDecoder().decode(bytes));
    const text =
      payload?.delta?.text ??
      payload?.completion ??
      payload?.generation ??
      payload?.outputText;
    if (typeof text === "string") parts.push(text);
  }
  return parts.join("");
}
