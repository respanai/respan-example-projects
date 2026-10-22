import {
  initRespan,
  shutdown,
  StaticRetriever,
  tracingConfig,
} from "./_shared";

export async function retrieverInvoke(): Promise<void> {
  const runtime = await initRespan("typescript-langchain-retriever-invoke");
  const retriever = new StaticRetriever();

  try {
    const documents = await retriever.invoke(
      "callback tracing",
      tracingConfig(runtime, "retriever_invoke"),
    );
    console.log(documents.map((doc) => doc.pageContent).join(" | "));
  } finally {
    await shutdown(runtime);
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  await retrieverInvoke();
}
