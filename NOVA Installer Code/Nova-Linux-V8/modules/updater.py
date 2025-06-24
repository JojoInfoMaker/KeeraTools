import os
import sys
import shutil
import requests
import zipfile
import tempfile
import logging

GITHUB_REPO = "Nixiews/Nova-Installer"
LOCAL_VERSION_FILE = os.path.join(os.path.dirname(__file__), "..", "version.txt")
EXPECTED_VERSION = "V1L"

logger = logging.getLogger(__name__)

def get_local_version():
    if not os.path.exists(LOCAL_VERSION_FILE):
        return None
    with open(LOCAL_VERSION_FILE, "r") as f:
        return f.read().strip()

def get_latest_release():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return data["tag_name"], data["zipball_url"]

def update_from_github(zip_url):
    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, "latest.zip")
        # Download zip
        with requests.get(zip_url, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(zip_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        # Extract zip
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(tmpdir)
        # Find the extracted root folder
        extracted_root = next(
            os.path.join(tmpdir, d) for d in os.listdir(tmpdir)
            if os.path.isdir(os.path.join(tmpdir, d))
        )
        # Copy all files/folders to current directory (preserve structure)
        for item in os.listdir(extracted_root):
            s = os.path.join(extracted_root, item)
            d = os.path.join(os.path.dirname(__file__), "..", item)
            if os.path.isdir(s):
                if os.path.exists(d):
                    shutil.rmtree(d)
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)

def check_and_update():
    try:
        local_version = get_local_version()
        if local_version == EXPECTED_VERSION:
            logger.info("Already on latest expected version.")
            return
        latest_version, zip_url = get_latest_release()
        if local_version != latest_version:
            logger.info(f"Updating from {local_version} to {latest_version}")
            update_from_github(zip_url)
            # Write new version
            with open(LOCAL_VERSION_FILE, "w") as f:
                f.write(latest_version)
            # Optionally, restart the app
            os.execv(sys.executable, [sys.executable] + sys.argv)
    except Exception as e:
        logger.error(f"Update failed: {e}")
