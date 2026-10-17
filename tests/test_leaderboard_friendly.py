"""Messaggio user-friendly + log generico per la classifica online."""
import importlib.util
import os
import sys
import urllib.error

import pytest


@pytest.fixture(scope="module")
def mw():
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "math-wizard.py")
    spec = importlib.util.spec_from_file_location("mw_leaderboard", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["mw_leaderboard"] = module
    spec.loader.exec_module(module)
    return module


def test_fetch_dns_error_returns_friendly_message(mw, monkeypatch):
    def boom(*args, **kwargs):
        raise urllib.error.URLError("[Errno 11001] getaddrinfo failed")

    monkeypatch.setattr(mw.urllib.request, "urlopen", boom)
    ok, res = mw.fetch_challenge_leaderboard("https://example.invalid/t", "k", 50, None, 3, 1)
    assert ok is False
    assert res == "Connessione al server classifica non riuscita."


def test_fetch_generic_error_keeps_detail(mw, monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("qualcosa di rotto")

    monkeypatch.setattr(mw.urllib.request, "urlopen", boom)
    ok, res = mw.fetch_challenge_leaderboard("https://example.invalid/t", "k", 50, None, 3, 1)
    assert ok is False
    assert res == "Lettura non riuscita: qualcosa di rotto"


def test_log_message_writes_file(mw, tmp_path, monkeypatch):
    log = tmp_path / "mw_test.log"
    monkeypatch.setattr(mw, "LOG_FILE", str(log))
    mw.log_message("riga di prova")
    mw.log_message("seconda riga")
    content = log.read_text(encoding="utf-8")
    assert "riga di prova" in content
    assert "seconda riga" in content
    assert content.startswith("[")


def test_log_message_never_raises(mw, tmp_path, monkeypatch):
    monkeypatch.setattr(mw, "LOG_FILE", str(tmp_path / "no_dir" / "nested" / "x.log"))
    mw.log_message("deve fallire silenziosamente")
