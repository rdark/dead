from dataclasses import dataclass
from typing import Tuple, List
from os import environ
import time
import logging

ErrorThreshold = float


@dataclass(frozen=True)
class LoggingConfig(object):
    stdout: bool = False
    level: int = logging.INFO


def logging_config_env_builder() -> LoggingConfig:
    env_lookup = {
        "stdout": environ.get("LOG_STDOUT"),
        "level": environ.get("LOG_LEVEL"),
    }
    found_kwargs = {}
    for k in env_lookup.keys():
        if env_lookup[k] is not None:
            v = env_lookup[k]
            if k == "stdout":
                v = bool(v)
            elif k == "level":
                v = getattr(logging, v)
            found_kwargs[k] = v
    return LoggingConfig(**found_kwargs)


@dataclass(frozen=True)
class StatsConfig(object):
    api_key: str
    app_key: str
    source_metric_query: str
    error_thresholds: Tuple[ErrorThreshold, ...]
    destination_metric_tags: List[str]
    destination_metric_name: str
    granularity_divisor: int = 1
    start_time: int = int(time.time() - 7200)
    end_time: int = int(start_time + 3600)


def stats_config_env_builder() -> StatsConfig:
    env_lookup = {
        "api_key": environ.get("DATADOG_API_KEY"),
        "app_key": environ.get("DATADOG_APP_KEY"),
        "source_metric_query": environ.get("SOURCE_METRIC_QUERY"),
        "error_thresholds": environ.get("ERROR_THRESHOLDS"),
        "destination_metric_tags": environ.get("DESTINATION_METRIC_TAGS"),
        "destination_metric_name": environ.get("DESTINATION_METRIC_NAME"),
        "granularity_divisor": environ.get("GRANULARITY_DIVISOR"),
        "start_time": environ.get("START_TIME"),
        "end_time": environ.get("END_TIME"),
    }
    found_kwargs = {}
    for k in env_lookup.keys():
        if env_lookup[k] is not None:
            v = env_lookup[k]
            if k == "error_thresholds":
                v = tuple([float(x) for x in v.split(",")])
            elif k == "destination_metric_tags":
                v = v.split(",")
            elif k == "granularity_divisor" or k == "start_time" or k == "end_time":
                v = int(v)
            found_kwargs[k] = v
    return StatsConfig(**found_kwargs)

