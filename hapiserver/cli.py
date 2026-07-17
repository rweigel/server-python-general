
def cli(config=None):
  import logging
  import argparse

  # Define the text for the header
  description = """
  HAPI Server
  -----------
  Example usage:
    python hapiserver.py --config CONFIG_FILE.json

  Pass additional Uvicorn arguments as needed
    python hapiserver.py --config CONFIG_FILE.json [Uvicorn options]
  For Uvicorn options, see:
    python -m uvicorn --help
  """

  import utilrsw.uvicorn

  # Get default uvicorn command-line args
  clargs_uvicorn = utilrsw.uvicorn.cli()


  config_help = "Path to JSON configuration file. Relative paths in configuration "
  config_help += "file are interpreted as relative to the directory "
  config_help += "hapiserver.py is executed from."

  clargs = {
    "config": {
      "help": config_help,
      "type": str,
      "required": True
    },
    **clargs_uvicorn,
    "debug": {
      "help": "Verbose logging.",
      "action": "store_true",
      "default": False
    },
    "log-level": {
      "help": "Set the logging level. Overrides debug flag if set.",
      "type": str,
      "default": None
    }
  }

  if config is not None:
    # Test functions call cli() with a path to a config file, so set that
    # as the default and make --config not required in that case.
    clargs['config']['default'] = str(config)
    clargs['config']['required'] = False

  parser_kwargs = {
    "description": description,
    "formatter_class": argparse.RawDescriptionHelpFormatter
  }

  parser = argparse.ArgumentParser()
  parser = argparse.ArgumentParser(**parser_kwargs)

  for k, v in clargs.items():
    parser.add_argument(f'--{k}', **v)

  args, _ = parser.parse_known_args()
  if args.debug:
    logging.getLogger('hapiserver').setLevel(logging.DEBUG)
  if args.log_level:
    logging.getLogger('hapiserver').setLevel(args.log_level.upper())

  logger = logging.getLogger(__name__)
  logger.debug(f"Command line arguments: {args}")

  # Split args into dict wil keys 'server' and 'app', where 'server' contains
  # args for uvicorn and 'app' contains args for the app.
  configs = utilrsw.uvicorn.cli(parser=parser)

  configs['app'] = configs['app']['config']

  # Store the effective hapiserver log level inside the app config so it is
  # written to APP_CONFIG and available to the uvicorn worker process.
  if isinstance(configs['app'], dict):
    configs['app']['log_level'] = logging.getLogger('hapiserver').level

  return configs
