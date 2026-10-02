import assert from "node:assert/strict";
import { randomUUID } from "node:crypto";
import { createServer } from "node:http";
import { createRequire } from "node:module";
import protobuf from "protobufjs";

process.env.RESPAN_SPAN_NAME_STYLE = "semantic";

const require = createRequire(import.meta.url);
const n8nPackage = require("n8n/package.json");
assert.equal(n8nPackage.version, "2.37.7", "the real-native smoke is pinned to n8n 2.37.7");

// These are n8n's actual compiled 2.37.7 OTel service and span emitter. The
// instrumentation itself does not patch these private modules: its preload
// still hooks only the public @opentelemetry/sdk-node package they require.
const { OtelService } = require("n8n/dist/modules/otel/otel.service.js");
const { ExecutionLevelTracer } = require(
  "n8n/dist/modules/otel/execution-level-tracer.js",
);

const configuredEndpointValue = process.env.N8N_SMOKE_OTLP_ENDPOINT?.trim().replace(/\/+$/, "");
const configuredEndpoint = configuredEndpointValue || undefined;
const capturedRequests = [];
const collector = configuredEndpoint ? undefined : await startLoopbackCollector(capturedRequests);
const collectorAddress = collector?.address();
assert.ok(
  configuredEndpoint || (collectorAddress && typeof collectorAddress !== "string"),
  "loopback collector failed to bind",
);

const exporterEndpoint =
  configuredEndpoint ?? `http://127.0.0.1:${collectorAddress.port}`;
const exporterTracingPath =
  process.env.N8N_SMOKE_OTLP_PATH ?? (configuredEndpoint ? "/v2/traces" : "/v1/traces");
const exporterHeaders = process.env.N8N_SMOKE_OTLP_HEADERS ?? "";
const runId = process.env.RESPAN_EXAMPLE_RUN_ID ?? `n8n-${Date.now()}`;
const workflowName = `respan-n8n-native-${runId}`;
const executionId = `execution-${randomUUID()}`;
const workflowId = randomUUID();
const node = {
  id: randomUUID(),
  name: "Prepare deterministic output",
  type: "n8n-nodes-base.set",
  typeVersion: 3.4,
};
const failedWorkflowName = `${workflowName}-failure`;
const failedExecutionId = `execution-failure-${randomUUID()}`;
const failedWorkflowId = randomUUID();
const failedNode = {
  id: randomUUID(),
  name: "Fail deterministically",
  type: "n8n-nodes-base.stopAndError",
  typeVersion: 1,
};
const logger = {
  debug() {},
  info() {},
  warn() {},
  error() {},
};
const settings = {
  exporterEndpoint,
  exporterTracingPath,
  exporterHeaders,
  exporterServiceName: "n8n",
  tracesSampleRate: 1,
  injectOutbound: false,
};
const settingsService = { getSettings: () => settings };
const service = new OtelService(
  settingsService,
  { instanceId: "respan-n8n-native-smoke", instanceType: "main" },
  logger,
  {},
);

let serviceStarted = false;
let emittedTraceId;
let emittedFailureTraceId;
try {
  // startSdk() is the real method n8n's public OTel lifecycle calls after it
  // loads settings. Calling it directly avoids booting unrelated DB/UI/task-
  // runner services while preserving n8n's exact NodeSDK/exporter construction.
  const nativeExporterUrl = service.startSdk(settings);
  serviceStarted = true;
  assert.equal(nativeExporterUrl, `${exporterEndpoint}${exporterTracingPath}`);

  // Construct this after the provider starts because n8n intentionally caches
  // its tracer in the ExecutionLevelTracer constructor.
  const tracer = new ExecutionLevelTracer(settingsService, logger);
  const tracingContext = tracer.startWorkflow({
    executionId,
    workflow: {
      id: workflowId,
      name: workflowName,
      versionId: randomUUID(),
      nodeCount: 1,
      customAttributes: { fixture: "real-native-service" },
    },
    project: {
      id: "respan-n8n-smoke-project",
      customAttributes: { run_id: runId },
    },
  });
  emittedTraceId = traceIdFromTraceparent(tracingContext?.traceparent);
  tracer.startNode({ executionId, node });
  tracer.endNode({
    executionId,
    node,
    inputItemCount: 1,
    outputItemCount: 1,
    customAttributes: { fixture: "real-native-service" },
  });
  tracer.endWorkflow({
    executionId,
    mode: "manual",
    status: "success",
    isRetry: false,
  });

  const failureContext = tracer.startWorkflow({
    executionId: failedExecutionId,
    workflow: {
      id: failedWorkflowId,
      name: failedWorkflowName,
      versionId: randomUUID(),
      nodeCount: 1,
      customAttributes: { fixture: "real-native-service-failure" },
    },
    project: {
      id: "respan-n8n-smoke-project",
      customAttributes: { run_id: runId },
    },
  });
  emittedFailureTraceId = traceIdFromTraceparent(failureContext?.traceparent);
  tracer.startNode({ executionId: failedExecutionId, node: failedNode });
  const nodeFailure = {
    message: "deterministic n8n node failure",
    name: "NodeOperationError",
    description: "NodeOperationError",
    constructor: { name: "NodeOperationError" },
    stack: "NodeOperationError: deterministic n8n node failure",
  };
  tracer.endNode({
    executionId: failedExecutionId,
    node: failedNode,
    inputItemCount: 1,
    outputItemCount: 0,
    error: nodeFailure,
    customAttributes: { fixture: "real-native-service-failure" },
  });
  tracer.endWorkflow({
    executionId: failedExecutionId,
    mode: "manual",
    status: "error",
    error: new Error("deterministic n8n workflow failure"),
    isRetry: false,
  });

  // n8n owns the sole provider. Its shutdown flushes the real batch processor
  // and native OTLP/Protobuf exporter before unregistering global OTel state.
  await service.shutdown();
  serviceStarted = false;
} finally {
  if (serviceStarted) await service.shutdown().catch(() => {});
  if (collector) await closeServer(collector);
}

let evidence;
if (collector) {
  evidence = assertLoopbackEvidence(capturedRequests, {
    executionId,
    workflowId,
    workflowName,
    nodeId: node.id,
    failedExecutionId,
    failedWorkflowId,
    failedWorkflowName,
    failedNodeId: failedNode.id,
    tracingPath: exporterTracingPath,
    traceId: emittedTraceId,
    failureTraceId: emittedFailureTraceId,
  });
}

console.log(
  JSON.stringify(
    {
      scenario: "real-n8n-2.37.7-native-otel-service",
      n8n_version: n8nPackage.version,
      run_id: runId,
      target: collector ? "loopback" : "configured-otlp-endpoint",
      workflow_name: workflowName,
      trace_id: emittedTraceId,
      failure_workflow_name: failedWorkflowName,
      failure_trace_id: emittedFailureTraceId,
      ...evidence,
    },
    null,
    2,
  ),
);

async function startLoopbackCollector(requests) {
  const server = createServer((request, response) => {
    const chunks = [];
    request.on("data", (chunk) => chunks.push(chunk));
    request.on("end", () => {
      requests.push({
        method: request.method,
        url: request.url,
        contentType: request.headers["content-type"],
        body: Buffer.concat(chunks),
      });
      response.writeHead(200, { "content-type": "application/x-protobuf" });
      response.end();
    });
  });
  await new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", resolve);
  });
  return server;
}

async function closeServer(server) {
  if (!server.listening) return;
  await new Promise((resolve, reject) => {
    server.close((error) => (error ? reject(error) : resolve()));
  });
}

function assertLoopbackEvidence(requests, expected) {
  assert.ok(requests.length > 0, "n8n's native exporter sent no OTLP request");
  for (const request of requests) {
    assert.equal(request.method, "POST");
    assert.equal(request.url, expected.tracingPath);
    assert.match(request.contentType ?? "", /application\/x-protobuf/);
  }

  const decoded = requests.flatMap((request) => decodeTraceRequest(request.body));
  const spans = decoded.flatMap((resourceSpans) =>
    resourceSpans.scopeSpans.flatMap((scopeSpans) => scopeSpans.spans),
  );
  assert.deepEqual(
    spans.map((span) => span.name).sort(),
    ["task", "task", "workflow", "workflow"],
  );

  const workflow = spans.find(
    (span) => attributesObject(span.attributes)["traceloop.entity.name"] === expected.workflowName,
  );
  const failedWorkflow = spans.find(
    (span) =>
      attributesObject(span.attributes)["traceloop.entity.name"] === expected.failedWorkflowName,
  );
  const task = spans.find(
    (span) => attributesObject(span.attributes)["traceloop.entity.name"] === "Prepare deterministic output",
  );
  const failedTask = spans.find(
    (span) => attributesObject(span.attributes)["traceloop.entity.name"] === "Fail deterministically",
  );
  assert.ok(workflow && task && failedWorkflow && failedTask);
  assert.equal(hex(task.traceId), hex(workflow.traceId));
  assert.equal(hex(workflow.traceId), expected.traceId);
  assert.equal(hex(task.parentSpanId), hex(workflow.spanId));
  assert.equal(hex(failedTask.traceId), hex(failedWorkflow.traceId));
  assert.equal(hex(failedWorkflow.traceId), expected.failureTraceId);
  assert.equal(hex(failedTask.parentSpanId), hex(failedWorkflow.spanId));
  assert.equal(workflow.status?.code, 1);
  assert.equal(task.status?.code, 1);
  assert.equal(failedWorkflow.status?.code, 2);
  assert.equal(failedTask.status?.code, 2);

  const workflowAttrs = attributesObject(workflow.attributes);
  const taskAttrs = attributesObject(task.attributes);
  const failedWorkflowAttrs = attributesObject(failedWorkflow.attributes);
  const failedTaskAttrs = attributesObject(failedTask.attributes);
  assert.equal(workflowAttrs["respan.entity.log_type"], "workflow");
  assert.equal(workflowAttrs["traceloop.entity.name"], expected.workflowName);
  assert.equal(workflowAttrs.status_code, 200);
  assert.equal(taskAttrs["respan.entity.log_type"], "task");
  assert.equal(taskAttrs["traceloop.entity.name"], "Prepare deterministic output");
  assert.equal(taskAttrs.status_code, 200);
  assert.equal(failedWorkflowAttrs.status_code, 500);
  assert.equal(failedTaskAttrs.status_code, 500);
  assert.equal(failedWorkflowAttrs["error.message"], "deterministic n8n workflow failure");
  assert.equal(failedTaskAttrs["error.message"], "deterministic n8n node failure");
  assert.equal(Object.keys(workflowAttrs).some((key) => key.startsWith("n8n.")), false);
  assert.equal(Object.keys(taskAttrs).some((key) => key.startsWith("n8n.")), false);
  assert.equal(
    Object.keys(failedWorkflowAttrs).some((key) => key.startsWith("n8n.")),
    false,
  );
  assert.equal(Object.keys(failedTaskAttrs).some((key) => key.startsWith("n8n.")), false);

  const workflowMetadata = JSON.parse(workflowAttrs["respan.metadata"]);
  const taskMetadata = JSON.parse(taskAttrs["respan.metadata"]);
  const failedWorkflowMetadata = JSON.parse(failedWorkflowAttrs["respan.metadata"]);
  const failedTaskMetadata = JSON.parse(failedTaskAttrs["respan.metadata"]);
  assert.equal(workflowMetadata.n8n["workflow.id"], expected.workflowId);
  assert.equal(workflowMetadata.n8n["workflow.name"], expected.workflowName);
  assert.equal(workflowMetadata.n8n["execution.id"], expected.executionId);
  assert.equal(workflowMetadata.n8n["execution.status"], "success");
  assert.equal(taskMetadata.n8n["node.id"], expected.nodeId);
  assert.equal(taskMetadata.n8n["node.type"], "n8n-nodes-base.set");
  assert.equal(failedWorkflowMetadata.n8n["workflow.id"], expected.failedWorkflowId);
  assert.equal(failedWorkflowMetadata.n8n["execution.id"], expected.failedExecutionId);
  assert.equal(failedWorkflowMetadata.n8n["execution.status"], "error");
  assert.equal(failedWorkflowMetadata.n8n["execution.error_type"], "Error");
  assert.equal(failedTaskMetadata.n8n["node.id"], expected.failedNodeId);
  assert.equal(failedTaskMetadata.n8n["node.type"], "n8n-nodes-base.stopAndError");
  assert.ok(failedWorkflow.events.some((event) => event.name === "exception"));
  assert.ok(failedTask.events.some((event) => event.name === "exception"));

  const resourceAttrs = decoded.map((item) => attributesObject(item.resource?.attributes));
  assert.ok(
    resourceAttrs.some(
      (attrs) =>
        attrs["service.version"] === "2.37.7" &&
        attrs["n8n.instance.id"] === "respan-n8n-native-smoke" &&
        attrs["n8n.instance.role"] === "main",
    ),
  );

  return {
    span_names: spans.map((span) => span.name).sort(),
    trace_id: hex(workflow.traceId),
    failure_trace_id: hex(failedWorkflow.traceId),
    hierarchy: {
      workflow: hex(workflow.spanId),
      task_parent: hex(task.parentSpanId),
      failure_workflow: hex(failedWorkflow.spanId),
      failure_task_parent: hex(failedTask.parentSpanId),
    },
  };
}

function decodeTraceRequest(body) {
  const root = protobuf.parse(otelTraceSchema()).root;
  const requestType = root.lookupType("ExportTraceServiceRequest");
  return requestType.decode(body).resourceSpans;
}

function attributesObject(attributes = []) {
  return Object.fromEntries(attributes.map(({ key, value }) => [key, anyValue(value)]));
}

function anyValue(value) {
  if (Object.hasOwn(value, "stringValue")) return value.stringValue;
  if (Object.hasOwn(value, "boolValue")) return value.boolValue;
  if (Object.hasOwn(value, "intValue")) return Number(value.intValue);
  if (Object.hasOwn(value, "doubleValue")) return value.doubleValue;
  if (Object.hasOwn(value, "bytesValue")) return Buffer.from(value.bytesValue);
  if (Object.hasOwn(value, "arrayValue")) return value.arrayValue.values.map(anyValue);
  if (Object.hasOwn(value, "kvlistValue")) {
    return attributesObject(value.kvlistValue.values);
  }
  return undefined;
}

function hex(value) {
  return Buffer.from(value ?? []).toString("hex");
}

function traceIdFromTraceparent(traceparent) {
  const match = /^00-([0-9a-f]{32})-[0-9a-f]{16}-[0-9a-f]{2}$/i.exec(traceparent ?? "");
  assert.ok(match, "n8n's real ExecutionLevelTracer returned no valid traceparent");
  return match[1].toLowerCase();
}

function otelTraceSchema() {
  return `
  syntax = "proto3";
  message ExportTraceServiceRequest { repeated ResourceSpans resourceSpans = 1; }
  message ResourceSpans {
    Resource resource = 1;
    repeated ScopeSpans scopeSpans = 2;
    string schemaUrl = 3;
  }
  message Resource { repeated KeyValue attributes = 1; uint32 droppedAttributesCount = 2; }
  message ScopeSpans {
    InstrumentationScope scope = 1;
    repeated Span spans = 2;
    string schemaUrl = 3;
  }
  message InstrumentationScope {
    string name = 1;
    string version = 2;
    repeated KeyValue attributes = 3;
    uint32 droppedAttributesCount = 4;
  }
  message Span {
    bytes traceId = 1;
    bytes spanId = 2;
    string traceState = 3;
    bytes parentSpanId = 4;
    string name = 5;
    int32 kind = 6;
    fixed64 startTimeUnixNano = 7;
    fixed64 endTimeUnixNano = 8;
    repeated KeyValue attributes = 9;
    uint32 droppedAttributesCount = 10;
    repeated Event events = 11;
    SpanStatus status = 15;
    fixed32 flags = 16;
  }
  message Event {
    fixed64 timeUnixNano = 1;
    string name = 2;
    repeated KeyValue attributes = 3;
    uint32 droppedAttributesCount = 4;
  }
  message SpanStatus { string message = 2; int32 code = 3; }
  message KeyValue { string key = 1; AnyValue value = 2; }
  message AnyValue {
    oneof value {
      string stringValue = 1;
      bool boolValue = 2;
      int64 intValue = 3;
      double doubleValue = 4;
      ArrayValue arrayValue = 5;
      KeyValueList kvlistValue = 6;
      bytes bytesValue = 7;
    }
  }
  message ArrayValue { repeated AnyValue values = 1; }
  message KeyValueList { repeated KeyValue values = 1; }
`;
}
