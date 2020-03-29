from dead.config import logging_config_env_builder, stats_config_env_builder

import logging

import pytest


def test_logging_config_env_builder_level(monkeypatch):
    cfg = logging_config_env_builder()
    assert cfg.level == logging.INFO
    monkeypatch.setenv("LOG_LEVEL", "WARN")
    cfg = logging_config_env_builder()
    assert cfg.level == logging.WARN


def test_logging_config_env_builder_stdout(monkeypatch):
    cfg = logging_config_env_builder()
    assert cfg.stdout is False
    monkeypatch.setenv("LOG_STDOUT", "TRUE")
    cfg = logging_config_env_builder()
    assert cfg.stdout is True


def test_stats_config_env_builder(monkeypatch):
    with pytest.raises(TypeError):
        _ = stats_config_env_builder()
    monkeypatch.setenv("DATADOG_API_KEY", "foo")
    monkeypatch.setenv("DATADOG_APP_KEY", "foo")
    monkeypatch.setenv("SOURCE_METRIC_QUERY", "foo")
    monkeypatch.setenv("ERROR_THRESHOLDS", "1,8,2.8,0.1")
    monkeypatch.setenv("DESTINATION_METRIC_TAGS", "foo:bar,bar:foo")
    monkeypatch.setenv("DESTINATION_METRIC_NAME", "foo")
    monkeypatch.setenv("START_TIME", "8")
    cfg = stats_config_env_builder()
    assert cfg.error_thresholds[2] == 2.8
    assert len(cfg.error_thresholds) == 4
    assert cfg.destination_metric_tags[0] == "foo:bar"
    assert len(cfg.destination_metric_tags) == 2
    assert cfg.start_time == 8

