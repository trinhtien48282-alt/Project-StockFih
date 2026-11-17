# Error log: stockfih.log in the per-user data folder, plus a hook for uncaught exceptions.
# No GUI imports. The app passes `on_error` to tell the user something went wrong.
import logging
import sys
import threading
from collections.abc import Callable
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG = logging.getLogger("stockfih")  # every "stockfih.*" logger feeds the file


def setup(log_dir: Path, on_error: Callable[[Path], None] | None = None) -> Path | None:
    # Returns the log file path, or None when the folder cannot be written (the app still runs).
    path = log_dir / "stockfih.log"
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(path, maxBytes=256_000, backupCount=2, encoding="utf-8")
    except OSError:
        return None
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    LOG.addHandler(handler)
    LOG.setLevel(logging.INFO)

    def on_uncaught(kind, value, tb) -> None:
        if issubclass(kind, KeyboardInterrupt):
            sys.__excepthook__(kind, value, tb)
            return
        LOG.critical("Uncaught exception", exc_info=(kind, value, tb))
        # Dialogs belong to the GUI thread only.
        if on_error and threading.current_thread() is threading.main_thread():
            try:
                on_error(path)
            except Exception:
                LOG.exception("Error reporter failed")

    def on_thread(args) -> None:
        if args.exc_type is not SystemExit:
            LOG.critical(
                "Uncaught exception in thread",
                exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
            )

    sys.excepthook = on_uncaught
    threading.excepthook = on_thread
    return path
