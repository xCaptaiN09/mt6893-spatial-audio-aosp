#!/system/bin/sh
set -u
umask 077
MODDIR=${0%/*}
. "$MODDIR/common.sh"
[ "$(id -u)" = 0 ] || { echo '{"error":"Root access is required"}'; exit 1; }
command=${1:-status}
helper() {
    [ "$(file_sha "$MODDIR/control.jar")" = "$(cat "$MODDIR/CONTROL-JAR-SHA256")" ] || {
        echo '{"error":"Control helper checksum failed"}'; return 1;
    }
    CLASSPATH="$MODDIR/control.jar" timeout -k 2 12 app_process /system/bin SpatialControl "$1"
}
require_mounts() {
    check_mounts /proc/1/root || {
        echo '{"error":"Audio payload is not mounted as expected. Reboot and check your module mounting setup."}'
        return 1
    }
}
case "$command" in
    status)
        # Headphone enumeration remains useful even when the payload is absent.
        state=$(helper status) || { echo "$state"; exit 1; }
        case "$state" in
            '{'*) ;;
            *) echo '{"error":"Android did not return a valid status"}'; exit 1;;
        esac
        mounted=false
        check_mounts /proc/1/root && mounted=true
        echo "${state%\}},\"mounted\":$mounted}"
        ;;
    on|off)
        require_mounts || exit 1
        mkdir "$MODDIR/.control-lock" 2>/dev/null || { echo '{"error":"Another operation is running"}'; exit 1; }
        trap 'rmdir "$MODDIR/.control-lock" 2>/dev/null' EXIT
        state=$(helper "$command") || { echo "$state"; exit 1; }
        echo "$command" > "$MODDIR/choice.conf.tmp.$$" &&
            mv "$MODDIR/choice.conf.tmp.$$" "$MODDIR/choice.conf" || exit 1
        echo "${state%\}},\"mounted\":true}"
        ;;
    settings) am start -a android.settings.SOUND_SETTINGS >/dev/null ;;
    report)
        report="/sdcard/Download/mt6893-spatial-aosp-$(date +%Y%m%d-%H%M%S)-$$.txt"
        {
            echo "MT6893 Spatial Audio AOSP $(sed -n 's/^version=//p' "$MODDIR/module.prop")"
            date; getenforce
            echo "Saved preference: $(cat "$MODDIR/choice.conf" 2>/dev/null)"
            echo "Framework properties: $(getprop ro.audio.spatializer_enabled), stereo $(getprop ro.audio.stereo_spatialization_enabled)"
            echo "=== Module and provider layout ==="
            ls -ldZ "$MODDIR/system" "$MODDIR/system/vendor" "$MODDIR/vendor" /system/vendor /vendor /data/adb/metamodule 2>&1
            echo "Self mount namespace: $(readlink /proc/self/ns/mnt); init: $(readlink /proc/1/ns/mnt)"
            if [ -f /data/adb/metamodule/module.prop ]; then
                sed -n '/^id=/p;/^name=/p;/^version=/p;/^metamodule=/p' /data/adb/metamodule/module.prop
            fi
            for flag in disable remove update skip_mount; do
                [ ! -e "$MODDIR/$flag" ] || echo "Spatial module flag: $flag"
            done
            echo "=== Mount provider log (if present) ==="
            for provider_log in /data/adb/magic_mount/log.txt /data/adb/magic_mount/magic_mount.log /data/adb/magic_mount/log; do
                [ ! -f "$provider_log" ] || tail -n 100 "$provider_log"
            done
            echo "=== Mount verification (init namespace) ==="
            while read -r expected target; do
                actual=$(file_sha "/proc/1/root$target")
                [ "$actual" != "$expected" ] && verdict=MISMATCH || verdict=MATCH
                echo "$verdict $actual $target"
            done < "$MODDIR/LIVE-SHA256SUMS"
            echo "=== Boot result ==="; cat "$MODDIR/boot-status.txt" 2>/dev/null
            echo "=== Framework control ==="; helper status
            echo "=== Audio HAL library mappings ==="
            for p in $(pidof android.hardware.audio.service); do
                echo "PID $p namespace: $(readlink "/proc/$p/ns/mnt")"
                grep -E 'libmt6893spatial|liboplus_spat|libspcxxrt|libspstdc|libc[+][+]|libutils' "/proc/$p/maps"
            done
            echo "=== Audio policy ==="; timeout 12 dumpsys -t 10 media.audio_policy
            echo "=== AudioFlinger ==="; timeout 12 dumpsys -t 10 media.audio_flinger
            echo "=== AudioService ==="; timeout 12 dumpsys -t 10 audio
            echo "=== Recent audio integration messages (may include earlier attempts) ==="
            timeout 8 logcat -b main -b system -d -t 4000 -v threadtime 2>&1 |
                grep -iE 'spatial|OplusEffect|EffectsFactory|audio_effects|avc:.*(audio|vendor_configs_file)'
            echo "Enablement/registration alone does not prove active processing."
        } > "$report" 2>&1
        [ -s "$report" ] || exit 1
        chmod 0644 "$report"
        echo "Report saved: $report"
        ;;
    demo)
        require_mounts || exit 1
        mkdir "$MODDIR/.control-lock" 2>/dev/null || { echo 'Another operation is running'; exit 1; }
        trap 'rmdir "$MODDIR/.control-lock" 2>/dev/null' EXIT
        work=$(mktemp -d /data/local/tmp/aosp-spatial-demo.XXXXXX) || exit 1
        player=
        finish_demo() {
            if [ -n "$player" ]; then kill -TERM "$player" 2>/dev/null || true; wait "$player" 2>/dev/null || true; fi
            rm -rf -- "$work"
            rmdir "$MODDIR/.control-lock" 2>/dev/null
        }
        trap finish_demo EXIT
        trap 'exit 130' INT
        trap 'exit 143' TERM
        state=$(helper status) || exit 1
        echo "$state" | grep -q '"enabled":true' || { echo 'Select Spatial Audio first.'; exit 1; }
        echo "$state" | grep -q '"available":true' || { echo 'Connect supported headphones first.'; exit 1; }
        [ "$(file_sha "$MODDIR/demo.jar")" = "$(cat "$MODDIR/DEMO-JAR-SHA256")" ] || { echo 'Demo checksum failed'; exit 1; }
        log="$work/player.log"
        echo 'Use a low media volume. Playing 24 seconds of 7.1.4 channel noise.'
        CLASSPATH="$MODDIR/demo.jar" timeout -k 2 36 app_process /system/bin SpatialPlaybackProbe "$work" > "$log" 2>&1 &
        player=$!
        wait "$player"; result=$?; player=
        if [ "$result" != 0 ]; then
            echo 'Channel demo could not complete. Use Save diagnostic report for details.'
            tail -n 12 "$log"
        else
            echo 'Channel demo finished.'
        fi
        exit "$result"
        ;;
    *) echo '{"error":"Unknown operation"}'; exit 1 ;;
esac
