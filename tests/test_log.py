from dead.config import logging_config_env_builder
from dead.log import logger

import logging

import pytest


def test_logger(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("LOG_STDOUT", "TRUE")
    cfg = logging_config_env_builder()
    log = logger(__name__, cfg)
    assert log.level == logging.DEBUG
    log.info("foo")

