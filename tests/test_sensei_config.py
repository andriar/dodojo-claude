"""Sensei vault detection cascade: env > auto-detect > fallback."""
from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SENSEI_SCRIPTS = REPO / "skills" / "sensei" / "scripts"
sys.path.insert(0, str(SENSEI_SCRIPTS))


def _reload_config(monkeypatch, home: Path, **env):
    monkeypatch.setenv("HOME", str(home))
    for k in ("SENSEI_VAULT", "SENSEI_STATE", "SENSEI_HOME", "SENSEI_HISTORY", "SENSEI_REPOS"):
        monkeypatch.delenv(k, raising=False)
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    if "_config" in sys.modules:
        del sys.modules["_config"]
    return importlib.import_module("_config")


def test_explicit_env_wins(monkeypatch, tmp_path):
    custom = tmp_path / "anywhere"
    cfg = _reload_config(monkeypatch, tmp_path, SENSEI_VAULT=str(custom))
    assert cfg.VAULT == custom.resolve()


def test_autodetect_obsidian(monkeypatch, tmp_path):
    vault = tmp_path / "Documents" / "Obsidian Vault"
    vault.mkdir(parents=True)
    cfg = _reload_config(monkeypatch, tmp_path)
    assert cfg.VAULT == (vault / "Sensei").resolve()


def test_fallback_to_state_reports(monkeypatch, tmp_path):
    cfg = _reload_config(monkeypatch, tmp_path, SENSEI_STATE=str(tmp_path / "state"))
    assert cfg.VAULT == (tmp_path / "state" / "reports").resolve()
