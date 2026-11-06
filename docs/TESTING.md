# Testing and open investigations

## Current evidence

- The native OEM effect loads, initializes and processes private buffers on the
  test phone after the compatibility adapter's OEM channel-count initialization.
- Spatial playback, headphone enumeration, native controls and the WebUI are
  reported working on the inspected RMX3031 setup.
- Private generated-tone tests completed 45 cases without callback errors,
  guard errors, invalid samples or clipping. Ten translated stereo outputs were
  byte-identical to the engine's native stereo reference.
- Source/ZIP/manifest checks and host fixtures exercise the guarded installer,
  previous-payload acceptance, preference retention, missing mounts, MMRS staging
  and demo cleanup. Host tests do not substitute for a phone playback test.

Raw phone dumps, private report archives, screenshots, downloaded videos and
third-party app APKs are deliberately not part of this repository.

## Open: YouTube LFE section

Test video: [Dolby Atmos 5.1 channel surround test](https://www.youtube.com/watch?v=s4tm8Ly3coI),
approximately **00:46-00:54**.

The downloaded E-AC-3 file is six-channel 5.1(side), 48 kHz. Its LFE channel has
strong energy near 60 Hz in this section. A default FFmpeg stereo downmix drops
that LFE contribution, and an earlier converted stereo MP3 was silent there.
Phone Stats for nerds selected **itag 251 Opus**, the stereo format listed for this
video; an earlier AudioFlinger capture also showed a stereo YouTube track.

This supports investigating source selection and decoder/downmix behaviour before
the Spatializer. It does not prove which stream ColorOS previously used, why the
ROMs differ, or that every delivered stereo rendition has the same waveform.
Decoder capability checks remain an investigation, not an implemented fix.

## Open: short-clip crackle

The maintainer reports crackle after some rear-left/rear-right clips in
`com.mdev.surroundsoundtest` with Spatial Audio enabled; Original mode is clean.
The continuous WebUI channel demo was reported clean. Private tail tests did not
establish a causal defect. Start/stop behaviour is a hypothesis to test, not a
confirmed cause and not a fix included in this release.

## Useful phone checks

Keep the same headphones, low media volume and player for comparisons. Check:

1. Original playback before enabling Spatial Audio.
2. Spatial playback with known multichannel content.
3. Short clips, pauses, seeks and track changes.
4. Headphone unplug/replug, saved mode after reboot and module removal.
5. The explicit diagnostic export while reproducing a failure.

Record app/version, source codec/channel layout and whether the source is local
or streamed. A visual surround label or an enabled toggle alone does not establish
multichannel input, processing correctness or accurate localization.
