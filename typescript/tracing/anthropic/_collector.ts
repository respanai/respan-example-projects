import { createServer } from "node:http";
import { appendFile } from "node:fs/promises";
import type { AddressInfo } from "node:net";
export async function localCollector() {
  const payloads: any[] = [];
  const server = createServer(async (req, res) => {
    let body = "";
    for await (const chunk of req) body += chunk;
    payloads.push(JSON.parse(body));
    res.writeHead(200, { "content-type": "application/json" });
    res.end("{}");
  });
  await new Promise<void>((r) => server.listen(0, "127.0.0.1", r));
  return {
    url: `http://127.0.0.1:${(server.address() as AddressInfo).port}`,
    async close(caseId: string, runId: string) {
      server.closeAllConnections();
      await new Promise<void>((r) => server.close(() => r()));
      const spans = payloads.flatMap((p) =>
        (p.resourceSpans ?? []).flatMap((r: any) =>
          (r.scopeSpans ?? []).flatMap((s: any) => s.spans ?? []),
        ),
      );
      if (!spans.length) throw Error("No local exported spans");
      if (JSON.stringify(payloads).includes("respan.internal."))
        throw Error("Internal exporter hints survived");
      if (process.env.RESPAN_EXAMPLE_CAPTURE)
        await appendFile(
          process.env.RESPAN_EXAMPLE_CAPTURE,
          JSON.stringify({ runId, caseId, payloads }) + "\n",
        );
      console.log(
        JSON.stringify({
          caseId,
          runId,
          localExport: {
            spans: spans.length,
            ids: spans.map((s: any) => ({
              name: s.name,
              traceId: s.traceId,
              spanId: s.spanId,
              parentSpanId: s.parentSpanId,
            })),
          },
        }),
      );
    },
  };
}
