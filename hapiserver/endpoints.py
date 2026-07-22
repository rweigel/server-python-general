import json
import logging

import hapiserver

logger = logging.getLogger(__name__)


# Endpoint response functions
def hapi(query_params, config):
  import os

  error = _query_param_error('hapi', query_params)
  if error:
    logger.debug(f"_query_param_error() returned error: {error}")
    return hapiserver.error(error, config)

  default = os.path.normpath(os.path.join(os.path.dirname(__file__)))
  default = os.path.join(default, "..", "html", "index.html")
  fname = config.get("index.html", None)
  if fname is None:
    logger.debug(f"No index.html configured, using default: {default}")
    fname = default

  logger.debug("Reading: " + fname)
  try:
    with open(fname) as f:
      content = f.read()
      response = {
        "status_code": 200,
        "content": content,
      }
  except Exception as e:
    logger.error(f"Error reading {fname}: {e}")
    response = {
      "status_code": 404,
      "content": "Not Found",
    }

  response['headers'] = _headers(config, cors=False)
  response['media_type'] = "text/html"
  return response


def about(query_params, config):
  import json

  error = _query_param_error('about', query_params)
  if error:
    logger.debug(f"_query_param_error() returned error: {error}")
    return hapiserver.error(error, config)

  content = {
    "HAPI": hapiserver.HAPI_VERSION,
    "status": {
      "code": 1200, "message": "OK"
    },
    **config['about']
  }
  return {
    "content": json.dumps(content, indent=2),
    "media_type": "application/json",
    "headers": _headers(config),
  }


def capabilities(query_params, config):
  import json

  error = _query_param_error('capabilities', query_params)
  if error:
    logger.debug(f"_query_param_error() returned error: {error}")
    return hapiserver.error(error, config)

  content = {
    "HAPI": hapiserver.HAPI_VERSION,
    "status": {
      "code": 1200,
      "message": "OK"
    },
    **config.get('capabilities', {"outputFormats": ["csv"]})
  }
  return {
    "content": json.dumps(content, indent=2),
    "media_type": "application/json",
    "headers": _headers(config),
  }


def catalog(query_params, config):

  error = _query_param_error('catalog', query_params)
  if error:
    logger.debug(f"_query_param_error() returned error: {error}")
    return hapiserver.error(error, config)

  catalog, error = _call('catalog', query_params, config)
  if error:
    return hapiserver.error(error, config)

  content = {
    "HAPI": hapiserver.HAPI_VERSION,
    "status": {
      "code": 1200,
      "message": "OK"
    },
    "catalog": catalog
  }

  response = {
    "content": json.dumps(content, indent=2),
    "media_type": "application/json",
    "headers": _headers(config),
  }

  return response


def info(query_params, config):

  error = _query_param_error('info', query_params)
  if error:
    logger.debug(f"_query_param_error() returned error: {error}")
    return hapiserver.error(error, config)

  info, error = _call('info', query_params, config)
  if error:
    return hapiserver.error(error, config)

  if isinstance(info, str):
    info = json.loads(info)

  content = {
    "HAPI": hapiserver.HAPI_VERSION,
    "status": {
      "code": 1200,
      "message": "OK"
    },
    **info
  }

  return {
    "content": json.dumps(content, indent=2),
    "media_type": "application/json",
    "headers": _headers(config),
  }


def data(query_params, config):

  error = _query_param_error('data', query_params)
  if error:
    logger.debug(f"_query_param_error() returned error: {error}")
    return hapiserver.error(error, config)

  data, error = _call('data', query_params, config)
  if error:
    return hapiserver.error(error, config)

  response = {
    "content": data,
    "media_type": "text/csv",
    "headers": _headers(config),
  }

  return response


def _query_params_dict(query_params):
  """Convert Starlette QueryParams to a plain dict.

  Args:
    query_params: Starlette QueryParams object

  Returns:
    dict: Plain dictionary with query parameter keys and values
  """

  if isinstance(query_params, dict):
    return query_params

  result = {}
  for key in query_params.keys():
    values = query_params.getlist(key)
    if len(values) == 1:
      result[key] = values[0]
    else:
      result[key] = values

  return result


def _query_param_error(endpoint, query):

  logger.debug("_query_param_error(): Checking query parameters.")

  query = _query_params_dict(query)

  if endpoint == 'hapi':
    allowed = []
    required = []

  if endpoint == 'capabilities':
    allowed = []
    required = []

  if endpoint == 'about':
    allowed = []
    required = []

  if endpoint == 'catalog':
    allowed = [] # TODO: Add support for depth and resolve_references
    required = []

  if endpoint == 'info':
    allowed = ["dataset"]
    required = ["dataset"]

  if endpoint == 'data':
    allowed = ["dataset", "start", "stop", "parameters"]
    required = ["dataset", "start", "stop"]

  for p in query:
    if p not in allowed and not p.startswith('x_'):
      return {
        "code": 1401,
        "message": f"Unknown query parameter '{p}'. Allowed: {', '.join(allowed)}",
        "message_console": f"Unknown query parameter '{p}'"
      }

  for p in required:
    if p not in query:
      return {
        "code": 1400,
        "message": f"Missing '{p}' parameter"
      }

  return None


def _call(endpoint, query_params, config):
  logger.debug(f"/{endpoint} query str:  '{query_params}'")
  query = _query_params_dict(query_params)
  logger.debug(f"/{endpoint} query dict: {query}")

  args = {}
  if endpoint == 'info':
    dataset, error = _get('dataset', query, config)
    args = {"dataset": dataset}
    if error:
      logger.debug(f"_get() returned error: {error}")
      return None, error

  if endpoint == 'data':
    args = {}
    for p in ['dataset', 'parameters', 'start', 'stop']:
      args[p], error = _get(p, query, config)
      if error:
        return None, error

  if 'scripts' in config and endpoint in config['scripts']:

    args = [str(args[x]) for x in args.keys()]

    if len(args) > 0:
      data, error = hapiserver.exec(config["scripts"][endpoint], args=args)
    else:
      data, error = hapiserver.exec(config["scripts"][endpoint])
    if error:
      message = "Script returned error"
      error = {
        "code": 1500,
        "message": message,
        "message_console": message,
        "exception": error
      }
      return None, error

    if endpoint == 'data':
      # For /data, the script is expected to return CSV data as a string.
      # Return directly in the response.
      return data, None

    try:
      data = json.loads(data)
    except Exception as e:
      message = f"Error parsing JSON returned by script: '{data}'"
      error = {
        "code": 1500,
        "message": message,
        "message_console": message,
        "exception": e
      }
      return None, error

    return data, None


  if 'functions' in config and endpoint in config['functions']:
    func = config['functions'][endpoint]
    logger.debug(f"Calling {func}({args})")
    try:
      args = [str(args[x]) for x in args.keys()]
      if len(args) > 0:
        data = func(*args)
      else:
        data = func()
    except Exception as e:
      message = f"Error executing {endpoint} function"
      error = {
        "code": 1500,
        "message": message,
        "message_console": message,
        "exception": e
      }
      logger.debug(f"Error executing {endpoint} function: {e}")
      return None, error

    return data, None

  return None, {
    "code": 1500,
    "message": f"No script or function configured for endpoint '{endpoint}'"
  }


def _headers(config, cors=True):
  server = f"HAPI/{hapiserver.HAPI_VERSION} Server"
  server += ";https://github.com/hapi-server/server-python-general"
  server += f"; v{hapiserver.__version__}"
  headers = {"Server": server}
  if cors:
    headers.update({
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Headers": "*",
      "Access-Control-Allow-Methods": "GET, HEAD, OPTIONS",
    })
  return headers


def _get(name, query, config):

  import json

  if name == 'dataset':
    response = catalog({}, config)
    if response.get('status_code', 200) != 200:
      return None, {"code": response.get('status_code', 1500), "message": "Failed to get catalog"}

    try:
      datasets = json.loads(response['content'])['catalog']
    except Exception as e:
      error = {
        "code": 1500,
        "message_console": f"_get(): Error parsing catalog JSON: {e}"
      }
      return None, error

    dataset_ids = [dataset['id'] for dataset in datasets]
    if query['dataset'] not in dataset_ids:
      error = {
        "code": 1406,
        "message": f"Invalid dataset. Allowed datasets: {', '.join(dataset_ids)}",
        "message_console": f"_get(): dataset '{query['dataset']}' not found in catalog"
      }
      return None, error

    return query['dataset'], None


  # TODO: Validate start/stop
  if name == 'start':
    return query['start'], None

  if name == 'stop':
    return query['stop'], None

  if name == 'parameters':

    if 'parameters' not in query:
      return '', None
    parameters = query['parameters']
    if parameters is None:
      return '', None
    if parameters == '':
      return '', None

    response = info({'dataset': query['dataset']}, config)
    if response.get('status_code', 200) != 200:
      return None, {"code": response.get('status_code', 1500), "message": "Failed to get info"}

    try:
      info_content = json.loads(response['content'])
    except Exception as e:
      error = {
        "code": 1500,
        "message_console": f"_get(): Error parsing info JSON: {e}"
      }
      return None, error


    parameters_known = []
    if parameters:
      parameters_known = [p['name'] for p in info_content.get('parameters', [])]

    for p in parameters.split(","):
      if p not in parameters_known:
        error = {
          "code": 1407,
          "message": f"Unknown parameter. Allowed: {', '.join(parameters_known)}",
          "message_console": f"data(): Unknown parameter '{p}'"
        }
        return None, error

    return parameters, None
