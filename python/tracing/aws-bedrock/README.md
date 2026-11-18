# AWS Bedrock Runtime tracing examples

Run the complete suite with released boto3 and the Bedrock instrumentation:

```bash
pip install 'respan-instrumentation-aws-bedrock[instruments]' python-dotenv
python run_all.py
```

Local recording is the default. Ten controlled scenarios exercise native boto3
HTTP response parsing and CRC-validated AWS event-stream frames: InvokeModel,
Converse, ConverseStream, tool history/results/schema, native validation errors,
InvokeModel streaming, a 5001-dimensional embedding, privacy and suppression,
stream errors, and body readinto/context/partial-close behavior. The native client
uses an invalid endpoint with a controlled transport response, so these cases do
not call AWS. Scripts skip operations absent from the installed service model.

Export the same suite explicitly:

```bash
RESPAN_EXAMPLE_EXPORT=1 RESPAN_EXAMPLE_RUN_ID=bedrock-my-run python run_all.py
```

Only export mode loads the repository root `.env` and requires `RESPAN_API_KEY`.
`RESPAN_EXAMPLE_ENV_FILE` can select another environment file.
`RESPAN_EXAMPLE_LOCAL_PATH` saves local span records; `RESPAN_EXAMPLE_WIRE_PATH`
observes actual HTTP bodies posted by the released `RespanSpanExporter`.
These artifact files contain controlled example payloads.

`11_live_optional.py` skips by default. To make a real, billable AWS inference
request, separately set `AWS_BEDROCK_LIVE=1`, `AWS_BEDROCK_MODEL_ID`, and configure
AWS credentials/region through boto3's usual provider chain. Export is an
independent opt-in. Controlled runs establish SDK and exporter behavior; they do
not establish AWS credentials, deployed model access, or backend semantic
acceptance. Boto3 1.43.108 does not expose a bidirectional client method.
