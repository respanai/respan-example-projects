#!/usr/bin/env node
import { KnowledgeBaseClient, WorkspaceClient } from "dify-client";
import { withDifyRuntime } from "./_shared.js";

const workflowName = "dify_typescript_knowledge_workspace.workflow";

await withDifyRuntime(workflowName, async (runtime) => {
  const datasetId = process.env.DIFY_RAG_DATASET_ID || "dataset-local";
  const knowledge = new KnowledgeBaseClient({
    apiKey: runtime.key("DIFY_DATASET_API_KEY"),
    baseUrl: runtime.baseUrl,
  });
  const datasets = await knowledge.listDatasets({ page: 1, limit: 20 });
  const workspace = new WorkspaceClient({
    apiKey: runtime.key("DIFY_DATASET_API_KEY"),
    baseUrl: runtime.baseUrl,
  });
  const models = await workspace.getModelsByType("llm");

  let pipelineRunId: unknown = null;
  const startNodeId = process.env.DIFY_RAG_START_NODE_ID;
  if (runtime.isLocal || startNodeId) {
    const pipeline = await knowledge.runPipeline(datasetId, {
      inputs: {},
      datasource_type: process.env.DIFY_RAG_DATASOURCE_TYPE || "online_document",
      datasource_info_list: [],
      start_node_id: startNodeId || "start-local",
      is_published: true,
      response_mode: "blocking",
    });
    if (Symbol.asyncIterator in pipeline) throw new Error("Expected blocking RAG pipeline");
    pipelineRunId = pipeline.data.workflow_run_id;
  }

  const result = {
    datasets: Array.isArray(datasets.data.data) ? datasets.data.data.length : 0,
    models: Array.isArray(models.data.data) ? models.data.data.length : 0,
    pipelineRunId,
  };
  runtime.setResult(result);
  return result;
});
