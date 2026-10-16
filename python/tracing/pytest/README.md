# pytest tracing examples

The eight isolated scenarios exercise the installed plugin, complete native JSON parameters, pass/skip/xfail/XPASS, setup/call/teardown failures, async tests, collection errors, interruption, nested application spans, and two real xdist workers. Expected native failures keep their exit codes; the runner succeeds only when each scenario and its recorded span tree meet the contract.

```bash
pip install -r requirements.txt
python run_all.py
```

The default run records spans locally. To export explicitly, configure `RESPAN_API_KEY` and run `RESPAN_EXAMPLE_EXPORT=1 python run_all.py`. Only export mode loads the repository `.env` without overriding shell values. `RESPAN_EXAMPLE_RUN_ID` supplies a shared lookup marker; `RESPAN_EXAMPLE_REPORT_DIR` saves the actual local spans. Worker reports retain each native process's separate session tree.

For development, install only the target instrumentation editable and keep the vendor/Respan companion dependencies released. The suite is validated against pytest 9.1.1 and the declared 7.4.0 floor; a clean wheel built from the sdist must run the same examples.

Content-disabled traces omit canonical input/output and failure messages while retaining outcomes, numeric exit codes, phase durations and exception types. Fixture return values are never inspected. No HTTP or model usage fields are inferred from test outcomes. Backend projection of status or payloads requires separate stored-trace inspection.
