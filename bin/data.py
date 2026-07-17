def data(dataset, parameters, start, stop, format=None):
  # Start and stop passed are always to nanosecond precision

  import os
  import ast
  import pandas

  # ENV variable given in config JSON file
  SERVERCONFIG = os.getenv("SERVER_CONFIG")

  # Parse SERVERCONFIG as dict string
  server_config = ast.literal_eval(SERVERCONFIG)

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
