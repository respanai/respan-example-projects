"""Score app.answer() on a Respan dataset and fail CI under a threshold.

Uses only documented Respan API endpoints:
  1. POST /api/datasets/{golden}/logs/list/       read the golden questions + expected answers
  2. POST /api/datasets/                          create this run's dataset
  3. POST /api/datasets/{run}/logs/bulk/          store each question with app.answer()'s output
  4. POST /api/datasets/{run}/eval-reports/create/ run the evaluator over the outputs
  5. GET  /api/datasets/{run}/eval-reports/list/   wait for the average score
"""

import json
import os
import sys
import time
import urllib.request

from app import answer

BASE_URL = os.environ["RESPAN_BASE_URL"]
DATASET_ID = os.environ["RESPAN_DATASET_ID"]
EVALUATOR_ID = os.environ["RESPAN_EVALUATOR_ID"]
MIN_SCORE = float(os.environ.get("MIN_SCORE", "4"))
# The dashboard lives next to the API: api.respan.ai -> platform.respan.ai.
APP_URL = BASE_URL.replace("api.", "platform.", 1)

HEADERS = {
    "Authorization": f"Bearer {os.environ['RESPAN_API_KEY']}",
    "Content-Type": "application/json",
}


def call(method, path, json_body=None):
    data = json.dumps(json_body).encode() if json_body is not None else None
    request = urllib.request.Request(f"{BASE_URL}/api{path}", data=data, headers=HEADERS, method=method)
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read() or "null")


def wait_for(check, what, timeout=300):
    deadline = time.time() + timeout
    while time.time() < deadline:
        result = check()
        if result:
            return result
        time.sleep(3)
    sys.exit(f"Timed out waiting for {what}")


def list_rows(dataset_id):
    return call("POST", f"/datasets/{dataset_id}/logs/list/?page_size=500", json_body={})["results"]


# 1. The golden questions and their expected answers, managed in Respan.
golden = list_rows(DATASET_ID)

# 2-3. Run the code under test on every question; store the answers as this run's dataset.
run_name = f"CI {os.environ.get('GITHUB_REPOSITORY', 'local')} {os.environ.get('RUN_LABEL', '')}".strip()
run_id = call("POST", "/datasets/", json_body={"name": run_name, "is_empty": True})["id"]
logs = [
    {"input": row["input"], "output": answer(row["input"]), "expected_output": row["expected_output"]}
    for row in golden
]
call("POST", f"/datasets/{run_id}/logs/bulk/", json_body={"logs": logs})
wait_for(lambda: len(list_rows(run_id)) == len(logs), "the rows to be stored")

# 4-5. Score the outputs with the evaluator and wait for the result.
task = call("POST", f"/datasets/{run_id}/eval-reports/create/", json_body={"evaluator_ids": [EVALUATOR_ID]})
task_id = task["created_tasks"][0]["task_id"]


def finished_report():
    for report in call("GET", f"/datasets/{run_id}/eval-reports/list/")["results"]:
        if report["task_id"] != task_id:
            continue
        if report["status"] == "failed" or report["primary_score_avg"] is not None:
            return report
    return None


report = wait_for(finished_report, "the evaluator")
if report["status"] == "failed":
    sys.exit(f"Evaluator run failed: {report['error_message']}")
average = report["primary_score_avg"]

# Print per-row scores, write a job summary, and gate on the average.
link = f"{APP_URL}/platform/evaluations/datasets/{run_id}/logs"
lines = [
    f"### Respan eval: average {average:.2f} (threshold {MIN_SCORE})",
    "",
    "| Question | Answer | Score |",
    "|---|---|---|",
]
for row in list_rows(run_id):
    score = next(iter(row["scores"].values()), {}).get("numerical_value")
    lines.append(f"| {row['input']} | {row['output'][:120]} | {score} |")
lines += ["", f"[Open the results in Respan]({link})"]
summary = "\n".join(lines)
print(summary)
if os.environ.get("GITHUB_STEP_SUMMARY"):
    with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
        f.write(summary + "\n")

# An annotation puts the result on the run page and the pull request's checks.
if average < MIN_SCORE:
    print(f"::error title=Respan eval::Average score {average:.2f} is below the threshold {MIN_SCORE}")
    sys.exit(f"FAIL: average score {average:.2f} is below {MIN_SCORE}")
print(f"::notice title=Respan eval::Average score {average:.2f} meets the threshold {MIN_SCORE}")
print(f"PASS: average score {average:.2f} >= {MIN_SCORE}")
