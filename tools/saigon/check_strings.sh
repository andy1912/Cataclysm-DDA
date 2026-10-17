#!/usr/bin/env bash
# Gate: every translatable string in the Saigon mod must be extractable by the repo's
# JSON string extractor (lang/extract_json_strings.py), the one lang/update_pot.sh runs.
# Pass 1 extracts only data/mods/saigon_2000s into a temp .pot and reports the count.
# Pass 2 extracts data/json + the mod together, so a plural form that conflicts with a
# dda string (which would abort lang/update_pot.sh) is caught too.
# Fails if the extractor exits non-zero or prints anything: it is silent on success, and
# everything it prints (unknown type, missing field, plural conflict) is an error.
# If python3 lacks polib (used only to rewrite the reference .pot header), the extractor
# is run through a shim that stubs polib and skips that header step; extraction is identical.
# Usage: tools/saigon/check_strings.sh [-k]   (-k keeps the temp dir and prints its path)
set -u
cd "$(dirname "$0")/../.."
keep=0
[ "${1:-}" = "-k" ] && keep=1
mod=data/mods/saigon_2000s
tmp=$(mktemp -d "${TMPDIR:-/tmp}/saigon_strings.XXXXXX")
[ $keep -eq 0 ] && trap 'rm -rf "$tmp"' EXIT

extract() {  # extract <pot> <log> <include_dir>...
    local pot=$1 log=$2
    shift 2
    local args=()
    for d in "$@"; do args+=(-i "$d"); done
    printf 'msgid ""\nmsgstr ""\n"Content-Type: text/plain; charset=UTF-8\\n"\n' > "$pot"
    if python3 -c 'import polib' 2>/dev/null; then
        python3 lang/extract_json_strings.py "${args[@]}" -n saigon_2000s -r "$pot" > "$log" 2>&1
    else
        mkdir -p "$tmp/shim"
        echo '# stub: polib is only needed by sanitize(), which this gate skips' > "$tmp/shim/polib.py"
        PYTHONPATH="$tmp/shim:lang" python3 -c '
import runpy, sys
import string_extractor.pot_export as pe
pe.sanitize = lambda reference, pkg_name=None: None
sys.argv = ["lang/extract_json_strings.py"] + sys.argv[1:]
runpy.run_path("lang/extract_json_strings.py", run_name="__main__")
' "${args[@]}" -n saigon_2000s -r "$pot" > "$log" 2>&1
    fi
}

fail=0
extract "$tmp/saigon.pot" "$tmp/saigon.log" "$mod"
rc=$?
if [ $rc -ne 0 ] || [ -s "$tmp/saigon.log" ]; then
    echo "FAIL: extractor on $mod (exit $rc):"
    tail -40 "$tmp/saigon.log"
    fail=1
fi
extract "$tmp/combined.pot" "$tmp/combined.log" data/json "$mod"
rc=$?
if [ $rc -ne 0 ] || [ -s "$tmp/combined.log" ]; then
    echo "FAIL: extractor on data/json + $mod (exit $rc):"
    tail -40 "$tmp/combined.log"
    fail=1
fi
# entries = msgid lines minus the header's empty msgid
count=$(grep -c '^msgid ' "$tmp/saigon.pot")
count=$((count - 1))
[ $keep -eq 1 ] && echo "kept: $tmp"
if [ $fail -eq 0 ]; then
    echo "OK: $count strings extracted from $mod"
else
    echo "FAIL: string extraction ($count strings extracted from $mod)"
fi
exit $fail
