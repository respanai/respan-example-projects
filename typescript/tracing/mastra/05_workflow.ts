import assert from "node:assert/strict";
import { createStep, createWorkflow } from "@mastra/core/workflows";
import { z } from "zod";
import {
  createRuntime,
  EXAMPLE_RUN_ID,
  runWithRespanWorkflow,
} from "./_shared.js";
const shape = z.object({ value: z.number() });
const step = createStep({
  id: "double",
  inputSchema: shape,
  outputSchema: shape,
  execute: async ({ inputData }) => ({ value: inputData.value * 2 }),
});
const workflow = createWorkflow({
  id: "native-workflow",
  inputSchema: shape,
  outputSchema: shape,
})
  .then(step)
  .commit();
const { mastra, respan } = createRuntime({}, { workflow });
const result = await runWithRespanWorkflow(
  mastra,
  respan,
  "Mastra Native Workflow",
  async () =>
    (await mastra.getWorkflow("workflow").createRun()).start({
      inputData: { value: 21 },
    }),
);
assert.equal(result.status, "success");
console.log(
  JSON.stringify({
    runId: EXAMPLE_RUN_ID,
    scenario: "workflow",
    status: result.status,
  }),
);
