"""Dify Knowledge Base, RAG pipeline, and Workspace calls traced by Respan."""

from __future__ import annotations

import os

from _shared import DifyExampleRuntime, print_result


def main() -> None:
    workflow_name = "dify_knowledge_workspace.workflow"
    with DifyExampleRuntime(workflow_name) as runtime:
        dataset_id = os.getenv("DIFY_RAG_DATASET_ID", "dataset-local")
        knowledge = runtime.knowledge_base_client(dataset_id)
        workspace = runtime.workspace_client()
        if knowledge is None or workspace is None:
            summary = {
                "workflow": workflow_name,
                "status": "skipped",
                "reason": "installed dify-client does not expose Knowledge Base and Workspace clients",
            }
            runtime.set_result(summary)
            print_result("knowledge_workspace", summary)
            return

        datasets = knowledge.list_datasets(page=1, page_size=20)
        datasets.raise_for_status()
        models = workspace.get_available_models("llm")
        models.raise_for_status()

        pipeline_result = None
        start_node_id = os.getenv("DIFY_RAG_START_NODE_ID")
        if runtime.is_local or start_node_id:
            pipeline = knowledge.run_rag_pipeline(
                inputs={},
                datasource_type=os.getenv(
                    "DIFY_RAG_DATASOURCE_TYPE", "online_document"
                ),
                datasource_info_list=[],
                start_node_id=start_node_id or "start-local",
                is_published=True,
                response_mode="blocking",
            )
            pipeline.raise_for_status()
            pipeline_result = pipeline.json().get("workflow_run_id")

        summary = {
            "workflow": workflow_name,
            "status": "completed",
            "datasets": len(datasets.json().get("data", [])),
            "models": len(models.json().get("data", [])),
            "pipeline_run_id": pipeline_result,
        }
        runtime.set_result(summary)
        print_result("knowledge_workspace", summary)


if __name__ == "__main__":
    main()
