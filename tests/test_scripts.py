import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_check_sources_offline():
    out = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "check_sources.py"), "--offline"],
        capture_output=True, text=True, check=False,
    )
    assert out.returncode == 0, out.stdout + out.stderr
