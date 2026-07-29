# Start server using
#   Recommended:
#     uvicorn demo-app:app --host 0.0.0.0 --port 8001 --workers 4
#   Alternative:
#     gunicorn demo-app:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8001 --workers 4

import logging

import hapiserver
logging.getLogger('hapiserver').setLevel(logging.DEBUG)

# Set method for specifying catalog, info, and data functions in config.
method = 3

config_o = {
  "path": "/hapi",
  # Store config used by scripts or functions for catalog, info, and data in ENV.
  "ENV": {
    "DATA_DIR": "data",
    "CACHE_DIR": "cache",
    "BIN_DIR": "bin"
  },
  "about": {
    "id": "Demo",
    "title": "Demo HAPI Server using hapiserver Python package"
  },
  "capabilities": {
    # outputFormats is anything supported by the data() function.
    "outputFormats": ["csv"],
    # catalogDepthOptions is anything supported by the catalog() function.
    "catalogDepthOptions": ["dataset", "all"]
  }
}

if method == 1:
  # Import functions and include in config.

  from bin.info import info
  from bin.data import data
  from bin.catalog import catalog

  functions = {
    "catalog": catalog,
    "info": info,
    "data": data
  }

  config = config_o.copy()
  config.update({"functions": functions})
  app = hapiserver.app(config)

if method == 2:
  # Include functions in config as strings and resolve at runtime.
  # Useful when config is stored in a .json file.

  config = config_o.copy()
  config.update({
    "functions": {
      "catalog": "bin.catalog.catalog",
      "info": "bin.info.info",
      "data": "bin.data.data"
    }
  })

  app = hapiserver.app(config)

if method == 3:
  # Reference command line scripts for catalog, info, and data.
  # Useful when config is stored in a .json file.
  # Here $BIN_DIR is replaced with the value of config["ENV"]["BIN_DIR"]
  # and if it is a relative path, it is resolved relative to current working
  # directory.
  config = config_o.copy()
  config.update({
    "scripts": {
      "catalog": "$BIN_DIR/catalog.py --depth={depth} --config={config}",
      "info": "$BIN_DIR/info.py --dataset={dataset} --config={config}",
      "data": "$BIN_DIR/data.py --dataset={dataset} --parameters={parameters} --start={start} --stop={stop} --format={format} --config={config}"
    }
  })

  app = hapiserver.app(config)
