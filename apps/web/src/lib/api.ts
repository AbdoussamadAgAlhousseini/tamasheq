import { API_URL } from "./capabilities";

export type ApiErrorCode =
  | "not_configured"
  | "rate_limited"
  | "refused"
  | "unavailable"
  | "provider_error"
  | "invalid"
  | "network";

export class ApiError extends Error {
  constructor(public code: ApiErrorCode) {
    super(code);
  }
}

const KNOWN: ApiErrorCode[] = [
  "not_configured",
  "rate_limited",
  "refused",
  "unavailable",
  "provider_error",
];

/** POST JSON vers l'API ; les erreurs sont ramenées à un code connu de l'interface. */
export async function postJson<T>(path: string, body: unknown): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch {
    throw new ApiError("network");
  }
  if (response.ok) return (await response.json()) as T;
  const data = (await response.json().catch(() => null)) as { detail?: { code?: string } } | null;
  const code = data?.detail?.code as ApiErrorCode | undefined;
  throw new ApiError(code && KNOWN.includes(code) ? code : "invalid");
}

export const API_ERRORS: Record<ApiErrorCode, { fr: string; en: string }> = {
  not_configured: {
    fr: "Cette fonction n'est pas activée sur ce serveur.",
    en: "This feature is not enabled on this server.",
  },
  rate_limited: {
    fr: "Trop de requêtes en peu de temps. Réessayez dans une minute.",
    en: "Too many requests in a short time. Try again in a minute.",
  },
  refused: {
    fr: "Le modèle a refusé de répondre à cette demande.",
    en: "The model declined this request.",
  },
  unavailable: {
    fr: "Le service de modèle est indisponible pour le moment. Réessayez plus tard.",
    en: "The model service is unavailable right now. Try again later.",
  },
  provider_error: {
    fr: "Erreur du fournisseur de modèle. L'équipe doit vérifier la configuration.",
    en: "Model provider error. The team needs to check the configuration.",
  },
  invalid: { fr: "Demande refusée par le serveur.", en: "Request rejected by the server." },
  network: { fr: "Serveur injoignable.", en: "Server unreachable." },
};
