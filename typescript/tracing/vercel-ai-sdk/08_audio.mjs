import assert from "node:assert/strict";
import { generateSpeech, transcribe, experimental_streamTranscribe } from "ai";
import { MockSpeechModelV4, MockTranscriptionModelV4 } from "ai/test";
import { runVercelCase } from "./vercel-common.mjs";

// Official AI SDK models keep this telemetry example deterministic. Requests
// still pass through the real SDK and OTel adapter before export to Respan.
const audio = new Uint8Array([1, 2, 3, 4]);
const response = { timestamp: new Date(), modelId: "audio-fixture" };
const chunks = parts => new ReadableStream({ start(controller) { for (const part of parts) controller.enqueue(part); controller.close(); } });

await runVercelCase("audio", async ({ telemetry }) => {
  const speech = await generateSpeech({
    model: new MockSpeechModelV4({ provider: "test", modelId: "speech-fixture", doGenerate: async () => ({
      audio, warnings: [], response, usage: { inputTokens: 3, audioSeconds: 0.5 },
    }) }),
    text: "Speak this example", telemetry: telemetry("speech"),
  });
  assert.equal(speech.audio.uint8Array.length, 4);

  const transcript = await transcribe({
    model: new MockTranscriptionModelV4({ provider: "test", modelId: "transcription-fixture", doGenerate: async () => ({
      text: "example transcript", segments: [], warnings: [], response, usage: { inputTokens: 4, outputTokens: 2 },
    }) }),
    audio, telemetry: telemetry("transcribe"),
  });
  assert.equal(transcript.text, "example transcript");

  const streamed = experimental_streamTranscribe({
    model: new MockTranscriptionModelV4({ provider: "test", modelId: "stream-transcription-fixture", doStream: async () => ({ stream: chunks([
      { type: "stream-start", warnings: [] },
      { type: "transcript-delta", delta: "streamed transcript" },
      { type: "finish", text: "streamed transcript", segments: [], usage: { durationSeconds: 1.5 } },
    ]) }) }),
    audio: chunks([audio]), inputAudioFormat: { mediaType: "audio/pcm", sampleRate: 16000, channels: 1 },
    telemetry: telemetry("stream_transcribe"),
  });
  for await (const _ of streamed.fullStream) { /* consume all lifecycle events */ }
  assert.equal(await streamed.text, "streamed transcript");

  await assert.rejects(generateSpeech({
    model: new MockSpeechModelV4({ provider: "test", modelId: "speech-error-fixture", doGenerate: async () => { throw new Error("Expected audio example failure"); } }),
    text: "Controlled failure", maxRetries: 0, telemetry: telemetry("speech_error"),
  }), /Expected audio example failure/);

  await generateSpeech({
    model: new MockSpeechModelV4({ provider: "test", modelId: "speech-private-fixture", doGenerate: async () => ({ audio, warnings: [], response }) }),
    text: "PRIVATE_AUDIO_EXAMPLE", telemetry: { ...telemetry("speech_private"), recordInputs: false, recordOutputs: false },
  });
  console.log("5 audio scenarios passed (speech, transcription, streaming, error, privacy)");
});
