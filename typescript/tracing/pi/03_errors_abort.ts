import { finish, isDirect } from "./_shared.ts";
import { assert, scenario, byType } from "./_shared.ts";
export async function main() {
  const error = await scenario("native-error", {
    responses: [{ status: 400, error: "controlled native error" }],
  });
  assert.equal(byType(error.spans, "chat")[0].status.code, 2);
  await scenario(
    "native-abort",
    { responses: [{ text: "partial", hold: true }] },
    {},
    async (fixture, spans) => {
      const pending = fixture.session.prompt("abort controlled request");
      await new Promise<void>((resolve) => {
        const unsubscribe = fixture.session.subscribe((event: any) => {
          if (event.type === "message_update") {
            unsubscribe();
            resolve();
          }
        });
      });
      await fixture.session.abort();
      await pending;
      assert.equal(byType(spans, "chat")[0].status.code, 2);
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
