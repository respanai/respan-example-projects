# Claude Code + Respan

Trace every Claude Code session in Respan, including every sub-agent it spawns, while
the session runs. Built for long sessions: hours of work and dozens of sub-agents are
captured in full, with every parent-child relationship kept.

## What you get

```
Session (thread claudecode_<session id>)
├─ Trace: Turn 1: "Investigate the bug"          root span (claude_code.turn = 1)
│  ├─ claude.chat (claude-opus-...)               one span per model response: tokens, cache, reasoning, tool calls
│  ├─ Tool: Read / Bash / Edit ...                input, output, duration, errors
│  └─ Tool: Agent                                 the call that spawned a sub-agent
│     └─ Sub-agent: <description>                 the sub-agent's own run
│        ├─ claude.chat ...                       its model calls, with their own tokens
│        ├─ Tool: Grep ...
│        └─ Tool: Agent                           sub-agents of sub-agents nest the same way
│           └─ Sub-agent: ...
├─ Trace: Turn 2: ...                             same session and thread id
└─ ...
```

- **One trace per turn**, so a 10-hour session never keeps one trace open. Every span
  of the session carries the same session and thread id (`claudecode_<session id>`):
  the Threads view, or a `session_identifier` filter, shows the whole session.
- **Sub-agents are nested** under the `Tool: Agent` call that spawned them, at any
  depth, as ordinary child spans of the same trace. A background sub-agent that
  finishes during a later turn still appears in the trace of the turn that started it.
  Each `Sub-agent` span carries `claude_code.agent_id`, `claude_code.agent_type` and
  `claude_code.spawn_depth`.
- **Resumed sessions** (`--resume`, `--continue`) record the session they resumed in
  `claude_code.resumed_from_session` and do not re-send the copied history.
- **Sent while the session runs**: on every tool call, sub-agent finish and response,
  not only at the end. Every span is sent once: a turn's root and a sub-agent's root
  are sent when they finish, so while a turn or sub-agent is still running its spans
  appear at the top level of the trace and nest under their parent once it closes and
  is sent. A sub-agent that never reports SubagentStop is closed
  once its transcript has been quiet for 10 minutes; one that is continued after it
  finished (SendMessage) gets a new `Sub-agent (continued N)` span.
- **Nothing lost**: the hook reads each transcript from where it stopped (it never
  re-reads a file from the start) and only moves on after Respan accepted the spans.
  Span ids come from the transcript, so a retry re-sends the same ids: if a send timed
  out after Respan had stored it, that span is stored twice under one span id (the
  trace view shows it once; the logs list shows both).
- **Never slows Claude Code down**: the hook queues the event and returns
  (about 0.1 s); a background worker does the export. It always exits 0 and prints
  nothing.

## Setup

Requires Python 3.8+. It uses `requests` when installed and the standard library otherwise (with `certifi`'s CA bundle when available), so it works from any `python3` on your PATH.

1. Copy the hook:

   ```bash
   mkdir -p ~/.claude/hooks
   cp respan_hook.py ~/.claude/hooks/
   ```

2. Register it for `Stop`, `SubagentStop` and `PostToolUse` in `~/.claude/settings.json`
   (see `.claude/settings.json.example`):

   ```json
   {
     "hooks": {
       "Stop":         [{ "hooks": [{ "type": "command", "command": "python3 ~/.claude/hooks/respan_hook.py" }] }],
       "SubagentStop": [{ "hooks": [{ "type": "command", "command": "python3 ~/.claude/hooks/respan_hook.py" }] }],
       "PostToolUse":  [{ "hooks": [{ "type": "command", "command": "python3 ~/.claude/hooks/respan_hook.py" }] }]
     }
   }
   ```

   `Stop` alone still works: everything is sent at the end of each response instead
   of as it happens.

3. Turn it on (globally, or per project in `.claude/settings.local.json`):

   ```json
   {
     "env": {
       "TRACE_TO_RESPAN": "true",
       "RESPAN_API_KEY": "your-api-key"
     }
   }
   ```

The first event of a session that started before you installed the hook sends the
whole session so far.

## Environment variables

| Variable | Description |
|---|---|
| `TRACE_TO_RESPAN` | `"true"` to enable (required) |
| `RESPAN_API_KEY` | Your Respan API key (required) |
| `RESPAN_BASE_URL` | Default `https://api.respan.ai/api`; enterprise: `https://endpoint.respan.ai/api` |
| `RESPAN_CUSTOMER_ID` | Customer identifier on every span (default `claude-code`) |
| `RESPAN_METADATA` | JSON object added to every span's metadata, e.g. `'{"team":"core"}'` |
| `CC_RESPAN_MAX_CHARS` | Max characters kept per input/output (default `4000`) |
| `RESPAN_HOOK_DEBUG` | `1` for a verbose log |

## Files it writes

Only under `~/.claude/state/`: `respan_state_v2.json` (where each transcript was read
up to), `respan_hook_v2.{events,lock,dirty}` (the event queue and worker lock) and
`respan_hook.log` (rotated at 5 MB). Transcripts are only read. The `respan_state.json`
of the previous version of this hook is not used.

## Troubleshooting

```bash
tail -f ~/.claude/state/respan_hook.log      # errors are always logged; RESPAN_HOOK_DEBUG=1 for more
```

- Nothing in Respan: check `TRACE_TO_RESPAN` is the string `"true"` and the key is right.
- Respan unreachable: events wait in `respan_hook_v2.events` and are retried on the next hook run.

## Tests

```bash
pip install pytest
pytest tests
```

The tests build synthetic transcripts (plain turns, parallel and nested sub-agents, a
background sub-agent finishing in a later turn, a 2,000-turn session, resume, send
failures, concurrent hook runs) and check every exported span.
