"""Rebuild reflection-based Android DEX helpers with JDK 17 and pinned R8/D8."""

import argparse, io, re, shutil, subprocess, zipfile
from common import ROOT, file_sha, refresh_project_pins, write_atomic

R8_SHA = "58366f77067207c39a17d469de7b05701d2877212a9c55201bcb0af43e59e903"
if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--r8", required=True, help="path to official R8 8.7.18 r8.jar")
    p.add_argument(
        "--update",
        action="store_true",
        help="replace committed JARs and refresh source/hash records after successful builds",
    )
    args = p.parse_args()
    r8 = __import__("pathlib").Path(args.r8).resolve()
    if file_sha(r8) != R8_SHA:
        raise SystemExit("R8 checksum mismatch; expected official 8.7.18.")
    version = subprocess.run(
        ["java", "-version"], capture_output=True, text=True, check=True
    )
    if not re.search(r'version "17[.]', version.stderr + version.stdout):
        raise SystemExit("Expected JDK 17.")
    outputs = []
    for name, jarname in [
        ("SpatialControl", "control.jar"),
        ("SpatialPlaybackProbe", "demo.jar"),
    ]:
        work = ROOT / "build/java" / name
        classes = work / "classes"
        dex = work / "dex"
        classes.mkdir(parents=True, exist_ok=True)
        dex.mkdir(exist_ok=True)
        compiler = (
            ["javac"] if shutil.which("javac") else ["java", "com.sun.tools.javac.Main"]
        )
        subprocess.run(
            [
                *compiler,
                "--release",
                "8",
                "-Xlint:all",
                "-d",
                str(classes),
                str(ROOT / "src/java" / (name + ".java")),
            ],
            check=True,
        )
        subprocess.run(
            [
                "java",
                "-cp",
                str(r8),
                "com.android.tools.r8.D8",
                "--min-api",
                "23",
                "--output",
                str(dex),
                str(classes / (name + ".class")),
            ],
            check=True,
        )
        data = io.BytesIO()
        with zipfile.ZipFile(data, "w") as z:
            info = zipfile.ZipInfo("classes.dex", (2026, 11, 6, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, (dex / "classes.dex").read_bytes())
        target = ROOT / "build/java" / jarname
        write_atomic(target, data.getvalue())
        outputs.append((target, jarname))
        print("Built:", target.relative_to(ROOT), "SHA-256:", file_sha(target))
    if args.update:
        for source, name in outputs:
            write_atomic(ROOT / "module" / name, source.read_bytes())
        refresh_project_pins("java")
        print(
            "Updated committed helpers and project provenance. New JARs need playback/control checks on the phone."
        )
