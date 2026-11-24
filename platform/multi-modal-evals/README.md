# Respan Multi-Modal Tool Evaluation Workflow

This project demonstrates a complete workflow for evaluating LLM agents with tool calls using Respan's evaluation platform.

## Workflow Overview

### 1. Agent Demo & Log Generation
- **Agent**: `agent.py` - Travel assistant with 4 tools (search_places, check_weather, find_hotels, recommend_activities)
- **Features**: Multi-modal inputs (text + images), prompt management, tool calls
- **Output**: Logs tagged with `metadata.eval_run` for filtering

### 2. Log Management
- **Logs API**: `logs/logs.py` - Fetch logs by time range and filters
- **Usage**: `main.py` - Get logs filtered by `metadata__eval_run`

### 3. Evaluator Creation  
- **Evaluators API**: `evaluators/evaluators.py` - Create custom LLM evaluators
- **Example**: Tool Call Accuracy Evaluator with scoring rubric (0.0-1.0)

### 4. Testset Management
- **Testsets API**: `testsets/testsets.py` - Create testsets from logs or manual data
- **Columns**: category, name, is_booking_hotel, is_checking_weather, expected_tools
- **Usage**: Convert log variables into testset rows

### 5. Prompt Management
- **Prompts API**: `prompts/prompts.py` - Create, version, and manage prompts
- **Usage**: Fetch actual prompts instead of hardcoding prompt messages
- **Versioning**: Compare different prompt versions in experiments

### 6. Experiment Creation & Execution
- **Experiments API**: `experiments/experiments.py` - Create experiments with prompt versions
- **Structure**: Columns = prompt versions (using prompt_id), Rows = testset data
- **Evaluation**: Run experiments and apply evaluators

## Quick Start

```python
# 1. Run agent demo
python -m example_workflows.multi_modal_tool_evals.agent

# 2. Fetch logs  
python -m example_workflows.multi_modal_tool_evals.main

# 3. Create evaluator
from evaluators import create_llm_evaluator
evaluator = create_llm_evaluator(
    evaluator_slug='tool_call_accuracy',
    name='Tool Call Accuracy',
    evaluator_definition='Evaluate tool call correctness...',
    scoring_rubric='Score 1.0: Perfect usage...'
)

# 4. Create testset
from testsets import create_testset, create_testset_rows
testset = create_testset("Travel Agent Tests", columns=[...])
create_testset_rows(testset['id'], rows)

# 5. Create & run experiment with prompts
from prompts import list_prompts, get_prompt
from experiments import create_experiment, run_experiment, run_experiment_evals

# Use actual prompts instead of hardcoded messages
prompt = get_prompt('your-prompt-id')
experiment = create_experiment("Agent Comparison", 
    columns=[{"prompt_id": prompt['id'], "prompt_version": 1}], 
    rows=[...])
run_experiment(experiment['id'])
run_experiment_evals(experiment['id'], ['tool_call_accuracy'])
```

## API Examples

### Create Evaluator
```python
create_llm_evaluator(
    evaluator_slug='tool_call_accuracy',
    name='Tool Call Accuracy Evaluator', 
    evaluator_definition='Evaluate whether the AI agent correctly identified the need for tool calls...',
    scoring_rubric='''
    Score 1.0: Perfect tool usage - called all necessary tools with correct parameters
    Score 0.8: Good tool usage - called most necessary tools correctly
    Score 0.6: Adequate tool usage - called some necessary tools but missed important ones
    Score 0.4: Poor tool usage - called wrong tools or missed most necessary tool calls
    Score 0.0: No tool calls when tools were clearly needed
    '''
)
```

### Create Testset  
```python
testset = create_testset(
    name="Travel Agent Tests",
    description="Multi-modal travel agent evaluation",
    column_definitions=[
        {"field": "category"},
        {"field": "name"},
        {"field": "is_booking_hotel"},
        {"field": "expected_tools"}
    ]
)

create_testset_rows(testset['id'], [
    {"row_data": {
        "category": "beach",
        "name": "Mike",
        "is_booking_hotel": False,
        "expected_tools": "search_places"
    }}
])
```

### Create Prompt & Experiment
```python
# Create and version prompts
from prompts import create_prompt, create_prompt_version
prompt = create_prompt("Travel Agent", "Multi-modal travel assistant")
version = create_prompt_version(prompt['prompt_id'], [
    {"role": "system", "content": "You are a travel assistant..."},
    {"role": "user", "content": "User {{name}} wants {{category}} travel"}
])

# Create experiment using prompt ID
experiment = create_experiment(
    name="Travel Agent Comparison",
    columns=[
        {
            "model": "gpt-4o",
            "name": "Travel Agent v1",
            "prompt_id": prompt['prompt_id'],
            "prompt_version": 1,
            "tools": [...],
            "temperature": 0.7
        }
    ],
    rows=[{"input": {"category": "beach", "name": "Mike"}}]
)

run_experiment(experiment['id'])
run_experiment_evals(experiment['id'], ['tool_call_accuracy'])
```

## Results Analysis

The workflow provides:
- **Tool Call Accuracy Scores**: 0.0-1.0 for each prompt version
- **Comparative Analysis**: See which prompt performs better
- **Detailed Evaluation**: Reasoning behind each score
- **Cost Tracking**: Evaluation costs per run

Example results show Travel Agent v2 (more aggressive) scored higher on complex scenarios requiring multiple tool calls.

