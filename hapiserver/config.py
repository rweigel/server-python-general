import os
import json
import logging
import sys

logger = logging.getLogger(__name__)


def config(config_input=None, config_dir=None):
  """Read, resolve, and return the hapiserver config as a dict.

  Accepts:
    - a file path string
    - a dict with a 'config' key (as returned by hapiserver.cli())
    - a fully-formed config dict (passed through after env expansion)
    - None: reads path from the HAPISERVER_CONFIG environment variable

  ENV variables defined in the config are set as OS environment variables
  and all $VAR references throughout the config are expanded before returning.
  """

  logger.debug(f"Called with: {config_input!r}")

  if not isinstance(config_input, (str, dict)):
    _exit_error(f"Invalid config input type: {type(config_input).__name__}. Expected str or dict.")


  if isinstance(config_input, dict):
    if 'app' in config_input:
      logger.debug("Input is a dict with 'app' key. Calling config() on config_input['app'] and returning input with 'app' key set to result.")
      config_input['app'] = config(config_input['app'])
      return config_input
    else:
      logger.debug("Config input is a dict without 'app' key; treating as app config")


  if isinstance(config_input, str):
    logger.debug(f"Reading config from file path: {config_input}")
    config_path = os.path.abspath(config_input)
    if not os.path.exists(config_path):
      _exit_error(f"Config file not found: {config_path}")

    logger.debug(f"Reading: {config_path}")
    try:
      with open(config_path) as f:
        cfg = json.load(f)
    except Exception as e:
      _exit_error(f"Failed to read config file '{config_path}': {e}")

    return config(cfg, config_dir=os.path.dirname(config_path))


  _set_env(config_input)
  _resolve_env(config_input)
  _resolve_scripts(config_input, config_dir=config_dir)
  _resolve_functions(config_input)

  logger.debug(f"config resolved: {config_input!r}")

  _check_config(config_input)

  return config_input


def _exit_error(message):
  logger.error(message)
  print(f"Error: {message}", file=sys.stderr)
  print("Exiting with code 1", file=sys.stderr)
  exit(1)

def _resolve_scripts(cfg, config_dir=None):
  for script_name, script in cfg.get("scripts", {}).items():
    cfg['scripts'][script_name] = os.path.expanduser(script)
    if config_dir is not None and not os.path.isabs(cfg['scripts'][script_name]):
      logger.debug(f"Resolving script path {cfg['scripts'][script_name]}")
      cfg['scripts'][script_name] = os.path.join(config_dir, cfg['scripts'][script_name])
      logger.debug(f"Resolved script path {cfg['scripts'][script_name]}")
    if not os.path.exists(cfg['scripts'][script_name]):
      _exit_error(f"Script file for endpoint /{script_name} not found: '{script}'")


def _resolve_functions(cfg):
  """Resolve string function references in cfg['functions'] to callables.

  String format: 'module.path.function_name' (standard Python dotted path).
  Skips values that are already callable.
  """
  import importlib

  for key, value in cfg.get('functions', {}).items():
    if callable(value):
      continue
    if not isinstance(value, str):
      logger.warning(f"functions.{key}: expected str or callable, got {type(value).__name__}")
      continue
    last_dot = value.rfind('.')
    if last_dot == -1:
      logger.warning(f"functions.{key}: '{value}' has no '.' separator; skipping")
      continue
    module_path = value[:last_dot]
    func_name = value[last_dot + 1:]
    try:
      module = importlib.import_module(module_path)
      cfg['functions'][key] = getattr(module, func_name)
      logger.debug(f"Resolved functions.{key} -> {module_path}.{func_name}")
    except Exception as e:
      logger.warning(f"functions.{key}: failed to resolve '{value}': {e}")


def _set_env(config):
  import os
  for name, value in config.get("ENV", {}).items():
    os.environ[name] = str(value)
    logger.debug(f"Environment variable set: {name}={value}")


def _resolve_env(config):
  import os
  import re

  regex =r'\$(?:{(?P<braced>[A-Za-z_][A-Za-z0-9_]*)}|(?P<plain>[A-Za-z_][A-Za-z0-9_]*))'
  env_pattern = re.compile(regex)

  def _replace_env(obj):
    if isinstance(obj, dict):
      for k, v in obj.items():
        obj[k] = _replace_env(v)
      return obj
    if isinstance(obj, list):
      return [_replace_env(v) for v in obj]
    if isinstance(obj, tuple):
      return tuple(_replace_env(v) for v in obj)
    if isinstance(obj, str):
      def repl(m):
        name = m.group('braced') or m.group('plain')
        return os.environ.get(name, '')
      return env_pattern.sub(repl, obj)
    return obj

  logger.debug('Expanding ENV variables in configuration file')
  try:
    _replace_env(config)
  except Exception as e:
    logger.warning(f"Environment variable substitution failed: {e}")


def _check_config(config):
  import os

  logger.debug('Checking configuration file')

  endpoints = ['catalog', 'info', 'data']
  for endpoint in endpoints:
    has_script = endpoint in config.get('scripts', {})
    has_function = endpoint in config.get('functions', {})
    if not has_script and not has_function:
      logger.warning(f"No script or function configured for endpoint '/{endpoint}'.")

  if "about" not in config:
    _exit_error("Configuration missing 'about' section.")

  fname = config.get("index.html", None)
  if fname is not None:
    fname = os.path.expanduser(fname)
    config['index.html'] = os.path.expanduser(config['index.html'])
    if not os.path.exists(config['index.html']):
      _exit_error(f"index.html file not found: '{fname}'")

  for script_name, script in config.get("scripts", {}).items():
    config['scripts'][script_name] = os.path.expanduser(script)
    if not os.path.exists(config['scripts'][script_name]):
      _exit_error(f"Script file for endpoint /{script_name} not found: '{script}'")

  for endpoint in config.get("scripts", {}):
    if 'functions' in config and endpoint in config['functions']:
      _exit_error(f"Both script and function defined for /{endpoint} in config.")

