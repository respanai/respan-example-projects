import { OpenInferenceSpanKind, observe } from "@arizeai/phoenix-otel";
import {
  createRespan,
  finishRespan,
  logExampleResult,
  runWithArizeWorkflow,
} from "./_shared.js";

class SupportPlanner {
  @observe({ name: "arize.observed_plan", kind: OpenInferenceSpanKind.CHAIN })
  async plan(question: string) {
    return {
      question,
      steps: ["retrieve docs", "draft answer", "review confidence"],
    };
  }

  @observe({ name: "arize.observed_agent", kind: OpenInferenceSpanKind.AGENT })
  async answer(question: string) {
    const plan = await this.plan(question);
    return {
      plan,
      answer: `Use ${plan.steps.join(", ")} for: ${question}`,
    };
  }
}

const workflowName = "arize-ts-observe-decorator.workflow";
const respan = createRespan();

try {
  const result = await runWithArizeWorkflow(respan, workflowName, async () => {
    const planner = new SupportPlanner();
    return await planner.answer(
      "How do decorators create OpenInference spans?",
    );
  });

  logExampleResult(workflowName, {
    answer: result.answer,
    stepCount: result.plan.steps.length,
  });
} finally {
  await finishRespan(respan);
}
