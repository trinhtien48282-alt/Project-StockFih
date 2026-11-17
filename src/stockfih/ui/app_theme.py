from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

# shortcut: Fusion + Qt color scheme. Needs PySide6 6.8 or newer (we have 6.12).
THEMES = {
    "System": Qt.ColorScheme.Unknown,  # follow Windows / Fedora setting
    "Light": Qt.ColorScheme.Light,
    "Dark": Qt.ColorScheme.Dark,
}


def apply_theme(name: str) -> None:
    app = QApplication.instance()
    app.setStyle("Fusion")  # native styles ignore the dark palette
    app.styleHints().setColorScheme(THEMES.get(name, Qt.ColorScheme.Unknown))
