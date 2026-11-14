from PySide6.QtWidgets import QApplication

from stockfih.ui.main_window import MainWindow


def run() -> int:
    app = QApplication([])
    # Names decide the per-user data folder (profiles database, avatars).
    app.setOrganizationName("StockFih")
    app.setApplicationName("StockFih")
    window = MainWindow()
    window.show()
    return app.exec()
