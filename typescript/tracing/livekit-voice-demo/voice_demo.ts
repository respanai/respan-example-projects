/**
 * A real LiveKit voice agent (TypeScript), traced by the published Respan SDK.
 *
 * The same scripted phone call as the Python demo: a caller asks a dental
 * clinic's receptionist agent to move an appointment, talks over the agent
 * mid-sentence, and books a new time.
 *
 * The pipeline is LiveKit Agents' real one (AgentSession with Silero VAD and the
 * stock OpenAI STT / LLM / TTS plugins). The LLM goes through the Respan
 * gateway; speech goes to the local OpenAI-compatible speech server
 * (../../../python/tracing/livekit-voice-demo/speech_server.py: Whisper and
 * macOS voices), so only a Respan API key is needed. The two ends of the phone
 * line are stand-ins: the caller's microphone plays pre-recorded speech in real
 * time, and the agent's speaker plays out on a real-time clock, so talking over
 * the agent cuts it off as on a real call. No LiveKit server is needed.
 *
 * Writes to ./out: otlp_payload.json (the exact JSON bodies the SDK POSTed to
 * /v2/traces), spans.json (the same spans, flattened) and call.json.
 */
import { initializeLogger, voice } from "@livekit/agents";
import * as openai from "@livekit/agents-plugin-openai";
import * as silero from "@livekit/agents-plugin-silero";
import { AudioFrame } from "@livekit/rtc-node";
import { LiveKitInstrumentor } from "@respan/instrumentation-livekit";
import { Respan } from "@respan/respan";
import { config } from "dotenv";
import { mkdirSync, writeFileSync } from "node:fs";
import https from "node:https";
import { syncBuiltinESMExports } from "node:module";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
export const OUT = join(HERE, "out");
config({ path: join(HERE, ".env"), override: true });

const SAMPLE_RATE = 24000;
const FRAME_MS = 20;
const FRAME_SAMPLES = (SAMPLE_RATE * FRAME_MS) / 1000;
const SESSION_ID_ATTRIBUTE = "respan.sessions.session_identifier";
const SPEECH_BASE_URL = process.env.SPEECH_BASE_URL ?? "http://127.0.0.1:8765/v1";
const CALLER_VOICE = "Daniel";
const AGENT_VOICE = "Samantha";

const INSTRUCTIONS =
  "You are the receptionist at Bright Smile Dental, on a phone call. " +
  "Keep each reply to one or two spoken sentences, no lists or markdown. " +
  "When the caller asks about a day, offer three specific appointment times on " +
  "that day with the dentist's name, Dr. Patel, in one longer sentence.";

type Line = { text: string; interruptAfterS?: number };
export const CALLER_SCRIPT: Line[] = [
  { text: "Hi, I need to move my cleaning appointment, it's under Jordan Lee." },
  { text: "Do you have anything on Thursday afternoon?" },
  { text: "Sorry, actually Friday morning would be better for me.", interruptAfterS: 1.5 },
  { text: "Ten o'clock works, please book it. Thanks!" },
];
export const EXPECTED_TURNS = CALLER_SCRIPT.length;
export const EXPECTED_INTERRUPTED_TURN = 2;

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

async function callerVoice(text: string): Promise<Int16Array> {
  const response = await fetch(`${SPEECH_BASE_URL}/audio/speech`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ model: "say", voice: CALLER_VOICE, input: text, response_format: "pcm" }),
  });
  if (!response.ok) throw new Error(`speech server: ${response.status}`);
  const bytes = new Uint8Array(await response.arrayBuffer());
  return new Int16Array(bytes.buffer, bytes.byteOffset, Math.floor(bytes.byteLength / 2));
}

/** The caller's microphone: silence, or the next scripted line, in real time. */
class CallerMicrophone extends voice.AudioInput {
  private pending = new Int16Array(0);
  private doneResolvers: Array<() => void> = [];
  private closed = false;

  constructor() {
    super();
    let nextAt = performance.now();
    const stream = new ReadableStream<AudioFrame>({
      pull: async (controller) => {
        if (this.closed) return controller.close();
        nextAt += FRAME_MS;
        await sleep(Math.max(0, nextAt - performance.now()));
        const chunk = this.pending.subarray(0, FRAME_SAMPLES);
        this.pending = this.pending.subarray(FRAME_SAMPLES);
        if (chunk.length && !this.pending.length) {
          this.doneResolvers.splice(0).forEach((resolve) => resolve());
        }
        const frame = new Int16Array(FRAME_SAMPLES);
        frame.set(chunk);
        controller.enqueue(new AudioFrame(frame, SAMPLE_RATE, 1, FRAME_SAMPLES));
      },
    });
    this.multiStream.addInputStream(stream);
  }

  say(samples: Int16Array): Promise<void> {
    const joined = new Int16Array(this.pending.length + samples.length);
    joined.set(this.pending);
    joined.set(samples, this.pending.length);
    this.pending = joined;
    return new Promise((resolve) => this.doneResolvers.push(resolve));
  }

  stop(): void {
    this.closed = true;
  }
}

/** The agent's speaker: audio plays on a real-time clock and stops when cut off. */
class PhoneSpeaker extends voice.AudioOutput {
  private pushed = 0;
  private started = 0;
  private finishing: Promise<void> | null = null;
  private interrupt: (() => void) | null = null;
  interruptions = 0;

  constructor() {
    super(SAMPLE_RATE, undefined, { pause: false });
  }

  async captureFrame(frame: AudioFrame): Promise<void> {
    await super.captureFrame(frame);
    if (this.finishing) await this.finishing;
    if (!this.pushed) {
      this.started = performance.now();
      this.onPlaybackStarted(Date.now());
    }
    this.pushed += frame.samplesPerChannel / frame.sampleRate;
  }

  flush(): void {
    super.flush();
    if (this.pushed && !this.finishing) this.finishing = this.playOut();
  }

  clearBuffer(): void {
    if (!this.pushed) return;
    if (!this.finishing) this.finishing = this.playOut();
    this.interrupt?.();
  }

  private async playOut(): Promise<void> {
    const remainingMs = this.started + this.pushed * 1000 - performance.now();
    const interrupted = await new Promise<boolean>((resolve) => {
      const timer = setTimeout(() => resolve(false), Math.max(0, remainingMs));
      this.interrupt = () => {
        clearTimeout(timer);
        resolve(true);
      };
    });
    const played = interrupted
      ? Math.min(this.pushed, (performance.now() - this.started) / 1000)
      : this.pushed;
    this.interruptions += Number(interrupted);
    this.pushed = 0;
    this.interrupt = null;
    this.finishing = null;
    this.onPlaybackFinished({ playbackPosition: played, interrupted });
  }
}

/**
 * Keep a copy of every OTLP JSON body the SDK sends to /v2/traces. The SDK uses
 * OpenTelemetry's OTLP HTTP exporter, which writes through node:https, so the
 * body is teed there: these are the exact bytes on the wire.
 */
function captureExportedPayloads(): unknown[] {
  const payloads: unknown[] = [];
  const realRequest = https.request;
  (https as { request: typeof https.request }).request = ((...args: Parameters<typeof https.request>) => {
    const request = realRequest(...args);
    const target = args[0];
    const path = typeof target === "string" ? target : target instanceof URL ? target.href : (target.path ?? "");
    if (!String(path).includes("/v2/traces")) return request;
    const chunks: Buffer[] = [];
    const write = request.write.bind(request);
    const end = request.end.bind(request);
    request.write = ((chunk: unknown, ...rest: unknown[]) => {
      if (chunk) chunks.push(Buffer.from(chunk as Buffer));
      return (write as (...a: unknown[]) => boolean)(chunk, ...rest);
    }) as typeof request.write;
    request.end = ((chunk?: unknown, ...rest: unknown[]) => {
      if (chunk && typeof chunk !== "function") chunks.push(Buffer.from(chunk as Buffer));
      try {
        payloads.push(JSON.parse(Buffer.concat(chunks).toString("utf8")));
      } catch {
        payloads.push({ unparsed_bytes: Buffer.concat(chunks).length });
      }
      return (end as (...a: unknown[]) => typeof request)(chunk, ...rest);
    }) as typeof request.end;
    return request;
  }) as typeof https.request;
  syncBuiltinESMExports(); // so `import { request } from "https"` sees the tee too
  return payloads;
}

type AnyValue = Record<string, unknown>;
function flatten(payloads: unknown[]) {
  const rows: AnyValue[] = [];
  for (const payload of payloads as AnyValue[]) {
    for (const resource of (payload.resourceSpans as AnyValue[]) ?? []) {
      for (const scope of (resource.scopeSpans as AnyValue[]) ?? []) {
        for (const span of (scope.spans as AnyValue[]) ?? []) {
          const attrs: AnyValue = {};
          for (const a of (span.attributes as AnyValue[]) ?? []) {
            const value = (a.value ?? {}) as AnyValue;
            attrs[a.key as string] = Object.values(value)[0];
          }
          rows.push({
            name: attrs["traceloop.entity.name"] ?? span.name,
            kind: span.name,
            trace_id: span.traceId,
            span_id: span.spanId,
            parent_span_id: span.parentSpanId || null,
            session_id: attrs[SESSION_ID_ATTRIBUTE] ?? null,
            voice: Object.fromEntries(
              Object.entries(attrs)
                .filter(([k]) => k.includes(".voice."))
                .map(([k, v]) => [k.split(".voice.")[1], v]),
            ),
            attributes: attrs,
          });
        }
      }
    }
  }
  return rows;
}

function waitFor(session: voice.AgentSession, state: string, timeoutMs = 30000): Promise<void> {
  if (session.agentState === state) return Promise.resolve();
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      session.off(voice.AgentSessionEventTypes.AgentStateChanged, onChange);
      reject(new Error(`timed out waiting for agent state ${state}`));
    }, timeoutMs);
    const onChange = (ev: { newState: string }) => {
      if (ev.newState !== state) return;
      clearTimeout(timer);
      session.off(voice.AgentSessionEventTypes.AgentStateChanged, onChange);
      resolve();
    };
    session.on(voice.AgentSessionEventTypes.AgentStateChanged, onChange);
  });
}

export async function runCall() {
  initializeLogger({ pretty: false, level: "warn" });
  mkdirSync(OUT, { recursive: true });
  const payloads = captureExportedPayloads();
  const respanBase = process.env.RESPAN_BASE_URL ?? "https://api.respan.ai/api";
  const respan = new Respan({
    apiKey: process.env.RESPAN_API_KEY,
    baseURL: respanBase,
    appName: "livekit-voice-demo-ts",
    instrumentations: [new LiveKitInstrumentor()],
  });
  await respan.initialize();

  const voices = await Promise.all(CALLER_SCRIPT.map((line) => callerVoice(line.text)));
  const microphone = new CallerMicrophone();
  const speaker = new PhoneSpeaker();
  const session = new voice.AgentSession({
    vad: await silero.VAD.load(),
    stt: new openai.STT({ model: "whisper-1", baseURL: SPEECH_BASE_URL, apiKey: "local", language: "en", useRealtime: false }),
    llm: new openai.LLM({ model: "gpt-4o-mini", baseURL: respanBase, apiKey: process.env.RESPAN_API_KEY }),
    tts: new openai.TTS({ model: "tts-1", voice: AGENT_VOICE as never, baseURL: SPEECH_BASE_URL, apiKey: "local" }),
    turnHandling: {
      turnDetection: "vad",
      interruption: { enabled: true, mode: "vad", minDuration: 0.4, resumeFalseInterruption: false },
    },
  });
  const transcript: Array<{ role: string; text: string; interrupted: boolean }> = [];
  session.on(voice.AgentSessionEventTypes.ConversationItemAdded, (ev) => {
    const item = ev.item as { type?: string; role?: string; textContent?: string; interrupted?: boolean };
    if (item.type === "message") {
      transcript.push({ role: item.role ?? "", text: item.textContent ?? "", interrupted: !!item.interrupted });
    }
  });
  session.input.audio = microphone;
  session.output.audio = speaker;
  await session.start({ agent: new voice.Agent({ instructions: INSTRUCTIONS }), record: false });
  await sleep(500);

  for (const [i, line] of CALLER_SCRIPT.entries()) {
    if (line.interruptAfterS !== undefined) {
      await waitFor(session, "speaking");
      await sleep(line.interruptAfterS * 1000);
    } else {
      await waitFor(session, "listening");
    }
    console.log(`caller: ${line.text}`);
    await microphone.say(voices[i]);
    const next = CALLER_SCRIPT[i + 1];
    if (!next || next.interruptAfterS === undefined) {
      await waitFor(session, "speaking");
      await waitFor(session, "listening", 60000);
    }
  }
  await sleep(1000);
  await session.close();
  microphone.stop();
  await respan.flush();
  await respan.shutdown();

  const spans = flatten(payloads);
  const sessionIds = [...new Set(spans.map((s) => s.session_id).filter(Boolean))].sort();
  const result = {
    session_id: sessionIds.length === 1 ? (sessionIds[0] as string) : sessionIds,
    transcript,
    agent_cut_off: speaker.interruptions,
    exported_spans: spans.length,
    export_requests: payloads.length,
  };
  writeFileSync(join(OUT, "otlp_payload.json"), JSON.stringify(payloads, null, 2));
  writeFileSync(join(OUT, "spans.json"), JSON.stringify(spans, null, 2));
  writeFileSync(join(OUT, "call.json"), JSON.stringify(result, null, 2));
  for (const item of transcript) {
    console.log(`  ${item.role.padStart(9)}: ${item.text}${item.interrupted ? " [cut off]" : ""}`);
  }
  console.log(
    `session_id=${JSON.stringify(result.session_id)} spans=${spans.length} ` +
      `export_requests=${payloads.length} agent_cut_off=${speaker.interruptions}`,
  );
  return result;
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  runCall().then(
    () => process.exit(0),
    (error) => {
      console.error(error);
      process.exit(1);
    },
  );
}
