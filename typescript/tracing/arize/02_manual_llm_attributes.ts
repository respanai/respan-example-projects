import {
  OpenInferenceSpanKind,
  getLLMAttributes,
  withSpan,
} from "@arizeai/phoenix-otel";
import {
  createRespan,
  finishRespan,
  logExampleResult,
  runWithArizeWorkflow,
} from "./_shared.js";

const answerWithSyntheticModel = withSpan(
  async (question: string) => ({
    question,
    role: "assistant",
    content: `Synthetic answer for: ${question}`,
    tokenCount: {
      prompt: 18,
      completion: 22,
      total: 40,
    },
  }),
  {
    name: "arize.synthetic_llm_turn",
    kind: OpenInferenceSpanKind.LLM,
    processOutput: (output) =>
      getLLMAttributes({
        provider: "openai",
        modelName: "gpt-4o-mini",
        inputMessages: [{ role: "user", content: output.question }],
        outputMessages: [{ role: output.role, content: output.content }],
        tokenCount: output.tokenCount,
        invocationParameters: {
          temperature: 0.1,
          max_tokens: 128,
        },
      }),
  },
);

const classifyRequest = withSpan(
  async (request: { text: string }) => ({
    label: request.text.includes("trace") ? "observability" : "general",
    confidence: 0.98,
  }),
  {
    name: "arize.classify_request",
    kind: OpenInferenceSpanKind.CHAIN,
  },
);

const workflowName = "arize-ts-manual-llm.workflow";
const respan = createRespan();

try {
  const result = await runWithArizeWorkflow(respan, workflowName, async () => {
    const classification = await classifyRequest({
      text: "trace Arize helper spans",
    });
    const llm = await answerWithSyntheticModel(
      "Explain Respan and Arize helper tracing.",
    );
    return { classification, llm };
  });

  logExampleResult(workflowName, result);
} finally {
  await finishRespan(respan);
}
