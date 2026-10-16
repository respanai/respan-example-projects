import type { Respan } from "@respan/respan";
import {
  withSpan,
  getEmbeddingAttributes,
  getRetrieverAttributes,
  traceTool,
  getOutputAttributes,
} from "@arizeai/openinference-core";
import {
  OpenInferenceSpanKind,
  MimeType,
} from "@arizeai/openinference-semantic-conventions";
import { workflow } from "./_shared.js";
export async function run(respan: Respan) {
  const vector = Array.from({ length: 5001 }, (_, index) => index / 5001);
  const embedding = withSpan(() => vector, {
    name: "embed-documents",
    kind: OpenInferenceSpanKind.EMBEDDING,
    processOutput: () =>
      getEmbeddingAttributes({
        modelName: "fixture-embedding",
        embeddings: [{ text: "fixture document", vector }],
      }),
  });
  const retrieve = withSpan(
    (query: string) => [
      { id: "doc-0", content: query, score: 0, metadata: { accepted: false } },
    ],
    {
      name: "retrieve-documents",
      kind: OpenInferenceSpanKind.RETRIEVER,
      processOutput: (documents) => getRetrieverAttributes({ documents }),
    },
  );
  const empty = traceTool((_args: Record<string, never>) => null, {
    name: "empty-result",
    processOutput: (output) =>
      getOutputAttributes({
        value: JSON.stringify(output),
        mimeType: MimeType.JSON,
      }),
  });
  return workflow(respan, "retrieval-embeddings", () => {
    const documents = retrieve("fixture document");
    return {
      documentCount: documents.length,
      dimensions: embedding().length,
      empty: empty({}),
    };
  });
}
