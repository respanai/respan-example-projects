import { writeFile } from "node:fs/promises";
import { OpenAI, OpenAIEmbedding, OpenAIResponses } from "@llamaindex/openai";
import { Respan } from "@respan/respan";
import {
  LlamaIndexInstrumentor,
  type LlamaIndexInstrumentorOptions,
} from "@respan/instrumentation-llama-index";
import { startFixture } from "./_fixture.js";

export async function runNamedWorkflow<T>(
  workflowName: string,
  fn: (clients: {
    llm: OpenAI;
    embedding: OpenAIEmbedding;
    responses: OpenAIResponses;
    respan: Respan;
  }) => Promise<T>,
  options: LlamaIndexInstrumentorOptions = {},
): Promise<T> {
  const fixture = await startFixture();
  const live = process.env.LLAMA_INDEX_LIVE === "true";
  const exporting = process.env.RESPAN_EXPORT === "true";
  if (live && (!process.env.OPENAI_API_KEY || !process.env.LLAMA_INDEX_MODEL))
    throw new Error(
      "Set OPENAI_API_KEY and LLAMA_INDEX_MODEL for explicit live provider calls.",
    );
  if (exporting && !process.env.RESPAN_API_KEY)
    throw new Error("Set RESPAN_API_KEY for explicit hosted export.");
  const clientOptions = {
    apiKey: live ? process.env.OPENAI_API_KEY : "local-fixture",
    baseURL: live ? process.env.OPENAI_BASE_URL : `${fixture.baseURL}/v1`,
    maxRetries: 0,
  };
  const respan = new Respan({
    apiKey: exporting ? process.env.RESPAN_API_KEY : "local-fixture",
    baseURL: exporting ? process.env.RESPAN_BASE_URL : fixture.baseURL,
    appName: workflowName,
    traceContent: true,
    silenceInitializationMessage: true,
    instrumentations: [
      new LlamaIndexInstrumentor({ workflowName, ...options }),
    ],
  });
  try {
    await respan.initialize();
    const llm = new OpenAI({
      ...clientOptions,
      model: (process.env.LLAMA_INDEX_MODEL ?? "gpt-4o-mini") as any,
      additionalChatOptions: { stream_options: { include_usage: true } },
    });
    const embedding = new OpenAIEmbedding({
      ...clientOptions,
      model: (process.env.LLAMA_INDEX_EMBEDDING_MODEL ??
        "text-embedding-3-small") as any,
    });
    const responses = new OpenAIResponses({
      ...clientOptions,
      model: (process.env.LLAMA_INDEX_MODEL ?? "gpt-4o-mini") as any,
    });

    const runId =
      process.env.RESPAN_EXAMPLE_RUN_ID ?? `${workflowName}-${Date.now()}`;
    return await respan.propagateAttributes(
      {
        custom_identifier: runId,
        trace_group_identifier: runId,
        metadata: {
          example_set: "typescript/tracing/llama-index",
          run_id: runId,
        },
      },
      () =>
        respan.withWorkflow({ name: workflowName }, () =>
          fn({ llm, embedding, responses, respan }),
        ),
    );
  } finally {
    await respan.shutdown();
    if (process.env.RESPAN_CAPTURE_PATH)
      await writeFile(
        process.env.RESPAN_CAPTURE_PATH,
        JSON.stringify(fixture.captured, null, 2),
      );
    console.log(
      JSON.stringify({
        workflow: workflowName,
        collectedBatches: fixture.captured.length,
      }),
    );
    await fixture.close();
  }
}
