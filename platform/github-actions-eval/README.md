# Respan eval in GitHub Actions (no stored secret)

Score an LLM app on every pull request with a Respan evaluator, and fail the check when the
score drops. The workflow gets its Respan API key from GitHub's OIDC token, so the repository
stores no Respan secret.

Guide: [GitHub Actions](https://www.respan.ai/docs/documentation/admin/github-actions-oidc)

## Files

```
app.py            # the code under test: a support bot that answers through the Respan gateway
respan_eval.py    # runs app.answer() over a Respan dataset, scores it, gates on the average
requirements.txt
```

The workflow is [`.github/workflows/respan-eval-example.yml`](../../.github/workflows/respan-eval-example.yml)
at the repository root, because GitHub runs workflows only from there. Its `paths:` filter runs
it only for pull requests that change this folder.

## What a run does

1. The job requests a GitHub OIDC token with the audience `respan` and exchanges it for a
   1-hour Respan API key (`POST /api/integrations/github-actions/token/`).
2. `respan_eval.py` reads the golden questions from a Respan dataset, runs `app.answer()` on
   each, stores the answers as a new dataset and runs a Respan evaluator over them.
3. The job prints a score table, also in the job summary with a link to the results in Respan,
   and fails when the average score is below `MIN_SCORE`.

## Use it in your repository

1. [Create a trust rule](https://www.respan.ai/docs/apis/github-actions/create-trust-rule) on
   your project for your repository.
2. In Respan, create a dataset of questions with `expected_output`, and an evaluator.
3. Copy the workflow and this folder, and set `RESPAN_PROJECT_ID`, `RESPAN_DATASET_ID` and
   `RESPAN_EVALUATOR_ID` in the workflow to yours.

The workflow calls `https://api.respan.ai` unless the repository variable `RESPAN_BASE_URL`
is set.

> **Staging for now.** In this repository `RESPAN_BASE_URL` is set to
> `https://staging-api.respan.ai`, and the IDs in the workflow are a staging project's, because
> the OIDC exchange is live on staging first. Once it is live in production, delete the
> variable and replace the IDs.

## Run it locally

```bash
pip install -r requirements.txt
export RESPAN_BASE_URL=https://api.respan.ai RESPAN_API_KEY=... \
  RESPAN_DATASET_ID=... RESPAN_EVALUATOR_ID=...
python respan_eval.py
```
