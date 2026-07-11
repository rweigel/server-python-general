def data(dataset, parameters, start, stop, format=None):
  # Start and stop passed are always to nanosecond precision
  import pandas
  data = [
    ['1970-01-01T00:00:00Z', 0],
    ['1970-01-01T00:00:01Z', 1]
  ]

  # Convert to CSV
  df = pandas.DataFrame(data, columns=["Time", "scalar"])
  csv_data = df.to_csv(index=False)
  return csv_data
