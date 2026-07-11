def catalog():
  return [{"id": "demo1"}]

if __name__ == "__main__":
  import json
  print(json.dumps(catalog(), indent=2))