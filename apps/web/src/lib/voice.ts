// Contrats de /api/v1/voice (services/api/app/routers/voice.py).
import { API_URL } from "./capabilities";

export type Prompt = { id: string; text: string; script: "Latn" | "Tfng" };

export type RecordingRights = {
  license: string;
  allow_publication: boolean;
  allow_training: boolean;
  allow_voice_synthesis: boolean;
  variant: string | null;
  prompt_text_id: string | null;
  transcription: string | null;
};

export const MAX_SECONDS = 60;

export async function fetchPrompt(): Promise<Prompt | null> {
  const response = await fetch(`${API_URL}/api/v1/voice/prompts?limit=1`);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  const prompts = (await response.json()) as Prompt[];
  return prompts[0] ?? null;
}

export class UploadError extends Error {}

export async function uploadRecording(
  token: string,
  audio: Blob,
  rights: RecordingRights,
): Promise<void> {
  const form = new FormData();
  form.append("audio", audio, audio.type.includes("ogg") ? "recording.ogg" : "recording.webm");
  form.append("metadata", JSON.stringify(rights));
  let response: Response;
  try {
    response = await fetch(`${API_URL}/api/v1/voice/recordings`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: form,
    });
  } catch {
    throw new UploadError("network");
  }
  if (response.ok) return;
  const data = (await response.json().catch(() => null)) as { detail?: unknown } | null;
  throw new UploadError(typeof data?.detail === "string" ? data.detail : `HTTP ${response.status}`);
}
