import subprocess
from PyQt5.QtCore import QThread, pyqtSignal
from core import APPDATA

_WINGET_APPINSTALLER_UPDATED = False


class InstallThread(QThread):
    log_signal  = pyqtSignal(str)
    done_signal = pyqtSignal(list, list)
    prog_signal = pyqtSignal(int, int)

    def __init__(self, apps, mode="install", package_manager="winget"):
        super().__init__()
        self.apps            = apps
        self.mode            = mode
        self.package_manager = package_manager.lower()
        self._abort          = False
        self._current_proc   = None

    def abort(self):
        self._abort = True
        if self._current_proc is not None:
            try:
                self._current_proc.kill()
            except Exception:
                pass

    def _update_app_installer(self):
        global _WINGET_APPINSTALLER_UPDATED
        if _WINGET_APPINSTALLER_UPDATED:
            return
        _WINGET_APPINSTALLER_UPDATED = True

        self.log_signal.emit(
            "\n" + "─" * 70 + "\n"
            "⟳  Mise à jour de Microsoft.AppInstaller (winget)…\n"
            + "─" * 70 + "\n"
        )
        APPDATA.log_install("Mise à jour de Microsoft.AppInstaller via winget")
        cmd = [
            "winget", "update", "Microsoft.AppInstaller",
            "--accept-package-agreements",
            "--accept-source-agreements",
        ]
        try:
            r = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1, universal_newlines=True,
                stdin=subprocess.DEVNULL,
            )
            for line in r.stdout:
                self.log_signal.emit(line)
            r.wait()
            if r.returncode == 0:
                self.log_signal.emit("✓  Microsoft.AppInstaller est à jour.\n\n")
                APPDATA.log_install("  ✓ Microsoft.AppInstaller — succès")
            else:
                self.log_signal.emit(
                    f"ℹ  Microsoft.AppInstaller — code {r.returncode} "
                    f"(déjà à jour ou non disponible, on continue).\n\n"
                )
                APPDATA.log_install(
                    f"  ℹ Microsoft.AppInstaller — code retour {r.returncode} (non bloquant)"
                )
        except Exception as e:
            self.log_signal.emit(f"⚠  Impossible de mettre à jour AppInstaller : {e}\n\n")
            APPDATA.log_install(f"  ⚠ Microsoft.AppInstaller — exception : {e}", level="warning")

    def run(self):
        global _WINGET_APPINSTALLER_UPDATED
        success, failed = [], []
        total = len(self.apps)

        winget_cmd_map = {
            "install"  : ["winget", "install", "--id", "{id}",
                          "--accept-package-agreements", "--accept-source-agreements"],
            "update"   : ["winget", "upgrade", "--id", "{id}",
                          "--accept-package-agreements", "--accept-source-agreements"],
            "uninstall": ["winget", "uninstall", "--id", "{id}"],
        }
        choco_cmd_map = {
            "install"  : ["choco", "install", "{id}", "-y", "--no-progress"],
            "update"   : ["choco", "upgrade",  "{id}", "-y", "--no-progress"],
            "uninstall": ["choco", "uninstall", "{id}", "-y"],
        }

        cmd_map = winget_cmd_map if self.package_manager == "winget" else choco_cmd_map
        pm_name = "Winget" if self.package_manager == "winget" else "Chocolatey (NOT WORK / NON FONCTIONNEL)"
        verb_map = {"install": "Installation", "update": "Mise à jour", "uninstall": "Désinstallation"}

        if self.package_manager == "winget" and not _WINGET_APPINSTALLER_UPDATED:
            self._update_app_installer()

        APPDATA.log_install(f"=== Début : {verb_map[self.mode]} de {total} application(s) via {pm_name} ===")

        for idx, (name, wid) in enumerate(self.apps):
            if self._abort:
                break
            self.prog_signal.emit(idx, total)
            self.log_signal.emit(f"\n{'='*70}\n>>> {verb_map[self.mode]} de {name}...\n{'='*70}\n")
            APPDATA.log_install(f"{verb_map[self.mode]} : {name}  (id={wid}, manager={pm_name})")
            cmd = [c.replace("{id}", wid) for c in cmd_map[self.mode]]
            try:
                self._current_proc = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, bufsize=1, universal_newlines=True
                )
                for line in self._current_proc.stdout:
                    if self._abort:
                        self._current_proc.kill()
                        break
                    self.log_signal.emit(line)
                self._current_proc.wait()
                rc = self._current_proc.returncode
                self._current_proc = None

                if self._abort:
                    break

                if rc == 0:
                    success.append(name)
                    self.log_signal.emit(f"\n✓ {name} — OK\n")
                    APPDATA.log_install(f"  ✓ {name} — succès")
                else:
                    failed.append(name)
                    self.log_signal.emit(f"\n✗ {name} — code {rc}\n")
                    APPDATA.log_install(f"  ✗ {name} — code retour {rc}", level="error")
            except FileNotFoundError:
                failed.append(name)
                error_msg = f"✗ {self.package_manager} introuvable"
                self.log_signal.emit(f"\n{error_msg}\n")
                APPDATA.log_install(f"  {error_msg}", level="critical")
                break
            except Exception as e:
                if self._abort:
                    break
                failed.append(name)
                self.log_signal.emit(f"\n✗ Erreur : {e}\n")
                APPDATA.log_install(f"  ✗ {name} — exception : {e}", level="error")

        self.prog_signal.emit(total, total)
        self.done_signal.emit(success, failed)
        status = "ANNULÉ" if self._abort else "Fin"
        APPDATA.log_install(
            f"=== {status} : {len(success)} succès, {len(failed)} échec(s)"
            + (f" — {', '.join(failed)}" if failed else "") + " ==="
        )
