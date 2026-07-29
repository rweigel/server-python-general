import json
import logging

import hapiserver

logger = logging.getLogger(__name__)


def hapi(query, config):
  """Response for /hapi endpoint"""
  import os

  error = _query_error('hapi', query, config)
  if error:
    logger.debug(f"_query_error() returned error: {error}")
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


def about(query, config):
  """Response for /about endpoint"""

  import json

  error = _query_error('about', query, config)
  if error:
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


def capabilities(query, config):
  """Response for /capabilities endpoint"""

  import json

  error = _query_error('capabilities', query, config)
  if error:
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


def _get_json(endpoint, query, config):
  content, error = _call(endpoint, query, config)
  if error:
    return None, error

  if isinstance(content, str):
    try:
      content = json.loads(content)
    except Exception as e:
      message = f"Error parsing JSON returned by {endpoint} function"
      error = {
        "code": 1500,
        "message": message,
        "message_console": f"{message}: '{content}'",
        "exception": e
      }
      return None, error

  return content, None


def _get_catalog(query, config):
  return _get_json('catalog', query, config)


def catalog(query, config):
  """Response for /catalog endpoint"""

  error = _query_error('catalog', query, config)
  if error:
    return hapiserver.error(error, config)

  catalog, error = _get_catalog(query, config)
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


def _get_info(query, config):
  return _get_json('info', query, config)


def info(query, config):
  """Response for /info endpoint"""

  error = _query_error('info', query, config)
  if error:
    return hapiserver.error(error, config)

  query = _normalize_query('info', query)

  catalog, error = _get_catalog(query, config)
  if error:
    return hapiserver.error(error, config)

  error = _dataset_error(query['dataset'], catalog)
  if error:
    return hapiserver.error(error, config)

  info, error = _get_info(query, config)
  if error:
    return hapiserver.error(error, config)
  info = info.copy()

  if 'parameters' in query:
    error = _parameters_error(query['parameters'], info)
    if error:
      return hapiserver.error(error, config)

    parameters_list = query['parameters'].split(',')
    if info['parameters']:
      if info['parameters'][0]['name'] not in parameters_list:
        parameters_list = [info['parameters'][0]['name']] + parameters_list
    info['parameters'] = [p for p in info['parameters'] if p['name'] in parameters_list]

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


def data(query, config):
  """Response for /data endpoint"""

  error = _query_error('data', query, config)
  if error:
    logger.debug(f"_query_error() returned error: {error}")
    return hapiserver.error(error, config)

  catalog, error = _get_catalog(query, config)
  if error:
    return hapiserver.error(error, config)

  query = _normalize_query('data', query)

  error = _dataset_error(query['dataset'], catalog)
  if error:
    return hapiserver.error(error, config)

  info, error = _get_info(query, config)
  if error:
    return hapiserver.error(error, config)

  error = _parameters_error(query.get('parameters', ''), info)
  if error:
    return hapiserver.error(error, config)

  error = _start_stop_error('data', query, config, info)
  if error:
    return hapiserver.error(error, config)

  data, error = _call('data', query, config)
  if error:
    return hapiserver.error(error, config)

  response = {
    "content": data,
    "media_type": _data_media_type(query.get('format', 'csv')),
    "headers": _headers(config),
  }

  return response


def _data_media_type(format):
  if format == 'csv':
    return 'text/csv'
  if format == 'json':
    return 'application/json'
  return 'application/octet-stream'


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


def _parameters_error(parameters, info):
  if not parameters:
    return None

  info_parameters = [p['name'] for p in info['parameters']]
  query_parameters = parameters.split(',')
  invalid_parameters = [p for p in query_parameters if p not in info_parameters]
  if invalid_parameters:
    error = {
      "code": 1407,
      "message": f"Invalid parameters: {', '.join(invalid_parameters)}. Allowed parameters: {', '.join(info_parameters)}",
      "message_console": f"Invalid parameters: {', '.join(invalid_parameters)}"
    }
    return error

  duplicate_parameters = [
    p for p in dict.fromkeys(query_parameters)
    if query_parameters.count(p) > 1
  ]
  if duplicate_parameters:
    error = {
      "code": 1411,
      "message": f"Duplicate parameters: {', '.join(duplicate_parameters)}",
      "message_console": f"Duplicate parameters: {', '.join(duplicate_parameters)}"
    }
    return error

  ordered_parameters = query_parameters
  if info_parameters and info_parameters[0] not in ordered_parameters:
    ordered_parameters = [info_parameters[0]] + ordered_parameters

  parameter_indices = [info_parameters.index(p) for p in ordered_parameters]
  if parameter_indices != sorted(parameter_indices):
    error = {
      "code": 1411,
      "message": (
        "Parameters out of order. Must follow the order defined in /info: "
        f"{', '.join(info_parameters)}"
      ),
      "message_console": f"Parameters out of order: {', '.join(query_parameters)}"
    }
    return error

  return None


def _dataset_error(dataset_id, catalog):

  dataset_ids = [dataset['id'] for dataset in catalog]
  if dataset_id not in dataset_ids:
    error = {
      "code": 1406,
      "message": f"Invalid dataset. Allowed datasets: {', '.join(dataset_ids)}",
      "message_console": f"dataset '{dataset_id}' not found in catalog"
    }
    return error

  return None


def _start_stop_error(endpoint, query, config, info):

  import hapiclient
  from utilrsw.time import isoduration_to_timedelta

  for name in ['start', 'stop']:
    try:
      dt = hapiclient.hapitime2datetime(query[name], allow_missing_Z=True)
      query[name + "_datetime"] = dt[0]
      query[name + "_normalized"] = hapiclient.datetime2hapitime(dt[0])
    except Exception as e:
      error = {
        "code": 1402 if name == 'start' else 1403,
        "message": f"Invalid {name} time",
        "message_console": f"Invalid {name} time: {query[name]}. Error: {e}"
      }
      return error

  if query['stop_datetime'] <= query['start_datetime']:
    error = {
      "code": 1404,
      "message": "Invalid time range: stop <= start",
      "message_console": f"Invalid time range: stop ({query['stop_normalized']}) <= start ({query['start_normalized']})"
    }
    return error

  info_normalized_datetime = {}
  for name in ['start', 'stop']:
    key = f'{name}Date'
    if key not in info:
      msg = f"Missing {key} in info"
      return {
        "code": 1500,
        "message": msg,
        "message_console": msg
      }

    try:
      info_normalized_datetime[name] = hapiclient.hapitime2datetime(info[key], allow_missing_Z=True)[0]
    except Exception as e:
      msg = f"Invalid value for {key} in info: {info[key]}"
      error = {
        "code": 1500,
        "message": msg,
        "message_console": f"{msg}. Error: {e}"
      }
      return error

  a = query['start_datetime'] < info_normalized_datetime['start']
  b = query['stop_datetime'] > info_normalized_datetime['stop']
  if a or b:
    message = ""
    message_console = ""
    if a:
      if query['start_datetime'] < info_normalized_datetime['start']:
        message += f"start < startDate ({info['startDate']})"
        message_console = f"start ({query['start_datetime']}) < startDate ({info['startDate']})"
    if b:
      if message:
        message += "; "
      message += f"stop > stopDate ({info['stopDate']})"
      if message_console:
        message_console += "; "
      message_console += f"stop ({query['stop']}) > stopDate ({info['stopDate']})"

    error = {
      "code": 1405,
      "message": message,
      "message_console": message_console
    }

    return error

  if 'maxRequestDuration' in info:
    max_duration = info['maxRequestDuration']
    # Convert from ISO 8601 duration to seconds.
    try:
      max_duration_secs = isoduration_to_timedelta(
        max_duration,
        start=query['start_datetime']
      ).total_seconds()
    except Exception as e:
      error = {
        "code": 1500,
        "message": f"Invalid maxRequestDuration value in info: {max_duration}",
        "message_console": f"Invalid maxRequestDuration value in info: {max_duration}. Error: {e}"
      }
      return error
    duration = (query["stop_datetime"] - query["start_datetime"]).total_seconds()
    if duration > max_duration_secs:
      msg = f"Invalid time range: duration ({duration} seconds) > "
      msg += f"maxRequestDuration ({max_duration_secs} seconds)"
      error = {
        "code": 1408,
        "message": msg,
        "message_console": msg
      }

      return error

  return None


def _normalize_query(endpoint, query):
  if 'id' in query:
    query['dataset'] = query['id']
    del query['id']
  if 'time.min' in query:
    query['start'] = query['time.min']
    del query['time.min']
  if 'time.max' in query:
    query['stop'] = query['time.max']
    del query['time.max']

  return query


def _query_error(endpoint, query, config):
  """Check for errors in query that do not require info or catalog metadata.

  Args:
      endpoint (str): The API endpoint (e.g., 'catalog', 'info', 'data', ...)
      query (dict): The query as a dictionary.

  Returns:
      dict or None: Error dict if an error, otherwise None
  """

  logger.debug("Checking query parameters.")

  allowed = []
  required = []
  equivalent = {}

  if endpoint == 'catalog':
    if 'depth' in query:
      depth_options = config.get('capabilities', {}).get('catalogDepthOptions', [])
      if query['depth'] not in depth_options:
        error = {
          "code": 1401,
          "message": f"Invalid depth value. Allowed values: {', '.join(depth_options)}",
          "message_console": f"Invalid depth value: '{query['depth']}'"
        }
        return error

    allowed = ["depth"]
    required = []

  if endpoint == 'info':
    if 'resolve_references' in query:
      resolve_references = config.get('capabilities', {}).get('resolveReferences', False)
      if not resolve_references:
        error = {
          "code": 1401,
          "message": "resolve_references is not supported by this server.",
          "message_console": "resolve_references requested but not advertised in capabilities."
        }
        return error

      if query['resolve_references'] not in ['true', 'false']:
        error = {
          "code": 1412,
          "message": "Invalid resolve_references value. Must be 'true' or 'false'.",
          "message_console": f"Invalid resolve_references value: {query['resolve_references']}."
        }
        return error

    allowed = ["id", "dataset", "parameters", "resolve_references"]
    required = ["dataset"]
    equivalent = {"dataset": "id"}

  if endpoint == 'data':
    output_formats = config.get('capabilities', {}).get('outputFormats', ['csv'])
    if 'format' in query and query['format'] not in output_formats:
      error = {
        "code": 1409,
        "message": f"Invalid stream format. Allowed formats: {', '.join(output_formats)}",
        "message_console": f"Invalid stream format: '{query['format']}'"
      }
      return error

    if 'include' in query and query['include'] not in ['header']:
      error = {
        "code": 1410,
        "message": "Invalid include value. Allowed values 'header'",
        "message_console": f"Invalid include value: '{query['include']}'"
      }
      return error

    allowed = ["id", "dataset", "time.min", "start", "time.max", "stop", "parameters", "format", "include"]
    required = ["dataset", "start", "stop"]
    equivalent = {"dataset": "id", "start": "time.min", "stop": "time.max"}

  for p in query:
    if p not in allowed and not p.startswith('x_'):
      return {
        "code": 1401,
        "message": f"Unknown query parameter '{p}'. Allowed: {', '.join(allowed)}",
        "message_console": f"Unknown query parameter '{p}'"
      }

  for p in required:
    if p not in query and (p not in equivalent or equivalent[p] not in query):
      return {
        "code": 1400,
        "message": f"Missing '{p}' parameter"
      }

  for p, eq in equivalent.items():
    if p in query and eq in query:
      return {
        "code": 1400,
        "message": f"Query parameter '{eq}' is equivalent to '{p}'. Use only one of them."
      }

  return None


def _call(endpoint, query, config):

  args = {}
  if endpoint == 'catalog' and 'depth' in query:
    args = {"depth": query['depth']}

  if endpoint == 'info':
    args = {"dataset": query['dataset']}

  if endpoint == 'data':
    args = {
      'dataset': query['dataset'],
      'parameters': query.get('parameters', ''),
      'start': query['start_normalized'],
      'stop': query['stop_normalized']
    }
    if 'format' in query:
      args['format'] = query['format']

  if 'scripts' in config and endpoint in config['scripts']:

    script_vals = {**query, **args}
    script, script_args = _script_command(config['scripts'][endpoint], script_vals)

    if len(script_args) > 0:
      data, error = hapiserver.exec(script, args=script_args)
    else:
      data, error = hapiserver.exec(script)
    if error:
      message = "Endpoint script returned error"
      error = {
        "code": 1500,
        "message": message,
        "message_console": message,
        "exception": error
      }
      return None, error

    if endpoint == 'data':
      # For /data, the script is expected to return binary or CSV, so no
      # JSON parsing is needed.
      return data, None

    try:
      data = json.loads(data)
    except Exception as e:
      message = f"Error parsing JSON returned by script: '{data}'"
      error = {
        "code": 1500,
        "message": message,
        "exception": e
      }
      return None, error

    return data, None


  if 'functions' in config and endpoint in config['functions']:
    func = config['functions'][endpoint]
    logger.debug(f"Calling {func}({args})")
    try:
      import inspect

      func_params = inspect.signature(func).parameters
      args = [str(args[x]) for x in args.keys()]
      config_kwarg = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in func_params.values())
      if len(args) > 0:
        if 'config' in func_params or config_kwarg:
          data = func(*args, config=config)
        else:
          data = func(*args)
      else:
        if 'config' in func_params or config_kwarg:
          data = func(config=config)
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
      return None, error

    return data, None

  return None, {
    "code": 1500,
    "message": f"No script or function configured for endpoint '{endpoint}'"
  }


def _script_command(script, query):
  from hapiserver.config import _split_script

  script_path, configured_args = _split_script(script)
  script_args = []
  for arg in configured_args:
    try:
      script_args.append(arg.format(**query))
    except KeyError:
      script_args.append('')

  while script_args and script_args[-1] == '':
    script_args.pop()

  return script_path, script_args
