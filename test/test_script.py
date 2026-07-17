# Usage:
#   python test_script.py

import logging

format = '%(name)s %(levelname)s: %(message)s'
logging.basicConfig(level=logging.DEBUG, format=format)
logger = logging.getLogger(__name__)

wait = {
  "retries": 10,
  "delay": 0.5
}

def test_scripts():
  import pathlib
  config = pathlib.Path(__file__).parent / "configs" / "demo-scripts.json"
  _run_tests(config)


def test_functions():
  import pathlib
  config = pathlib.Path(__file__).parent / "configs" / "demo-functions.json"
  _run_tests(config)


def _run_tests(config):
  import requests

  import hapiserver

  # Get default configs and override with command line arguments.
  configs = hapiserver.cli(config=config)

  port = configs['server']['--port']
  url_base = f"http://0.0.0.0:{port}/hapi"

  wait['url'] = url_base

  process = hapiserver.start(configs, wait)

  _log_test_title(url_base)

  url = url_base
  response = requests.get(url)
  assert response.status_code == 200
  assert 'text/html' in response.headers['Content-Type']

  url = f"{url_base}/catalog"
  response = requests.get(url)
  assert response.status_code == 200
  assert 'application/json' in response.headers['Content-Type']
  response_json = response.json()
  assert 'catalog' in response_json
  catalog = response_json['catalog']
  assert isinstance(catalog, list)
  assert len(catalog) > 0
  assert 'HAPI' in response_json
  assert 'status' in response_json

  url = f"{url_base}/capabilities"
  response = requests.get(url)
  assert response.status_code == 200
  assert 'application/json' in response.headers['Content-Type']
  capabilities = response.json()
  assert isinstance(capabilities, dict)
  assert 'outputFormats' in capabilities
  assert 'HAPI' in response_json
  assert 'status' in response_json


  for dataset in catalog:
    url = f"{url_base}/info?dataset={dataset['id']}"
    response = requests.get(url)
    assert response.status_code == 200
    assert 'application/json' in response.headers['Content-Type']
    info = response.json()
    assert isinstance(info, dict)
    assert 'HAPI' in info
    assert 'status' in info
    assert 'parameters' in info

    url = f"{url_base}/data?dataset={dataset['id']}&start=1970-01-01T00:00:00Z&stop=1970-01-01T00:00:01Z"
    response = requests.get(url)
    assert response.status_code == 200
    assert 'text/csv' in response.headers['Content-Type']


  # Test 404 responses
  url = f"{url_base}x"
  _log_test_title(url)
  response = requests.get(url)
  assert response.status_code == 404

  for endpoint in ['', 'catalog', 'info', 'data', 'about']:
    url = f"{url_base}/{endpoint}x"
    _log_test_title(url)
    response = requests.get(url)
    assert response.status_code == 404

  hapiserver.stop(process)


def _log_test_title(url):
  msg = f"Testing {url}"
  line = len(msg)*"-"
  logger.info(line)
  logger.info(msg)
  logger.info(line)


if __name__ == "__main__":
  #test_scripts()
  test_functions()
