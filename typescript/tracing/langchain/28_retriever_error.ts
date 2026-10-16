import { BaseRetriever } from "@langchain/core/retrievers";

import { initRespan, shutdown, tracingConfig } from "./_shared";

class FailingRetriever extends BaseRetriever {
  lc_namespace = ["respan", "examples", "langchain"];

  async _getRelevantDocuments(query: string): Promise<never> {
    throw new Error(`retriever failed for ${query}`);
  }
}

export async function retrieverError(): Promise<void> {
  const runtime = await initRespan("typescript-langchain-retriever-error");
  const retriever = new FailingRetriever();

  try {
    await retriever.invoke(
      "missing",
      tracingConfig(runtime, "retriever_error"),
    );
  } catch (error) {
    console.log(`caught expected error: ${(error as Error).message}`);
  } finally {
    await shutdown(runtime);
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  await retrieverError();
}
