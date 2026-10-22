import http from "node:http";
import { appendFile } from "node:fs/promises";
import type { AddressInfo } from "node:net";
export async function startLocalCollector() {
  const payloads: any[] = [];
  const server = http.createServer(async (req, res) => {
    let body = "";
    for await (const chunk of req) body += chunk;
    payloads.push(JSON.parse(body));
    res.writeHead(200, { "content-type": "application/json" });
    res.end("{}");
  });
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  return {
    url: `http://127.0.0.1:${(server.address() as AddressInfo).port}`,
    async close(workflowName: string, runId: string) {
      server.closeAllConnections();
      await new Promise<void>((resolve) => server.close(() => resolve()));
      const spans = payloads.flatMap((payload) =>
        (payload.resourceSpans ?? []).flatMap((resource: any) =>
          (resource.scopeSpans ?? []).flatMap(
            (scope: any) => scope.spans ?? [],
          ),
        ),
      );
      if (!spans.length)
        throw new Error("The local collector received no exported spans.");
      if (JSON.stringify(payloads).includes("respan.internal."))
        throw new Error("Internal attributes survived the public exporter.");
      if (process.env.RESPAN_LOCAL_CAPTURE_FILE)
        await appendFile(
          process.env.RESPAN_LOCAL_CAPTURE_FILE,
          JSON.stringify({ workflowName, runId, payloads }) + "\n",
        );
      console.log(
        JSON.stringify({
          workflowName,
          runId,
          localExport: {
            spans: spans.length,
            ids: spans.map((span: any) => ({
              name: span.name,
              traceId: span.traceId,
              spanId: span.spanId,
              parentSpanId: span.parentSpanId,
            })),
          },
        }),
      );
    },
  };
}
