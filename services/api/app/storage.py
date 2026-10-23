"""Stockage des fichiers audio.

`LocalStorage` (répertoire local) sert au développement et à un hébergement sur un seul
serveur. Un stockage objet compatible S3 implémentera la même interface au déploiement.
"""

import re
import shutil
from pathlib import Path
from typing import Protocol

_KEY = re.compile(r"^[a-z0-9][a-z0-9/_.-]{0,200}$")


class Storage(Protocol):
    def put(self, key: str, source: Path) -> None: ...
    def path(self, key: str) -> Path: ...
    def delete(self, key: str) -> None: ...


class LocalStorage:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def _resolve(self, key: str) -> Path:
        # Clés générées par l'application ; la vérification empêche toute sortie du répertoire.
        if not _KEY.match(key) or ".." in key:
            raise ValueError(f"clé de stockage invalide : {key!r}")
        path = (self.root / key).resolve()
        if not path.is_relative_to(self.root):
            raise ValueError(f"clé de stockage invalide : {key!r}")
        return path

    def put(self, key: str, source: Path) -> None:
        target = self._resolve(key)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)

    def path(self, key: str) -> Path:
        return self._resolve(key)

    def delete(self, key: str) -> None:
        self._resolve(key).unlink(missing_ok=True)
