import { z } from "zod";
import { zodResponseFormat } from "writer-sdk/helpers/zod";
import {
  createRespan,
  createWriterClient,
  DEFAULT_CHAT_MODEL,
  logExampleResult,
  runWithWriterWorkflow,
  shutdownRespan,
  withTimeout,
} from "./_shared.js";

const workflowName = "writer.structured_output.workflow";
const respan = createRespan();
const writer = createWriterClient();

const responseSchema = z.object({
  title: z.string(),
  priority: z.enum(["low", "medium", "high"]),
  tags: z.array(z.string()),
});

try {
  const completion = await withTimeout(
    runWithWriterWorkflow(respan, workflowName, async () => {
      return await writer.chat.parse({
        model: DEFAULT_CHAT_MODEL,
        messages: [
          {
            role: "user",
            content: "Return a JSON task summary for Writer tracing.",
          },
        ],
        response_format: zodResponseFormat(
          responseSchema,
          "writer_trace_summary",
        ),
      });
    }),
    workflowName,
  );

  logExampleResult(workflowName, {
    expected: "one chat span with response_format metadata",
    actual: completion.choices[0]?.message?.parsed,
  });
} finally {
  await shutdownRespan(respan);
}
