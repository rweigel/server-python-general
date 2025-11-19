def cli():
  import argparse

  # Define the text for the header
  description = """
  HAPI Server
  --------------------
  Example usage:
    python hapiserver.py --config conf/demo.json
    python hapiserver.py --config conf/demos.json

  Pass additional Uvicorn arguments as needed
    python hapiserver.py --config conf/demos.json [Uvicorn options]
  See
    python -m uvicorn --help
  """

  import utilrsw.uvicorn

  # Get default server clargs from utilrsw.uvicorn
  clargs_uvicorn = utilrsw.uvicorn.cli()

  config_help = "Path to JSON configuration file. Relative paths are "
  config_help += "interpreted as relative to current working directory "
  config_help += "hapiserver.py is executed from."

  clargs = {
    "config": {
      "help": config_help,
      "type": str,
      "default": "bin/psws/config.json"
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

  parser_kwargs = {
    "description": description,
    "formatter_class": argparse.RawDescriptionHelpFormatter
  }

  parser = argparse.ArgumentParser()
  parser = argparse.ArgumentParser(**parser_kwargs)

  for k, v in clargs.items():
    parser.add_argument(f'--{k}', **v)

  configs = utilrsw.uvicorn.cli(parser=parser)

  return configs
