# Usage:
#   python test_demo.py

import logging

format = '%(name)s %(levelname)s: %(message)s'
logging.basicConfig(level=logging.DEBUG, format=format)
logger = logging.getLogger(__name__)

wait = {
  "retries": 10,
  "delay": 0.5
}

def test_start_stop_error():
  from hapiserver.endpoints import _start_stop_error

  def validate(
    start="1970-01-01T00:00:00Z",
    stop="1970-01-01T00:00:01Z",
    missing_info=None,
    **info_overrides):

    query = {
      "dataset": "demo1",
      "start": start,
      "stop": stop
    }

    info = {
      "startDate": "1970-01-01T00:00:00Z",
      "stopDate": "1970-01-01T00:00:02Z",
      **info_overrides
    }

    if missing_info:
      del info[missing_info]

    return _start_stop_error('data', query, {}, info), query

  error, query = validate()
  assert error is None
  assert 'start_datetime' in query
  assert 'stop_datetime' in query
  assert query['start_normalized'] == "1970-01-01T00:00:00.000000Z"
  assert query['stop_normalized'] == "1970-01-01T00:00:01.000000Z"

  error, _ = validate(start="INVALID")
  assert error['code'] == 1402
  assert error['message'] == "Invalid start time"

  error, _ = validate(stop="INVALID")
  assert error['code'] == 1403
  assert error['message'] == "Invalid stop time"

  error, _ = validate(stop="1970-01-01T00:00:00Z")
  assert error['code'] == 1404
  assert 'stop <= start' in error['message']

  error, _ = validate(startDate="INVALID")
  assert error['code'] == 1500
  assert 'Invalid value for startDate in info' in error['message']

  error, _ = validate(stopDate="INVALID")
  assert error['code'] == 1500
  assert 'Invalid value for stopDate in info' in error['message']

  error, _ = validate(missing_info="startDate")
  assert error['code'] == 1500
  assert error['message'] == "Missing startDate in info"

  error, _ = validate(missing_info="stopDate")
  assert error['code'] == 1500
  assert error['message'] == "Missing stopDate in info"

  error, _ = validate(start="1969-12-31T23:59:59Z")
  assert error['code'] == 1405
  assert 'start < startDate' in error['message']

  error, _ = validate(stop="1970-01-01T00:00:03Z")
  assert error['code'] == 1405
  assert 'stop > stopDate' in error['message']

  error, _ = validate(
    start="1969-12-31T23:59:59Z",
    stop="1970-01-01T00:00:03Z"
  )
  assert error['code'] == 1405
  assert 'start < startDate' in error['message']
  assert 'stop > stopDate' in error['message']

  error, _ = validate(maxRequestDuration="INVALID")
  assert error['code'] == 1500
  assert 'Invalid maxRequestDuration value in info' in error['message']

  error, _ = validate(stop="1970-01-01T00:00:02Z", maxRequestDuration="PT1S")
  assert error['code'] == 1408
  assert 'duration (2.0 seconds)' in error['message']
  assert 'maxRequestDuration (1.0 seconds)' in error['message']

  error, _ = validate(maxRequestDuration="PT1S")

  assert error is None


def test_parameters_error():
  from hapiserver.endpoints import _parameters_error

  info = {
    "parameters": [
      {"name": "Time"},
      {"name": "scalar"}
    ]
  }

  assert _parameters_error("", info) is None
  assert _parameters_error("Time,scalar", info) is None
  assert _parameters_error("scalar", info) is None

  error = _parameters_error("INVALID", info)
  assert error['code'] == 1407

  error = _parameters_error("scalar,scalar", info)
  assert error['code'] == 1411
  assert error['message'] == "Duplicate parameters: scalar"

  error = _parameters_error("scalar,Time", info)
  assert error['code'] == 1411
  assert 'Parameters out of order' in error['message']


def test_metadata_json_error():
  from hapiserver.endpoints import _get_catalog, _get_info

  def valid_catalog():
    return '[{"id": "demo1"}]'

  def malformed_catalog():
    return 'INVALID'

  def malformed_info(dataset):
    return 'INVALID'

  catalog, error = _get_catalog({}, {"functions": {"catalog": valid_catalog}})
  assert error is None
  assert catalog == [{"id": "demo1"}]

  catalog, error = _get_catalog({}, {"functions": {"catalog": malformed_catalog}})
  assert catalog is None
  assert error['code'] == 1500
  assert error['message'] == "Error parsing JSON returned by catalog function"
  assert 'exception' in error

  info, error = _get_info({"dataset": "demo1"}, {"functions": {"info": malformed_info}})
  assert info is None
  assert error['code'] == 1500
  assert error['message'] == "Error parsing JSON returned by info function"
  assert 'exception' in error


def test_resolve_script_with_arguments():
  import pathlib
  import tempfile

  from hapiserver.config import _resolve_scripts, _split_script
  from hapiserver.endpoints import _script_command

  with tempfile.TemporaryDirectory() as tmp_dir:
    tmp_path = pathlib.Path(tmp_dir)
    bin_dir = tmp_path / "bin files"
    bin_dir.mkdir()
    script_path = bin_dir / "catalog.py"
    script_path.touch()
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    cfg = {"scripts": {"catalog": "'../bin files/catalog.py' {depth}"}}

    _resolve_scripts(cfg, config_dir=str(config_dir))

    resolved_path, script_args = _split_script(cfg['scripts']['catalog'])
    assert pathlib.Path(resolved_path).resolve() == script_path.resolve()
    assert script_args == ['{depth}']

    cmd_path, cmd = _script_command(cfg['scripts']['catalog'], {})
    assert cmd_path == resolved_path
    assert cmd == []

    cmd_path, cmd = _script_command(cfg['scripts']['catalog'], {'depth': 'all'}
    )
    assert cmd_path == resolved_path
    assert cmd == ['all']

    cmd_path, cmd = _script_command("catalog.py", {'depth': 'all'})
    assert cmd_path == "catalog.py"
    assert cmd == []

    data_script = "data.py --dataset={dataset} --parameters={parameters} "
    data_script += "--start={start} --stop={stop} --format={format} --config={config}"


    data_query = {
        'dataset': 'demo1',
        'parameters': '',
        'start': '1970-01-01T00:00:00.000000Z',
        'stop': '1970-01-01T00:00:01.000000Z'
    }
    _, cmd = _script_command(data_script, data_query)
    assert cmd == [
      '--dataset=demo1',
      '--parameters=',
      '--start=1970-01-01T00:00:00.000000Z',
      '--stop=1970-01-01T00:00:01.000000Z'
    ]


def test_scripts():
  import pathlib
  config = pathlib.Path(__file__).parent / "configs" / "demo-scripts.json"

  logger.info("Executing test_scripts()")
  _run_tests(config)
  logger.info("")
  logger.info("")


def test_functions():
  import pathlib
  config = pathlib.Path(__file__).parent / "configs" / "demo-functions.json"

  logger.info("Executing test_functions()")
  _run_tests(config)
  logger.info("")
  logger.info("")


def _check_data_response(resp):
  assert resp.status_code == 200
  assert 'text/csv' in resp.headers['Content-Type']
  assert resp.text.strip() == "1970-01-01T00:00:00Z,0"


def _run_tests(config):
  import requests

  import hapiserver

  # Get default configs and override with command line arguments.
  configs = hapiserver.cli(config=config)

  port = configs['server']['--port']
  url_base = f"http://0.0.0.0:{port}/hapi"

  wait['url'] = url_base

  process = hapiserver.start(configs, wait)

  _log_test_title(url_base)

  url = url_base
  response = requests.get(url)
  assert response.status_code == 200
  assert 'text/html' in response.headers['Content-Type']

  url = f"{url_base}/catalog"
  response = requests.get(url)
  assert response.status_code == 200
  assert 'application/json' in response.headers['Content-Type']
  response_json = response.json()
  assert 'catalog' in response_json
  catalog = response_json['catalog']
  assert isinstance(catalog, list)
  assert len(catalog) > 0
  assert 'HAPI' in response_json
  assert 'status' in response_json

  url = f"{url_base}/catalog?depth=dataset"
  response = requests.get(url)
  assert response.status_code == 200
  assert 'application/json' in response.headers['Content-Type']
  response_json_dataset = response.json()
  assert response_json_dataset == response_json

  url = f"{url_base}/catalog?depth=all"
  response = requests.get(url)
  assert response.status_code == 200
  assert 'application/json' in response.headers['Content-Type']
  # Most tests on response_json_catalog_all later
  response_json_catalog_all = response.json()

  url = f"{url_base}/capabilities"
  response = requests.get(url)
  assert response.status_code == 200
  assert 'application/json' in response.headers['Content-Type']
  capabilities = response.json()
  assert isinstance(capabilities, dict)
  assert 'outputFormats' in capabilities
  assert 'HAPI' in response_json
  assert 'status' in response_json


  start = "1970-01-01T00:00:00Z"
  stop = "1970-01-01T00:00:01Z"

  for dataset in catalog:
    url = f"{url_base}/info?dataset={dataset['id']}"
    response = requests.get(url)
    assert response.status_code == 200
    assert 'application/json' in response.headers['Content-Type']
    info = response.json()
    assert isinstance(info, dict)
    assert 'HAPI' in info
    assert 'status' in info
    assert 'parameters' in info

    catalog_all_dataset = next(
      item for item in response_json_catalog_all['catalog']
      if item['id'] == dataset['id']
    )
    info_without_envelope = {
      key: value for key, value in info.items()
      if key not in ['HAPI', 'status']
    }
    assert catalog_all_dataset['info'] == info_without_envelope

    ds = dataset['id']

    url = f"{url_base}/info?dataset={ds}&parameters=scalar"
    response = requests.get(url)
    assert response.status_code == 200
    parameter_names = [parameter['name'] for parameter in response.json()['parameters']]
    assert parameter_names == ['Time', 'scalar']

    url = f"{url_base}/data?dataset={ds}&start={start}&stop={stop}"
    response = requests.get(url)
    _check_data_response(response)

    for q in ['dataset', 'id']:
      url = f"{url_base}/data?{q}={ds}&parameters=scalar&start={start}&stop={stop}"
      response = requests.get(url)
      _check_data_response(response)

    for q in ['time.min', 'start']:
      url = f"{url_base}/data?dataset={ds}&parameters=scalar&{q}={start}&stop={stop}"
      response = requests.get(url)
      _check_data_response(response)

    for q in ['time.max', 'stop']:
      url = f"{url_base}/data?dataset={ds}&parameters=scalar&start={start}&{q}={stop}"
      response = requests.get(url)
      _check_data_response(response)

    url = f"{url_base}/data?dataset={ds}&parameters=scalar&start={start}&stop={stop}&format=csv&include=header"
    response = requests.get(url)
    assert response.status_code == 200


  # Test error responses
  url = f"{url_base}x"
  _log_test_title(url)
  response = requests.get(url)
  assert response.status_code == 404

  for endpoint in ['', 'catalog', 'info', 'data', 'about']:
    url = f"{url_base}/{endpoint}x"
    _log_test_title(url)
    response = requests.get(url)
    assert response.status_code == 404


  url = f"{url_base}/about?xxxabc=123"
  response = requests.get(url)
  assert response.status_code == 400
  json_response = response.json()
  assert 'status' in json_response
  assert 'code' in json_response['status']
  assert json_response['status']['code'] == 1401


  url = f"{url_base}/catalog?xxxabc=123"
  response = requests.get(url)
  assert response.status_code == 400
  json_response = response.json()
  assert 'status' in json_response
  assert 'code' in json_response['status']
  assert json_response['status']['code'] == 1401

  url = f"{url_base}/info?dataset=demo1&xxxabc=123"
  response = requests.get(url)
  assert response.status_code == 400
  json_response = response.json()
  assert 'status' in json_response
  assert 'code' in json_response['status']
  assert json_response['status']['code'] == 1401

  allowed_dataset_ids = ', '.join(dataset['id'] for dataset in catalog)

  url = f"{url_base}/info?dataset=INVALID"
  response = requests.get(url)
  assert response.status_code == 404
  json_response = response.json()
  assert json_response['status']['code'] == 1406
  assert 'Invalid dataset' in json_response['status']['message']
  assert f"Allowed datasets: {allowed_dataset_ids}" in json_response['status']['message']

  url = f"{url_base}/catalog?depth=invalid"
  response = requests.get(url)
  assert response.status_code == 400
  json_response = response.json()
  assert json_response['status']['code'] == 1401

  url = f"{url_base}/info?dataset=demo1&resolve_references=true"
  response = requests.get(url)
  assert response.status_code == 400
  json_response = response.json()
  assert json_response['status']['code'] == 1401

  url = f"{url_base}/info?dataset=demo1&resolve_references=invalid"
  response = requests.get(url)
  assert response.status_code == 400
  json_response = response.json()
  assert json_response['status']['code'] == 1401


  start_stop = f"start={start}&stop={stop}"
  url = f"{url_base}/data?xxxdataset=demo1&{start_stop}"
  response = requests.get(url)
  assert response.status_code == 400
  json_response = response.json()
  assert 'status' in json_response
  assert 'code' in json_response['status']
  assert json_response['status']['code'] == 1401

  url = f"{url_base}/data?dataset={dataset['id']}&start=INVALIDZ&stop={stop}"
  response = requests.get(url)
  assert response.status_code == 400
  json_response = response.json()
  assert 'status' in json_response
  assert 'code' in json_response['status']
  assert json_response['status']['code'] == 1402

  url = f"{url_base}/data?dataset={dataset['id']}&start={start}&stop=INVALIDZ"
  response = requests.get(url)
  assert response.status_code == 400
  json_response = response.json()
  assert 'status' in json_response
  assert 'code' in json_response['status']
  assert json_response['status']['code'] == 1403

  url = f"{url_base}/data?dataset={dataset['id']}&start={stop}&stop={start}"
  response = requests.get(url)
  assert response.status_code == 400
  json_response = response.json()
  assert 'status' in json_response
  assert 'code' in json_response['status']
  assert json_response['status']['code'] == 1404

  url = f"{url_base}/data?dataset={dataset['id']}&start=1969-12-31T23:59:59Z&stop={start}"
  response = requests.get(url)
  assert response.status_code == 400
  json_response = response.json()
  assert 'status' in json_response
  assert 'code' in json_response['status']
  assert json_response['status']['code'] == 1405

  url = f"{url_base}/data?dataset=INVALID&{start_stop}"
  response = requests.get(url)
  assert response.status_code == 404
  json_response = response.json()
  assert 'status' in json_response
  assert 'code' in json_response['status']
  assert json_response['status']['code'] == 1406
  assert 'Invalid dataset' in json_response['status']['message']
  assert f"Allowed datasets: {allowed_dataset_ids}" in json_response['status']['message']

  url = f"{url_base}/data?dataset={dataset['id']}&parameters=INVALID&{start_stop}"
  response = requests.get(url)
  assert response.status_code == 404
  json_response = response.json()
  assert 'status' in json_response
  assert 'code' in json_response['status']
  assert json_response['status']['code'] == 1407

  url = f"{url_base}/info?dataset={dataset['id']}&parameters=INVALID1,INVALID2"
  response = requests.get(url)
  assert response.status_code == 404
  json_response = response.json()
  assert json_response['status']['code'] == 1407
  assert 'Invalid parameters: INVALID1, INVALID2' in json_response['status']['message']
  assert 'Allowed parameters: Time, scalar' in json_response['status']['message']

  url = f"{url_base}/data?dataset={dataset['id']}&parameters=INVALID1,INVALID2&{start_stop}"
  response = requests.get(url)
  assert response.status_code == 404
  json_response = response.json()
  assert json_response['status']['code'] == 1407
  assert 'Invalid parameters: INVALID1, INVALID2' in json_response['status']['message']
  assert 'Allowed parameters: Time, scalar' in json_response['status']['message']

  url = f"{url_base}/data?dataset={dataset['id']}&format=invalid&{start_stop}"
  response = requests.get(url)
  assert response.status_code == 400
  json_response = response.json()
  assert json_response['status']['code'] == 1409

  url = f"{url_base}/data?dataset={dataset['id']}&include=invalid&{start_stop}"
  response = requests.get(url)
  assert response.status_code == 400
  json_response = response.json()
  assert json_response['status']['code'] == 1410


  hapiserver.stop(process)


def _log_test_title(url):
  msg = f"Testing {url}"
  line = len(msg)*"-"
  logger.info(line)
  logger.info(msg)
  logger.info(line)


if __name__ == "__main__":
  test_resolve_script_with_arguments()
  test_metadata_json_error()
  test_parameters_error()
  test_start_stop_error()
  test_scripts()
  test_functions()
