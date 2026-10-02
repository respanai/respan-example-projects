#!/usr/bin/env node
import { CompletionClient, WorkflowClient } from "dify-client";
import { withDifyRuntime } from "./_shared.js";

const workflowName = "dify_typescript_completion_workflow.workflow";

await withDifyRuntime(workflowName, async (runtime) => {
  const completionClient = new CompletionClient({
    apiKey: runtime.key("DIFY_COMPLETION_API_KEY"),
    baseUrl: runtime.baseUrl,
  });
  const completion = await completionClient.createCompletionMessage({
    inputs: { query: "Translate tracing to French." },
    user: "respan-dify-ts-completion",
    response_mode: "blocking",
  });
  if (Symbol.asyncIterator in completion) throw new Error("Expected blocking completion");

  const workflowClient = new WorkflowClient({
    apiKey: runtime.key("DIFY_WORKFLOW_API_KEY"),
    baseUrl: runtime.baseUrl,
  });
  const workflow = await workflowClient.run({
    inputs: { query: "Summarize Dify tracing." },
    user: "respan-dify-ts-workflow",
    response_mode: "blocking",
  });
  if (Symbol.asyncIterator in workflow) throw new Error("Expected blocking workflow");

  const result = {
    completion: completion.data.answer,
    workflowRunId: workflow.data.workflow_run_id,
    workflowOutput: workflow.data.data,
  };
  runtime.setResult(result);
  return result;
});
