"""Package the checked-in preview without compilers, downloads or private inputs."""

from pathlib import Path
import json, re, shutil, struct, zipfile
from common import ROOT, file_sha, json_read, sha, write_atomic


def check_project_pins():
    pins = json_read(ROOT / "provenance/project-binaries.json")
    native = pins["native"]
    if file_sha(ROOT / "module" / native["binary"]) != native["sha256"]:
        raise ValueError(
            "Adapter differs from project provenance. Rebuild with tools/build_native.py --update."
        )
    for path, digest in native["sources"].items():
        if file_sha(ROOT / path) != digest:
            raise ValueError(
                "Native source changed: "
                + path
                + ". Rebuild with tools/build_native.py --update."
            )
    actual = {
        p.relative_to(ROOT).as_posix()
        for p in (ROOT / "src/native").rglob("*")
        if p.is_file()
    }
    if actual != set(native["sources"]):
        raise ValueError("Native source inventory changed; rebuild with --update.")
    for name, item in pins["java"].items():
        if (
            file_sha(ROOT / "module" / item["binary"]) != item["sha256"]
            or file_sha(ROOT / item["source"]) != item["source_sha256"]
        ):
            raise ValueError(
                "Java helper/source changed: "
                + name
                + ". Rebuild with tools/build_java.py --update."
            )
    return pins


def build():
    pins = check_project_pins()
    source = ROOT / "module"
    oem = json_read(ROOT / "provenance/oem-assets.json")
    for name, digest in oem.items():
        if file_sha(source / name) != digest:
            raise ValueError("Original OEM asset changed: " + name)
    files = {}
    for path in sorted(source.rglob("*")):
        if path.is_symlink():
            raise ValueError(
                "Symlinks are not allowed in the committed module template: "
                + str(path)
            )
        if path.is_file():
            files[path.relative_to(source).as_posix()] = path.read_bytes()
    props = {}
    for line in files["module.prop"].decode().splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key in props:
            raise ValueError("Duplicate module.prop key: " + key)
        props[key] = value
    if props.get("id") != "mt6893-spatial-aosp":
        raise ValueError("Keep the stable module ID for upgrades.")
    version = props["version"]
    if not re.fullmatch(r"v\d+\.\d+\.\d+-[A-Za-z0-9.-]+", version):
        raise ValueError("Expected a prerelease version such as v0.1.3-preview.")
    if int(props["versionCode"]) <= 0:
        raise ValueError("Invalid versionCode.")
    # All shipped native objects must be ARM32; link-time libc/libdl stubs stay out.
    for name, data in files.items():
        if name.endswith(".so"):
            if Path(name).name in ("libc.so", "libdl.so"):
                raise ValueError("Build-only stub in module tree.")
            if (
                data[:5] != b"\x7fELF\x01"
                or struct.unpack_from("<H", data, 18)[0] != 40
            ):
                raise ValueError("Expected ARM32 ELF: " + name)
    for name in ("control.jar", "demo.jar"):
        with zipfile.ZipFile(source / name) as z:
            if z.testzip() or "classes.dex" not in z.namelist():
                raise ValueError("Invalid DEX archive: " + name)
    for name in ("LICENSE", "NOTICE", "THIRD_PARTY.md"):
        files[name] = (ROOT / name).read_bytes()
    files["README.txt"] = (ROOT / "docs/INSTALL.txt").read_bytes()
    for path in sorted((ROOT / "licenses").glob("*")):
        files["licenses/" + path.name] = path.read_bytes()
    files["SOURCES.txt"] = (ROOT / "provenance/SOURCES.txt").read_bytes()
    files["CONTROL-JAR-SHA256"] = (sha(files["control.jar"]) + "\n").encode()
    files["DEMO-JAR-SHA256"] = (sha(files["demo.jar"]) + "\n").encode()
    live = {
        name.removeprefix("system"): sha(data)
        for name, data in files.items()
        if name.startswith("system/")
    }
    if len(live) != 16:
        raise ValueError("Expected the reviewed 16-file live payload.")
    files["LIVE-SHA256SUMS"] = "".join(
        f"{digest}  {name}\n" for name, digest in sorted(live.items())
    ).encode()
    info = {
        "project": "mt6893-spatial-audio-aosp",
        "version": version,
        "versionCode": int(props["versionCode"]),
        "target": "Inspected RMX3031 Evolution X Android 17 12.3 audio build",
        "module_id": props["id"],
        "project_binaries": pins,
        "oem_assets": oem,
        "live_payload": live,
        "build": "Deterministic Python standard-library packaging; committed prebuilt binaries verified against their source/hash records.",
        "known_issues": [
            "YouTube test-video LFE rumble remains absent; stream selection/decoder capability investigation is open.",
            "Surround Sound Test can crackle after short channel clips with Spatial Audio enabled.",
        ],
    }
    files["BUILD-INFO.json"] = (
        json.dumps(info, indent=2, sort_keys=True) + "\n"
    ).encode()
    files["INSTALL-SHA256SUMS"] = "".join(
        f"{sha(data)}  {name}\n" for name, data in sorted(files.items())
    ).encode()
    stage = ROOT / "build/module"
    if stage.exists():
        shutil.rmtree(stage)
    for name, data in files.items():
        path = stage / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        path.chmod(0o755 if name.endswith(".sh") else 0o644)
    dist = ROOT / "dist"
    dist.mkdir(exist_ok=True)
    archive = dist / f"MT6893-Spatial-Audio-AOSP-{version}.zip"
    with zipfile.ZipFile(
        archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as z:
        for name, data in sorted(files.items()):
            item = zipfile.ZipInfo(name, (2026, 11, 6, 0, 0, 0))
            item.create_system = 3
            item.external_attr = (0o100755 if name.endswith(".sh") else 0o100644) << 16
            item.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(item, data)
    digest = file_sha(archive)
    write_atomic(
        archive.with_name(archive.name + ".sha256"),
        f"{digest}  {archive.name}\n".encode(),
    )
    summary = {
        "archive": archive.relative_to(ROOT).as_posix(),
        "size": archive.stat().st_size,
        "sha256": digest,
        "members": len(files),
        "live_payload": live,
    }
    write_atomic(
        ROOT / "build/summary.json", (json.dumps(summary, indent=2) + "\n").encode()
    )
    print("Built:", archive.relative_to(ROOT))
    print("SHA-256:", digest)
    print("Original OEM assets and prebuilt/source pins verified.")
    return archive, stage


if __name__ == "__main__":
    build()
