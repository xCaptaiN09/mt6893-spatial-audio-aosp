"""Run meaningful host tests. Android boot and hardware playback are separate."""

import shutil, subprocess, sys
from common import ROOT
from check import run

if __name__ == "__main__":
    run()
    subprocess.run([sys.executable, str(ROOT / "tests/test_provenance.py")], check=True)
    for script in (ROOT / "build/module").glob("*.sh"):
        subprocess.run(["sh", "-n", str(script)], check=True)
    subprocess.run([sys.executable, str(ROOT / "tests/test_installer.py")], check=True)
    subprocess.run([sys.executable, str(ROOT / "tests/test_demo.py")], check=True)
    compiler = shutil.which("cc")
    if not compiler:
        raise SystemExit("A C compiler is required for adapter host tests.")
    out = ROOT / "build/native-adapter-host-test"
    subprocess.run(
        [
            compiler,
            "-std=c11",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-I" + str(ROOT / "src/native"),
            str(ROOT / "tests/native_adapter_test.c"),
            "-o",
            str(out),
        ],
        check=True,
    )
    subprocess.run([str(out)], check=True)
    node = shutil.which("node")
    if not node:
        raise SystemExit("Node.js is required for WebUI source syntax checks.")
    subprocess.run([node, "--check", str(ROOT / "module/webroot/app.js")], check=True)
    print(
        "Host checks passed. See docs/TESTING.md for phone validation and known issues."
    )
