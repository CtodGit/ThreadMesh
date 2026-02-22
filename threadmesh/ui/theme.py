# ThreadMesh - UI theme and stylesheet
# AGPL-3.0-or-later
#
# Mid-dark grey background with neon cyan/amber/green accents.
# Alien (1979) / 80s sci-fi aesthetic.

from threadmesh.config import (
    COLOR_BG_DARK, COLOR_BG_MID, COLOR_BG_PANEL,
    COLOR_ACCENT_CYAN, COLOR_ACCENT_AMBER, COLOR_ACCENT_GREEN,
    COLOR_TEXT_PRIMARY, COLOR_TEXT_DIM, COLOR_HIGHLIGHT,
)

STYLESHEET = f"""
/* ── Base ── */
QWidget {{
    background-color: {COLOR_BG_DARK};
    color: {COLOR_TEXT_PRIMARY};
    font-family: "Segoe UI", "Inter", "Helvetica Neue", sans-serif;
    font-size: 13px;
    border: none;
}}

/* ── Main window ── */
QMainWindow {{
    background-color: {COLOR_BG_DARK};
}}

/* ── Menu bar ── */
QMenuBar {{
    background-color: {COLOR_BG_MID};
    color: {COLOR_TEXT_PRIMARY};
    border-bottom: 1px solid {COLOR_ACCENT_CYAN}22;
}}
QMenuBar::item:selected {{
    background-color: {COLOR_HIGHLIGHT};
    color: {COLOR_ACCENT_CYAN};
}}
QMenu {{
    background-color: {COLOR_BG_MID};
    border: 1px solid {COLOR_ACCENT_CYAN}44;
}}
QMenu::item:selected {{
    background-color: {COLOR_HIGHLIGHT};
    color: {COLOR_ACCENT_CYAN};
}}

/* ── Toolbar ── */
QToolBar {{
    background-color: {COLOR_BG_MID};
    border-bottom: 1px solid {COLOR_ACCENT_CYAN}33;
    spacing: 4px;
    padding: 4px 8px;
}}
QToolButton {{
    background-color: transparent;
    color: {COLOR_TEXT_PRIMARY};
    border: 1px solid transparent;
    border-radius: 4px;
    padding: 4px 10px;
    font-size: 12px;
}}
QToolButton:hover {{
    background-color: {COLOR_HIGHLIGHT};
    border: 1px solid {COLOR_ACCENT_CYAN}66;
    color: {COLOR_ACCENT_CYAN};
}}
QToolButton:pressed {{
    background-color: {COLOR_ACCENT_CYAN}22;
    border: 1px solid {COLOR_ACCENT_CYAN};
}}
QToolButton:checked {{
    background-color: {COLOR_ACCENT_CYAN}22;
    border: 1px solid {COLOR_ACCENT_CYAN}88;
    color: {COLOR_ACCENT_CYAN};
}}

/* ── Buttons ── */
QPushButton {{
    background-color: {COLOR_BG_MID};
    color: {COLOR_TEXT_PRIMARY};
    border: 1px solid {COLOR_ACCENT_CYAN}55;
    border-radius: 4px;
    padding: 5px 14px;
}}
QPushButton:hover {{
    background-color: {COLOR_HIGHLIGHT};
    border-color: {COLOR_ACCENT_CYAN};
    color: {COLOR_ACCENT_CYAN};
}}
QPushButton:pressed {{
    background-color: {COLOR_ACCENT_CYAN}22;
}}
QPushButton#primary {{
    background-color: {COLOR_ACCENT_CYAN}22;
    border-color: {COLOR_ACCENT_CYAN};
    color: {COLOR_ACCENT_CYAN};
    font-weight: bold;
}}
QPushButton#primary:hover {{
    background-color: {COLOR_ACCENT_CYAN}44;
}}

/* ── Side panel ── */
QDockWidget {{
    background-color: {COLOR_BG_PANEL};
    color: {COLOR_TEXT_PRIMARY};
    titlebar-close-icon: none;
}}
QDockWidget::title {{
    background-color: {COLOR_BG_MID};
    color: {COLOR_ACCENT_CYAN};
    padding: 6px 10px;
    border-bottom: 1px solid {COLOR_ACCENT_CYAN}33;
    font-weight: bold;
    font-size: 12px;
    letter-spacing: 1px;
    text-transform: uppercase;
}}

/* ── Group boxes (panel sections) ── */
QGroupBox {{
    border: 1px solid {COLOR_ACCENT_CYAN}33;
    border-radius: 4px;
    margin-top: 10px;
    padding-top: 8px;
    font-size: 11px;
    color: {COLOR_TEXT_DIM};
    text-transform: uppercase;
    letter-spacing: 1px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    color: {COLOR_ACCENT_CYAN}aa;
}}

/* ── Sliders ── */
QSlider::groove:horizontal {{
    background-color: {COLOR_BG_MID};
    height: 4px;
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background-color: {COLOR_ACCENT_CYAN};
    width: 12px;
    height: 12px;
    margin: -4px 0;
    border-radius: 6px;
}}
QSlider::sub-page:horizontal {{
    background-color: {COLOR_ACCENT_CYAN}66;
    border-radius: 2px;
}}

/* ── Spin boxes and line edits ── */
QSpinBox, QDoubleSpinBox, QLineEdit {{
    background-color: {COLOR_BG_MID};
    color: {COLOR_TEXT_PRIMARY};
    border: 1px solid {COLOR_ACCENT_CYAN}33;
    border-radius: 3px;
    padding: 3px 6px;
}}
QSpinBox:focus, QDoubleSpinBox:focus, QLineEdit:focus {{
    border-color: {COLOR_ACCENT_CYAN};
}}

/* ── Combo boxes ── */
QComboBox {{
    background-color: {COLOR_BG_MID};
    color: {COLOR_TEXT_PRIMARY};
    border: 1px solid {COLOR_ACCENT_CYAN}33;
    border-radius: 3px;
    padding: 3px 8px;
}}
QComboBox:hover {{
    border-color: {COLOR_ACCENT_CYAN}88;
}}
QComboBox QAbstractItemView {{
    background-color: {COLOR_BG_MID};
    color: {COLOR_TEXT_PRIMARY};
    selection-background-color: {COLOR_HIGHLIGHT};
    selection-color: {COLOR_ACCENT_CYAN};
    border: 1px solid {COLOR_ACCENT_CYAN}44;
}}

/* ── Status bar ── */
QStatusBar {{
    background-color: {COLOR_BG_MID};
    color: {COLOR_TEXT_DIM};
    border-top: 1px solid {COLOR_ACCENT_CYAN}22;
    font-size: 11px;
    padding: 2px 8px;
}}
QStatusBar QLabel {{
    color: {COLOR_TEXT_DIM};
    padding: 0 8px;
    border-right: 1px solid {COLOR_ACCENT_CYAN}22;
}}

/* ── Scroll bars ── */
QScrollBar:vertical {{
    background-color: {COLOR_BG_DARK};
    width: 8px;
}}
QScrollBar::handle:vertical {{
    background-color: {COLOR_ACCENT_CYAN}44;
    border-radius: 4px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{
    background-color: {COLOR_ACCENT_CYAN}88;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

/* ── Labels ── */
QLabel#accent {{
    color: {COLOR_ACCENT_CYAN};
}}
QLabel#amber {{
    color: {COLOR_ACCENT_AMBER};
}}
QLabel#good {{
    color: {COLOR_ACCENT_GREEN};
}}
QLabel#section {{
    color: {COLOR_TEXT_DIM};
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 1px;
}}

/* ── Separator ── */
QFrame[frameShape="4"], QFrame[frameShape="5"] {{
    color: {COLOR_ACCENT_CYAN}22;
}}
"""


def apply(app):
    app.setStyleSheet(STYLESHEET)
