#!/usr/bin/env bash
# Validate one or more mods with the curses build's --check-mods.
# Fails if the process exits non-zero, prints "Error loading data", or logs any ERROR
# or WARNING. The exit code alone is not trustworthy: a caught JSON exception skips
# finalize, and the process may then abort (rc 134) or exit with a misleading code.
# On "Error loading data" the run is killed early: the deferred-object teardown that
# follows logs thousands of backtraced errors and can take ~40 minutes.
# Usage: tools/saigon/check_mod.sh [mod_id ...]   (default: saigon_2000s)
set -u
cd "$(dirname "$0")/../.."
mods=("$@")
[ ${#mods[@]} -eq 0 ] && mods=(saigon_2000s)
ud="${SAIGON_USERDIR:-$HOME/code/cdda-saigon-logs/userdir}"
mkdir -p "$ud/config" "$ud/save"
rm -f "$ud/config/debug.log"
out_file="$ud/check_mod_output.txt"
./cataclysm --userdir "$ud/" --check-mods "${mods[@]}" < /dev/null > "$out_file" 2>&1 &
pid=$!
aborted=0
while kill -0 "$pid" 2>/dev/null; do
    if grep -q "Error loading data" "$out_file"; then
        sleep 2
        kill "$pid" 2>/dev/null
        aborted=1
        break
    fi
    sleep 2
done
wait "$pid" 2>/dev/null
rc=$?
out=$(cat "$out_file")
fail=0
if [ $aborted -eq 1 ]; then
    echo "$out" | grep -A20 "Error loading data" | head -30
    echo "FAIL: Error loading data (run killed before teardown)"
    exit 1
fi
echo "$out"
errors=$(grep -E "ERROR|WARNING" "$ud/config/debug.log" 2>/dev/null)
if [ $rc -ne 0 ]; then echo "FAIL: exit code $rc"; fail=1; fi
if [ -n "$errors" ]; then
    echo "FAIL: debug.log has $(echo "$errors" | wc -l | tr -d ' ') ERROR/WARNING lines:"
    echo "$errors" | head -40
    fail=1
fi
[ $fail -eq 0 ] && echo "OK: ${mods[*]}"
exit $fail
