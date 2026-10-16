"""Run every bounded LangChain example in a fresh process."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

EXAMPLES = tuple(
    f"{index:02d}_{name}.py"
    for index, name in enumerate(
        (
            "quickstart",
            "chat_model_invoke",
            "chat_model_stream",
            "chat_model_batch",
            "chat_model_batch_as_completed",
            "chat_model_ainvoke",
            "chat_model_astream",
            "chat_model_abatch",
            "chat_model_abatch_as_completed",
            "chat_model_astream_events",
            "llm_invoke",
            "llm_stream",
            "model_bind_tools",
            "model_with_structured_output",
            "tool_invoke",
            "tool_ainvoke",
            "prompt_chain_invoke",
            "runnable_parallel_invoke",
            "retriever_invoke",
            "agent_invoke",
            "agent_stream_updates",
            "agent_stream_messages",
            "agent_stream_custom",
            "agent_structured_output",
            "custom_event",
            "runnable_with_retry",
            "chain_error",
            "tool_error",
            "retriever_error",
            "langgraph_state_graph",
            "langgraph_interrupt_resume",
            "provider_http_and_sse",
            "privacy",
            "tool_artifact_vectors",
        )
    )
)


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    passed = 0
    skipped = []
    failed = []
    from langchain import agents

    has_agent = hasattr(agents, "create_agent")
    try:
        from langgraph import types

        has_interrupt = hasattr(types, "interrupt")
    except ImportError:
        has_interrupt = False
    for script_name in EXAMPLES:
        index = int(script_name[:2])
        if (19 <= index <= 23 and not has_agent) or (index == 30 and not has_interrupt):
            skipped.append(script_name)
            print(f"SKIP {script_name}: public API absent in installed minimum")
            continue
        print(f"\n=== {script_name} ===", flush=True)
        result = subprocess.run(
            [sys.executable, str(base_dir / script_name)], check=False
        )
        if result.returncode:
            failed.append(script_name)
        else:
            passed += 1
    summary = {
        "passed": passed,
        "skipped": skipped,
        "failed": failed,
        "total": len(EXAMPLES),
    }
    print(json.dumps(summary))
    target = os.getenv("LANGCHAIN_RUNNER_REPORT")
    if target:
        Path(target).write_text(json.dumps(summary, indent=2))
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
