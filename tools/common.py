"""Small shared helpers for the release builders (Python standard library only)."""

from pathlib import Path
import hashlib, json, os, tempfile

ROOT = Path(__file__).resolve().parents[1]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    return sha(Path(path).read_bytes())


def json_read(path):
    return json.loads(Path(path).read_text())


def write_atomic(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix="." + path.name + ".", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as out:
            out.write(data)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def json_write(path, value):
    write_atomic(path, (json.dumps(value, indent=2, sort_keys=True) + "\n").encode())


def refresh_project_pins(group):
    if group not in ("native", "java"):
        raise ValueError("Expected native or java pin group.")
    path = ROOT / "provenance/project-binaries.json"
    data = json_read(path)
    if group == "native":
        native = data["native"]
        native["sha256"] = file_sha(ROOT / "module" / native["binary"])
        native["sources"] = {
            p.relative_to(ROOT).as_posix(): file_sha(p)
            for p in (ROOT / "src/native").rglob("*")
            if p.is_file()
        }
    else:
        for name, item in data["java"].items():
            item["sha256"] = file_sha(ROOT / "module" / item["binary"])
            item["source_sha256"] = file_sha(ROOT / item["source"])
    json_write(path, data)
