// Contrat de GET /api/v1/capabilities (services/api/app/routers/capabilities.py).

export type CapabilityName = "chat" | "translation" | "dictionary" | "knowledge" | "asr" | "tts";
export type CapabilityStatus = "not_available" | "experimental" | "evaluated";

export type Capability = { name: CapabilityName; status: CapabilityStatus; note: string };

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

let request: Promise<Capability[]> | null = null;

/** Une seule requête par chargement de page, partagée par tous les badges. */
export function fetchCapabilities(): Promise<Capability[]> {
  request ??= fetch(`${API_URL}/api/v1/capabilities`)
    .then((response) => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.json() as Promise<Capability[]>;
    })
    .catch((error: unknown) => {
      request = null; // permet de réessayer à la navigation suivante
      throw error;
    });
  return request;
}
