# Overview

This is the start of a Python HAPI server that uses FastAPI and an OpenAPI specification and provides many of the options on the [`Java`](https://github.com/hapi-server/server-java) and [`NodeJS`](https://github.com/hapi-server/server-nodejs) generic HAPI servers. It is an alternative to the existing [Python HAPI server](https://github.com/hapi-server/server-python), which does not have many of features of the Java and NodeJS generic HAPI servers.

# Usage

To start the server

```
python hapiserver.py --config bin/psws/config.json
```

For additional command-line options, see

```
python hapiserver.py --help
```

# Set-up

Assumes magnetometer data in directories as under `data/` - each subdir corresponds to data from a station with ID in `catalog.csv`.

The responses to HAPI endpoints are implemented as Python scripts that return the response to `stdout`.

Return response to `/hapi/catalog` request

```
python bin/psws/catalog.py
```

Return response to `/hapi/info` request

```
python bin/psws/info.py S000028
```

Return response to `/hapi/data` request

```
python bin/psws/data.py W2NAF 2025-10-20 2025-10-21
```

