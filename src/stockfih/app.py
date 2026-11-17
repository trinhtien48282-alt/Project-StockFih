import logging
from pathlib import Path

import chess
import PySide6
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSettings, QStandardPaths
from PySide6.QtWidgets import QApplication, QMessageBox

from stockfih import logsetup
from stockfih.ui.app_theme import apply_theme
from stockfih.ui.main_window import MainWindow

_reporting = False


def _report(log_path: Path) -> None:
    # A second error raised while the dialog is open must not stack another dialog.
    global _reporting
    if _reporting:
        return
    _reporting = True
    try:
        QMessageBox.critical(
            None, "StockFih", f"Something went wrong. Details are in this log file:\n{log_path}"
        )
    finally:
        _reporting = False


def run() -> int:
    app = QApplication([])
    # Names decide the per-user data folder (profiles database, avatars, logs).
    app.setOrganizationName("StockFih")
    app.setApplicationName("StockFih")
    data_dir = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation))
    logsetup.setup(data_dir / "logs", _report)
    logging.getLogger("stockfih").info(
        "Started: PySide6 %s, python-chess %s", PySide6.__version__, chess.__version__
    )
    apply_theme(QSettings().value("theme", "System", type=str))  # before any window exists
    app.setWindowIcon(QIcon(str(Path(__file__).parent / "resources" / "images" / "stockfih.svg")))
    window = MainWindow()
    window.show()
    return app.exec()
