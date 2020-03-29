from dead.config import StatsConfig, LoggingConfig, ErrorThreshold
from dead.log import logger

from typing import Dict, List, Union, Tuple
from dataclasses import dataclass

import datadog


@dataclass(frozen=True)
class Point:
    timestamp: float
    value: float


def availability(pointlist: List[Point], threshold: ErrorThreshold) -> float:
    breaches = [p for p in pointlist if p.value > threshold]
    return 100 - len(breaches) / len(pointlist) * 100


class Dead(object):
    """Datadog Error-rate to Availability Deducer"""
    def __init__(self, stats_config: StatsConfig, log_config: LoggingConfig):
        self._logger = logger(name=__name__, config=log_config)
        self._stats_config = stats_config
        datadog.initialize(api_key=self._stats_config.api_key, app_key=self._stats_config.app_key)
        self._query_result: Dict = {}
        self._error_rate: List[Point] = []
        self._availability: Dict[ErrorThreshold, List[Point]] = {}
        self._metrics = []

    @property
    def stats_config(self) -> StatsConfig:
        return self._stats_config

    @property
    def query_result(self) -> Dict:
        if not self._query_result:
            self._query_result = datadog.api.Metric.query(
                start=self.stats_config.start_time,
                end=self.stats_config.end_time,
            )
        return self._query_result

    @property
    def error_rate(self) -> List[Point]:
        if not self._error_rate:
            self._error_rate = [
                Point(timestamp=p[0], value=p[1])
                for p in self.query_result["series"][0]["pointlist"]
            ]
            self._logger.info(f"Retrieved {len(self._error_rate)} measurements "
                              f"for query {self.stats_config.source_metric_query}")
        return self._error_rate

    @property
    def availability(self) -> Dict[ErrorThreshold, List[Point]]:
        """
        Availability is represented by a dictionary, keyed by error threshold. The value is a list of Points.
        Where granularity_divisor is 1, the list will be a single Point representing an availability metric for the
        entire time period of the source data
        For an hour time period, with 60 points, you can report availability per 10 minutes by providing a
        granularity_divisor of 6. By the same logic, you can provide a granularity divisor of 60, and
        report boolean availability (i.e up or down) per metric.
        Upper bound of granularity divisor is limited to the number of measurements available - even if given
        correctly, we can sometimes have missing metrics
        """
        if not self._availability:
            gd = self.stats_config.granularity_divisor
            if gd > len(self.error_rate):
                self._logger.warning(f"Configured granularity divisor ({gd}) greater than metric samples " +
                                     f"available ({len(self.error_rate)}) - aligning")
                gd = len(self.error_rate)
            n = int(len(self.error_rate) / gd)
            # Split source pointlist into chunks of size n
            pl_groups = [self.error_rate[i * n:(i + 1) * n]
                         for i in range((len(self.error_rate) + n - 1) // n)]
            self._availability = {
                t: [Point(timestamp=p[-1].timestamp,
                          value=availability(pointlist=p, threshold=t))
                    for p in pl_groups]
                for t in self.stats_config.error_thresholds
            }
        return self._availability

    @property
    def metrics(self) -> List[Dict[str, Union[str, List[str], List[Tuple[float, float]]]]]:
        if not self._metrics:
            self._metrics = [
                {
                    "metric": f"{self.stats_config.destination_metric_name}.{e}",
                    "tags": self.stats_config.destination_metric_tags,
                    "type": "gauge",
                    "points": [
                        (p.timestamp, p.value)
                        for p in points
                    ],
                } for e, points in self.availability.items()
            ]
        return self._metrics

    def send(self) -> Dict[str, str]:
        return datadog.api.Metric.send(metrics=self.metrics, attach_host_name=False)


