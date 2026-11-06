"""Rebuild only the project-authored ARM32 adapter; never execute target binaries."""

import argparse, shutil, subprocess
from common import ROOT, file_sha, refresh_project_pins, write_atomic


def build(zig):
    version = subprocess.check_output([zig, "version"], text=True).strip()
    if version != "0.14.1":
        raise SystemExit("Expected Zig 0.14.1; use --zig /path/to/zig-0.14.1/zig")
    work = ROOT / "build/native"
    work.mkdir(parents=True, exist_ok=True)
    # Stubs are built here, never in the module tree or installable ZIP.
    for name in ("spatial_compat.c", "spatial_effect_abi.h", "spatial_buffer.exports"):
        shutil.copyfile(ROOT / "src/native" / name, work / name)
    shutil.copytree(
        ROOT / "src/native/link-stubs", work / "link-stubs", dirs_exist_ok=True
    )
    commands = []
    for name in ("libc", "libdl"):
        args = [
            "cc",
            "-target",
            "arm-linux-android",
            "-mcpu=cortex_a9",
            "-mfloat-abi=softfp",
            "-Oz",
            "-shared",
            "-nostdlib",
            "-fPIC",
            "-fno-stack-protector",
            "-fno-builtin",
            "-Wl,--version-script=link-stubs/" + name + ".map",
            "-Wl,-soname," + name + ".so",
            "-o",
            "link-stubs/" + name + ".so",
            "link-stubs/android_public_stubs.c",
        ]
        if name == "libdl":
            args.append("-DSTUB_LIBDL")
        commands.append(args)
    commands.append(
        [
            "cc",
            "-target",
            "arm-linux-android",
            "-mcpu=cortex_a9",
            "-mfloat-abi=softfp",
            "-Oz",
            "-shared",
            "-nostdlib",
            "-fPIC",
            "-fno-stack-protector",
            "-fvisibility=hidden",
            "-ffunction-sections",
            "-fdata-sections",
            "-Wl,--gc-sections",
            "-Wl,--version-script=spatial_buffer.exports",
            "-Wl,-z,defs",
            "-Wl,-soname,libmt6893spatial.so",
            "-o",
            "libmt6893spatial.so",
            "spatial_compat.c",
            "link-stubs/libc.so",
            "link-stubs/libdl.so",
        ]
    )
    for args in commands:
        subprocess.run([zig, *args], cwd=work, check=True)
    return work / "libmt6893spatial.so"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zig", default="zig")
    parser.add_argument(
        "--update",
        action="store_true",
        help="replace the committed adapter and refresh its source/hash records after a successful build",
    )
    args = parser.parse_args()
    built = build(args.zig)
    expected = ROOT / "module/system/vendor/lib/soundfx/libmt6893spatial.so"
    print("Built:", built.relative_to(ROOT))
    print("SHA-256:", file_sha(built))
    print("Matches committed adapter:", file_sha(built) == file_sha(expected))
    if args.update:
        write_atomic(expected, built.read_bytes())
        refresh_project_pins("native")
        print(
            "Updated committed adapter and project provenance. Run tests before release."
        )
