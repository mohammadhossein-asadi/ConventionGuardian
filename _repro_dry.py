import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from conventionguardian import scanner  # noqa: E402


def run(root, args):
    return subprocess.run(
        [sys.executable, "-m", "conventionguardian", *args],
        cwd=root,
        capture_output=True,
        text=True,
    )


def main():
    root = Path(tempfile.mkdtemp(prefix="cg-dry-"))
    (root / ".gitkeep").write_text("", encoding="utf-8")
    (root / "app.py").write_text(
        "def  hello( name ):\n    return 'hi  ' + name\n", encoding="utf-8"
    )
    (root / "util.py").write_text(
        "def foo(a,b):\n    return a + b\n", encoding="utf-8"
    )
    (root / "scratch.txt").write_text("dirty", encoding="utf-8")

    def git(*args):
        r = subprocess.run(
            ["git", *args], cwd=root, capture_output=True, text=True
        )
        assert r.returncode == 0, r.stderr
        return r

    git("init")
    git("add", ".")
    git("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-m", "init")

    from typer.testing import CliRunner

    import conventionguardian.cli as cli

    monkey_find_root = scanner.find_root

    class MP:
        def setattr(self, mod, name, value):
            setattr(mod, name, value)
        def undo(self):
            setattr(scanner, "find_root", monkey_find_root)

    mp = MP()
    mp.setattr(scanner, "find_root", lambda: root)

    r1 = CliRunner().invoke(cli.app, ["adopt", "--allow-dirty"])
    print("=== RUN ok ===", r1.exit_code)
    print(r1.output)
    if r1.exception:
        import traceback
        traceback.print_exception(type(r1.exception), r1.exception, r1.exception.__traceback__)

    git("add", ".")
    git("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-m", "adopt")

    r2 = CliRunner().invoke(cli.app, ["adopt"])
    print("=== RUN again ===", r2.exit_code)
    print(r2.output)
    if r2.exception:
        import traceback
        traceback.print_exception(type(r2.exception), r2.exception, r2.exception.__traceback__)

    r3 = CliRunner().invoke(cli.app, ["adopt", "--dry-run"])
    print("=== RUN dry ===", r3.exit_code)
    print(r3.output)
    if r3.exception:
        import traceback
        traceback.print_exception(type(r3.exception), r3.exception, r3.exception.__traceback__)


if __name__ == "__main__":
    main()
