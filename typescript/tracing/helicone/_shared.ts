import * as HeliconeHelpers from "@helicone/helpers";
import { HeliconeManualLogger } from "@helicone/helpers";
import { HeliconeInstrumentor } from "@respan/instrumentation-helicone";
import { Respan } from "@respan/respan";
import dotenv from "dotenv";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  startMockHeliconeServer,
  type MockHeliconeServer,
} from "./_mock_server.js";

const exampleDir = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(exampleDir, "../../..");
dotenv.config({
  path: path.join(repoRoot, ".env"),
  override: false,
  quiet: true,
});

export const RUN_ID =
  process.env.RESPAN_EXAMPLE_RUN_ID ?? `helicone-ts-${Date.now()}`;

export interface HeliconeExampleRuntime {
  respan: Respan;
  logger: HeliconeManualLogger;
  mock: MockHeliconeServer;
}

export interface HeliconeExampleRuntimeOptions {
  traceContent?: boolean;
  loggerHeaders?: Record<string, string>;
}

export async function createRuntime(
  options: HeliconeExampleRuntimeOptions = {},
): Promise<HeliconeExampleRuntime> {
  const apiKey = process.env.RESPAN_API_KEY;
  if (!apiKey) {
    throw new Error(
      "Set RESPAN_API_KEY in the respan-example-projects repo root .env file.",
    );
  }

  const mock = await startMockHeliconeServer();
  const respan = new Respan({
    apiKey,
    baseURL: process.env.RESPAN_BASE_URL,
    appName: "helicone-typescript-examples",
    traceContent: true,
    silenceInitializationMessage: true,
    instrumentations: [
      new HeliconeInstrumentor({
        sdkModule: HeliconeHelpers,
        traceContent: options.traceContent,
      }),
    ],
  });

  try {
    await respan.initialize();
  } catch (error) {
    await mock.close();
    throw error;
  }

  return {
    respan,
    logger: new HeliconeManualLogger({
      // The mock only requires a non-empty value. Derive it locally so the
      // example contains and reads no Helicone credential.
      apiKey: new URL(mock.baseUrl).host,
      loggingEndpoint: mock.baseUrl,
      headers: options.loggerHeaders,
    }),
    mock,
  };
}

export async function runWorkflow<T>(
  runtime: HeliconeExampleRuntime,
  workflowName: string,
  fn: () => Promise<T>,
): Promise<T> {
  return await runtime.respan.propagateAttributes(
    {
      custom_identifier: RUN_ID,
      trace_group_identifier: workflowName,
      metadata: {
        example_set: "typescript/tracing/helicone",
        run_id: RUN_ID,
        example_run_id: RUN_ID,
        workflow_name: workflowName,
      },
    },
    () => runtime.respan.withWorkflow(
      {
        name: workflowName,
        associationProperties: {
          example_set: "typescript/tracing/helicone",
          library: "@helicone/helpers",
          language: "typescript",
        },
      },
      fn,
    ),
  );
}

export async function shutdownRuntime(runtime: HeliconeExampleRuntime): Promise<void> {
  try {
    await runtime.respan.shutdown();
  } finally {
    await runtime.mock.close();
  }
}

export function logResult(
  workflowName: string,
  details: Record<string, unknown>,
): void {
  console.log(JSON.stringify({
    workflowName,
    runId: RUN_ID,
    ...details,
  }, null, 2));
}

export function jsonLineStream(values: unknown[]): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder();
  return new ReadableStream<Uint8Array>({
    start(controller) {
      for (const value of values) {
        controller.enqueue(encoder.encode(`${JSON.stringify(value)}\n`));
      }
      controller.close();
    },
  });
}

export interface HeliconeCompatibleStream<T> extends AsyncIterable<T> {
  tee(): [HeliconeCompatibleStream<T>, HeliconeCompatibleStream<T>];
  toReadableStream(): ReadableStream<T>;
}

export function heliconeValueStream<T>(values: T[]): HeliconeCompatibleStream<T> {
  const create = (): HeliconeCompatibleStream<T> => ({
    async *[Symbol.asyncIterator]() {
      for (const value of values) yield value;
    },
    tee() {
      return [create(), create()];
    },
    toReadableStream() {
      return new ReadableStream<T>({
        start(controller) {
          for (const value of values) controller.enqueue(value);
          controller.close();
        },
      });
    },
  });
  return create();
}
