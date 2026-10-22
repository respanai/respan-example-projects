import {
  OITracer,
  OpenInferenceSpanKind,
  getEmbeddingAttributes,
  getInputAttributes,
  getRetrieverAttributes,
  trace,
  withSpan,
} from "@arizeai/phoenix-otel";
import {
  createRespan,
  finishRespan,
  logExampleResult,
  runWithArizeWorkflow,
} from "./_shared.js";

const retrieveDocuments = withSpan(
  async (query: string) => [
    { id: "doc-1", content: `Architecture notes for ${query}`, score: 0.97 },
    {
      id: "doc-2",
      content: "OpenInference spans need canonical Respan translation.",
      score: 0.93,
    },
  ],
  {
    name: "arize.retrieve_documents",
    kind: OpenInferenceSpanKind.RETRIEVER,
    processInput: (query) => getInputAttributes(query),
    processOutput: (documents) =>
      getRetrieverAttributes({
        documents: documents.map((document) => ({
          id: document.id,
          content: document.content,
          score: document.score,
        })),
      }),
  },
);

const embedDocuments = withSpan(
  async (documents: Array<{ content: string }>) =>
    documents.map((document, index) => ({
      text: document.content,
      vector: [0.1 + index, 0.2 + index, 0.3 + index],
    })),
  {
    name: "arize.embed_documents",
    kind: OpenInferenceSpanKind.EMBEDDING,
    processInput: (documents) =>
      getInputAttributes(
        JSON.stringify(documents.map((document) => document.content)),
      ),
    processOutput: (embeddings) =>
      getEmbeddingAttributes({
        modelName: "text-embedding-3-small",
        embeddings: embeddings.map((item) => ({
          text: item.text,
          vector: item.vector,
        })),
      }),
  },
);

function createRedactedClassifier() {
  const redactedTracer = new OITracer({
    tracer: trace.getTracer("arize-redacted-classifier"),
    traceConfig: {
      hideInputs: true,
      hideOutputs: true,
      hideOutputText: true,
      hideEmbeddingVectors: true,
    },
  });

  return withSpan(
    async (text: string) => ({ label: "needs-human-review", text }),
    {
      tracer: redactedTracer,
      name: "arize.redacted_classifier",
      kind: OpenInferenceSpanKind.LLM,
    },
  );
}

const workflowName = "arize-ts-retrieval-redaction.workflow";
const respan = createRespan();

try {
  const result = await runWithArizeWorkflow(respan, workflowName, async () => {
    const classifyWithRedaction = createRedactedClassifier();
    const documents = await retrieveDocuments("Arize TypeScript integration");
    const embeddings = await embedDocuments(documents);
    const classification = await classifyWithRedaction(
      "Sensitive prompt: trace this account issue",
    );
    return {
      documentCount: documents.length,
      embeddingCount: embeddings.length,
      classification: classification.label,
    };
  });

  logExampleResult(workflowName, result);
} finally {
  await finishRespan(respan);
}
