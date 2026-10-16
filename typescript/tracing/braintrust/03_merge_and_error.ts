import { assert, runScenario, withoutContent } from "./_shared.js";

await runScenario("merge-error-and-privacy", async (logger, openai) =>
  logger.traced(
    async (parent) => {
      const span = parent.startSpan({
        name: "merged-native-task",
        type: "task",
        event: {
          input: { step: "start" },
          metadata: { initial: true },
          tags: ["initial"],
        },
      });
      await logger.flush();
      span.log({
        metadata: { updated: true },
        tags: ["updated"],
        output: { complete: true },
      });
      span.end();
      const error = new Error("Controlled native task failure");
      await assert.rejects(
        parent.traced(
          async () => {
            throw error;
          },
          { name: "native-error", type: "task" },
        ),
        (caught) => caught === error,
      );
      await assert.rejects(
        openai.chat.completions.create({
          model: "fixture-error",
          messages: [{ role: "user", content: "Controlled provider failure" }],
        }),
        (caught: any) => caught.status === 400,
      );
      await parent.traced(
        async (score) =>
          score.log({
            input: { candidate: "fixture" },
            output: 0,
            scores: { correct: 0 },
            expected: null,
          }),
        { name: "native-score", type: "score" },
      );
      await withoutContent(async () =>
        parent.traced(
          async (privateSpan) =>
            privateSpan.log({
              input: "private fixture input",
              output: "private fixture output",
            }),
          { name: "native-private", type: "task" },
        ),
      );
      return {
        mergeUpdates: 2,
        controlledErrors: 2,
        score: 0,
        privateSpan: true,
      };
    },
    { name: "merge-parent", type: "task" },
  ),
);
