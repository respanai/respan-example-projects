import Anthropic from "@anthropic-ai/sdk";
import { AnthropicInstrumentor } from "@respan/instrumentation-anthropic";
import { Respan } from "@respan/respan";
import { context, trace } from "@opentelemetry/api";
import { ATTR_GEN_AI_TOOL_CALL_ID } from "@opentelemetry/semantic-conventions/incubating";
import { SpanAttributes } from "@traceloop/ai-semantic-conventions";
import { FIXTURE_MODEL, fixtureFetch } from "./_fixture.js";
import { localCollector } from "./_collector.js";
export const RUN_ID =
  process.env.RESPAN_EXAMPLE_RUN_ID || `typescript-anthropic-${Date.now()}`;
export const MODEL =
  process.env.RESPAN_ANTHROPIC_MODEL?.trim() || FIXTURE_MODEL;
export const LIVE = process.env.RESPAN_ANTHROPIC_LIVE === "1";
const EXPORT = process.env.RESPAN_EXAMPLE_EXPORT === "1";
export async function createRuntime() {
  if (LIVE && !process.env.RESPAN_ANTHROPIC_MODEL?.trim())
    throw Error("Live mode requires an explicit RESPAN_ANTHROPIC_MODEL.");
  if (LIVE && !process.env.ANTHROPIC_API_KEY)
    throw Error("Live mode requires ANTHROPIC_API_KEY.");
  if (EXPORT && !process.env.RESPAN_API_KEY)
    throw Error("Explicit export requires RESPAN_API_KEY.");
  const override = process.env.RESPAN_EXAMPLE_COLLECTOR_URL;
  const collector = !EXPORT && !override ? await localCollector() : undefined;
  const client = new Anthropic({
    apiKey: LIVE ? process.env.ANTHROPIC_API_KEY : "fixture-provider",
    maxRetries: 0,
    ...(LIVE ? {} : { fetch: fixtureFetch }),
  });
  const respan = new Respan({
    apiKey: EXPORT ? process.env.RESPAN_API_KEY : "local-fixture",
    baseURL: override ?? collector?.url ?? process.env.RESPAN_BASE_URL,
    appName: "typescript-anthropic-examples",
    instrumentations: [
      new AnthropicInstrumentor({ sdkModule: { default: Anthropic } }),
    ],
    silenceInitializationMessage: true,
  });
  return {
    client,
    respan,
    async close(caseId: string) {
      await respan.shutdown();
      await collector?.close(caseId, RUN_ID);
    },
  };
}
export async function runCase<T>(
  respan: Respan,
  caseId: string,
  fn: () => Promise<T>,
): Promise<T> {
  await respan.initialize();
  return await respan.propagateAttributes(
    {
      custom_identifier: RUN_ID,
      trace_group_identifier: `anthropic_${caseId}`,
      metadata: {
        example: "typescript-anthropic-direct",
        run_id: RUN_ID,
        case_id: caseId,
      },
    },
    () => respan.withWorkflow({ name: `anthropic_${caseId}` }, fn),
  );
}
export function log(caseId: string, details: Record<string, unknown>) {
  console.log(JSON.stringify({ caseId, runId: RUN_ID, ...details }));
}
export function toolInput(name: string, id: string, args: unknown) {
  const span = trace.getSpan(context.active());
  span?.setAttribute(ATTR_GEN_AI_TOOL_CALL_ID, id);
  span?.setAttribute(
    SpanAttributes.TRACELOOP_ENTITY_INPUT,
    JSON.stringify({ name, arguments: args }),
  );
}
