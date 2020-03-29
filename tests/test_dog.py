from dead import dog
from dead.config import StatsConfig, logging_config_env_builder

import json
from collections import defaultdict
from typing import Type

import pytest
from requests import Response
from datadog.api.http_client import RequestClient


def dd_results_1() -> bytes:
    return open('tests/fixtures/dd_results_1.json', 'rb').read()


class MockRequestClient(RequestClient):
    @staticmethod
    def get() -> Type[Response]:
        r = Response
        r.status_code = 200
        r.content = dd_results_1()
        return r

    @staticmethod
    def post() -> Type[Response]:
        r = Response
        r.status_code = 202
        r.content = '{"status": "ok"}'.encode("utf-8")
        return r


def test_availability():
    pls = {
        "one_point": [dog.Point(*[1583607420000.0, 0.0016489296797448777])],
        "two_point_same": [
            dog.Point(*[1583607420000.0, 0.0016489296797448777]),
            dog.Point(*[1583607420000.0, 0.0016489296797448777])
        ],
        "two_point": [
            dog.Point(*[1583607420000.0, 0.01]),
            dog.Point(*[1583607480000.0, 0.02]),
        ],
        "five_point": [
            dog.Point(*[1583607240000.0, 0.01]),
            dog.Point(*[1583607300000.0, 0.02]),
            dog.Point(*[1583607360000.0, 0.03]),
            dog.Point(*[1583607420000.0, 0.04]),
            dog.Point(*[1583607480000.0, 0.05]),
        ],
    }
    test_cases = [
        {
            "name": "Single point should be 100% available at 1% error rate",
            "input": [pls["one_point"], 1],
            "expected": 100.0
        },
        {
            "name": "Single point should be 0% available at 0.0000001% error rate",
            "input": [pls["one_point"], 0.0000001],
            "expected": 0.0
        },
        {
            "name": "Two points the same should be 100% available at 1% error rate",
            "input": [pls["two_point_same"], 1],
            "expected": 100.0
        },
        {
            "name": "Two points the same should be 0% available at 0.0000001% error rate",
            "input": [pls["two_point_same"], 0.0000001],
            "expected": 0.0
        },
        {
            "name": "Two points should be 50% available at 0.01% error rate",
            "input": [pls["two_point"], 0.01],
            "expected": 50.0
        },
        {
            "name": "Two points should be 0% available at 0.001% error rate",
            "input": [pls["two_point"], 0.001],
            "expected": 0.0
        },
        {
            "name": "Five points should be 20% available at 0.01% error rate",
            "input": [pls["five_point"], 0.01],
            "expected": 20.0
        },
        {
            "name": "Five points should be 80% available at 0.044% error rate",
            "input": [pls["five_point"], 0.044],
            "expected": 80.0
        },
    ]
    for test_case in test_cases:
        assert test_case["expected"] == dog.availability(*test_case["input"]), test_case["name"]


def test_dead(monkeypatch):
    def mock_request_client(*args, **kwargs):
        if kwargs["method"] == "POST":
            return MockRequestClient.post()
        return MockRequestClient().get()

    monkeypatch.setattr(RequestClient, "request", mock_request_client)
    fixture = json.loads(dd_results_1())
    et = (0.1, 0.01, 0.005, 0.001)

    cfg_div_1 = StatsConfig(
        error_thresholds=et,
        source_metric_query="qry",
        destination_metric_tags=["foo:bar"],
        destination_metric_name="foo",
        granularity_divisor=1,
        api_key="foo",
        app_key="bar",
    )
    d1 = dog.Dead(stats_config=cfg_div_1, log_config=logging_config_env_builder())
    assert cfg_div_1.start_time == d1.stats_config.start_time
    assert cfg_div_1.end_time == d1.stats_config.end_time
    assert d1.error_rate[10].timestamp == fixture["series"][0]["pointlist"][10][0]
    assert d1.error_rate[11].value == fixture["series"][0]["pointlist"][11][1]
    assert len(d1.error_rate) == len(fixture["series"][0]["pointlist"])
    assert len(d1.availability[et[0]]) == cfg_div_1.granularity_divisor
    assert d1.availability[et[0]][0].value == 100.0
    assert d1.availability[et[1]][0].value == 96.66666666666667
    assert d1.availability[et[2]][0].value == 76.66666666666667
    assert d1.availability[et[3]][0].value == 1.6666666666666714
    assert d1.metrics[0]["points"][0][0] == d1.availability[et[0]][0].timestamp
    assert d1.metrics[0]["metric"] == f"{cfg_div_1.destination_metric_name}.{et[0]}"
    assert d1.send()["status"] == "ok"

    cfg_div_6 = StatsConfig(
        error_thresholds=et,
        source_metric_query="qry",
        destination_metric_tags=["foo:bar"],
        destination_metric_name="foo",
        granularity_divisor=6,
        api_key="foo",
        app_key="bar",
    )
    d6 = dog.Dead(stats_config=cfg_div_6, log_config=logging_config_env_builder())
    assert len(d6.availability[et[0]]) == cfg_div_6.granularity_divisor
    assert d6.availability[et[1]][4].value == 100.0
    assert d6.availability[et[1]][4].timestamp < d6.availability[et[1]][5].timestamp
    assert d6.availability[et[2]][2].value == 50.0
    assert d6.availability[et[-1]][5].value == 0.0
    assert d6.metrics[-1]["points"][-1][1] == d6.availability[et[-1]][0].value
    assert d6.send()["status"] == "ok"

    cfg_div_60 = StatsConfig(
        error_thresholds=et,
        source_metric_query="qry",
        destination_metric_tags=["foo:bar"],
        destination_metric_name="foo",
        # should be upper bound by number of points
        granularity_divisor=61,
        api_key="foo",
        app_key="bar",
    )
    d60 = dog.Dead(stats_config=cfg_div_60, log_config=logging_config_env_builder())
    # When divisor is the same as number of inputs, we should only have 0.0 or 100.0
    assert len(d60.availability[et[2]]) == 60
    found = defaultdict(int)
    for d in d60.availability[et[2]]:
        found[d.value] += 1
    assert len(found.keys()) == 2
    assert found[100.0] == 46
    assert found[0.0] == 14


