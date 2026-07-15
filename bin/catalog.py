def catalog():
  """
  Note that catalog responses should be fast (not much slower than the time to
  read and send a file the size of a catalog from disk). If building the catalog
  requires a long time, consider caching the catalog response in a file
  and updating the file when there is a change.
  """
  return [
    {"id": "demo1", "title": "Demo dataset 1"}
  ]

if __name__ == "__main__":
  import json
  print(json.dumps(catalog(), indent=2))