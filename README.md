# Respan Example Projects

Example projects demonstrating [Respan](https://respan.ai) tracing, observability, and platform integrations.

## Structure

```
python/
  tracing/
    respan-tracing-sdk/   # Core respan-tracing SDK examples (basic usage, span operations, multi-provider)
    openai-sdk/           # OpenAI 7.x feature suite with deterministic HTTP and opt-in live validation
    openai-agents-sdk/    # OpenAI Agents SDK with Respan tracing (basic, patterns, handoffs, tools, research bot)
    claude-agent-sdk/     # Claude Agent SDK with Respan tracing
    dspy/                 # DSPy native instrumentation examples
    langfuse/             # Langfuse integration example
    instructor/           # Instructor library example
    langchain/            # LangChain agent example
    cursor-sdk/           # Cursor SDK hook replay tracing examples
    browser-use/          # browser-use agents: 27 scenarios mirroring browser-use's examples, live trace checks
    playwright/           # Playwright for Python: 14 scenarios, every Playwright call as a span, live trace checks
    skyvern/              # Skyvern browser agents (local mode): 8 scenarios, live trace checks
    stagehand/            # Stagehand v4 (Python) on local Chrome: 15 scenarios, live trace checks
  gateway/
    model-testing/        # Platform Live model availability + separate streaming performance benchmark
    google-genai/         # Google Gemini SDK example
  dev-tools/
    claude-code/          # Claude Code tracing hook
    cursor/               # Cursor IDE tracing hook

typescript/
  tracing/
    respan-tracing-sdk/   # Core @respan/tracing SDK examples (basic, advanced, span management, multi-provider)
      nextjs-openai/      # Next.js + OpenAI with @respan/tracing directly
    claude-agent-sdk/     # Claude Agent SDK with Respan tracing
    eve/                  # Eve agent framework with Respan tracing
    vercel-tracing/       # Vercel AI SDK + Next.js with @respan/exporter-vercel
    mastra/               # Mastra framework with @respan/exporter-vercel
    playwright/           # Playwright (Node): 14 scenarios, every Playwright call as a span, live trace checks
    puppeteer/            # Puppeteer: 15 scenarios, every Puppeteer call as a span, live trace checks
    stagehand/            # Stagehand v4 (TypeScript) on local Chrome: 15 scenarios, live trace checks
  gateway/
    google-genai/         # Google Gemini SDK example

fullstack/
  vercel-ai-fastapi/      # Next.js frontend + FastAPI backend with Respan tracing
  textbook-tutor/         # RAG study tutor: FastAPI + Chroma + LlamaIndex, gateway
                          # logging with no SDK, and experiments grading retrieval
                          # and generation over a fixed question set

platform/
  demo-setup-python/      # Python scripts for demo account setup (logging, datasets, evaluators, prompts)
  demo-setup-typescript/  # TypeScript scripts for demo account setup
  experiments/            # Experiment workflow notebooks
  multi-modal-evals/      # Multi-modal tool evaluation workflows
```

## Getting Started

1. Clone this repository
2. Navigate to the example you want to run
3. Follow the README in each directory for setup instructions

For availability checks of models listed under Models > Live on the platform, use the
[model availability checker](python/gateway/model-testing/README.md). It discovers
models dynamically, calls them with `RESPAN_API_KEY`, and records each result in
the same format.

For repeatable TTFT and throughput measurements, use the separate
[performance benchmark](python/gateway/model-testing/BENCHMARK.md), which defaults
to Prism's DeepSeek V4 Flash and V4.1 Flash models.

## Documentation

- [Respan Docs](https://www.respan.ai/docs) - Full documentation
- [Python Tracing SDK](https://www.respan.ai/docs/sdks/python/tracing/quickstart) - Python SDK quickstart
- [TypeScript Tracing SDK](https://www.respan.ai/docs/sdks/typescript/tracing/quickstart) - TypeScript SDK quickstart
- [Integrations](https://www.respan.ai/docs/integrations/overview) - Integration guides
