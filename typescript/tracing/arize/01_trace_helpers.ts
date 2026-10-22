import {
  context,
  setAttributes,
  setMetadata,
  setPromptTemplate,
  setSession,
  setTags,
  setUser,
  traceAgent,
  traceChain,
  traceTool,
} from "@arizeai/phoenix-otel";
import {
  createRespan,
  finishRespan,
  logExampleResult,
  runWithArizeWorkflow,
  RUN_ID,
} from "./_shared.js";

const searchKnowledgeBase = traceTool(
  async ({ query }: { query: string }) => [
    {
      id: "doc-routing",
      title: "Trace routing",
      content: `Route spans for ${query}`,
    },
    {
      id: "doc-context",
      title: "Context",
      content: "Propagate session, user, tags, and metadata.",
    },
  ],
  { name: "arize.search_knowledge_base" },
);

const summarizeDocuments = traceChain(
  async (documents: Array<{ title: string; content: string }>) =>
    documents.map((doc) => `${doc.title}: ${doc.content}`).join(" | "),
  { name: "arize.summarize_documents" },
);

const supportAgent = traceAgent(
  async (question: string) => {
    const documents = await searchKnowledgeBase({ query: question });
    const answer = await summarizeDocuments(documents);
    return { answer, documentCount: documents.length };
  },
  { name: "arize.support_agent" },
);

const workflowName = "arize-ts-trace-helpers.workflow";
const respan = createRespan();

try {
  const result = await runWithArizeWorkflow(respan, workflowName, async () => {
    let ctx = context.active();
    ctx = setSession(ctx, { sessionId: `${RUN_ID}-session` });
    ctx = setUser(ctx, { userId: "arize-example-user" });
    ctx = setMetadata(ctx, {
      example_script: "01_trace_helpers",
      run_id: RUN_ID,
    });
    ctx = setTags(ctx, ["respan-example", "arize", "trace-helpers"]);
    ctx = setPromptTemplate(ctx, {
      template: "Answer using docs about {topic}",
      variables: { topic: "typescript tracing" },
      version: "v1",
    });
    ctx = setAttributes(ctx, { "app.request_id": `${RUN_ID}-01` });

    return await context.with(
      ctx,
      async () =>
        await supportAgent(
          "How should I trace Arize TypeScript helper spans with Respan?",
        ),
    );
  });

  logExampleResult(workflowName, result);
} finally {
  await finishRespan(respan);
}
