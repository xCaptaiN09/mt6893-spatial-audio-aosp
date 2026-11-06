"""Exercise the real controller with a mock player: export only on request."""

from pathlib import Path
import os
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "build/module"


for mode in ("success", "failure"):
    with tempfile.TemporaryDirectory(prefix="aosp-demo-") as tmp:
        root = Path(tmp)
        stage = root / "module"
        live = root / "live"
        tools = root / "bin"
        shutil.copytree(MODULE, stage)
        shutil.copytree(stage / "system/vendor", live / "vendor")
        downloads = root / "Downloads"
        downloads.mkdir()
        work = root / "private"
        work.mkdir()
        tools.mkdir()
        script = (
            (stage / "control.sh")
            .read_text()
            .replace("/proc/1/root", str(live))
            .replace("/data/local/tmp", str(work))
            .replace("/sdcard/Download", str(downloads))
        )
        (stage / "control.sh").write_text(script)
        mock = tools / "app_process"
        mock.write_text("""#!/bin/sh
if [ "$2" = SpatialPlaybackProbe ]; then
    echo private-phase > "$3/phase.txt"
    echo 'Mock player output stays private'
    [ "$FIXTURE_DEMO" != failure ] || exit 4
else
    echo '{"enabled":true,"available":true,"level":1,"headTrackerAvailable":false,"device":"USB test"}'
fi
""")
        mock.chmod(0o755)
        env = {
            **os.environ,
            "PATH": str(tools) + ":" + os.environ["PATH"],
            "FIXTURE_DEMO": mode,
        }
        run = subprocess.run(
            ["sh", str(stage / "control.sh"), "demo"],
            env=env,
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert run.returncode == (0 if mode == "success" else 4), (
            run.stdout,
            run.stderr,
        )
        assert not list(
            downloads.iterdir()
        ), "Demo must never export files to Downloads"
        assert not list(work.iterdir()), "Private player output must be cleaned up"
        assert not (stage / ".control-lock").exists()
        assert "report saved" not in run.stdout.lower()
        if mode == "success":
            assert "Channel demo finished." in run.stdout
        # The separate, explicitly requested diagnostic action still exports.
        run = subprocess.run(
            ["sh", str(stage / "control.sh"), "report"],
            env=env,
            capture_output=True,
            text=True,
            timeout=8,
        )
        assert run.returncode == 0 and "Report saved:" in run.stdout, (
            run.stdout,
            run.stderr,
        )
        assert len(list(downloads.glob("mt6893-spatial-aosp-*.txt"))) == 1
        print(
            "PASS demo",
            mode,
            ": no automatic export, private cleanup; explicit report export remains available",
        )
