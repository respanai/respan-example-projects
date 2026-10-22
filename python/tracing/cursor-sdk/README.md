# Cursor Python SDK and hook examples

These controlled examples exercise native `cursor-sdk` 1.0.35 (minimum 1.0.24) and configuration-version-one payloads from the [current Cursor hook reference](https://cursor.com/docs/hooks). Native cases use the actual released SDK and HTTP/Connect parsing with an in-process mock transport. They do not launch a bridge, execute a shell command, edit a real file, or contact a paid Cursor agent.

## Install and run

The native tracing and newer hook fixes are in the companion SDK PR. Install its checkout in a fresh environment after resolving released dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt build poetry-core
python -m pip install --no-deps --no-build-isolation -e "$RESPAN_SOURCE/python-sdks/instrumentations/respan-instrumentation-cursor-sdk"
python run_all.py
```

Set `RESPAN_SOURCE` to the companion Respan checkout. Only the target adapter is editable; tracing/SDK/provider dependencies are released packages. Current tested tracing/SDK are 2.20.1/2.7.6; minimum are 2.17.0/2.6.26 with OTel1.38/std0.59b0/AI0.4.1. `respan-sdk` 2.6.1 lacks the required constant module. Minimum native1.0.24 explicitly skips billed usage because that method is absent.

The default uses memory export and requires no credentials. The runner gives all 11 scripts one marker, enforces timeouts and aggregates failures. `.env` loading does not override shell values. Hook state is isolated under a temporary directory, not the user's Cursor state file. Respan export is an explicit choice:

```bash
export RESPAN_API_KEY="..."
export RESPAN_EXAMPLE_EXPORT=1
export RESPAN_EXAMPLE_RUN_ID="cursor-fixture-run"
python run_all.py
```

Export targets `https://api.respan.ai/api/v2/traces`. Stored trace status, inferred usage and payload projections may differ from canonical OTLP; an HTTP200 alone does not establish semantic acceptance.

| Script | Coverage |
| --- | --- |
| 01 | Hook prompt, reasoning, edit, response and terminal stop |
| 02 | Dedicated shell/MCP observations with complete source data |
| 03 | Aborted stop and repeated terminal-event suppression |
| 04 | Full original hook transcript |
| 05 | Actual sync Run, modern step callback, model/per-send options, full5,000-element tool vector and source usage |
| 06 | Actual async Run/stream, awaited callback and legacy tool message |
| 07 | Failed native result, actual HTTP503 and explicit billed usage when available |
| 08 | Current generic tool success/failure, source call IDs, subagents, compaction and multiple assistant messages |
| 09 | Start-private native run and generation stay private after re-enabling content; disk and spans checked |
| 10 | Session, independent Tab read/edit and workspace lifecycle observations |
| 11 | Installed command's neutral permission JSON with explicit telemetry opt-out |

The first ten scripts produce traces; script11 checks five real CLI subprocesses without export. Hook error/cancelled states use OTel ERROR and do not fabricate HTTP status. Agent/task records preserve actual returned data without inventing LLM token fields. Credentials/environment/header values are redacted, full allowed tool arguments/results are retained, and private pending state is discarded.

Keep generic `postToolUse` completion hooks separate from dedicated `afterShellExecution`/`afterMCPExecution`/`afterFileEdit` completion hooks when configuring Cursor, since dedicated events may omit a shared invocation ID. `afterAgentResponse` is an assistant-message observation; `stop` ends the loop. Subagent correlation needs IDs for overlapping same-type workers. Session/Tab/workspace events are independent roots.

No live Cursor/bridge/cloud execution or paid inference is enabled by these scripts. Native store/custom-tool registration, administrative/conversation/artifact/download/observe RPCs and real Cursor permissions are outside this example set.
