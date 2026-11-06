#!/system/bin/sh
ui_print " "
package_version=$(sed -n 's/^version=//p' "$MODPATH/module.prop")
ui_print "MT6893 Spatial Audio AOSP | $package_version"
ui_print "Evolution X Android 17 — inspected RMX3031 build"
ui_print " "
MODDIR=$MODPATH
. "$MODDIR/common.sh"
[ "$(getprop ro.build.version.sdk)" = 37 ] || abort "Expected Android SDK 37."
[ "$(getprop ro.board.platform)" = mt6893 ] || abort "Expected MT6893."
for legacy in mt6893-spatial-audio mt6893-spatializer-test; do
    [ ! -f "/data/adb/modules/$legacy/module.prop" ] || abort "Remove the ColorOS Spatial Audio module and reboot first."
done
ui_print "[1/3] Checking the inspected audio build"
while read -r expected target; do
    actual=$(file_sha "/proc/1/root$target")
    modified=$(awk -v p="$target" '$2==p {print $1;exit}' "$MODDIR/LIVE-SHA256SUMS")
    previous=$(awk -v p="$target" -v h="$actual" '$2==p && $1==h {print $1;exit}' "$MODDIR/PREVIOUS-LIVE-SHA256SUMS")
    if [ "$actual" != "$expected" ] &&
       { [ -z "$modified" ] || [ "$actual" != "$modified" ]; } &&
       { [ -z "$previous" ] || [ "$actual" != "$previous" ]; }; then
        abort "Audio file differs from the reviewed build: $target"
    fi
done < "$MODDIR/BASE-SHA256SUMS"
active_policy=$(timeout 10 dumpsys media.audio_policy 2>/dev/null | sed -n 's/^[[:space:]]*Config source: //p')
case "$active_policy" in
    /vendor/etc/audio_policy_configuration.xml|/vendor/etc/audio_policy_configuration_a2dp_offload_disabled.xml) ;;
    *) abort "The active audio policy is not covered by this preview: $active_policy";;
esac
ui_print "Active policy: $active_policy"
ui_print "[2/3] Verifying the package and conflicts"
(cd "$MODDIR" && sha256sum -c INSTALL-SHA256SUMS >/dev/null) || abort "Package checksum verification failed."
while read -r expected target; do
    case "$target" in */audio_effects.xml|*/audio_policy_configuration*.xml) continue;; esac
    for prefix in /proc/1/root/vendor /proc/1/root/odm; do
        counterpart="$prefix${target#/vendor}"
        if [ -e "$counterpart" ] || [ -L "$counterpart" ]; then
            actual=$(file_sha "$counterpart")
            previous=$(awk -v p="$target" -v h="$actual" '$2==p && $1==h {print $1;exit}' "$MODDIR/PREVIOUS-LIVE-SHA256SUMS")
            [ "$actual" = "$expected" ] || [ -n "$previous" ] || abort "An existing file conflicts: $counterpart"
        fi
    done
done < "$MODDIR/LIVE-SHA256SUMS"
ui_print "[3/3] Preparing labels and controls"
# MMRS scans the physical system/vendor tree. Its installation hook may have
# moved the first extraction to vendor/ before the standard second extraction.
# Remove that redundant copy only after checking every file against the manifest.
if [ "${KSU_METAMODULE:-}" = mmrs ]; then
    [ -d "$MODDIR/system/vendor" ] && [ ! -L "$MODDIR/system/vendor" ] ||
        abort "MMRS requires a physical system/vendor folder. Reinstall with Magic Mount active."
    if [ -d "$MODDIR/vendor" ] && [ ! -L "$MODDIR/vendor" ]; then
        [ -z "$(find "$MODDIR/vendor" -mindepth 1 ! -type d ! -type f -print)" ] ||
            abort "Unexpected special entry in duplicate vendor staging."
        expected_count=$(wc -l < "$MODDIR/LIVE-SHA256SUMS" | tr -d '[:space:]')
        duplicate_count=$(find "$MODDIR/vendor" -type f | wc -l | tr -d '[:space:]')
        [ "$duplicate_count" = "$expected_count" ] || abort "Unexpected duplicate vendor contents."
        while read -r expected target; do
            [ "$(file_sha "$MODDIR$target")" = "$expected" ] || abort "Duplicate vendor payload differs: $target"
        done < "$MODDIR/LIVE-SHA256SUMS"
        rm -rf -- "$MODDIR/vendor" || abort "Cannot remove the verified duplicate staging copy."
    fi
    ui_print "Magic Mount layout: physical system/vendor, with provider-managed vendor link."
fi
vendor_stage=$(staged /vendor) || abort "Vendor staging directory missing."
set_perm_recursive "$vendor_stage" 0 0 0755 0644 u:object_r:vendor_file:s0
set_perm_recursive "$vendor_stage/etc" 0 0 0755 0644 u:object_r:vendor_configs_file:s0
while read -r expected target; do
    path=$(staged "$target") || abort "Unsupported staged path: $target"
    [ "$(file_context "$path")" = "$expected" ] || abort "Staged file or directory label is wrong: $target"
done < "$MODDIR/FILE-CONTEXTS"
for script in common.sh control.sh service.sh action.sh; do
    set_perm "$MODDIR/$script" 0 0 0755
done
set_perm "$MODDIR/control.jar" 0 0 0644
set_perm "$MODDIR/demo.jar" 0 0 0644
choice=on
old_choice=/data/adb/modules/mt6893-spatial-aosp/choice.conf
if [ -f "$old_choice" ]; then
    case "$(cat "$old_choice")" in off) choice=off;; on) choice=on;; esac
fi
echo "$choice" > "$MODDIR/choice.conf"
set_perm "$MODDIR/choice.conf" 0 0 0600
ui_print " "
ui_print "Preview staged. Reboot, connect headphones and open WebUI."
ui_print "Known playback issues remain; read the prerelease notes."
ui_print "Original / Spatial Audio uses Android's enabled state."
ui_print "No USB fix, ColorOS app or framework patch is installed."
ui_print "A working module-mounting mechanism is required."
ui_print "Play media, then use Action to save the integration report."
ui_print "If audio routing fails, disable this module and reboot."
