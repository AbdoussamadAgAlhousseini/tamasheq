"use client";

import { useEffect, useRef, useState } from "react";

import { type CapabilityStatus, fetchCapabilities } from "@/lib/capabilities";
import {
  ChatError,
  type ChatErrorCode,
  type ChatTurn,
  MAX_CHARS,
  MAX_MESSAGES,
  sendChat,
} from "@/lib/chat";

import { T } from "./T";

type Shown = ChatTurn & { model?: string; truncated?: boolean };

const ERRORS: Record<ChatErrorCode, { fr: string; en: string }> = {
  not_configured: {
    fr: "L'assistant n'est pas activé sur ce serveur.",
    en: "The assistant is not enabled on this server.",
  },
  rate_limited: {
    fr: "Trop de messages en peu de temps. Réessayez dans une minute.",
    en: "Too many messages in a short time. Try again in a minute.",
  },
  refused: {
    fr: "Le modèle a refusé de répondre à ce message.",
    en: "The model declined to answer this message.",
  },
  unavailable: {
    fr: "Le service de modèle est indisponible pour le moment. Réessayez plus tard.",
    en: "The model service is unavailable right now. Try again later.",
  },
  provider_error: {
    fr: "Erreur du fournisseur de modèle. L'équipe doit vérifier la configuration.",
    en: "Model provider error. The team needs to check the configuration.",
  },
  invalid: { fr: "Message refusé par le serveur.", en: "Message rejected by the server." },
  network: { fr: "Serveur injoignable.", en: "Server unreachable." },
};

export function Chat() {
  const [status, setStatus] = useState<CapabilityStatus | "loading" | "error">("loading");
  const [turns, setTurns] = useState<Shown[]>([]);
  const [draft, setDraft] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<ChatErrorCode | null>(null);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetchCapabilities()
      .then((all) => setStatus(all.find((c) => c.name === "chat")?.status ?? "not_available"))
      .catch(() => setStatus("error"));
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: "nearest" });
  }, [turns, pending]);

  if (status === "loading") return null;
  if (status === "error" || status === "not_available") {
    return (
      <p role="note" className="rounded-md border border-line bg-surface p-4 text-sm">
        {status === "error" ? (
          <T fr={ERRORS.network.fr} en={ERRORS.network.en} />
        ) : (
          <T fr={ERRORS.not_configured.fr} en={ERRORS.not_configured.en} />
        )}
      </p>
    );
  }

  const full = turns.length + 1 >= MAX_MESSAGES;

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    const content = draft.trim();
    if (!content || pending || full) return;
    const history: Shown[] = [...turns, { role: "user", content }];
    setTurns(history);
    setDraft("");
    setError(null);
    setPending(true);
    try {
      const reply = await sendChat(history.map(({ role, content }) => ({ role, content })));
      setTurns([
        ...history,
        {
          role: "assistant",
          content: reply.reply,
          model: reply.model,
          truncated: reply.truncated,
        },
      ]);
    } catch (e) {
      // Le message non envoyé revient dans le champ ; l'historique reste cohérent.
      setTurns(turns);
      setDraft(content);
      setError(e instanceof ChatError ? e.code : "invalid");
    } finally {
      setPending(false);
    }
  }

  return (
    <section aria-labelledby="chat-title" className="rounded-lg border border-line bg-surface">
      <h2 id="chat-title" className="sr-only">
        <T fr="Conversation" en="Conversation" />
      </h2>
      <p role="note" className="border-b border-line p-4 text-sm">
        <strong>
          <T fr="Expérimental. " en="Experimental. " />
        </strong>
        <T
          fr="Les capacités du modèle en tamasheq n'ont pas encore été évaluées : ses réponses peuvent contenir des erreurs ou des mots inexistants. Ne les utilisez pas comme référence. La conversation n'est pas enregistrée et disparaît si vous quittez la page."
          en="The model's Tamasheq abilities have not been evaluated yet: its answers may contain errors or non-existent words. Do not use them as a reference. The conversation is not saved and disappears if you leave the page."
        />
      </p>

      <ol className="flex flex-col gap-4 p-4" aria-live="polite">
        {turns.map((turn, i) => (
          <li
            key={i}
            data-role={turn.role}
            className={turn.role === "user" ? "self-end max-w-[85%]" : "max-w-[95%]"}
          >
            <p className="text-xs font-medium text-muted">
              {turn.role === "user" ? <T fr="Vous" en="You" /> : <T fr="Assistant" en="Assistant" />}
            </p>
            <div
              dir="auto"
              className={`mt-1 whitespace-pre-wrap rounded-lg px-3 py-2 ${
                turn.role === "user" ? "bg-accent text-on-accent" : "border border-line"
              }`}
            >
              {turn.content}
            </div>
            {turn.role === "assistant" && (
              <p className="mt-1 text-xs text-muted">
                <T
                  fr={`Réponse générée par ${turn.model}, non vérifiée.`}
                  en={`Generated by ${turn.model}, not verified.`}
                />
                {turn.truncated && (
                  <>
                    {" "}
                    <T fr="Réponse incomplète (coupée)." en="Incomplete answer (cut off)." />
                  </>
                )}
              </p>
            )}
          </li>
        ))}
        {pending && (
          <li className="text-sm text-muted" role="status">
            <T fr="L'assistant rédige une réponse…" en="The assistant is writing…" />
          </li>
        )}
      </ol>
      <div ref={endRef} />

      <form onSubmit={submit} className="border-t border-line p-4">
        {error && (
          <p role="alert" className="mb-3 text-sm font-medium">
            <T fr={ERRORS[error].fr} en={ERRORS[error].en} />
          </p>
        )}
        {full ? (
          <p className="mb-3 text-sm">
            <T
              fr="Conversation trop longue : commencez-en une nouvelle."
              en="Conversation too long: start a new one."
            />
          </p>
        ) : (
          <>
            <label htmlFor="chat-input" className="text-sm font-medium">
              <T fr="Votre message" en="Your message" />
            </label>
            <textarea
              id="chat-input"
              dir="auto"
              rows={3}
              maxLength={MAX_CHARS}
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) e.currentTarget.form?.requestSubmit();
              }}
              className="mt-1 block w-full rounded-md border border-line bg-background p-2"
            />
          </>
        )}
        <div className="mt-3 flex flex-wrap gap-3">
          {!full && (
            <button
              type="submit"
              disabled={pending || !draft.trim()}
              className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-on-accent disabled:opacity-50"
            >
              <T fr="Envoyer" en="Send" />
            </button>
          )}
          {turns.length > 0 && (
            <button
              type="button"
              disabled={pending}
              onClick={() => {
                setTurns([]);
                setError(null);
              }}
              className="rounded-md border border-line px-4 py-2 text-sm"
            >
              <T fr="Nouvelle conversation" en="New conversation" />
            </button>
          )}
        </div>
      </form>
    </section>
  );
}
