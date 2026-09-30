#!/usr/bin/env bash
# Validate one or more mods with the curses build's --check-mods.
# Fails if the process exits non-zero, prints "Error loading data", or logs any ERROR
# or WARNING. The exit code alone is not trustworthy: a caught JSON exception skips
# finalize, and the process may then abort (rc 134) or exit with a misleading code.
# Usage: tools/saigon/check_mod.sh [mod_id ...]   (default: saigon_2000s)
set -u
cd "$(dirname "$0")/../.."
mods=("$@")
[ ${#mods[@]} -eq 0 ] && mods=(saigon_2000s)
ud="${SAIGON_USERDIR:-$HOME/code/cdda-saigon-logs/userdir}"
mkdir -p "$ud/config" "$ud/save"
rm -f "$ud/config/debug.log"
out=$(./cataclysm --userdir "$ud/" --check-mods "${mods[@]}" < /dev/null 2>&1)
rc=$?
echo "$out"
errors=$(grep -E "ERROR|WARNING" "$ud/config/debug.log" 2>/dev/null)
fail=0
if [ $rc -ne 0 ]; then echo "FAIL: exit code $rc"; fail=1; fi
if echo "$out" | grep -q "Error loading data"; then echo "FAIL: Error loading data"; fail=1; fi
if [ -n "$errors" ]; then
    echo "FAIL: debug.log has $(echo "$errors" | wc -l | tr -d ' ') ERROR/WARNING lines:"
    echo "$errors" | head -40
    fail=1
fi
[ $fail -eq 0 ] && echo "OK: ${mods[*]}"
exit $fail
