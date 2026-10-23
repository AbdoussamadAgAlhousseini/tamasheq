"use client";

import { useEffect, useRef, useState } from "react";

import { fetchPrompt, MAX_SECONDS, type Prompt, uploadRecording, UploadError } from "@/lib/voice";

import { T } from "./T";
import { TokenLogin, useAuth } from "./TokenLogin";

const LICENSES = [
  {
    value: "CC-BY-4.0",
    fr: "CC BY 4.0 : réutilisation libre avec attribution",
    en: "CC BY 4.0: free reuse with attribution",
  },
  { value: "CC0-1.0", fr: "CC0 : domaine public", en: "CC0: public domain" },
  {
    value: "TAMASHEQ-usage-interne",
    fr: "Usage par le projet TAMASHEQ uniquement",
    en: "Use by the TAMASHEQ project only",
  },
];

type Rec = { blob: Blob; url: string; seconds: number };
type Phase = "idle" | "recording" | "recorded" | "sending" | "sent";
type Problem = "denied" | "unsupported" | "short" | { upload: string } | null;

export function VoiceRecorder() {
  const auth = useAuth();
  const [prompt, setPrompt] = useState<Prompt | null | "free">(null);
  const [promptError, setPromptError] = useState(false);
  const [transcription, setTranscription] = useState("");
  const [variant, setVariant] = useState("");
  const [license, setLicense] = useState(LICENSES[0].value);
  const [consent, setConsent] = useState({ publication: false, training: false, voice: false });
  const [phase, setPhase] = useState<Phase>("idle");
  const [seconds, setSeconds] = useState(0);
  const [recording, setRecording] = useState<Rec | null>(null);
  const [problem, setProblem] = useState<Problem>(null);
  const [promptRequest, setPromptRequest] = useState(0);
  const recorder = useRef<MediaRecorder | null>(null);
  const timer = useRef<ReturnType<typeof setInterval> | null>(null);
  const signedIn = auth !== null;

  const nextPrompt = () => setPromptRequest((n) => n + 1);

  useEffect(() => {
    if (!signedIn) return;
    let active = true;
    fetchPrompt()
      .then((p) => {
        if (!active) return;
        setPromptError(false);
        setPrompt(p ?? "free");
      })
      .catch(() => active && setPromptError(true));
    return () => {
      active = false;
    };
  }, [signedIn, promptRequest]);

  useEffect(
    () => () => {
      if (timer.current) clearInterval(timer.current);
      recorder.current?.stream.getTracks().forEach((t) => t.stop());
    },
    [],
  );

  if (!auth) {
    return (
      <section aria-labelledby="record" className="rounded-lg border border-line bg-surface p-4">
        <h2 id="record" className="text-lg font-semibold">
          <T fr="Enregistrer sa voix" en="Record your voice" />
        </h2>
        <p className="mt-2 text-sm">
          <T
            fr="La collecte d'enregistrements est ouverte aux personnes disposant d'un compte."
            en="Recording collection is open to people with an account."
          />
        </p>
        <div className="mt-4">
          <TokenLogin />
        </div>
      </section>
    );
  }
  const token = auth.token;

  async function start() {
    setProblem(null);
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
      setProblem("unsupported");
      return;
    }
    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      setProblem("denied");
      return;
    }
    const type = ["audio/webm;codecs=opus", "audio/ogg;codecs=opus", "audio/webm"].find((t) =>
      MediaRecorder.isTypeSupported(t),
    );
    const rec = new MediaRecorder(stream, type ? { mimeType: type } : undefined);
    const chunks: Blob[] = [];
    const started = Date.now();
    rec.ondataavailable = (e) => chunks.push(e.data);
    rec.onstop = () => {
      stream.getTracks().forEach((t) => t.stop());
      if (timer.current) clearInterval(timer.current);
      const elapsed = (Date.now() - started) / 1000;
      if (elapsed < 1) {
        setProblem("short");
        setPhase("idle");
        return;
      }
      const blob = new Blob(chunks, { type: rec.mimeType || "audio/webm" });
      setRecording({ blob, url: URL.createObjectURL(blob), seconds: elapsed });
      setPhase("recorded");
    };
    recorder.current = rec;
    rec.start();
    setSeconds(0);
    setPhase("recording");
    timer.current = setInterval(() => {
      const elapsed = Math.floor((Date.now() - started) / 1000);
      setSeconds(elapsed);
      if (elapsed >= MAX_SECONDS && rec.state === "recording") rec.stop();
    }, 250);
  }

  function stop() {
    if (recorder.current?.state === "recording") recorder.current.stop();
  }

  function discard() {
    if (recording) URL.revokeObjectURL(recording.url);
    setRecording(null);
    setPhase("idle");
  }

  async function send() {
    if (!recording) return;
    setPhase("sending");
    setProblem(null);
    try {
      await uploadRecording(token, recording.blob, {
        license,
        allow_publication: consent.publication,
        allow_training: consent.training,
        allow_voice_synthesis: consent.voice,
        variant: variant.trim() || null,
        prompt_text_id: prompt && prompt !== "free" ? prompt.id : null,
        transcription: prompt === "free" && transcription.trim() ? transcription.trim() : null,
      });
      discard();
      setTranscription("");
      setPhase("sent");
      nextPrompt();
    } catch (e) {
      setProblem({ upload: e instanceof UploadError ? e.message : "?" });
      setPhase("recorded");
    }
  }

  const checkbox = (key: keyof typeof consent, fr: string, en: string) => (
    <label className="flex items-start gap-2">
      <input
        type="checkbox"
        className="mt-1"
        checked={consent[key]}
        onChange={(e) => setConsent({ ...consent, [key]: e.target.checked })}
      />
      <span>
        <T fr={fr} en={en} />
      </span>
    </label>
  );

  return (
    <section aria-labelledby="record" className="rounded-lg border border-line bg-surface">
      <div className="border-b border-line p-4">
        <h2 id="record" className="text-lg font-semibold">
          <T fr="Enregistrer sa voix" en="Record your voice" />
        </h2>
        <div className="mt-2">
          <TokenLogin />
        </div>
      </div>

      <div className="flex flex-col gap-4 p-4">
        <div>
          <h3 className="text-sm font-semibold">
            <T fr="1. Ce que vous enregistrez" en="1. What you record" />
          </h3>
          {promptError && (
            <p role="alert" className="mt-1 text-sm">
              <T fr="Serveur injoignable." en="Server unreachable." />
            </p>
          )}
          {prompt && prompt !== "free" ? (
            <>
              <p className="mt-2 text-sm text-muted">
                <T fr="Lisez cette phrase à voix haute :" en="Read this sentence aloud:" />
              </p>
              <p
                lang={`taq-${prompt.script}`}
                className="mt-1 rounded-md border border-line p-3 text-lg"
                data-testid="prompt"
              >
                {prompt.text}
              </p>
              <div className="mt-2 flex flex-wrap gap-3 text-sm">
                <button type="button" onClick={nextPrompt} className="underline">
                  <T fr="Autre phrase" en="Another sentence" />
                </button>
                <button type="button" onClick={() => setPrompt("free")} className="underline">
                  <T fr="Parler librement" en="Speak freely" />
                </button>
              </div>
            </>
          ) : (
            prompt === "free" && (
              <label className="mt-2 flex flex-col text-sm">
                <T
                  fr="Parole libre. Transcription de ce que vous dites (facultatif, en latin ou en tifinagh) :"
                  en="Free speech. Transcription of what you say (optional, in Latin or Tifinagh script):"
                />
                <textarea
                  dir="auto"
                  rows={2}
                  maxLength={2000}
                  value={transcription}
                  onChange={(e) => setTranscription(e.target.value)}
                  className="mt-1 rounded-md border border-line bg-background p-2"
                />
              </label>
            )
          )}
        </div>

        <fieldset className="flex flex-col gap-2 text-sm">
          <legend className="font-semibold">
            <T fr="2. Vos choix (modifiables par un retrait)" en="2. Your choices (you can withdraw later)" />
          </legend>
          {checkbox(
            "publication",
            "J'accepte que l'enregistrement soit écouté publiquement sur le site.",
            "I agree that the recording may be played publicly on the site.",
          )}
          {checkbox(
            "training",
            "J'accepte qu'il serve à entraîner ou évaluer des modèles de reconnaissance de la parole.",
            "I agree that it may be used to train or evaluate speech recognition models.",
          )}
          {checkbox(
            "voice",
            "J'accepte qu'il serve à créer une voix de synthèse à partir de la mienne.",
            "I agree that it may be used to create a synthetic voice from mine.",
          )}
          <label className="mt-2 flex flex-col">
            <T fr="Licence" en="License" />
            <select
              value={license}
              onChange={(e) => setLicense(e.target.value)}
              className="mt-1 rounded-md border border-line bg-background p-2"
            >
              {LICENSES.map((l) => (
                <option key={l.value} value={l.value}>
                  {l.fr} / {l.en}
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col">
            <T fr="Variante parlée (facultatif)" en="Variety spoken (optional)" />
            <input
              value={variant}
              maxLength={200}
              onChange={(e) => setVariant(e.target.value)}
              className="mt-1 rounded-md border border-line bg-background p-2"
            />
          </label>
          <p className="text-muted">
            <T
              fr="Vous pourrez retirer votre enregistrement à tout moment : le fichier audio sera alors supprimé."
              en="You can withdraw your recording at any time: the audio file will then be deleted."
            />
          </p>
        </fieldset>

        <div>
          <h3 className="text-sm font-semibold">
            <T fr="3. Enregistrement (60 s au plus)" en="3. Recording (60 s maximum)" />
          </h3>
          <div className="mt-2 flex flex-wrap items-center gap-3">
            {phase === "recording" ? (
              <button
                type="button"
                onClick={stop}
                className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-on-accent"
              >
                <T fr="Arrêter" en="Stop" />
              </button>
            ) : (
              <button
                type="button"
                onClick={start}
                disabled={phase === "sending" || phase === "recorded"}
                className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-on-accent disabled:opacity-50"
              >
                <T fr="Enregistrer" en="Record" />
              </button>
            )}
            {phase === "recording" && (
              <span role="status" className="text-sm">
                <T fr="Enregistrement en cours : " en="Recording: " />
                {seconds} s
              </span>
            )}
          </div>
          {recording && (
            <div className="mt-3 flex flex-col gap-2">
              <audio controls src={recording.url} className="w-full" />
              <div className="flex flex-wrap gap-3">
                <button
                  type="button"
                  onClick={send}
                  disabled={phase === "sending"}
                  className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-on-accent disabled:opacity-50"
                >
                  <T fr="Envoyer" en="Send" />
                </button>
                <button
                  type="button"
                  onClick={discard}
                  disabled={phase === "sending"}
                  className="rounded-md border border-line px-4 py-2 text-sm"
                >
                  <T fr="Recommencer" en="Start again" />
                </button>
              </div>
            </div>
          )}
          {phase === "sent" && (
            <p role="status" className="mt-3 text-sm font-medium">
              <T
                fr="Merci ! Enregistrement reçu, en attente de relecture."
                en="Thank you! Recording received, awaiting review."
              />
            </p>
          )}
          {problem && (
            <p role="alert" className="mt-3 text-sm font-medium">
              {problem === "denied" && (
                <T fr="Accès au micro refusé." en="Microphone access denied." />
              )}
              {problem === "unsupported" && (
                <T
                  fr="Ce navigateur ne permet pas d'enregistrer."
                  en="This browser cannot record."
                />
              )}
              {problem === "short" && (
                <T fr="Enregistrement trop court." en="Recording too short." />
              )}
              {typeof problem === "object" && (
                <>
                  <T fr="Envoi refusé : " en="Upload rejected: " />
                  {problem.upload}
                </>
              )}
            </p>
          )}
        </div>
      </div>
    </section>
  );
}
