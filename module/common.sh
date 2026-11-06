#!/system/bin/sh
file_sha() { sha256sum "$1" 2>/dev/null | awk '{print $1}'; }
file_context() {
    context_line=$(ls -Zd "$1" 2>/dev/null) || return 1
    for field in $context_line; do
        case "$field" in u:object_r:*:s0|u:object_r:*:s0:*) echo "$field"; return 0;; esac
    done
    return 1
}
staged() {
    case "$1" in
        /vendor|/vendor/*)
            if [ -d "$MODDIR/system/vendor" ] && [ ! -L "$MODDIR/system/vendor" ]; then
                echo "$MODDIR/system$1"
            elif [ -d "$MODDIR/vendor" ] && [ ! -L "$MODDIR/vendor" ]; then
                echo "$MODDIR$1"
            else return 1; fi ;;
        *) return 1;;
    esac
}
check_mounts() {
    mount_root=$1
    mount_bad=0
    while read -r expected target; do
        [ "$(file_sha "$mount_root$target")" = "$expected" ] || mount_bad=$((mount_bad+1))
    done < "$MODDIR/LIVE-SHA256SUMS"
    [ "$mount_bad" = 0 ]
}
