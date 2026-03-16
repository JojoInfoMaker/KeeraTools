from PyQt5.QtGui import QFont, QFontDatabase
from core.config import C, FONT_PATH

_COMFORTAA = "Segoe UI"


def load_comfortaa():
    global _COMFORTAA
    if FONT_PATH.exists():
        fid = QFontDatabase.addApplicationFont(str(FONT_PATH))
        if fid != -1:
            families = QFontDatabase.applicationFontFamilies(fid)
            if families:
                _COMFORTAA = families[0]


def CF(size, bold=False) -> QFont:
    f = QFont(_COMFORTAA, size)
    f.setBold(bold)
    return f


def global_css() -> str:
    return f"""
* {{ font-family: '{_COMFORTAA}', 'Segoe UI', sans-serif; }}
QMainWindow, QDialog {{ background: {C['bg']}; }}
QWidget {{ background: transparent; color: {C['text']}; font-size: 15px; }}
QScrollBar:vertical {{ background: {C['surface']}; width: 7px; border-radius: 3px; margin: 0; }}
QScrollBar::handle:vertical {{ background: {C['border']}; border-radius: 3px; min-height: 28px; }}
QScrollBar::handle:vertical:hover {{ background: {C['accent']}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{ height: 0; }}
QTextEdit {{
    background: {C['surface']}; border: 1px solid {C['border']};
    border-radius: 8px; color: {C['text']};
    font-family: 'Consolas', monospace; font-size: 13px; padding: 8px;
}}
QMessageBox {{ background: {C['surface']}; color: {C['text']}; }}
QMessageBox QLabel {{ color: {C['text']}; background: transparent; font-size: 14px; }}
QMessageBox QPushButton {{
    background: {C['accent']}; color: white; border: none;
    border-radius: 7px; padding: 7px 18px; font-size: 13px;
}}
QComboBox {{
    background: {C['bg']}; color: {C['text']};
    border: 1px solid {C['border']}; border-radius: 7px;
    padding: 7px 14px; min-width: 200px; font-size: 14px;
    font-family: '{_COMFORTAA}', 'Segoe UI', sans-serif;
}}
QComboBox::drop-down {{ border: none; width: 28px; }}
QComboBox QAbstractItemView {{
    background: {C['surface']}; color: {C['text']};
    selection-background-color: {C['accent']};
    border: 1px solid {C['border']}; font-size: 14px;
}}
"""


def btn_style(color=None, outline=False) -> str:
    c   = color or C["accent"]
    fam = _COMFORTAA
    if outline:
        return f"""QPushButton {{
            background: transparent; color: {c};
            border: 1.5px solid {c}; border-radius: 8px;
            padding: 8px 20px; font-size: 13px; font-weight: 600;
            font-family: '{fam}', 'Segoe UI', sans-serif;
        }}
        QPushButton:hover {{ background: {c}22; }}
        QPushButton:pressed {{ background: {c}44; }}
        QPushButton:disabled {{ color: {C['muted']}; border-color: {C['border']}; }}"""
    return f"""QPushButton {{
        background: {c}; color: white; border: none;
        border-radius: 8px; padding: 9px 22px;
        font-size: 13px; font-weight: 600;
        font-family: '{fam}', 'Segoe UI', sans-serif;
    }}
    QPushButton:hover {{ background: {c}DD; }}
    QPushButton:pressed {{ background: {c}99; }}
    QPushButton:disabled {{ background: {C['border']}; color: {C['muted']}; }}"""


def nav_btn_style(active=False) -> str:
    fam = _COMFORTAA
    if active:
        return f"""QPushButton {{
            background: {C['accent']}; color: white; border: none;
            border-radius: 9px; padding: 11px 28px;
            font-size: 14px; font-weight: 700;
            font-family: '{fam}', 'Segoe UI', sans-serif;
        }}"""
    return f"""QPushButton {{
        background: transparent; color: {C['muted']}; border: none;
        border-radius: 9px; padding: 11px 28px; font-size: 14px;
        font-family: '{fam}', 'Segoe UI', sans-serif;
    }}
    QPushButton:hover {{ background: {C['surface2']}; color: {C['text']}; }}"""


def cat_btn_style(active=False) -> str:
    fam = _COMFORTAA
    if active:
        return f"""QPushButton {{
            background: {C['selected']}; color: {C['accent']};
            border: 1px solid {C['accent']}55;
            border-left: 3px solid {C['accent']};
            border-radius: 7px; padding: 11px 16px;
            font-size: 13px; font-weight: 600; text-align: left;
            font-family: '{fam}', 'Segoe UI', sans-serif;
        }}"""
    return f"""QPushButton {{
        background: transparent; color: {C['muted']}; border: none;
        border-left: 3px solid transparent; border-radius: 7px;
        padding: 11px 16px; font-size: 13px; text-align: left;
        font-family: '{fam}', 'Segoe UI', sans-serif;
    }}
    QPushButton:hover {{
        background: {C['surface2']}; color: {C['text']};
        border-left: 3px solid {C['border']};
    }}"""
