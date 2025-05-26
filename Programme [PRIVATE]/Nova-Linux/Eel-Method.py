import eel
import subprocess
import platform

eel.init('Web')

@eel.expose
def install_app(package_name, method):
    try:
        if method == "flatpak":
            result = subprocess.run(["flatpak", "install", "-y", package_name], capture_output=True, text=True)
        else:
            os_name = platform.system().lower()
            if "debian" in os_name or "ubuntu" in os_name:
                result = subprocess.run(["sudo", "apt", "install", "-y", package_name], capture_output=True, text=True)
            elif "fedora" in os_name:
                result = subprocess.run(["sudo", "dnf", "install", "-y", package_name], capture_output=True, text=True)
            elif "arch" in os_name:
                result = subprocess.run(["sudo", "pacman", "-S", "--noconfirm", package_name], capture_output=True, text=True)
            else:
                return "Unsupported OS"
        return result.stdout if result.returncode == 0 else result.stderr
    except Exception as e:
        return str(e)

eel.start('UI.html', mode='default', size=(600, 400))
