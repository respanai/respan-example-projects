import { OpenAIChatModel } from "beeai-framework/adapters/openai/backend/chat";
import { UnconstrainedMemory } from "beeai-framework/memory/unconstrainedMemory";
import { RequirementAgent } from "beeai-framework/agents/requirement/agent";
import { CalculatorTool } from "beeai-framework/tools/calculator";
import { createBeeAIRespanRuntime, runWithBeeAIWorkflow } from "./_respan.js";

export async function runToolCallingAgent(): Promise<void> {
  const workflowName = "beeai_tool_calling_agent.workflow";
  const { env, respan } = await createBeeAIRespanRuntime();

  try {
    const llm = new OpenAIChatModel(
      env.model,
      {},
      { apiKey: env.gatewayApiKey, baseURL: env.openAIEndpoint },
    );
    const agent = new RequirementAgent({
      llm,
      memory: new UnconstrainedMemory(),
      tools: [new CalculatorTool()],
      execution: { maxIterations: 4, maxRetriesPerStep: 1, totalMaxRetries: 2 },
    });

    const prompt =
      "Use the calculator tool to compute (19 + 23) * 2. Return only the number.";
    const answer = await runWithBeeAIWorkflow(
      respan,
      workflowName,
      { prompt, tool: "calculator", expression: "(19 + 23) * 2" },
      async () => {
        const result = await agent.run({ prompt });
        return result.result.text;
      },
    );

    console.log(`Workflow: ${workflowName}`);
    console.log(`Model: ${env.model}`);
    console.log(`Answer: ${answer}`);
  } finally {
    await respan.shutdown();
  }
}

await runToolCallingAgent();
