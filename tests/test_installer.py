"""Host fixtures of the actual installer; no mounts or phone mutations."""

from pathlib import Path
import hashlib, json, os, shutil, subprocess, tempfile, zipfile

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "build/module"


def sha(data):
    return hashlib.sha256(data).hexdigest()


WRAPPER = r"""
ui_print() { printf '%s\n' "$*"; }
abort() { printf 'ABORT: %s\n' "$*"; exit 7; }
getprop() {
    case "$1" in ro.build.version.sdk) echo "${FIXTURE_SDK:-37}";; ro.board.platform) echo mt6893;; esac
}
dumpsys() { echo "Config source: ${FIXTURE_POLICY:-/vendor/etc/audio_policy_configuration_a2dp_offload_disabled.xml}"; }
timeout() { shift; "$@"; }
set_perm_recursive() {
    python3 -c '
import json,os,sys
p,db,context=sys.argv[1:]
d=json.load(open(db)) if os.path.exists(db) else {}
for base,dirs,files in os.walk(p):
    for name in [base]+[os.path.join(base,n) for n in dirs+files]: d[name]=context
json.dump(d,open(db,"w"))
' "$1" "$FIXTURE_LABELS" "$6"
}
set_perm() { chmod "$4" "$1"; }
ls() {
    if [ "$1" = -Zd ]; then
        python3 -c '
import json,os,sys
d=json.load(open(os.environ["FIXTURE_LABELS"]))
label=d.get(sys.argv[1],"unlabelled")
if os.environ.get("FIXTURE_BAD_LABEL")=="1" and sys.argv[1].endswith("audio_effects.xml"):label="u:object_r:wrong_file:s0"
print(label,sys.argv[1])
' "$2"
    else command ls "$@"; fi
}
. "$FIXTURE_INSTALLER"
"""


def installer_case(
    case,
    expected_text=None,
    moved_vendor=False,
    upgrade=False,
    duplicate=None,
    **env_more,
):
    with tempfile.TemporaryDirectory(prefix="aosp-installer-") as tmp:
        temp = Path(tmp)
        stage = temp / "module"
        shutil.copytree(MODULE, stage)
        live = temp / "live"
        oldmods = temp / "installed"
        oldmods.mkdir()
        baseline = []
        for line in (stage / "BASE-SHA256SUMS").read_text().splitlines():
            _, target = line.split(None, 1)
            dest = live / target.lstrip("/")
            dest.parent.mkdir(parents=True, exist_ok=True)
            data = ("fixture for " + target).encode()
            dest.write_bytes(data)
            baseline.append(f"{sha(data)}  {target}\n")
        (stage / "BASE-SHA256SUMS").write_text("".join(baseline))
        if upgrade:
            previous = oldmods / "mt6893-spatial-aosp"
            previous.mkdir()
            (previous / "choice.conf").write_text("off\n")
            for source in (stage / "system").rglob("*"):
                if source.is_file():
                    target = live / source.relative_to(stage / "system")
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(source.read_bytes())
            if upgrade == "prior-pinned":
                # A synthetic historical payload tests path+hash acceptance.
                target = "/vendor/lib/soundfx/libmt6893spatial.so"
                data = b"known prior adapter fixture"
                (live / target.lstrip("/")).write_bytes(data)
                with (stage / "PREVIOUS-LIVE-SHA256SUMS").open("a") as f:
                    f.write(f"{sha(data)}  {target}\n")
        if moved_vendor:
            (stage / "system/vendor").rename(stage / "vendor")
            (stage / "system/vendor").symlink_to("../vendor", target_is_directory=True)
        (stage / "INSTALL-SHA256SUMS").write_text(
            "".join(
                f"{sha((stage / name).read_bytes())}  {name}\n"
                for name in (
                    line.split(None, 1)[1]
                    for line in (MODULE / "INSTALL-SHA256SUMS").read_text().splitlines()
                )
            )
        )
        if duplicate:
            shutil.copytree(stage / "system/vendor", stage / "vendor")
            if duplicate == "extra":
                (stage / "vendor/UNEXPECTED").write_text("unrelated")
            if duplicate == "corrupt":
                (stage / "vendor/lib/libspcxxrt.so").write_bytes(b"corrupt")
            env_more["KSU_METAMODULE"] = "mmrs"
        script = (
            (stage / "customize.sh")
            .read_text()
            .replace("/proc/1/root", str(live))
            .replace("/data/adb/modules", str(oldmods))
        )
        runner = temp / "customize-fixture.sh"
        runner.write_text(script)
        before = {
            str(p.relative_to(live)): sha(p.read_bytes())
            for p in live.rglob("*")
            if p.is_file()
        }
        if case == "mismatched audio file":
            (live / "vendor/etc/audio_effects.xml").write_text("changed by another mod")
        elif case == "corrupt payload":
            (stage / "control.jar").write_bytes(b"broken dex")
        elif case == "conflicting private runtime":
            runtime = live / "vendor/lib/libspcxxrt.so"
            runtime.parent.mkdir(parents=True, exist_ok=True)
            runtime.write_bytes(b"other project runtime")
        elif case == "conflicting adapter":
            adapter = live / "vendor/lib/soundfx/libmt6893spatial.so"
            adapter.parent.mkdir(parents=True, exist_ok=True)
            adapter.write_bytes(b"unreviewed adapter")
        # No installer invocation is allowed to write any captured live input.
        before = {
            str(p.relative_to(live)): sha(p.read_bytes())
            for p in live.rglob("*")
            if p.is_file()
        }
        env = {
            **os.environ,
            "MODPATH": str(stage),
            "FIXTURE_INSTALLER": str(runner),
            "FIXTURE_LABELS": str(temp / "labels.json"),
            **env_more,
        }
        proc = subprocess.run(
            ["bash", "-c", WRAPPER], env=env, capture_output=True, text=True, timeout=15
        )
        output = proc.stdout + proc.stderr
        if expected_text:
            assert proc.returncode == 7 and expected_text in output, (
                case,
                proc.returncode,
                output,
            )
        else:
            assert proc.returncode == 0 and "Preview staged." in output, (case, output)
            assert (stage / "choice.conf").read_text().strip() == (
                "off" if upgrade else "on"
            )
            labels = json.loads((temp / "labels.json").read_text())
            for line in (stage / "FILE-CONTEXTS").read_text().splitlines():
                expected, target = line.split(None, 1)
                prefix = "vendor" if (stage / "vendor").is_dir() else "system/vendor"
                path = stage / (prefix + target.removeprefix("/vendor"))
                assert labels[str(path)] == expected, target
            assert not any("/webroot" in p for p in labels)
        if duplicate == "valid" and not expected_text:
            assert (stage / "system/vendor").is_dir() and not (
                stage / "system/vendor"
            ).is_symlink()
            assert not (stage / "vendor").exists()
        after = {
            str(p.relative_to(live)): sha(p.read_bytes())
            for p in live.rglob("*")
            if p.is_file()
        }
        assert before == after
        print("PASS installer:", case)


if __name__ == "__main__":
    installer_case("clean staging")
    installer_case("manager vendor relocation", moved_vendor=True)
    installer_case("upgrade retains Original selection", upgrade=True)
    installer_case("pinned historical payload fixture", upgrade="prior-pinned")
    installer_case("MMRS duplicate staging", duplicate="valid")
    installer_case(
        "MMRS unexpected duplicate",
        "Unexpected duplicate vendor contents",
        duplicate="extra",
    )
    installer_case(
        "MMRS corrupt duplicate",
        "Duplicate vendor payload differs",
        duplicate="corrupt",
    )
    installer_case("mismatched audio file", "Audio file differs")
    installer_case("unsupported SDK", "Expected Android SDK 37", FIXTURE_SDK="36")
    installer_case(
        "unexpected active policy", "not covered", FIXTURE_POLICY="/odm/etc/unknown.xml"
    )
    installer_case("corrupt payload", "checksum verification failed")
    installer_case("conflicting private runtime", "An existing file conflicts")
    installer_case("conflicting adapter", "An existing file conflicts")
    installer_case("incorrect labels", "label is wrong", FIXTURE_BAD_LABEL="1")
