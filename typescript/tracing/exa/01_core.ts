import { printResult, runExaExample } from "./_shared.js";

const example = "core";
const result = await runExaExample({
  example,
  fn: async ({ client, mode }) => {
    const search = await client.search("recent retrieval instrumentation developments", {
      type: "auto",
      numResults: 1,
      contents: { highlights: true },
    });
    const contents = await client.getContents(["https://example.com/article"], {
      text: { maxCharacters: 1000 },
    });
    const answer = await client.answer("What does the loopback source say?", {
      systemPrompt: "Answer concisely and cite the source.",
    });
    return {
      mode,
      searchTitle: search.results[0]?.title,
      contentsText: contents.results[0]?.text,
      answer: answer.answer,
    };
  },
});
printResult(example, result.mode, result);
