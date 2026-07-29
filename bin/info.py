def info(dataset, config=None):
  datasets = {
    "demo1": {
      "startDate": "1970-01-01Z",
      "stopDate": "1970-01-01T00:00:02Z",
      "sampleStartDate": "1970-01-01Z",
      "sampleStopDate": "1970-01-01T00:00:02Z",
      "cadence": "PT1S",
      "parameters": [
        {
          "name": "Time",
          "type": "isotime",
          "units": "UTC",
          "fill": None,
          "length": 24
        },
        {
          "name": "scalar",
          "type": "double",
          "units": "m",
          "fill": "nan",
          "description": "A scalar time series"
        }
      ]
    }
  }

  return datasets[dataset]


if __name__ == "__main__":
  from hapiserver.cli import cl_call
  cl_call(info)