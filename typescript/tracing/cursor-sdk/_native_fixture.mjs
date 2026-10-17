import http from "node:http";
import { randomUUID } from "node:crypto";
export async function nativeFixture() {
  const requests = [];
  const runs = new Map();
  let count = 0;
  const server = http.createServer(async (req, res) => {
    let text = "";
    for await (const chunk of req) text += chunk;
    const body = text ? JSON.parse(text) : undefined;
    requests.push({ method: req.method, path: req.url, body });
    const json = (value, status = 200) => {
      res.statusCode = status;
      res.setHeader("content-type", "application/json");
      res.end(JSON.stringify(value));
    };
    if (req.url === "/api/v2/traces") {
      json({});
      return;
    }
    if (req.url === "/auth/exchange_user_api_key") {
      json({ error: { message: "fixture auth bypass" } }, 404);
      return;
    }
    if (req.url === "/v1/models") {
      json({
        items: [{ id: "cursor-fixture-model" }, { id: "cursor-fixture-next" }],
      });
      return;
    }
    if (
      req.method === "POST" &&
      (req.url === "/v1/agents" || req.url.endsWith("/runs"))
    ) {
      const agentId = body.agentId ?? req.url.split("/")[3];
      const id = `run-${randomUUID()}`;
      ++count;
      const run = {
        id,
        agentId,
        requestId: `request-fixture-${count}`,
        status: "RUNNING",
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString(),
        prompt: body.prompt,
      };
      runs.set(id, run);
      json({ agent: { id: agentId }, run });
      return;
    }
    const path = req.url.split("/");
    const run = runs.get(path[5]);
    if (req.method === "GET" && path.length === 4) {
      json({ id: path[3], status: "IDLE" });
      return;
    }
    if (run && req.url.endsWith("/cancel")) {
      run.status = "CANCELLED";
      json({});
      return;
    }
    if (run && req.url.endsWith("/stream")) {
      res.setHeader("content-type", "text/event-stream");
      const send = (name, value, id) =>
        res.write(
          `${id ? "id: " + id + "\n" : ""}event: ${name}\ndata: ${JSON.stringify(value)}\n\n`,
        );
      if (run.prompt.text === "error") {
        send("result", {
          status: "ERROR",
          error: { message: "controlled native error", code: "fixture_error" },
        });
        run.status = "ERROR";
        res.end();
        return;
      }
      const large = run.prompt.text === "large";
      send("thinking", { text: "native thinking" });
      send("tool_call", {
        callId: `tool-${run.id}`,
        name: "lookup_fixture",
        status: "running",
        args: {
          value: false,
          empty: "",
          zero: 0,
          items: large
            ? Array.from({ length: 80 }, (_, i) => ({ i, text: `item-${i}` }))
            : [],
        },
      });
      send("tool_call", {
        callId: `tool-${run.id}`,
        name: "lookup_fixture",
        status: "completed",
        result: {
          value: false,
          empty: "",
          zero: 0,
          items: large ? Array.from({ length: 5001 }, (_, i) => i / 5001) : [],
        },
      });
      send("assistant", { text: "native Cursor answer" });
      send(
        "interaction_update",
        {
          type: "turn-ended",
          usage: {
            inputTokens: 11,
            outputTokens: 7,
            cacheReadTokens: 3,
            cacheWriteTokens: 2,
            reasoningTokens: 4,
          },
        },
        `usage-${run.id}`,
      );
      send("result", {
        status: "FINISHED",
        result: "native Cursor answer",
        durationMs: 42,
      });
      run.status = "FINISHED";
      run.result = "native Cursor answer";
      res.end();
      return;
    }
    if (run && req.method === "GET") {
      json(run);
      return;
    }
    json({}, 404);
  });
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  const baseURL = `http://127.0.0.1:${server.address().port}`;
  const oldURL = process.env.CURSOR_BACKEND_URL;
  process.env.CURSOR_BACKEND_URL = baseURL;
  const originalFetch = globalThis.fetch;
  globalThis.fetch = (url, options) => {
    if (!String(url).startsWith(baseURL))
      throw new Error("Unexpected external Cursor fixture request");
    return originalFetch(url, options);
  };
  return {
    requests,
    runs,
    baseURL,
    options: {
      apiKey: "key-respan-cursor-fixture",
      agentId: "bc-" + randomUUID(),
      cloud: {},
      model: { id: "cursor-fixture-model" },
    },
    async close() {
      globalThis.fetch = originalFetch;
      if (oldURL === undefined) delete process.env.CURSOR_BACKEND_URL;
      else process.env.CURSOR_BACKEND_URL = oldURL;
      server.closeAllConnections();
      await new Promise((resolve) => server.close(resolve));
    },
  };
}

export async function nativeLocalFixture(Cursor, customTools) {
  const { mkdtemp, rm } = await import("node:fs/promises");
  const { tmpdir } = await import("node:os");
  const path = await import("node:path");
  if (!Cursor.JsonlLocalAgentStore) return undefined;
  const root = await mkdtemp(path.join(tmpdir(), "respan-cursor-native-"));
  const previousCatalog = process.env.CURSOR_SDK_LOCAL_MODEL_CATALOG_JSON;
  process.env.CURSOR_SDK_LOCAL_MODEL_CATALOG_JSON = JSON.stringify({
    items: [{ id: "cursor-fixture-model" }],
  });
  const original = Cursor.CursorAgentPlatform.prototype.acquireLocalExecutor;
  Cursor.CursorAgentPlatform.prototype.acquireLocalExecutor = async () => ({
    cacheMiss: false,
    async release() {},
    handle: {
      async run(input, options, listener) {
        const done = Promise.resolve().then(async () => {
          await listener.sendUpdate({
            type: "text-delta",
            text: "native local answer",
          });
          await options.customTools.lookup_fixture.execute(
            { value: 0, empty: "", enabled: false },
            {
              toolCallId: "native-local-call",
              sessionId: "native-child-session",
            },
          );
          await listener.sendUpdate({
            type: "turn-ended",
            usage: {
              inputTokens: 0,
              outputTokens: 0,
              cacheReadTokens: 0,
              cacheWriteTokens: 0,
            },
          });
        });
        return { abort() {}, done };
      },
    },
  });
  return {
    options: {
      apiKey: "key-respan-cursor-fixture",
      model: { id: "cursor-fixture-model" },
      local: {
        cwd: root,
        store: new Cursor.JsonlLocalAgentStore(root),
        customTools,
      },
    },
    async close() {
      Cursor.CursorAgentPlatform.prototype.acquireLocalExecutor = original;
      if (previousCatalog === undefined)
        delete process.env.CURSOR_SDK_LOCAL_MODEL_CATALOG_JSON;
      else process.env.CURSOR_SDK_LOCAL_MODEL_CATALOG_JSON = previousCatalog;
      await rm(root, { recursive: true, force: true });
    },
  };
}
