# Start server using
#   Recommended:
#     uvicorn demo:app --host 0.0.0.0 --port 8001 --workers 4
#   Alternative:
#     gunicorn demo:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8001 --workers 4

import logging

import hapiserver
logging.getLogger('hapiserver').setLevel(logging.DEBUG)

from bin.info import info
from bin.data import data
from bin.catalog import catalog

config = {
  "path": "/hapi",
  "functions": {
    "catalog": catalog,
    "info": info,
    "data": data
  },
  "about": {
    "id": "Demo",
    "title": "Demo HAPI Server using hapiserver Python package"
  }
}

app = hapiserver.app(config)
