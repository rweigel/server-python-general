"""
Usage:
  python data.py <dataset> <parameters> <start> <stop> [format] [config_file]

Examples:

  All parameters (parameters = '' => all parameters):
    python data.py demo1 '' 1970-01-01T00:00:00Z 1970-01-01T00:00:01Z

  Only primary time parameter:
    python data.py demo1 Time 1970-01-01T00:00:00Z 1970-01-01T00:00:01Z

  One parameter (primary time parameter is always included):
    python data.py demo1 scalar 1970-01-01T00:00:00Z 1970-01-01T00:00:01Z

  Two parameters:
    python data.py demo1 Time,scalar 1970-01-01T00:00:00Z 1970-01-01T00:00:01Z
"""

import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


def _read_file(file_name, parameters):
  """
  Simulate a data source that provides data in chunks of 1 minute.
  _read_file() always returns data in one-minute chunks that start on the
  0th minute of each hour.
  """

  import pandas

  logger.debug(f"Reading {file_name}")

  start, stop = file_name.replace(".bin", "").split('_')
  start = pandas.Timestamp(start)
  stop = pandas.Timestamp(stop)

  # Create a DataFrame with time from start to stop with 1 second cadence
  # and a scalar value that is the number of seconds since 1970-01-01T00:00:00Z

  time_index = pandas.date_range(start=start, end=stop, freq='1s', inclusive='left')
  data = pandas.DataFrame(index=time_index)
  data['Time'] = data.index.strftime('%Y-%m-%dT%H:%M:%SZ')
  data['scalar'] = (data.index - pandas.Timestamp('1970-01-01T00:00:00Z')) // pandas.Timedelta('1s')

  if not parameters:
    return data[['Time', 'scalar']]

  columns = ['Time']
  columns.extend(parameter for parameter in parameters.split(',') if parameter != 'Time')
  return data[columns]


def data(dataset, parameters, start, stop, format=None, config=None):
  # Start and stop passed are always to nanosecond precision

  import pandas

  chunk_size = {'minutes': 1}
  tfmt = '%Y-%m-%dT%H:%MZ'

  if format not in (None, 'csv'):
    raise ValueError(f"Unsupported format: {format}")

  request_start = pandas.Timestamp(start)
  request_stop = pandas.Timestamp(stop)
  if request_start >= request_stop:
    raise ValueError("start must be before stop")

  files = []
  chunk_start = request_start.floor('min')
  while chunk_start < request_stop:
    chunk_stop = chunk_start + pandas.Timedelta(**chunk_size)
    file_name = f"{chunk_start.strftime(tfmt)}_{chunk_stop.strftime(tfmt)}.bin"
    files.append(file_name)
    chunk_start = chunk_stop

  logger.debug(f"Files to read: {files}")

  first_output = True
  for file_name in files:
    chunk = _read_file(file_name, parameters)
    chunk = chunk[(chunk.index >= request_start) & (chunk.index < request_stop)]

    if not chunk.empty:
      yield chunk.to_csv(index=False, header=first_output)
      first_output = False



if __name__ == "__main__":
  import sys

  if len(sys.argv) < 5 or len(sys.argv) > 7:
    print("Usage: data.py <dataset> <parameters> <start> <stop> [format] [config_file]")
    sys.exit(1)

  format = sys.argv[5] if len(sys.argv) > 5 else None
  if len(sys.argv) > 6:
    import json
    config_file = sys.argv[6]
    with open(config_file) as file:
      config = json.load(file)
  else:
    config = None

  for chunk in data(*sys.argv[1:5], format=format, config=config):
    sys.stdout.write(chunk)