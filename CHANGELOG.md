# Changelog

## v0.1.4-preview — Android 16/17 AOSP installer compatibility

- Added Android 16 (SDK 36) support alongside Android 17 (SDK 37) in the installer guard.
- Expanded MT6893 / RMX3031 platform detection across fallback system/vendor properties and HAL presence for ROMs such as LineageOS that leave `ro.board.platform` empty.
- Logged audio service ELF class and active audio policy early during installation, and relaxed base vendor hash mismatches to non-fatal notices so other RMX3031 Android 16/17 AOSP ROMs can install cleanly.
- Live audio payload, native adapter, Android helpers, headphone tuning and WebUI remain unchanged from `v0.1.3-preview`.

## v0.1.3-preview — first public preview

- Ported the Oplus Spatializer integration to the inspected RMX3031 Evolution X
  Android 17 audio build while retaining the original v0.6 headphone tuning.
- Added OEM channel initialization and stereo-track metadata compatibility.
- Added native Original / Spatial Audio controls, USB/wired headphone status and
  one-time restoration of the saved selection after boot.
- Added the glow-ring WebUI with xCaptaiN09 credit, channel demo and explicit
  diagnostic export. Demo playback does not automatically create text reports.
- Added guarded installation, file-label checks, upgrade preference retention,
  pinned asset provenance, standalone build tools and source tests.

### Known issues

- The tested YouTube video still lacks its LFE-section rumble during live playback.
  Stats for nerds selected stereo Opus; the separately downloaded E-AC-3 5.1 source
  contains the rumble. Decoder/selection behaviour remains under investigation.
- Surround Sound Test can crackle after short channel clips with Spatial Audio on.
  The continuous WebUI demo did not reproduce the symptom in the maintainer's test.
- Other ROM builds, devices, Bluetooth routes and physical head tracking are not
  validated by this preview.

The public package reorganizes documentation, notices and build files around the
phone-tested preview. Its engine, native adapter, Android helpers, policy payload,
profiles and WebUI match that preview; unresolved bugs are not marked fixed.
