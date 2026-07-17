def data(dataset, parameters, start, stop, format=None, config=None):
  # Start and stop passed are always to nanosecond precision

  import pandas

  server_config = config if config is not None else {}
  yield_by_row = server_config.get("data", {}).get("yield_by_row", False)

  data = [
    ['1970-01-01T00:00:00Z', 0],
    ['1970-01-01T00:00:01Z', 1]
  ]

  if yield_by_row:
    # To reduce memory usage, can yield data in chunks. As a general rule,
    # choose largest chunk size for which first yield takes less than ~1 second.
    for row in data:
      yield ','.join(str(v) for v in row) + '\n'
  else:
    # Convert all data to CSV and yield as a single string
    df = pandas.DataFrame(data, columns=["Time", "scalar"])
    csv_data = df.to_csv(index=False)
    yield csv_data

if __name__ == "__main__":
  import sys

  if len(sys.argv) < 5:
    print("Usage: data.py <dataset> <parameters> <start> <stop> [format] [config_file]")
    sys.exit(1)
  if len(sys.argv) == 6:
    import json
    config_file = sys.argv[5]
    config = json.load(open(config_file))
  else:
    config = None

  format = sys.argv[5] if len(sys.argv) > 5 else None

  for chunk in data(*sys.argv[1:5], format=format, config=config):
    print(chunk, end='')