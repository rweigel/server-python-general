# Overview

This is the start of a Python HAPI server that uses FastAPI and an OpenAPI specification and provides many of the options on the [`Java`](https://github.com/hapi-server/server-java) and [`NodeJS`](https://github.com/hapi-server/server-nodejs) generic HAPI servers. It is an alternative to the existing [Python HAPI server](https://github.com/hapi-server/server-python), which does not have many of features of the Java and NodeJS generic HAPI servers.

To use, a data provider must create four files

1. `config.json`
2. `catalog.py` with a function returns `/catalog` metadata
3. `info.py` with a function returns `/info` metadata
4. `data.py` with a function that returns the `/data` response

Examples:
* [demo-app.py](demo-app.py) has examples of using the four files in [demo](demo).
* https://github.com/rweigel/server-python-general-demo
* https://github.com/rweigel/server-python-general-supermag
* https://github.com/rweigel/server-python-general-psws

# Install

```bash
pip install git+https://github.com/rweigel/server-python-general.git@main
```

```bash
git clone https://github.com/rweigel/server-python-general-demo
cd server-python-general-demo
hapiserver -h
```

# Examples

