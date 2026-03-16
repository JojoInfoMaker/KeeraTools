import sys
import re
import json
import shutil
import tempfile
import subprocess
import urllib.error
from pathlib import Path
from urllib.request import urlopen, Request


class AppUpdater:
    """Gère la vérification et l'installation des mises à jour depuis GitHub."""

    GITHUB_REPO    = "JojoInfoMaker/KeeraTools"
    GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    EXE_NAME       = "KeeraTools.exe"
    TIMEOUT        = 10

    def __init__(self, current_version: str, app_dir: Path = None):
        self.current_version = current_version

        if app_dir:
            self.app_dir = Path(app_dir)
        else:
            exe_location = Path(sys.argv[0]).resolve() if sys.argv[0] else Path(__file__).resolve()
            self.app_dir = exe_location.parent if exe_location.is_file() else exe_location

        self.exe_path = self.app_dir / self.EXE_NAME

        if not self.exe_path.exists() and sys.argv[0]:
            exe_from_argv = Path(sys.argv[0]).resolve()
            if exe_from_argv.exists() and (
                exe_from_argv.suffix.lower() == ".exe" or exe_from_argv.name == "python.exe"
            ):
                self.exe_path = exe_from_argv

        self.latest_info = None

    # ── Vérification ─────────────────────────────────────────────
    def check_for_updates(self, timeout=None) -> dict:
        timeout = timeout or self.TIMEOUT
        try:
            headers = {
                "User-Agent": "KeeraTools-Updater",
                "Accept":     "application/vnd.github.v3+json",
            }
            req = Request(self.GITHUB_API_URL, headers=headers)
            with urlopen(req, timeout=timeout) as response:
                data = json.loads(response.read().decode("utf-8"))

            latest_version_tag = data.get("tag_name", "").lstrip("v")

            exe_asset = next(
                (a for a in data.get("assets", []) if a["name"].endswith(".exe")),
                None
            )
            if not exe_asset:
                return {"has_update": False, "error": "Aucun fichier .exe trouvé dans la release"}

            def parse_version(v_str):
                try:
                    cleaned = v_str.lower().lstrip("v")
                    if not cleaned:
                        return (0,)
                    parts = cleaned.split(".")
                    result = []
                    for p in parts:
                        match = re.match(r"^\d+", p)
                        if match:
                            result.append(int(match.group()))
                    return tuple(result) if result else (0,)
                except Exception:
                    return (0,)

            has_update = parse_version(latest_version_tag) > parse_version(self.current_version)

            result = {
                "has_update":      has_update,
                "latest_version":  latest_version_tag,
                "download_url":    exe_asset["browser_download_url"],
                "current_version": self.current_version,
                "release_notes":   data.get("body", ""),
                "file_size":       exe_asset.get("size", 0),
                "created_at":      data.get("created_at", ""),
                "download_count":  exe_asset.get("download_count", 0),
            }
            self.latest_info = result
            return result

        except urllib.error.URLError as e:
            return {"has_update": False, "error": f"Erreur réseau: {e}"}
        except Exception as e:
            return {"has_update": False, "error": f"Erreur: {e}"}

    # ── Téléchargement ────────────────────────────────────────────
    def download_update(self, progress_callback=None) -> tuple:
        if not self.latest_info or not self.latest_info.get("download_url"):
            return False, "Pas d'URL de téléchargement disponible"

        temp_exe = Path(tempfile.gettempdir()) / self.EXE_NAME
        try:
            req = Request(self.latest_info["download_url"], headers={"User-Agent": "KeeraTools-Updater"})
            with urlopen(req, timeout=self.TIMEOUT) as response:
                total_size = int(response.headers.get("content-length", 0))
                downloaded = 0
                with open(temp_exe, "wb") as f:
                    while True:
                        chunk = response.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback and total_size > 0:
                            progress_callback(downloaded, total_size)
            return True, str(temp_exe)
        except Exception as e:
            if temp_exe.exists():
                temp_exe.unlink()
            return False, f"Erreur de téléchargement: {e}"

    # ── Installation ──────────────────────────────────────────────
    def install_update(self, temp_exe_path: str) -> tuple:
        try:
            temp_exe = Path(temp_exe_path)
            if not temp_exe.exists():
                return False, "Fichier temporaire introuvable"

            self.exe_path.parent.mkdir(parents=True, exist_ok=True)

            backup_exe = self.exe_path.parent / f"{self.exe_path.stem}.bak"
            if self.exe_path.exists():
                try:
                    if backup_exe.exists():
                        backup_exe.unlink()
                    shutil.copy2(self.exe_path, backup_exe)
                except Exception:
                    pass

            if self.exe_path.exists():
                try:
                    self.exe_path.unlink()
                except PermissionError:
                    temp_old = self.exe_path.parent / f"{self.exe_path.stem}.old"
                    try:
                        self.exe_path.rename(temp_old)
                    except Exception:
                        pass

            shutil.copy2(temp_exe, self.exe_path)
            try:
                temp_exe.unlink()
            except Exception:
                pass

            return True, "Mise à jour installée avec succès"
        except Exception as e:
            return False, f"Erreur d'installation: {e}"

    def apply_update_and_restart(self, temp_exe_path: str) -> bool:
        try:
            success, _ = self.install_update(temp_exe_path)
            if success and self.exe_path.exists():
                subprocess.Popen([str(self.exe_path)])
                return True
            return False
        except Exception:
            return False

    def restore_backup(self) -> tuple:
        try:
            backup_exe = self.app_dir / f"{self.EXE_NAME}.bak"
            if not backup_exe.exists():
                return False, "Pas de sauvegarde disponible"
            shutil.copy2(backup_exe, self.exe_path)
            return True, "Sauvegarde restaurée avec succès"
        except Exception as e:
            return False, f"Erreur: {e}"
