from dead.dog import Dead
from dead.config import logging_config_env_builder, stats_config_env_builder


def lambda_handler(_, __):
    d = Dead(stats_config=stats_config_env_builder(),
             log_config=logging_config_env_builder())
    d.send()
