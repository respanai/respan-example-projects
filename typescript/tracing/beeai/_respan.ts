import * as beeaiFramework from "beeai-framework";
import { BeeAIInstrumentor } from "@respan/instrumentation-beeai";
import { Respan } from "@respan/respan";
import { loadBeeAIExampleEnv, type BeeAIExampleEnv } from "./_env.js";

export const BEEAI_EXAMPLE_RUN_ID =
  process.env.RESPAN_EXAMPLE_RUN_ID ?? `beeai-ts-${Date.now()}`;

export interface BeeAIRespanRuntime {
  env: BeeAIExampleEnv;
  respan: Respan;
}

export async function createBeeAIRespanRuntime(): Promise<BeeAIRespanRuntime> {
  const env = loadBeeAIExampleEnv();
  const respan = new Respan({
    apiKey: env.respanApiKey,
    baseURL: env.respanBaseURL,
    appName: "beeai-typescript-examples",
    instrumentations: [
      new BeeAIInstrumentor({
        sdkModule: beeaiFramework,
      }),
    ],
    silenceInitializationMessage: true,
  });
  await respan.initialize();
  return { env, respan };
}

export async function runWithBeeAIWorkflow<T>(
  respan: Respan,
  workflowName: string,
  input: Record<string, unknown>,
  fn: () => Promise<T>,
): Promise<T> {
  return await respan.propagateAttributes(
    {
      custom_identifier: BEEAI_EXAMPLE_RUN_ID,
      trace_group_identifier: workflowName,
      metadata: {
        example: "beeai-typescript",
        run_id: BEEAI_EXAMPLE_RUN_ID,
        workflow_name: workflowName,
      },
    },
    async () =>
      await respan.withWorkflow(
        { name: workflowName, inputParameters: [input] },
        fn,
      ),
  );
}
