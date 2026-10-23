"""Vérification des fichiers audio avec ffprobe (FFmpeg), avant tout stockage.

Le type déclaré par le navigateur n'est pas cru : seul le contenu décodé par ffprobe compte.
"""

import json
import shutil
import subprocess  # noqa: S404 — appel à ffprobe avec une liste d'arguments, sans shell
from dataclasses import dataclass
from pathlib import Path

MAX_BYTES = 10 * 1024 * 1024
MIN_SECONDS = 0.5
MAX_SECONDS = 60.0

# Conteneur détecté par ffprobe → type MIME servi.
FORMATS = {
    "matroska,webm": "audio/webm",
    "ogg": "audio/ogg",
    "wav": "audio/wav",
    "mp3": "audio/mpeg",
    "mov,mp4,m4a,3gp,3g2,mj2": "audio/mp4",
    "flac": "audio/flac",
}


class InvalidAudio(ValueError):
    """Fichier refusé ; le message est destiné à l'utilisateur."""


@dataclass(frozen=True)
class AudioInfo:
    mime_type: str
    duration: float
    codec: str


def probe(path: Path) -> AudioInfo:
    ffprobe = shutil.which("ffprobe")
    if ffprobe is None:
        raise RuntimeError("ffprobe introuvable : installer FFmpeg sur le serveur")
    try:
        result = subprocess.run(  # noqa: S603
            [
                ffprobe,
                "-v",
                "error",
                "-show_entries",
                "format=format_name,duration:stream=codec_type,codec_name",
                "-of",
                "json",
                str(path),
            ],
            capture_output=True,
            timeout=15,
            check=False,
        )
    except subprocess.TimeoutExpired as e:
        raise InvalidAudio("analyse du fichier trop longue") from e
    if result.returncode != 0:
        raise InvalidAudio("fichier audio illisible")

    data = json.loads(result.stdout or b"{}")
    fmt = data.get("format", {})
    streams = data.get("streams", [])
    mime = FORMATS.get(fmt.get("format_name", ""))
    if mime is None:
        raise InvalidAudio(f"format non accepté : {fmt.get('format_name')!r}")
    if any(s.get("codec_type") == "video" for s in streams):
        raise InvalidAudio("le fichier contient de la vidéo")
    audio = [s for s in streams if s.get("codec_type") == "audio"]
    if len(audio) != 1:
        raise InvalidAudio("le fichier doit contenir exactement une piste audio")
    duration = _duration(fmt.get("duration"))
    if duration is None:
        raise InvalidAudio("durée inconnue")
    if not MIN_SECONDS <= duration <= MAX_SECONDS:
        raise InvalidAudio(
            f"durée de {duration:.1f} s hors limites ({MIN_SECONDS}–{MAX_SECONDS} s)"
        )
    return AudioInfo(mime_type=mime, duration=duration, codec=str(audio[0].get("codec_name")))


def _duration(value: object) -> float | None:
    try:
        return float(str(value))
    except ValueError:
        return None
