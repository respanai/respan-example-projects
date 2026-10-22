import { printResult, runExaExample } from "./_shared.js";

const example = "agent-research-tools";
const result = await runExaExample({
  example,
  fn: async ({ client, mode }) => {
    const tool = client.tools.webSearch({ numResults: 1 });
    const toolOutput = await tool.run({ query: "latest retrieval observability patterns" });
    const agent = await client.agent.runs.createAndWait(
      { query: "Create a one-line brief about retrieval observability." },
      { pollInterval: 50, timeoutMs: 120_000 },
    );

    let researchStatus = "skipped-live-deprecated";
    let researchOutput: unknown;
    if (mode === "loopback") {
      const research = await client.research.create({
        instructions: "Create a deterministic research brief.",
        model: "exa-research-fast",
      });
      const completed = await client.research.pollUntilFinished(research.researchId, {
        pollInterval: 50,
        timeoutMs: 10_000,
      });
      researchStatus = completed.status;
      researchOutput =
        completed.status === "completed"
          ? completed.output
          : { status: completed.status, response: completed };
    }
    return {
      mode,
      toolOutput,
      agentStatus: agent.status,
      agentOutput: agent.output,
      researchStatus,
      researchOutput,
    };
  },
});
printResult(example, result.mode, result);
