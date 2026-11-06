# Development

## Package the current state

Requirements: Python 3.10+ and the checked-in repository files.

```sh
python3 tools/build.py
python3 tools/check.py
```

This path is offline. It verifies the OEM/runtime/profile hashes and the
project-source/prebuilt associations, then creates a deterministic module ZIP and
checksum in `dist/`. `build/module/` is the exact staged installable tree.
ZIP entry order and timestamps are fixed; compressed bytes may differ between
zlib versions. Both output directories are ignored by Git. No private phone reports, old ROM workspaces,
compiler installation or previous release ZIPs are needed.

## Rebuild the adapter

Use **Zig 0.14.1**. The adapter targets ARMv7 softfp with the legacy Android
32-bit effect ABI. The builder creates link-time Bionic stubs only under
`build/native/link-stubs/`; those stub DSOs must never ship or run on a phone.

```sh
python3 tools/build_native.py --zig /absolute/path/to/zig-0.14.1/zig
```

The command prints whether its output matches the committed adapter. To adopt an
intentional native-source change after review:

```sh
python3 tools/build_native.py --zig /absolute/path/to/zig-0.14.1/zig --update
python3 tools/build.py
python3 tools/check.py
```

`--update` replaces the committed adapter and refreshes project source/hash pins.
It does not alter OEM DSP binaries or profiles. New native builds still need phone
validation before release.

## Rebuild the Java helpers

Use **JDK 17** and official Google **R8/D8 8.7.18**. The pinned R8 JAR SHA-256 is:

`58366f77067207c39a17d469de7b05701d2877212a9c55201bcb0af43e59e903`

R8 is a build dependency, not a repository or module payload. Obtain it from
[Google's Maven artifact](https://dl.google.com/dl/android/maven2/com/android/tools/r8/8.7.18/r8-8.7.18.jar)
and pass its local path:

```sh
python3 tools/build_java.py --r8 /absolute/path/to/r8.jar
```

This produces the rebuilt JARs under `build/java/`. Add `--update` only when adopting
intentional source changes; this updates the committed JARs and their source/hash
records. It may change the prebuilt bytes, especially for the demo originally
compiled with a different Java compiler. Confirm controls, playback and cleanup
on the phone after adopting new JARs.

## Host checks

```sh
python3 tools/build.py
python3 tools/check.py
python3 tools/test.py
```

The package checks need Python only. Additional host tests use a C compiler,
Bash and Node.js. They exercise the actual adapter source, installer guards,
preference retention, mount-layout staging and demo-report cleanup with fixtures.
They do not claim an Android boot or live hardware test.

Optional WebUI state and responsive-layout tests are in `tests/test_webui.cjs`.
With [Playwright and Chromium](https://playwright.dev/docs/intro) installed, run
`node tests/test_webui.cjs` after building. `SPATIAL_PLAYWRIGHT_PATH` can point to
an existing Playwright installation and `SPATIAL_BROWSER_BINARY` to an existing
Chromium executable. These optional browser dependencies are not bundled.

## Prepare another prerelease

1. Change `module/module.prop` version and increase `versionCode`.
2. Update installation text, changelog and a release note under `docs/releases/`.
3. Rebuild changed project binaries explicitly, then build and test the package.
4. Perform phone listening, routing, removal and upgrade checks.
5. Commit, tag and publish the corresponding ZIP and checksum.

Keep preview labels until the relevant playback defects are resolved and tested.
Avoid broad device/ROM claims based on one compatible build. See [PUBLISH.md](PUBLISH.md).
