import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { context, trace } from "@opentelemetry/api";
import { OTLPTraceExporter } from "@opentelemetry/exporter-trace-otlp-proto";
import { resourceFromAttributes } from "@opentelemetry/resources";
import { InMemorySpanExporter } from "@opentelemetry/sdk-trace-base";

// Resolve sdk-node only after the --import preload has activated its module
// hook. This is also how n8n loads its compiled OTel service at runtime.
const require = createRequire(import.meta.url);
const { NodeSDK } = require("@opentelemetry/sdk-node");
const n8nAgentsPackage = require("@n8n/agents/package.json");
const aiSdkOtelPackage = require("@ai-sdk/otel/package.json");
const { LegacyOpenTelemetry } = await import("@ai-sdk/otel");
assert.equal(n8nAgentsPackage.version, "0.22.2");
assert.equal(aiSdkOtelPackage.version, "1.0.87");

class TeeSpanExporter {
  constructor(...exporters) {
    this.exporters = exporters;
  }

  export(spans, callback) {
    let remaining = this.exporters.length;
    let finalResult = { code: 0 };
    for (const exporter of this.exporters) {
      try {
        exporter.export(spans, (result) => {
          if (result.code !== 0) finalResult = result;
          remaining -= 1;
          if (remaining === 0) callback(finalResult);
        });
      } catch (error) {
        finalResult = { code: 1, error };
        remaining -= 1;
        if (remaining === 0) callback(finalResult);
      }
    }
  }

  async forceFlush() {
    await Promise.all(
      this.exporters.map((exporter) => exporter.forceFlush?.() ?? Promise.resolve()),
    );
  }

  async shutdown() {
    await Promise.all(this.exporters.map((exporter) => exporter.shutdown()));
  }
}

const configuredEndpoint = process.env.N8N_SMOKE_OTLP_ENDPOINT?.trim().replace(/\/+$/, "");
const configuredPath = process.env.N8N_SMOKE_OTLP_PATH?.trim() || "/v2/traces";
const configuredHeaders = parseOtlpHeaders(process.env.N8N_SMOKE_OTLP_HEADERS);
const runId = process.env.RESPAN_EXAMPLE_RUN_ID ?? `n8n-agent-${Date.now()}`;
const workflowName = `n8n deterministic native spans ${runId}`;
const inMemoryExporter = new InMemorySpanExporter();
const wireExporter = configuredEndpoint
  ? new OTLPTraceExporter({
      url: `${configuredEndpoint}${configuredPath.startsWith("/") ? configuredPath : `/${configuredPath}`}`,
      headers: configuredHeaders,
    })
  : undefined;
const exporter = wireExporter
  ? new TeeSpanExporter(inMemoryExporter, wireExporter)
  : inMemoryExporter;
const sdk = new NodeSDK({
  resource: resourceFromAttributes({
    "service.name": "n8n",
    "service.version": "2.37.7",
    "n8n.instance.id": "deterministic-instance",
    "n8n.instance.role": "main",
  }),
  traceExporter: exporter,
});

sdk.start();

const workflowTracer = trace.getTracer("n8n-workflow");
const agentTracer = trace.getTracer("@n8n/agents");
const workflow = workflowTracer.startSpan("workflow.execute", {
  attributes: {
    "n8n.workflow.id": "deterministic-workflow",
    "n8n.workflow.name": workflowName,
    "n8n.workflow.version_id": "version-1",
    "n8n.workflow.node_count": 1,
    "n8n.execution.id": "deterministic-execution",
    "n8n.execution.mode": "manual",
    "n8n.project.custom.run_id": runId,
  },
});
const workflowContext = trace.setSpan(context.active(), workflow);
const node = workflowTracer.startSpan(
  "node.execute",
  {
    attributes: {
      "n8n.node.id": "agent-node",
      "n8n.node.name": "Run support agent",
      "n8n.node.type": "@n8n/n8n-nodes-langchain.agent",
      "n8n.node.type_version": 3,
      "n8n.node.items.input": 1,
      "n8n.node.items.output": 1,
    },
  },
  workflowContext,
);
const nodeContext = trace.setSpan(workflowContext, node);
const agent = agentTracer.startSpan(
  "support-agent.generate",
  {
    attributes: {
      "gen_ai.operation.name": "invoke_agent",
      "gen_ai.agent.name": "support-agent",
      "gen_ai.request.model": "openai/gpt-4o-mini",
      "gen_ai.conversation.id": "deterministic-thread",
      "gen_ai.prompt": JSON.stringify({
        agent: "support-agent",
        tool_count: 1,
        tools: [{ name: "lookup_customer", type: "local" }],
      }),
      agent_id: "deterministic-agent",
      project_id: "deterministic-project",
      thread_id: "deterministic-thread",
      source: "workflow",
      execution_id: "deterministic-execution",
      workflow_id: "deterministic-workflow",
      node_id: "agent-node",
    },
  },
  nodeContext,
);
const agentContext = trace.setSpan(nodeContext, agent);
const callId = "call-deterministic-agent-turn";
const toolCall = {
  type: "tool-call",
  toolCallId: "call-deterministic",
  toolName: "lookup_customer",
  input: { customer_id: "customer-7" },
};
const usage = {
  inputTokens: 12,
  outputTokens: 5,
  totalTokens: 17,
  inputTokenDetails: {
    noCacheTokens: 9,
    cacheReadTokens: 3,
    cacheWriteTokens: 0,
  },
  outputTokenDetails: { textTokens: 5, reasoningTokens: 0 },
};
const response = {
  id: "response-deterministic",
  modelId: "gpt-4o-mini-2026-08-01",
  timestamp: new Date("2026-09-01T00:00:00.000Z"),
};
const aiSdkTelemetry = new LegacyOpenTelemetry({ tracer: agentTracer });

context.with(agentContext, () =>
  aiSdkTelemetry.onStart({
    operationId: "ai.generateText",
    callId,
    functionId: "support-agent",
    recordInputs: true,
    recordOutputs: true,
    provider: "openai.chat",
    modelId: "gpt-4o-mini",
    headers: { authorization: "Bearer deterministic-secret-must-not-export" },
    instructions: "Answer with deterministic fixture data.",
    messages: [{ role: "user", content: "Look up customer 7" }],
    maxOutputTokens: 64,
    temperature: 0,
    maxRetries: 0,
  }),
);
aiSdkTelemetry.onStepStart({
  callId,
  provider: "openai.chat",
  modelId: "gpt-4o-mini",
  promptMessages: [
    {
      role: "user",
      content: [{ type: "text", text: "Look up customer 7" }],
    },
  ],
  stepTools: [
    {
      type: "function",
      name: "lookup_customer",
      description: "Look up a customer",
      inputSchema: {
        type: "object",
        properties: { customer_id: { type: "string" } },
      },
    },
  ],
  stepToolChoice: { type: "auto" },
});
aiSdkTelemetry.onToolExecutionStart({ callId, toolCall });
const toolResult = await aiSdkTelemetry.executeTool({
  callId,
  toolCallId: toolCall.toolCallId,
  execute: () =>
    agentTracer.startActiveSpan(
      "execute_tool lookup_customer",
      {
        attributes: {
          "gen_ai.operation.name": "execute_tool",
          "gen_ai.agent.name": "support-agent",
          "gen_ai.tool.name": "lookup_customer",
          "gen_ai.tool.call.id": toolCall.toolCallId,
          "gen_ai.tool.call.arguments": JSON.stringify(toolCall.input),
          "ai.toolCall.name": "lookup_customer",
          "ai.toolCall.id": toolCall.toolCallId,
          "ai.toolCall.args": JSON.stringify(toolCall.input),
        },
      },
      async (span) => {
        const result = { tier: "enterprise" };
        const serialized = JSON.stringify(result);
        span.setAttributes({
          "gen_ai.tool.call.result": serialized,
          "ai.toolCall.result": serialized,
        });
        span.end();
        return result;
      },
    ),
});
aiSdkTelemetry.onToolExecutionEnd({
  callId,
  toolCall,
  toolOutput: { type: "tool-result", output: toolResult },
});
aiSdkTelemetry.onStepEnd({
  callId,
  finishReason: "tool-calls",
  text: "Customer 7 is enterprise.",
  reasoning: [],
  toolCalls: [toolCall],
  files: [],
  response,
  usage,
  performance: {
    timeToFirstOutputMs: 8,
    responseTimeMs: 19,
    effectiveOutputTokensPerSecond: 263.16,
  },
});
aiSdkTelemetry.onEnd({
  operationId: "ai.generateText",
  callId,
  finishReason: "tool-calls",
  text: "Customer 7 is enterprise.",
  reasoning: [],
  toolCalls: [toolCall],
  files: [],
  usage,
  finalStep: { reasoning: [], providerMetadata: undefined },
});

const queryMemory = agentTracer.startSpan(
  "query_memory",
  {
    attributes: {
      "gen_ai.operation.name": "query_memory",
      "gen_ai.agent.name": "support-agent",
      "gen_ai.memory.types": ["session"],
      "gen_ai.memory.owners": ["customer-7"],
      "gen_ai.memory.store.types": ["in_memory"],
      "gen_ai.memory.store.names": ["support-history"],
    },
  },
  agentContext,
);
queryMemory.setAttributes({
  "gen_ai.memory.ids": ["message-1"],
  "gen_ai.memory.operations": ["query_memory"],
  "gen_ai.memory.descriptions": ["conversation history"],
});
queryMemory.end();

const saveMemory = agentTracer.startSpan(
  "save_memory",
  {
    attributes: {
      "gen_ai.operation.name": "save_memory",
      "gen_ai.agent.name": "support-agent",
      "gen_ai.memory.types": ["agent"],
      "gen_ai.memory.owners": ["customer-7"],
      "gen_ai.memory.store.types": ["in_memory"],
      "gen_ai.memory.store.names": ["support-history"],
    },
  },
  agentContext,
);
saveMemory.setAttributes({
  "gen_ai.memory.ids": ["memory-1"],
  "gen_ai.memory.operations": ["created"],
});
saveMemory.end();

agent.end();
node.end();
workflow.setAttributes({
  "n8n.execution.status": "success",
  "n8n.execution.is_retry": false,
});
workflow.end();

// InMemorySpanExporter clears its buffer during shutdown, so inspect after a
// provider flush and shut down only once the deterministic assertions finish.
await sdk._tracerProvider.forceFlush();
const spans = inMemoryExporter.getFinishedSpans();
const names = spans.map((span) => span.name).sort();
assert.deepEqual(names, [
  "agent.support-agent",
  "llm.gpt-4o-mini",
  "task",
  "task",
  "task",
  "tool.lookup_customer",
  "workflow",
]);

const workflowOut = spans.find((span) => span.name === "workflow");
const nodeOut = spans.find(
  (span) => span.attributes["traceloop.entity.name"] === "Run support agent",
);
const agentOut = spans.find((span) => span.name === "agent.support-agent");
const toolOut = spans.find((span) => span.name === "tool.lookup_customer");
const llmOut = spans.find((span) => span.name === "llm.gpt-4o-mini");
const queryMemoryOut = spans.find(
  (span) => span.attributes["traceloop.entity.name"] === "query_memory",
);
const saveMemoryOut = spans.find(
  (span) => span.attributes["traceloop.entity.name"] === "save_memory",
);
assert.ok(workflowOut && nodeOut && agentOut && llmOut && toolOut && queryMemoryOut && saveMemoryOut);
assert.equal(nodeOut.parentSpanContext?.spanId, workflowOut.spanContext().spanId);
assert.equal(agentOut.parentSpanContext?.spanId, nodeOut.spanContext().spanId);
assert.equal(llmOut.parentSpanContext?.spanId, agentOut.spanContext().spanId);
assert.equal(toolOut.parentSpanContext?.spanId, llmOut.spanContext().spanId);
assert.equal(queryMemoryOut.parentSpanContext?.spanId, agentOut.spanContext().spanId);
assert.equal(saveMemoryOut.parentSpanContext?.spanId, agentOut.spanContext().spanId);
assert.equal(llmOut.attributes["gen_ai.prompt.0.role"], "user");
assert.equal(llmOut.attributes["gen_ai.prompt.0.content"], "Look up customer 7");
assert.equal(llmOut.attributes["gen_ai.completion.0.role"], "assistant");
assert.equal(llmOut.attributes["gen_ai.completion.0.content"], "Customer 7 is enterprise.");
assert.equal(llmOut.attributes["gen_ai.usage.input_tokens"], 12);
assert.equal(llmOut.attributes["gen_ai.usage.output_tokens"], 5);
assert.equal(llmOut.attributes["llm.usage.total_tokens"], 17);
assert.equal(llmOut.attributes["llm.usage.cache_read_input_tokens"], 3);
assert.equal(Object.keys(llmOut.attributes).some((key) => key.startsWith("ai.")), false);
assert.equal(
  JSON.stringify(spans.map((span) => span.attributes)).includes(
    "deterministic-secret-must-not-export",
  ),
  false,
);
assert.deepEqual(JSON.parse(toolOut.attributes["traceloop.entity.input"]), {
  name: "lookup_customer",
  arguments: { customer_id: "customer-7" },
});
assert.deepEqual(JSON.parse(toolOut.attributes["traceloop.entity.output"]), {
  tier: "enterprise",
});
assert.deepEqual(JSON.parse(queryMemoryOut.attributes["respan.metadata"]).n8n.memory, {
  types: ["session"],
  owners: ["customer-7"],
  "store.types": ["in_memory"],
  "store.names": ["support-history"],
  ids: ["message-1"],
  operations: ["query_memory"],
  descriptions: ["conversation history"],
  operation: "query_memory",
  agent_name: "support-agent",
});
assert.ok(spans.every((span) => span.attributes.status_code === 200));

console.log(
  JSON.stringify(
    {
      scenario: "deterministic-native-n8n-spans",
      n8n_agents_version: n8nAgentsPackage.version,
      ai_sdk_otel_version: aiSdkOtelPackage.version,
      run_id: runId,
      target: configuredEndpoint ? "configured-otlp-endpoint-and-memory" : "in-memory",
      workflow_name: workflowName,
      span_names: names,
      trace_id: workflowOut.spanContext().traceId,
      hierarchy: {
        workflow: workflowOut.spanContext().spanId,
        node_parent: nodeOut.parentSpanContext?.spanId,
        agent_parent: agentOut.parentSpanContext?.spanId,
        llm_parent: llmOut.parentSpanContext?.spanId,
        tool_parent: toolOut.parentSpanContext?.spanId,
        query_memory_parent: queryMemoryOut.parentSpanContext?.spanId,
        save_memory_parent: saveMemoryOut.parentSpanContext?.spanId,
      },
    },
    null,
    2,
  ),
);

await sdk.shutdown();

function parseOtlpHeaders(value) {
  if (!value?.trim()) return {};
  return Object.fromEntries(
    value.split(",").flatMap((entry) => {
      const separator = entry.indexOf("=");
      if (separator <= 0) return [];
      const key = entry.slice(0, separator).trim();
      const headerValue = entry.slice(separator + 1).trim();
      return key && headerValue ? [[key, headerValue]] : [];
    }),
  );
}
