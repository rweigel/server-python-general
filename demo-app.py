# Start server using
#   Recommended:
#     uvicorn demo-app:app --host 0.0.0.0 --port 8001 --workers 4
#   Alternative:
#     gunicorn demo-app:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8001 --workers 4

import logging

import hapiserver
logging.getLogger('hapiserver').setLevel(logging.DEBUG)

# Set method for specifying catalog, info, and data functions in config.
method = 1

if method == 1:
  # Import functions and include in config.
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

if method == 2:
  # Include functions in config as strings and resolve at runtime.
  config = {
    "path": "/hapi",
    "functions": {
      "catalog": "bin.catalog.catalog",
      "info": "bin.info.info",
      "data": "bin.data.data"
    },
    "about": {
      "id": "Demo",
      "title": "Demo HAPI Server using hapiserver Python package"
    }
  }

  app = hapiserver.app(config)