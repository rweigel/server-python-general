# Shared helper for cloning/updating the server-python-demo repo used by
# test_app.py and test_demo.py.

DEMO_REPO = "https://github.com/hapi-server/server-python-demo.git"


def _ensure_demo_repo():
  import pathlib
  import subprocess

  demo_dir = pathlib.Path(__file__).parent / "server-python-demo"

  if (demo_dir / ".git").exists():
    subprocess.run(["git", "-C", str(demo_dir), "pull", "--quiet"], check=True)
  else:
    subprocess.run(["git", "clone", "--quiet", DEMO_REPO, str(demo_dir)], check=True)
  return demo_dir
