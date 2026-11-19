import assert from "node:assert/strict";
import fs from "node:fs/promises";
import fsSync from "node:fs";
import path from "node:path";
import os from "node:os";
import { fileURLToPath } from "node:url";
import dotenv from "dotenv";
import {
  Codex,
  type CodexOptions,
  type ThreadOptions,
} from "@openai/codex-sdk";
import * as CodexSDKModule from "@openai/codex-sdk";
import {
  RespanTelemetry as Respan,
  propagateAttributes,
} from "@respan/tracing";
import {
  CodexSDKInstrumentor,
  type CodexSDKInstrumentorOptions,
} from "@respan/instrumentation-codex-sdk";
import type { ReadableSpan, SpanExporter } from "@opentelemetry/sdk-trace-base";
export { assert };
export const EXAMPLE_DIR = path.dirname(fileURLToPath(import.meta.url));
export const RUN_ID =
  process.env.RESPAN_EXAMPLE_RUN_ID || `codex-sdk-ts-${Date.now()}`;
export const LIVE = process.env.CODEX_EXAMPLE_LIVE === "1";
const EXPORT = process.env.RESPAN_EXAMPLE_EXPORT === "1";
if (LIVE || EXPORT)
  dotenv.config({
    path: path.resolve(EXAMPLE_DIR, "../../../.env"),
    override: false,
  });
const nativeManifest = JSON.parse(
  fsSync.readFileSync(
    path.resolve(
      path.dirname(fileURLToPath(import.meta.resolve("@openai/codex-sdk"))),
      "../package.json",
    ),
    "utf8",
  ),
);
export const NATIVE_VERSION: string = nativeManifest.version;
export const CURRENT_FEATURES = Number(NATIVE_VERSION.split(".")[1]) >= 162;
export const captured: Array<{
  id: string;
  traceId: string;
  parentId?: string;
  name: string;
  attrs: Record<string, unknown>;
  status: unknown;
}> = [];
const collector: SpanExporter = {
  export(spans, callback) {
    for (const span of spans)
      captured.push({
        id: span.spanContext().spanId,
        traceId: span.spanContext().traceId,
        parentId: span.parentSpanContext?.spanId,
        name: span.name,
        attrs: { ...span.attributes },
        status: span.status,
      });
    callback({ code: 0 });
  },
  shutdown: async () => {},
};
const owners = new WeakMap<Respan, CodexSDKInstrumentor>();
export function createRespan(
  appName = "codex-sdk-typescript-examples",
  options: CodexSDKInstrumentorOptions = {},
): Respan {
  if (EXPORT && !process.env.RESPAN_API_KEY)
    throw new Error("Set RESPAN_API_KEY for explicit trace export.");
  const owner = new CodexSDKInstrumentor({
    sdkModule: CodexSDKModule,
    agentName: "controlled-codex-agent",
    ...options,
  });
  const respan = new Respan({
    appName,
    apiKey: EXPORT ? process.env.RESPAN_API_KEY : "",
    baseURL: process.env.RESPAN_BASE_URL,
    ...(!EXPORT ? { exporter: collector } : {}),
    traceContent: options.traceContent !== false,
    silenceInitializationMessage: true,
    disableBatch: true,
    disabledInstrumentations: [
      "http",
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
  });
  owners.set(respan, owner);
  return respan;
}
export function ownerFor(respan: Respan): CodexSDKInstrumentor {
  return owners.get(respan)!;
}
export function createCodex(
  options: {
    scenario?: string;
    codexPathOverride?: string;
    requestPath?: string;
    codexOptions?: CodexOptions;
  } = {},
): Codex {
  if (LIVE) {
    const apiKey = process.env.CODEX_API_KEY || process.env.OPENAI_API_KEY;
    if (!apiKey)
      throw new Error(
        "Set CODEX_API_KEY or OPENAI_API_KEY for explicit live inference.",
      );
    return new Codex({
      apiKey,
      baseUrl: process.env.CODEX_BASE_URL || process.env.OPENAI_BASE_URL,
      ...options.codexOptions,
      ...(options.codexPathOverride
        ? { codexPathOverride: options.codexPathOverride }
        : {}),
    });
  }
  return new Codex({
    ...options.codexOptions,
    codexPathOverride:
      options.codexPathOverride ||
      path.join(EXAMPLE_DIR, "_fixtures/controlled-codex.cjs"),
    env: {
      PATH: process.env.PATH || "",
      CODEX_FIXTURE_SCENARIO: options.scenario || "all",
      CODEX_FIXTURE_CACHE_WRITE: CURRENT_FEATURES ? "1" : "0",
      ...(options.requestPath
        ? { CODEX_FIXTURE_REQUEST_PATH: options.requestPath }
        : {}),
    },
  });
}
export function codexThreadOptions(
  overrides: ThreadOptions = {},
): ThreadOptions {
  return {
    workingDirectory: EXAMPLE_DIR,
    skipGitRepoCheck: true,
    sandboxMode: "read-only",
    approvalPolicy: "never",
    networkAccessEnabled: false,
    webSearchMode: "disabled",
    ...(process.env.CODEX_MODEL || !LIVE
      ? { model: process.env.CODEX_MODEL || "controlled-model" }
      : {}),
    ...overrides,
  };
}
export async function runWithCodexWorkflow<T>(
  respan: Respan,
  name: string,
  fn: () => Promise<T>,
): Promise<T> {
  await respan.initialize();
  await owners.get(respan)!.activate();
  if (EXPORT)
    respan.addProcessor({
      name: "controlled-capture",
      exporter: collector,
      filter: () => true,
      disableBatch: true,
    });
  return propagateAttributes(
    {
      trace_group_identifier: name,
      custom_identifier: RUN_ID,
      metadata: {
        example: "typescript-codex-sdk",
        run_id: RUN_ID,
        workflow_name: name,
        native_version: NATIVE_VERSION,
        controlled_transport: !LIVE,
      },
    },
    () => respan.withWorkflow({ name }, fn),
  );
}
export async function shutdownRespan(respan: Respan): Promise<void> {
  owners.get(respan)!.deactivate();
  await respan.shutdown();
  if (process.env.RESPAN_EXAMPLE_CAPTURE_PATH)
    await fs.writeFile(
      process.env.RESPAN_EXAMPLE_CAPTURE_PATH,
      JSON.stringify(captured, null, 2),
    );
}
export function logExampleResult(
  name: string,
  details: Record<string, unknown>,
): void {
  console.log(
    JSON.stringify({
      workflowName: name,
      runId: RUN_ID,
      nativeVersion: NATIVE_VERSION,
      controlledTransport: !LIVE,
      spanCount: captured.length,
      ...details,
    }),
  );
}
export async function createScratchWorkspace(name: string): Promise<string> {
  return fs.mkdtemp(path.join(os.tmpdir(), `respan-codex-${name}-`));
}
export async function createDemoImage(): Promise<string> {
  const dir = await createScratchWorkspace("image");
  const file = path.join(dir, "controlled.png");
  await fs.writeFile(
    file,
    Buffer.from(
      "iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAYAAABytg0kAAAAGElEQVR4nGP8z8DwnwEJMDIwMDAwAADpVgQDAZQcFwAAAABJRU5ErkJggg==",
      "base64",
    ),
  );
  return file;
}
export function verifyCaptured(): void {
  for (const span of captured) {
    assert.ok(
      !Object.keys(span.attrs).some((k) => k.startsWith("respan.internal.")),
    );
    assert.notEqual(span.attrs["respan.entity.log_type"], "chat");
    assert.equal(span.attrs["gen_ai.tool.call.id"], undefined);
  }
}
