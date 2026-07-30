# Usage:
#   pytest test_app.py
#   python test_app.py

import pathlib
import subprocess


def _run_script(server):
  script = pathlib.Path(__file__).parent / "test_app.sh"
  cmd = ["bash", str(script), server]
  print(f"Testing: {' '.join(cmd)}")
  result = subprocess.run(cmd, cwd=script.parent, capture_output=True, text=True, timeout=30)
  emsg = f"test_app.sh {server} failed (exit code {result.returncode}):\n{result.stdout}\n{result.stderr}"
  assert result.returncode == 0, emsg

def test_app_uvicorn():
  _run_script("uvicorn")

def test_app_gunicorn():
  _run_script("gunicorn")

if __name__ == "__main__":
  test_app_uvicorn()
  test_app_gunicorn()
