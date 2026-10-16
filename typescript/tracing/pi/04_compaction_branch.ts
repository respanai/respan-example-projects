import { finish, isDirect } from "./_shared.ts";
import { assert, scenario, byType } from "./_shared.ts";
export async function main() {
  const history = Array.from({ length: 75 }, (_, index) => ({
    role: "user",
    content: `history ${index} ` + "context ".repeat(80),
    timestamp: index + 1,
  }));
  await scenario(
    "manual-compaction",
    {
      extension: true,
      history,
      responses: [
        { text: "before summary" },
        { text: "native compaction summary" },
      ],
    },
    {},
    async (fixture, spans) => {
      await fixture.session.prompt("compact this context");
      const result = await fixture.session.compact();
      assert.equal(
        JSON.parse(
          byType(spans, "task")[0].attributes["traceloop.entity.output"],
        ).summary,
        result.summary,
      );
    },
  );
  await scenario(
    "branch-summary",
    {
      extension: true,
      responses: [
        { text: "first branch" },
        { text: "second branch" },
        { text: "native branch summary" },
        { text: "resumed branch" },
      ],
    },
    { traceScope: "session" },
    async (fixture, spans) => {
      await fixture.session.prompt("first branch");
      await fixture.session.prompt("second branch");
      const target = fixture.session.getUserMessagesForForking()[0].entryId;
      const result = await fixture.session.navigateTree(target, {
        summarize: true,
      });
      assert.equal(result.cancelled, false);
      assert.ok(
        byType(spans, "task").some((span) => span.name === "pi.branch_summary"),
      );
      await fixture.session.prompt("resume branch");
      assert.equal(
        new Set(spans.map((span) => span.spanContext().traceId)).size,
        1,
      );
    },
  );
}

if (isDirect(import.meta.url)) {
  try {
    await main();
  } finally {
    await finish();
  }
}
