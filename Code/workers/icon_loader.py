import urllib.request
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap


class IconLoaderThread(QThread):
    icon_loaded = pyqtSignal(str, QPixmap)  # (app_name, pixmap)

    def __init__(self, app_name: str, url: str, size: int = 96):
        super().__init__()
        self.app_name = app_name
        self.url      = url
        self.size     = size

    def run(self):
        if not self.url:
            return
        try:
            response   = urllib.request.urlopen(self.url, timeout=5)
            image_data = response.read()
            pixmap     = QPixmap()
            pixmap.loadFromData(image_data)
            if not pixmap.isNull():
                scaled = pixmap.scaledToWidth(self.size, Qt.SmoothTransformation)
                self.icon_loaded.emit(self.app_name, scaled)
        except Exception as e:
            print(f"[WARN] Impossible de charger {self.url}: {e}")
