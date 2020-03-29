# DataDog Error-rate to Availability Deducer

Deduce availability from a DataDog error rate query

Availability can be calculated as the amount of time (aka number of samples)
where the error rate was greater than the acceptable error threshold.

Given a metric query that returns an error percentage for a time period, and an
acceptable error rate, it will count all of the samples where the error rate
was greater than the acceptable error rate, divided by the number of samples
available, then multiply this number by 100 to return an availability
percentage for that time period. It also supports multiple acceptable error
rates, allowing for greater flexibility when setting metric thresholds

An example error percentage query:

```
100*(sum:fastly.status_5xx{fastly:service_name:production}.rollup(avg, 60)/sum:fastly.requests{fastly:service_name:production}.rollup(avg, 60))
```

## Rollup and Delayed Evaluation

It is recommended to use [rollup][dd_doc_rollup] with each of the metrics used,
to give more predictable results. You should also research/be aware of the
available granularity for the metrics involved.

To support this, as well as to provide better accuracy with delayed metrics, by
default this software evaluates a one hour time window, ending one hour ago.

[dd_doc_rollup]: https://docs.datadoghq.com/dashboards/functions/rollup/

# Configuration

## Time Period

Time period is not currently configurable by environment variables, and will
default to fetching one hours worth of metrics, ending one hour ago.

## Environment Variables

The following environment variables are required:

* `DATADOG_API_KEY` - API key for DataDog
* `DATADOG_APP_KEY` - APP key for DataDog
* `SOURCE_METRIC_QUERY` - A DataDog metric query string, that returns the error
  rate metric
* `ERROR_THRESHOLDS` - A comma-separated list of ints or floats that correspond
  to acceptable error thresholds. (e.g `0.1,0.02,0.01`). This software supports
  multiple error thresholds, each of which will result in a corresponding
  destination metric
* `DESTINATION_METRIC_TAGS` - A comma separated list of metric tags, in
  key:value format (e.g `env_type:production,env_name:production,aws_region:us-east-1`)
* `DESTINATION_METRIC_NAME` - The name of the destination metric (e.g
  `my.availability.metric`). Will be post-fixed with each of the given error
  thresholds given in `ERROR_THRESHOLDS`

The following environment variables are optional:

* `GRANULARITY_DIVISOR` - By default, this is `1`, which will result in a
  single availability metric covering the entire time period. For an hour time
  period, providing 1 metric point per minute, you can report availability per
  10 minutes by providing a granularity_divisor of `6`. By the same logic, you
  can provide a granularity divisor of `60`, which will result in a binary
  up/down availability metric for each of the per-minute metrics available. The
  upper bound of this metric is limited by the number of metric points
  available. The number of points returned will vary wildly depending upon the
  source metric; make sure to explore your metric data rather than making
  assumptions
* `LOG_LEVEL` - Configure the log level. Default: `INFO`
* `LOG_STDOUT` - if configured, and set to a 'truthy' string, then logging
  output will go to stdout

# Testing

Run all tests:

```bash
make test
```
