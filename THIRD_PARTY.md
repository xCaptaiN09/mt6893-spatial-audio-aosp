# Third-party materials

The project's MIT license applies to project-authored work only. It does not
relicense the OEM engine, tuning files or derived OEM configurations.

## Original release and donor

| Material | Pinned source |
| --- | --- |
| Original Spatial Audio release, profiles and playback demo | [xCaptaiN09/mt6893-spatial-audio](https://github.com/xCaptaiN09/mt6893-spatial-audio/tree/5b6d7fb4f31e8946767e0b732be689acf56f4071) |
| Donor runtime and OEM source provenance | [Jiovanni-dump/oneplus_op5d35l1_dump](https://github.com/Jiovanni-dump/oneplus_op5d35l1_dump/tree/6c4375b5d3fab596f1ad3f42d92162de7fddf95e) |
| Runtime input path | `odm/lib/libc++_shared.so` in the pinned donor |
| Audio policy and effect XML | Exact captured inputs from the inspected RMX3031 Evolution X audio build |

`provenance/oem-assets.json` pins all twelve shipped OEM/runtime/profile files.
`provenance/oem-adaptations.json` records original input hashes and the exact
runtime-name and eight profile-path edits. No OEM processing instructions or HP
profile bytes were changed by those adaptations.

The C++ runtime has a private `libspcxxrt.so` SONAME and matching plugin dependency.
The platform C++ runtime is not replaced. Upstream LLVM 8 libc++ and libc++abi
license notices are included because the donor's compiler comment identifies an
LLVM 8-based Android toolchain:

- [LLVM 8 libc++ license](https://github.com/llvm/llvm-project/blob/llvmorg-8.0.0/libcxx/LICENSE.TXT)
- [LLVM 8 libc++abi license](https://github.com/llvm/llvm-project/blob/llvmorg-8.0.0/libcxxabi/LICENSE.TXT)

OEM assets retain their original ownership. This repository does not assert or
grant an OEM redistribution license.

## Project binaries and interfaces

- `libmt6893spatial.so`: project-authored legacy-effect ABI adapter. Source is in
  `src/native/`; built with Zig 0.14.1 for ARMv7 softfp. Zig's MIT notice is retained.
- `control.jar`: project-authored Android Spatializer API reflection helper;
  source is `src/java/SpatialControl.java`.
- `demo.jar`: the original project's 24-second playback diagnostic;
  source is `src/java/SpatialPlaybackProbe.java`.
- Android effect interface declarations are based on AOSP, Apache 2.0; the full
  license text is retained under `licenses/`.

Project source-to-binary pins are in `provenance/project-binaries.json`.
The native link stubs are build-time declarations only; their generated `libc.so`
and `libdl.so` are never included in the module ZIP.

## External dependencies

[KernelSU](https://github.com/tiann/KernelSU),
[KernelSU-Next](https://github.com/KernelSU-Next/KernelSU-Next) and the installed
Magic Mount-rs provider retain their own licenses. They are not bundled here.
The root manager's public WebUI execution bridge is called by local JavaScript;
no remote scripts, analytics, fonts or runtime network assets are used.
