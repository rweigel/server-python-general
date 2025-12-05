def cli():
  import argparse

  config_default = "bin/psws/config.json"

  # Define the text for the header
  description = f"""
  HAPI Server
  -----------
  Example usage:
    python hapiserver.py --config {config_default}

  Pass additional Uvicorn arguments as needed
    python hapiserver.py --config {config_default} [Uvicorn options]
  For Uvicorn options, see:
    python -m uvicorn --help
  """

  import utilrsw.uvicorn

  # Get default server clargs from utilrsw.uvicorn
  clargs_uvicorn = utilrsw.uvicorn.cli()


  config_help = "Path to JSON configuration file. Relative paths are "
  config_help += "interpreted as relative to current working directory "
  config_help += f"hapiserver.py is executed from. Default: {config_default}"

  clargs = {
    "config": {
      "help": config_help,
      "type": str,
      "default": config_default
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
