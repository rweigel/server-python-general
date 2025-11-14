import os
import sys

import hapiserver
import argparse
parser = argparse.ArgumentParser(description="HAPI server")
help = "Path to configuration file (default: ./bin/psws/config.json)"
parser.add_argument("config", nargs="?", help=help)
parser.parse_known_args()

if len(sys.argv) > 1:
  config_file = sys.argv[1]
else:
  base = os.path.dirname(os.path.abspath(__file__))
  config_file = f"{base}/bin/psws/config.json"

import json
with open(config_file, "r") as f:
  config_data = f.read()
  config = json.loads(config_data)

#hapiserver.run(config_server=config['server'], config_app=config['app'])
hapiserver.run(config=config)
#hapiserver.run(config_file)


