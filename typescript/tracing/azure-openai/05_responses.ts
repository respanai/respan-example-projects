import {
  createAzureClient,
  createRespan,
  runWithExampleTrace,
  logExampleResult,
} from "./_shared.js";
const workflowName = "TypeScript Azure OpenAI Responses Example";
const respan = await createRespan("typescript-azure-openai-responses-example");
await respan.initialize();
try {
  const result = await runWithExampleTrace(respan, workflowName, async () => {
    const client = createAzureClient(
      process.env.AZURE_OPENAI_RESPONSES_DEPLOYMENT || "responses-deployment",
    );
    const parsed = await client.responses.parse({
      model:
        process.env.AZURE_OPENAI_RESPONSES_DEPLOYMENT || "responses-deployment",
      input: [
        { role: "user", content: [{ type: "input_text", text: "Say hello." }] },
      ],
      instructions: "",
    });
    const stream = client.responses.stream({
      model:
        process.env.AZURE_OPENAI_RESPONSES_DEPLOYMENT || "responses-deployment",
      input: "Say hello.",
    });
    const final = await stream.finalResponse();
    return { parsedText: parsed.output_text, streamedText: final.output_text };
  });
  logExampleResult(workflowName, result);
} finally {
  await respan.shutdown();
}
