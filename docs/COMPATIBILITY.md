# Compatibility and implementation

## Validated scope

The target is the inspected **RMX3031 Evolution X Android 17 12.3** audio build,
SDK 37, using its 32-bit MT6893 legacy audio-effect service. The tested root/mount
setup is KernelSU-Next plus Magic Mount-rs v4.1.12-959, SELinux enforcing.
The actual device kernel is 4.19.325. This does not establish support for every
MT6893 device, every AOSP ROM, Magisk or Bluetooth.

`module/BASE-SHA256SUMS` pins the captured policy, HAL and platform dependency
inputs. The installer accepts those inputs, the current payload or exact prior
hashes at the corresponding paths. The stable module ID is `mt6893-spatial-aosp`.
It rejects unreviewed audio-file changes and conflicting private runtime/adapter
files. Do not bypass those checks to claim another ROM supported.

## Composition of the port

The three policy/effect XML files retain their reviewed original elements. A
dedicated 48 kHz PCM16 Spatializer output is added to four wired/USB routes and
the effect is registered through the adapter. The platform primary audio HAL,
framework binaries and SELinux policy are not replaced.

The ARM32 adapter loads the retained OEM plugin under its original effect UUID.
After successful SET_CONFIG it sends OEM parameter `0x100100BA` with the configured
input count. Under the inspected 12-channel mixer, AOSP's input-mask metadata
(key 12) selects OEM count 2 only when every active track is stereo. Mixed,
multichannel or unknown layouts keep the full mixer count. Empty metadata keeps
the previous mode for tails; INIT clears state and reconfiguration reapplies the
remembered nonempty metadata. Buffers and DSP processing are forwarded unchanged.

Private phone buffer tests confirmed native stereo equivalence for ten generated
tone cases under that translation. Those tests do not prove every live source,
stream transition or player correct. The reported crackle and YouTube rumble are
still open investigations.

## Mounting and labels

The installer retains a physical `system/vendor` tree for the tested MMRS hook.
If that hook has created a redundant `vendor` copy, the installer verifies its
complete inventory and hashes before removing only that duplicate staging copy.
Vendor configuration and library labels are checked before installation finishes.
The boot service waits for boot completion, verifies the live files in init's
mount namespace and applies the saved selection once. It does not restart audio
services or poll the Spatializer continuously.

## Controls

The Android helper uses Spatializer API reflection rather than hardcoded Binder
transaction numbers. The WebUI uses the root manager's public local execution
bridge. Headphone enumeration stays available when mounts fail, while activation
is blocked. Head-tracking capability does not create a tracker in ordinary IEMs.
