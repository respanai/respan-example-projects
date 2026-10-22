import {
  createAgent,
  logExampleResult,
  resultText,
  runStrandsExample,
} from "./_shared.js";

const workflowName = "Strands Agents TS Streaming.workflow";
const result = await runStrandsExample({
  appName: "strands-agents-typescript-examples",
  workflowName,
  fn: async () => {
    const agent = createAgent("streaming");
    const stream = agent.stream(
      "Stream a short response with chunked model output.",
    );
    let eventCount = 0;
    let finalResult;
    while (true) {
      const next = await stream.next();
      if (next.done) {
        finalResult = next.value;
        break;
      }
      eventCount += 1;
    }
    return { finalResult, eventCount };
  },
});

logExampleResult(workflowName, {
  output: resultText(result.finalResult),
  eventCount: result.eventCount,
  stopReason: result.finalResult.stopReason,
});
