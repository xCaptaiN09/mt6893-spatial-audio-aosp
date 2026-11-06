#!/system/bin/sh
MODDIR=${0%/*}
. "$MODDIR/common.sh"
umask 077
for attempt in $(seq 1 60); do
    [ "$(getprop sys.boot_completed)" = 1 ] && break
    sleep 2
done
[ "$(getprop sys.boot_completed)" = 1 ] || exit 1
{
    date
    if ! check_mounts /proc/1/root; then
        echo "MOUNT CHECK FAILED. No controller operation was attempted."
        echo "Check KernelSU's module mounting support and reboot."
        exit 1
    fi
    choice=$(cat "$MODDIR/choice.conf" 2>/dev/null)
    case "$choice" in on|off) ;; *) choice=on;; esac
    echo "Applying saved preference once: $choice"
    sh "$MODDIR/control.sh" "$choice"
} > "$MODDIR/boot-status.txt" 2>&1
