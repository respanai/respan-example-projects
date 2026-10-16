import { Agent } from "@mastra/core/agent";
import { createStep, createWorkflow } from "@mastra/core/workflows";
import { z } from "zod";
import {
  createFailingModel,
  createRuntime,
  EXAMPLE_RUN_ID,
  getTraceWorkflowName,
  runWithRespanWorkflow,
} from "./_shared.js";

const workflowName = "Mastra Failure Example";
const failingAgent = new Agent({
  id: "mastra-failure-agent",
  name: "Mastra Failure Agent",
  instructions:
    "This request intentionally exercises the provider failure trace path.",
  model: createFailingModel(),
});

const failureWorkflow = createWorkflow({
  id: "mastra-agent-failure-workflow",
  inputSchema: z.object({ prompt: z.string() }),
  outputSchema: z.object({ text: z.string() }),
})
  .then(createStep(failingAgent))
  .commit();

const { mastra, respan } = createRuntime({ failingAgent }, { failureWorkflow });
let failureName: string | undefined;

try {
  await runWithRespanWorkflow(mastra, respan, workflowName, async () => {
    const workflow = mastra.getWorkflow("failureWorkflow");
    const run = await workflow.createRun();
    const result = await run.start({
      inputData: {
        prompt: "Exercise the expected provider failure path.",
      },
    });
    if (result.status === "failed") {
      throw result.error;
    }
    throw new Error(`Expected failed workflow, received ${result.status}`);
  });
} catch (error) {
  failureName = error instanceof Error ? error.name : "Error";
}

if (!failureName) {
  throw new Error("The intentional Mastra provider failure did not occur.");
}

console.log(
  JSON.stringify(
    {
      workflowName: getTraceWorkflowName(workflowName),
      runId: EXAMPLE_RUN_ID,
      expectedFailure: true,
      failureName,
    },
    null,
    2,
  ),
);
