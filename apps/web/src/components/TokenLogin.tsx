"use client";

import { useState, useSyncExternalStore } from "react";

import { getAuth, getServerAuth, signIn, signOut, subscribeAuth } from "@/lib/auth";

import { T } from "./T";

const ROLES = {
  contributor: { fr: "contributeur", en: "contributor" },
  reviewer: { fr: "réviseur", en: "reviewer" },
  admin: { fr: "administration", en: "administration" },
};

export function useAuth() {
  return useSyncExternalStore(subscribeAuth, getAuth, getServerAuth);
}

export function TokenLogin() {
  const auth = useAuth();
  const [token, setToken] = useState("");
  const [error, setError] = useState<"invalid" | "network" | null>(null);
  const [pending, setPending] = useState(false);

  if (auth) {
    return (
      <p className="flex flex-wrap items-center gap-3 text-sm">
        <span>
          <T fr="Connecté : " en="Signed in: " />
          <strong>{auth.account.pseudonym}</strong> (
          <T fr={ROLES[auth.account.role].fr} en={ROLES[auth.account.role].en} />)
        </span>
        <button type="button" onClick={signOut} className="underline">
          <T fr="Se déconnecter" en="Sign out" />
        </button>
      </p>
    );
  }

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!token.trim()) return;
    setPending(true);
    setError(null);
    try {
      await signIn(token.trim());
      setToken("");
    } catch (e) {
      setError(e instanceof Error && e.message === "invalid" ? "invalid" : "network");
    } finally {
      setPending(false);
    }
  }

  return (
    <form onSubmit={submit} className="flex flex-col gap-2 text-sm">
      <label htmlFor="token" className="font-medium">
        <T fr="Jeton d'accès" en="Access token" />
      </label>
      <p className="text-muted">
        <T
          fr="Les jetons sont remis par l'administration du projet aux contributeurs et réviseurs. Il est oublié à la fermeture de l'onglet."
          en="Tokens are given by the project administration to contributors and reviewers. It is forgotten when the tab is closed."
        />
      </p>
      <div className="flex flex-wrap gap-2">
        <input
          id="token"
          type="password"
          autoComplete="off"
          value={token}
          onChange={(e) => setToken(e.target.value)}
          className="min-w-0 flex-1 rounded-md border border-line bg-background p-2"
        />
        <button
          type="submit"
          disabled={pending || !token.trim()}
          className="rounded-md bg-accent px-4 py-2 font-medium text-on-accent disabled:opacity-50"
        >
          <T fr="Se connecter" en="Sign in" />
        </button>
      </div>
      {error && (
        <p role="alert" className="font-medium">
          {error === "invalid" ? (
            <T fr="Jeton invalide ou révoqué." en="Invalid or revoked token." />
          ) : (
            <T fr="Serveur injoignable." en="Server unreachable." />
          )}
        </p>
      )}
    </form>
  );
}
