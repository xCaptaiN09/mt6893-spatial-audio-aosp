"""Offline checks of the built module; Python standard library only."""

from pathlib import Path
import hashlib, json, re, struct, zipfile, zlib
from common import ROOT, file_sha, sha


def lines(data):
    result = {}
    for line in data.decode().splitlines():
        digest, name = line.split(None, 1)
        if not re.fullmatch("[0-9a-f]{64}", digest) or name in result:
            raise ValueError("Invalid/duplicate checksum entry: " + line)
        result[name] = digest
    return result


def run():
    summary = json.loads((ROOT / "build/summary.json").read_text())
    archive = ROOT / summary["archive"]
    stage = ROOT / "build/module"
    assert (
        file_sha(archive) == summary["sha256"]
        and archive.stat().st_size == summary["size"]
    )
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        members = z.namelist()
        assert len(members) == len(set(members)) == summary["members"]
        assert set(members) == {
            p.relative_to(stage).as_posix() for p in stage.rglob("*") if p.is_file()
        }
        for item in z.infolist():
            name = item.filename
            assert (
                not name.startswith("/")
                and ".." not in Path(name).parts
                and "\\" not in name
            )
            assert z.read(item) == (stage / name).read_bytes()
            assert item.external_attr >> 16 == (
                0o100755 if name.endswith(".sh") else 0o100644
            )
            if name.endswith(
                (".sh", ".js", ".css", ".html", ".txt", ".prop", ".md", ".json")
            ):
                assert b"\r" not in z.read(item)
        manifest = lines(z.read("INSTALL-SHA256SUMS"))
        assert set(manifest) == set(members) - {"INSTALL-SHA256SUMS"}
        for name, digest in manifest.items():
            assert sha(z.read(name)) == digest, name
        live = lines(z.read("LIVE-SHA256SUMS"))
        assert len(live) == 16
        assert set(live) == {
            name.removeprefix("system")
            for name in members
            if name.startswith("system/")
        }
        for name, digest in live.items():
            assert sha(z.read("system" + name)) == digest, name
        for name in ("control.jar", "demo.jar"):
            with zipfile.ZipFile(stage / name) as j:
                assert j.testzip() is None
                dex = j.read("classes.dex")
                assert dex.startswith(b"dex\n")
                assert (
                    struct.unpack_from("<I", dex, 8)[0]
                    == zlib.adler32(dex[12:]) & 0xFFFFFFFF
                )
                assert dex[12:32] == hashlib.sha1(dex[32:]).digest()
        assert z.read("CONTROL-JAR-SHA256").strip().decode() == sha(
            z.read("control.jar")
        )
        assert z.read("DEMO-JAR-SHA256").strip().decode() == sha(z.read("demo.jar"))
        for name in members:
            if name.endswith(".so"):
                b = z.read(name)
                assert (
                    b[:6] == b"\x7fELF\x01\x01"
                    and struct.unpack_from("<H", b, 18)[0] == 40
                )
                assert Path(name).name not in ("libc.so", "libdl.so")
        label_paths = {
            line.split(None, 1)[1]
            for line in z.read("FILE-CONTEXTS").decode().splitlines()
        }
        expected = set(live)
        for name in list(expected):
            parent = Path(name).parent
            while str(parent) != "/":
                expected.add(str(parent))
                parent = parent.parent
        assert label_paths == expected
        for line in z.read("FILE-CONTEXTS").decode().splitlines():
            label, name = line.split(None, 1)
            assert label == (
                "u:object_r:vendor_configs_file:s0"
                if name == "/vendor/etc" or name.startswith("/vendor/etc/")
                else "u:object_r:vendor_file:s0"
            )
        for filename in ("BASE-SHA256SUMS", "PREVIOUS-LIVE-SHA256SUMS"):
            for line in z.read(filename).decode().splitlines():
                digest, name = line.split(None, 1)
                assert (
                    re.fullmatch("[0-9a-f]{64}", digest)
                    and name.startswith("/vendor/")
                    and ".." not in Path(name).parts
                )
        assert b'<p class="author-credit">xCaptaiN09</p>' in z.read(
            "webroot/index.html"
        )
        assert not any(
            n.startswith(("source/", "reference/", "build/", "dist/")) for n in members
        )
    checksum = (archive.with_name(archive.name + ".sha256")).read_text()
    assert checksum == f'{summary["sha256"]}  {archive.name}\n'
    print(
        "PASS ZIP CRC, byte equality, DEX integrity, manifests, paths, permissions, labels, ARM32 payload and no build stubs."
    )
    print(
        "PASS release checksum, retained WebUI credit and runtime-only module layout."
    )


if __name__ == "__main__":
    run()
