import assert from "node:assert/strict";
import { OpenAIChatModel } from "beeai-framework/adapters/openai/backend/chat";
import { OpenAIEmbeddingModel } from "beeai-framework/adapters/openai/backend/embedding";
import { OpenAIClient } from "beeai-framework/adapters/openai/backend/client";
import { Version } from "beeai-framework";
import { ToolCallingAgent } from "beeai-framework/agents/toolCalling/agent";
import {
  AssistantMessage,
  SystemMessage,
  ToolMessage,
  UserMessage,
} from "beeai-framework/backend/message";
import { CalculatorTool } from "beeai-framework/tools/calculator";
import { DynamicTool, JSONToolOutput } from "beeai-framework/tools/base";
import { UnconstrainedMemory } from "beeai-framework/memory/unconstrainedMemory";
import { z } from "zod";
import {
  BEEAI_EXAMPLE_RUN_ID,
  createBeeAIRespanRuntime,
  runWithBeeAIWorkflow,
} from "./_respan.js";

// These fixtures replace only HTTP fetch. Models, agents, Run objects, schema
// conversion, streaming, tool callbacks and provider parsing remain the SDK's.
function client(handler: (body: Record<string, any>) => unknown): OpenAIClient {
  return new OpenAIClient({
    apiKey: "controlled-provider-key",
    fetch: async (_url, init) => {
      const body = JSON.parse(init?.body as string);
      const value = handler(body);
      return value instanceof Response ? value : Response.json(value);
    },
  });
}
function chat(message: Record<string, unknown>): Record<string, unknown> {
  return {
    id: "controlled-response",
    object: "chat.completion",
    created: 1,
    model: "gpt-4o-mini",
    choices: [
      {
        index: 0,
        message: { role: "assistant", ...message },
        finish_reason: message.tool_calls ? "tool_calls" : "stop",
      },
    ],
    usage: { prompt_tokens: 0, completion_tokens: 0, total_tokens: 0 },
  };
}
const modern = Number(Version.split(".")[2]) >= 14;
const { respan } = await createBeeAIRespanRuntime();
let scenarios = 0;
async function scenario(
  name: string,
  fn: () => Promise<unknown>,
): Promise<void> {
  await runWithBeeAIWorkflow(
    respan,
    `beeai_native_${name}.workflow`,
    { scenario: name, controlled_provider: true },
    fn,
  );
  scenarios++;
  console.log(`Passed: ${name}`);
}
try {
  await scenario("history_schema_calls", async () => {
    const lookup = new DynamicTool({
      name: "lookup",
      description: "Lookup a value",
      inputSchema: z.object({
        count: z.number(),
        enabled: z.boolean(),
        query: z.string(),
      }),
      handler: async () => new JSONToolOutput(false),
    });
    const llm = new OpenAIChatModel(
      "gpt-4o-mini",
      {},
      client(() =>
        chat({
          content: "",
          tool_calls: [
            {
              id: "call-current",
              type: "function",
              function: {
                name: "lookup",
                arguments: '{"count":0,"enabled":false,"query":""}',
              },
            },
          ],
        }),
      ),
    );
    const messages = [
      new SystemMessage("Keep the complete history"),
      new UserMessage("old request"),
      new AssistantMessage({
        type: "tool-call",
        toolCallId: "call-history",
        toolName: "lookup",
        input: { count: 0, enabled: false, query: "" },
        ...(!modern ? { args: { count: 0, enabled: false, query: "" } } : {}),
      }),
      new ToolMessage([
        {
          type: "tool-result",
          toolCallId: "call-history",
          toolName: "lookup",
          output: { type: "json", value: false },
          ...(!modern ? { result: false } : {}),
        },
        {
          type: "tool-result",
          toolCallId: "call-history-two",
          toolName: "lookup",
          output: { type: "json", value: 0 },
          ...(!modern ? { result: 0 } : {}),
        },
      ]),
      ...Array.from({ length: 71 }, (_, i) => new UserMessage(`history-${i}`)),
    ];
    let callbacks = 0;
    const run = llm.create({ messages, tools: [lookup] });
    assert.equal(
      run.observe((emitter) =>
        emitter.on("success", () => {
          callbacks++;
        }),
      ),
      run,
    );
    const result = await run;
    assert.equal(result.getToolCalls()[0].toolCallId, "call-current");
    assert.equal(callbacks, 1);
    return {
      messages: messages.length,
      tool_call: result.getToolCalls()[0].toolCallId,
    };
  });
  await scenario("requirement_agent", async () => {
    let turn = 0;
    const llm = new OpenAIChatModel(
      "gpt-4o-mini",
      {},
      client(() => {
        turn++;
        return !modern && turn === 2
          ? chat({ content: "84" })
          : chat({
              content: "",
              tool_calls: [
                {
                  id: turn === 1 ? "call-calculator" : "call-final",
                  type: "function",
                  function:
                    turn === 1
                      ? {
                          name: "Calculator",
                          arguments: '{"expression":"(19+23)*2"}',
                        }
                      : {
                          name: "final_answer",
                          arguments: '{"response":"84"}',
                        },
                },
              ],
            });
      }),
    );
    const Agent = modern
      ? (await import("beeai-framework/agents/requirement/agent"))
          .RequirementAgent
      : ToolCallingAgent;
    const agent = new Agent({
      llm,
      tools: [new CalculatorTool()],
      memory: new UnconstrainedMemory(),
    });
    const result = await agent.run({ prompt: "Compute (19+23)*2" });
    assert.equal(result.result.text, "84");
    assert.equal(turn, 2);
    return result.result.text;
  });
  await scenario("stream", async () => {
    const chunks = [
      {
        choices: [
          {
            index: 0,
            delta: { role: "assistant", content: "stream " },
            finish_reason: null,
          },
        ],
      },
      {
        choices: [
          { index: 0, delta: { content: "answer" }, finish_reason: null },
        ],
      },
      {
        choices: [{ index: 0, delta: {}, finish_reason: "stop" }],
        usage: { prompt_tokens: 0, completion_tokens: 0, total_tokens: 0 },
      },
    ].map((chunk) => ({
      id: "stream-id",
      object: "chat.completion.chunk",
      created: 1,
      model: "gpt-4o-mini",
      ...chunk,
    }));
    const llm = new OpenAIChatModel(
      "gpt-4o-mini",
      {},
      client(
        () =>
          new Response(
            chunks
              .map((chunk) => `data: ${JSON.stringify(chunk)}\n\n`)
              .join("") + "data: [DONE]\n\n",
            { headers: { "content-type": "text/event-stream" } },
          ),
      ),
    );
    let tokens = 0;
    const result = await llm
      .create({ messages: [new UserMessage("stream")], stream: true })
      .observe((emitter) =>
        emitter.on("newToken", () => {
          tokens++;
        }),
      );
    assert.equal(result.getTextContent(), "stream answer");
    assert.ok(tokens >= 2);
    return { text: result.getTextContent(), callbacks: tokens };
  });
  await scenario("embedding", async () => {
    const vector = Array.from({ length: 5001 }, (_, i) =>
      i === 0 ? 0 : i / 5001,
    );
    const embedding = new OpenAIEmbeddingModel(
      "text-embedding-3-small",
      {},
      client(() => ({
        object: "list",
        data: [{ object: "embedding", index: 0, embedding: vector }],
        model: "text-embedding-3-small",
        usage: { prompt_tokens: 0, total_tokens: 0 },
      })),
    );
    const result = await embedding.create({
      values: ["complete controlled vector"],
    });
    assert.deepEqual(result.embeddings, [vector]);
    return result.embeddings;
  });
  await scenario("tool_values", async () => {
    const values = [false, 0, "", []];
    const result: unknown[] = [];
    for (const value of values) {
      const expected = new JSONToolOutput(value);
      const tool = new DynamicTool({
        name: "values",
        description: "Preserve values",
        inputSchema: z.object({}),
        handler: async () => expected,
      });
      const actual = await tool.run({});
      assert.equal(actual, expected);
      result.push(actual.result);
    }
    return result;
  });
  await scenario("structured", async () => {
    const schema = {
      type: "object",
      properties: {
        count: { type: "number" },
        enabled: { type: "boolean" },
        text: { type: "string" },
      },
      required: ["count", "enabled", "text"],
      additionalProperties: false,
    };
    const llm = new OpenAIChatModel(
      "gpt-4o-mini",
      {},
      client((body) =>
        chat(
          !modern && body.tools?.length
            ? {
                content: "",
                tool_calls: [
                  {
                    id: "structured-call",
                    type: "function",
                    function: {
                      name: body.tools[0].function.name,
                      arguments: '{"count":0,"enabled":false,"text":""}',
                    },
                  },
                ],
              }
            : { content: '{"count":0,"enabled":false,"text":""}' },
        ),
      ),
    );
    const result = await llm.createStructure({
      messages: [new UserMessage("structure")],
      schema: modern
        ? { type: "object-json", schema, name: "value_schema" }
        : z.object({
            count: z.number(),
            enabled: z.boolean(),
            text: z.string(),
          }),
    });
    assert.deepEqual(result.object, { count: 0, enabled: false, text: "" });
    return result.object;
  });
  await scenario("errors", async () => {
    const llm = new OpenAIChatModel(
      "gpt-4o-mini",
      {},
      client(
        () =>
          new Response(
            JSON.stringify({
              error: {
                message: "controlled provider failure",
                type: "controlled_error",
              },
            }),
            { status: 400, headers: { "content-type": "application/json" } },
          ),
      ),
    );
    await assert.rejects(
      llm.create({
        messages: [new UserMessage("controlled failure")],
        maxRetries: 0,
      }),
    );
    return { controlled_error_observed: true };
  });
  await scenario("privacy", async () => {
    const previous = process.env.RESPAN_TRACE_CONTENT;
    process.env.RESPAN_TRACE_CONTENT = "false";
    try {
      const llm = new OpenAIChatModel(
        "gpt-4o-mini",
        {},
        client(() => chat({ content: "private controlled answer" })),
      );
      const result = await llm.create({
        messages: [new UserMessage("private controlled prompt")],
      });
      assert.equal(result.getTextContent(), "private controlled answer");
      return { privacy_case_completed: true };
    } finally {
      if (previous === undefined) delete process.env.RESPAN_TRACE_CONTENT;
      else process.env.RESPAN_TRACE_CONTENT = previous;
    }
  });
  console.log(JSON.stringify({ run_id: BEEAI_EXAMPLE_RUN_ID, scenarios }));
} finally {
  await respan.shutdown();
}
