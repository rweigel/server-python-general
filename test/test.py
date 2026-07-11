# Usage:
#   python test.py
#
# See
#  python test.py --help
# for configuration options, e.g.,
#  python test.py --config config.json --port 8080

import logging

format = '%(name)s %(levelname)s: %(message)s'
logging.basicConfig(level=logging.DEBUG, format=format)
logger = logging.getLogger(__name__)

wait = {
  "retries": 10,
  "delay": 0.5
}

def log_test_title(url):
  line = len(url)*"-"
  logger.info(line)
  logger.info(f"Testing {url}")
  logger.info(line)


def run_tests(configs, wait):
  import requests
  import utilrsw.uvicorn

  port = configs['server']['--port']
  url_base = f"http://0.0.0.0:{port}/hapi"

  wait['url'] = url_base

  utilrsw.uvicorn.start('hapiserver.app', configs, wait)

  url = url_base
  log_test_title(url)
  response = requests.get(url)
  assert response.status_code == 200
  assert 'text/html' in response.headers['Content-Type']
  assert 'HAPI' in response.text

  if False:
    url = url_base
    log_test_title(url)
    response = requests.get(url)
    assert response.status_code == 404
    exit()

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

  for dataset in catalog:
    url = f"{url_base}/info?dataset={dataset['id']}"
    response = requests.get(url)
    assert response.status_code == 200
    assert 'application/json' in response.headers['Content-Type']


def test_scripts():
  import hapiserver
  config = "config.json"

  # Get default configs and override with command line arguments.
  configs = hapiserver.cli(config=config)
  run_tests(configs, wait)

if __name__ == "__main__":
  test_scripts()
