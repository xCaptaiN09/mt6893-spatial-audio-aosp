# MT6893 Spatial Audio AOSP

Original Oplus headphone tuning, Android Spatializer controls and a local WebUI.

**v0.1.4-preview · RMX3031 · Evolution X Android 17 12.3**
By [xCaptaiN09](https://github.com/xCaptaiN09)

This is an experimental compatibility port for the inspected **Realme X7 Max
(RMX3031 / MT6893)** audio build. Spatial playback is audible on the test phone,
but two playback issues remain open. It is **not a universal AOSP release**.

## What is included

- Oplus Spatializer engine with the original v0.6 headphone profiles.
- An ARM32 compatibility adapter for OEM channel initialization and Android
  stereo-track metadata inside the inspected multichannel mixer.
- **Original / Spatial Audio** controls using Android's native Spatializer APIs.
- A dark WebUI with a blue, violet and teal glow ring, headphone status and
  `xCaptaiN09` credit. The animation is decorative.
- A 24-second channel demo and an explicit diagnostic-report action.
- Guarded installation, Android file labels and a saved on/off preference.

The channel demo creates no automatic report in Downloads. **Save diagnostic
report** and the root manager's **Action** button export a report only when
requested.

## Current status

| Area | Status |
| --- | --- |
| Spatial playback on the inspected RMX3031 build | Audible on the test phone |
| USB-headphone detection and native on/off controls | Working on the test phone |
| WebUI and channel demo | Working; UI approved by the maintainer |
| YouTube test-video rumble | **Unresolved**; YouTube selected a stereo Opus stream while a separate 5.1 version contains LFE |
| Surround Sound Test short clips | **Unresolved**; crackle can follow rear-channel clips with Spatial Audio on |
| Head tracking | Requires compatible hardware; not demonstrated on this setup |
| Bluetooth, other devices and other ROM builds | Not validated by this preview |

The shipped profiles include OEM Bluetooth variants, but that does **not** mean
Bluetooth playback is enabled or validated by this port. The preview's added
policy routes target wired and USB headphone outputs.

## Requirements

- The inspected RMX3031 Evolution X Android 17 12.3 audio build, **SDK 37**.
- KernelSU / KernelSU-Next and working systemless file mounting.
- **Magic Mount-rs v4.1.12-959** is the mounting provider used on the test phone.
- A compatible root-manager WebUI host for the interface.
- Wired or USB headphones. USB playback must already work on the ROM.

The installer checks the captured audio-policy, HAL and dependency hashes. It
stops on unreviewed changes rather than assuming another MT6893 ROM is compatible.
Magisk and other root/mount combinations are not claimed tested here.

## Install

1. Download **`MT6893-Spatial-Audio-AOSP-v0.1.4-preview.zip`** from
   [Releases](https://github.com/xCaptaiN09/mt6893-spatial-audio-aosp/releases).
2. Keep the working mounting provider enabled. Install the module ZIP through
   your root manager and **reboot**.
3. Connect headphones, open the module's WebUI and start at a low media volume.
4. Compare **Original** and **Spatial Audio** with the same audio.

Existing private previews use the same module ID, **`mt6893-spatial-aosp`**. Install
this ZIP over that module; the saved selection is retained. The repository ZIP
and GitHub's automatic source archives are **not installable module ZIPs**.

Do not stack another Spatializer port. This release does not include the old
ColorOS USB Audio Fix, a ColorOS Settings APK or display changes.

## If something goes wrong

- **Audio files not mounted:** check the mounting provider, then reboot.
- **Unexpected audio or routing:** select Original. If necessary, disable this
  module in the root manager and reboot.
- **Uninstall:** remove the module through the root manager and reboot.
- **Report a problem:** while reproducing it, use **Save diagnostic report**.
  Include the ROM/build, root manager, mounting provider, module version,
  headphone/DAC, player and source-channel format. Review logs before posting.

Enabled/available status confirms framework state; it does not prove that every
player or source is being spatialized correctly. The ring is not a microphone,
waveform or live sound meter.

## Build and development

The repository contains the current runtime payload, project source and pinned
provenance. Building the release ZIP needs **Python 3.10+ only**, with no network
access, Android SDK, compiler or private phone captures:

```sh
python3 tools/build.py
python3 tools/check.py
```

Output is written to `dist/`; it is ignored by Git. The handoff repository ZIP
also includes the prebuilt preview and checksum there for immediate release.

- [Development and source rebuilding](docs/DEVELOPMENT.md)
- [Compatibility and implementation](docs/COMPATIBILITY.md)
- [Testing and open investigations](docs/TESTING.md)
- [Changelog](CHANGELOG.md)
- [Push and prerelease commands](docs/PUBLISH.md)

## Credits and licensing

Maintained by **Muhammed Dilshad A. — xCaptaiN09**. The original project payload
comes from [mt6893-spatial-audio](https://github.com/xCaptaiN09/mt6893-spatial-audio).
OEM source provenance, runtime notices and upstream credits are recorded in
[THIRD_PARTY.md](THIRD_PARTY.md), [NOTICE](NOTICE) and `provenance/`.

[MIT](LICENSE) covers project-authored code and documentation. OEM libraries,
profiles and derived OEM configurations retain their original ownership and are
not relicensed under MIT. Android interface material and compiler/runtime notices
are retained under `licenses/`.
