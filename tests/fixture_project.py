"""Golden mini-project builder for tests (valid Python with seeded violations)."""

from __future__ import annotations

import subprocess
from pathlib import Path

FILES = {
    "sample_app/__init__.py": "",
    "sample_app/loose.py": (
        "import json, os\n"
        "from sample_app.helpers import helper\n"
        "import time\n"
        "\n"
        "\n"
        "def run():\n"
        "    data = {'a': 1, 'b': 2}\n"
        "    data['a'] = data['a'] + 1\n"
        "    helper(data)\n"
        "    return data\n"
    ),
    "sample_app/helpers.py": (
        "import time\n"
        "import os\n"
        "\n"
        "\n"
        "def helper(d):\n"
        "    d['b'] = d['b'] + len(d)\n"
        "    return d\n"
        "\n"
        "\n"
        "def prepareData(value):\n"
        "    return value + 1\n"
    ),
    "tests/test_loose.py": (
        "from sample_app.loose import run\n"
        "\n"
        "\n"
        "def test_run():\n"
        "    assert run()['a'] == 2\n"
    ),
    "tests/test_tabbed.py": (
        "from sample_app.tabbed import alpha\n"
        "\n"
        "\n"
        "def test_alpha():\n"
        "    assert alpha() == 1\n"
    ),
    "tests/test_helpers.py": (
        "from sample_app.helpers import prepareData\n"
        "\n"
        "def test_prepareData():\n"
        "    assert prepareData(1) == 2\n"
    ),
    "sample_app/tabbed.py": (
        "def alpha():\n"
        "    return 1\n"
        "\n"
        "\n"
        "def beta():\n"
        "\treturn 2"
    ),
    "pyproject.toml": (
        "[project]\n"
        "name = \"sample-app\"\n"
        "version = \"0.1.0\"\n"
        "\n"
        "[tool.pytest.ini_options]\n"
        "testpaths = [\"tests\"]\n"
        "pythonpath = [\".\"]\n"
    ),
}


def build(root: Path) -> Path:
    for rel, content in FILES.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return root


def git(cwd: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(cwd), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )


def build_git_repo(root: Path) -> Path:
    """Build the fixture and initialize it as a committed git repo."""
    build(root)
    git(root, "init")
    git(root, "config", "core.autocrlf", "false")
    git(root, "add", "-A")
    git(root, "-c", "user.email=cg@example.com",
        "-c", "user.name=cg", "commit", "-m", "init")
    return root
