"""Updating one compiler family must never bless stale binaries in another."""

from pathlib import Path
import copy, json, shutil, sys, tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import common, build

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp)
    for name in ("module", "src", "provenance"):
        shutil.copytree(ROOT / name, root / name)
    common.ROOT = root
    build.ROOT = root
    pins = common.json_read(root / "provenance/project-binaries.json")
    source = root / "src/java/SpatialControl.java"
    source.write_text(
        source.read_text()
        + "\n// Intentional source change without rebuilding the Java binary.\n"
    )
    common.refresh_project_pins("native")
    assert (
        common.json_read(root / "provenance/project-binaries.json")["java"]
        == pins["java"]
    )
    try:
        build.check_project_pins()
    except ValueError as e:
        assert "Java helper/source changed" in str(e)
    else:
        raise AssertionError(
            "Native refresh must not accept stale Java source/binary association."
        )
    # Reverse direction: Java refresh must leave stale native pins detectable.
    source = root / "src/native/spatial_compat.c"
    source.write_text(
        source.read_text() + "\n/* Deliberate native edit without rebuilding. */\n"
    )
    old_native = copy.deepcopy(
        common.json_read(root / "provenance/project-binaries.json")["native"]
    )
    common.refresh_project_pins("java")
    assert (
        common.json_read(root / "provenance/project-binaries.json")["native"]
        == old_native
    )
    try:
        build.check_project_pins()
    except ValueError as e:
        assert "Native source changed" in str(e)
    else:
        raise AssertionError("Java refresh must not accept a stale native binary.")
print(
    "PASS independent source/binary pin groups; stale other-family binaries remain rejected."
)
