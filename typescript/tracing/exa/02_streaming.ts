import { printResult, runExaExample } from "./_shared.js";

const example = "streaming";
const result = await runExaExample({
  example,
  fn: async ({ client, mode }) => {
    let search = "";
    for await (const chunk of client.streamSearch("stream a grounded search", { type: "auto" })) {
      search += chunk.content ?? "";
    }
    let answer = "";
    for await (const chunk of client.streamAnswer("stream an Exa answer")) {
      answer += chunk.content ?? "";
    }
    return { mode, search, answer };
  },
});
printResult(example, result.mode, result);
