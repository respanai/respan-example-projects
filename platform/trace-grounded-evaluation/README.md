# Trace-grounded task evaluation

<mark data-hl="sky">Use Respan's gateway</mark> to <mark data-hl="sky">judge an agent's recorded actions</mark>, cite evidence spans,
and compare the task verdict with a code-checked reference. The example keeps
task completion and the truthfulness of the final response as separate fields.

Replay is the default. It uses three synthetic cases and six captured gateway
replies, so it needs no credentials, installation, or model spend. Node 24 or
newer runs the TypeScript directly.

```bash
npm run replay
npm test
```

## <mark data-hl="mint">What the cases show</mark>

- An agent tries to delete a calendar event using a todo ID, receives an error,
  and still claims success.
- An agent deletes the right todo and submits the requested remaining count.
- An agent stops after an unsuccessful newsletter search and asks the user for
  details instead of completing the task.

`fixtures/cases.json` contains only the task and observable trace evidence.
`fixtures/recorded.json` stores reference task labels, the two rubrics, captured
replies, and source identities. Labels and author annotations are excluded from
the gateway request by an explicit input projection.

The captured model is `claude-haiku-4-5` and the capture date is October 26, 2026. The cases are a curated subset of [ablate](https://github.com/prnayyay/ablate),
an open-source agent-harness benchmark. References come from its deterministic
final-state and structured-answer checks. Source archive hashes and run IDs
are in the fixture. These are synthetic benchmark records, not customer data.
The MIT notice for the adapted code/data is in `fixtures/LICENSE`.

## Optional live gateway call

Set `RESPAN_API_KEY` in your shell. The gateway needs either Respan credits or
a provider key configured in the dashboard. `--byok` explicitly sends your local
`ANTHROPIC_API_KEY` in the documented per-request credentials field; Anthropic
then bills the inference calls.

```bash
# One call by default. Add --byok only when using your Anthropic key.
npm run live -- --byok

# After inspecting that output, run the full six-call demonstration.
RESPAN_EXAMPLE_RUN_ID=trace-judge-demo npm run live -- --byok --max-calls 6
```

You can also load an existing, git-ignored environment file with Node:

```bash
node --env-file=/path/to/.env example.ts --live --byok
```

`RESPAN_JUDGE_MODEL` optionally overrides the recorded model; verify its current
availability in the model catalog. The example uses Respan's
[`POST /api/chat/completions`](https://www.respan.ai/docs/apis/gateway/create-chat-completion)
endpoint and automatic gateway logging. It is a custom evaluation workflow and
does not create hosted evaluator objects or experiments.

Each live request includes the exact `RESPAN_EXAMPLE_RUN_ID` marker, case ID,
and rubric in metadata, plus a unique custom identifier. Find the logs by that
marker in Respan. Raw replies, usage, finish reason, response ID, Respan log ID,
and parse results are saved to `.out/`. Request credentials are not saved there.
The live command stops on the first invalid reply or unknown evidence ID, after
retaining the response. HTTP errors include the server explanation with keys
redacted. There are no automatic inference retries.

## Formatting and evidence are different checks

The recorded replies were valid JSON inside Markdown fences. A strict raw-JSON
parser initially rejected all of them. `parseReply` records whether it accepted
raw JSON or exactly one complete outer fence, then validates the same schema
and citation IDs. It rejects surrounding prose, multiple blocks, truncated JSON,
extra fields, duplicate citations, and unknown verdict values. Original reply
text is retained, so normalization does not hide format noncompliance.

An existing span ID does not establish that it supports the accompanying claim.
In one captured grounded explanation, the judge cites the failed deletion span
as evidence for the contents of the todo list; the direct evidence is the
separate `list_todos` span. The task verdict is still correct. Reference task
labels do not label explanation quality or `responseGrounded` correctness.

Both rubrics match the reference task verdicts on these three examples. This
replay is not evidence that the extra rubric is better, that the judge is
generally accurate, or that abstention works on incomplete traces. The baseline
already sees trace evidence. To study an improvement, fix the evaluator, separate
development and reserved task groups, and evaluate the selected change on the
reserved tasks without tuning further on those results.
