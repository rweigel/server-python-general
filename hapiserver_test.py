# Usage:
#   python serve_test.py [<config_file>]

import time
import logging
import requests

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


def log_test_title(url):
  line = len(url)*"-"
  logger.info(line)
  logger.info(f"Testing {url}")
  logger.info(line)



def run_tests(port, config_file):

  url_base = f"http://0.0.0.0:{port}/hapi"

  wait = {
    "url": url_base,
    "retries": 10,
    "delay": 0.5
  }
  import utilrsw.uvicorn
  utilrsw.uvicorn.start('hapiserver.app', config=config_file, wait=wait)

  url = url_base
  log_test_title(url)
  response = requests.get(url)
  assert response.status_code == 200
  assert 'text/html' in response.headers['Content-Type']
  assert 'HAPI' in response.text

  url = f"{url_base}/catalog"
  response = requests.get(url)
  assert response.status_code == 200
  assert 'application/json' in response.headers['Content-Type']
  assert 'catalog' in response.json()
  assert len(response.json()['catalog']) > 0

  url = f"{url_base}/info?dataset=S000028"
  response = requests.get(url)
  assert response.status_code == 200
  assert 'application/json' in response.headers['Content-Type']
  assert 'parameters' in response.json()
  assert len(response.json()['parameters']) > 0

  url = f"{url_base}/info?xdataset=S000028"
  response = requests.get(url)
  assert response.status_code == 400
  assert 'application/json' in response.headers['Content-Type']
  assert 'status' in response.json()
  assert response.json()['status']['code'] == 1401

  url = f"{url_base}/data?dataset=S000028&&start=2025-10-20T00:00:00Z&stop=2025-10-20T00:00:01Z"
  response = requests.get(url)
  assert response.status_code == 200
  assert 'text/csv' in response.headers['Content-Type']
  assert response.text.startswith('2025-10-20T00:00:00Z')

  url = f"{url_base}/data?dataset=S000028&&start=2025-10-20T00:00:00Z&stop=2025-10-20T00:00:01Z&parameters=Field_Vector"
  response = requests.get(url)
  assert response.status_code == 200
  assert 'text/csv' in response.headers['Content-Type']
  assert response.text.startswith('2025-10-20T00:00:00Z')

if __name__ == "__main__":
  import sys
  if len(sys.argv) > 1:
    config_file = sys.argv[1]
  else:
    config_file = "/Users/weigel/git/hapi/server-python-general/bin/psws/config.json"
  run_tests(5999, config_file)
