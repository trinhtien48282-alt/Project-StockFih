import sys
import threading

import pytest

from stockfih import logsetup


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    monkeypatch.setattr(sys, "excepthook", sys.excepthook)  # restored after each test
    monkeypatch.setattr(threading, "excepthook", threading.excepthook)
    yield
    for handler in list(logsetup.LOG.handlers):
        handler.close()  # Windows cannot delete a log file that is still open
        logsetup.LOG.removeHandler(handler)


def _boom():
    try:
        raise RuntimeError("boom")
    except RuntimeError:
        return sys.exc_info()


def test_uncaught_exception_is_logged_and_reported(tmp_path):
    seen = []
    path = logsetup.setup(tmp_path / "logs", seen.append)
    sys.excepthook(*_boom())
    assert seen == [path]
    text = path.read_text(encoding="utf-8")
    assert "Uncaught exception" in text and "boom" in text


def test_error_from_another_thread_is_logged_not_reported(tmp_path):
    seen = []
    path = logsetup.setup(tmp_path / "logs", seen.append)
    info = _boom()
    thread = threading.Thread(target=lambda: sys.excepthook(*info))
    thread.start()
    thread.join()
    assert seen == []  # a dialog from a worker thread would crash Qt
    assert "boom" in path.read_text(encoding="utf-8")


def test_unwritable_log_folder_is_not_fatal(tmp_path):
    blocker = tmp_path / "blocker"
    blocker.write_text("x")
    assert logsetup.setup(blocker / "logs") is None
