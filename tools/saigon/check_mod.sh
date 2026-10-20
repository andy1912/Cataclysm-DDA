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
# --check-mods never loads tilesets, so check the mod tilesets the way the tiles build will
# (sheet paths relative to the mod root, indices, declaring-sheet geometry).  A broken
# mod tileset aborts every world load in cataclysm-tiles.
if [[ " ${mods[*]} " == *" saigon_2000s "* ]]; then
    if ! python3 tools/saigon/art/validate_tileset.py > "$ud/validate_tileset.txt" 2>&1; then
        echo "FAIL: mod tileset (tools/saigon/art/validate_tileset.py):"
        head -20 "$ud/validate_tileset.txt"
        fail=1
    fi
    # B10: no dda item that reads as American may be reachable from Saigon loot
    # (deliberate exceptions are listed in the script's ALLOWED table)
    if ! python3 tools/saigon/audit_us_content.py > "$ud/audit_us_content.txt" 2>&1; then
        echo "FAIL: American items reachable from Saigon loot (tools/saigon/audit_us_content.py):"
        head -20 "$ud/audit_us_content.txt"
        fail=1
    fi
    # N3: every "item"/"item_group" the mod names must exist in dda or the mod.
    # The engine is silent about a bad id and the loot audit reads it as an item
    # id, so the mistake would otherwise hide until --check-mods.
    if ! python3 tools/saigon/check_refs.py > "$ud/check_refs.txt" 2>&1; then
        echo "FAIL: unresolved item/item_group references (tools/saigon/check_refs.py):"
        grep -v 'all resolve' "$ud/check_refs.txt" | head -20
        fail=1
    fi
    # T1: every translatable string in the mod extracts cleanly (the vi .po path)
    if ! tools/saigon/check_strings.sh > "$ud/check_strings.txt" 2>&1; then
        echo "FAIL: string extraction (tools/saigon/check_strings.sh):"
        head -20 "$ud/check_strings.txt"
        fail=1
    fi
    # S1: the original game's files stay untouched outside the documented engine patches
    if ! tools/saigon/check_separation.sh > "$ud/check_separation.txt" 2>&1; then
        echo "FAIL: fork changes outside the mod (tools/saigon/check_separation.sh):"
        head -20 "$ud/check_separation.txt"
        fail=1
    fi
    # the playtest mod (data/mods/saigon_playtest) replaces the profession whitelist, since the
    # engine keeps only one; its copy must hold every profession the main mod whitelists
    if ! python3 - > "$ud/check_playtest.txt" 2>&1 <<'PY'
import json, sys
def wl(path):
    for o in json.load(open(path)):
        if o.get("type") == "profession_blacklist" and o.get("subtype") == "whitelist":
            return set(o["professions"])
    return set()
main = wl("data/mods/saigon_2000s/settings/whitelists.json")
pt = wl("data/mods/saigon_playtest/profession.json")
missing = sorted(main - pt)
if missing:
    print("missing from the playtest whitelist:", ", ".join(missing))
    sys.exit(1)
PY
    then
        echo "FAIL: playtest whitelist out of date (data/mods/saigon_playtest/profession.json):"
        head -5 "$ud/check_playtest.txt"
        fail=1
    fi
    # CI's "JSON style check" formats every file in data/: the generators write unformatted JSON,
    # so a regenerated file must be run through tools/format/json_formatter.cgi before committing
    jsonbad=""
    jtmp=$(mktemp -d)
    while IFS= read -r f; do
        cp "$f" "$jtmp/x.json"
        tools/format/json_formatter.cgi "$jtmp/x.json" > /dev/null 2>&1
        cmp -s "$f" "$jtmp/x.json" || jsonbad="$jsonbad $f"
    done < <(find data/mods/saigon_2000s data/mods/saigon_playtest -name '*.json')
    rm -rf "$jtmp"
    if [ -n "$jsonbad" ]; then
        echo "FAIL: JSON not formatted (run tools/format/json_formatter.cgi on each):"
        printf '  %s\n' $jsonbad | head -20
        fail=1
    fi
    # the real map must be walkable: straight, ramped bridges and a way into every hẻm network
    if ! python3 tools/saigon/realmap/check_realmap.py > "$ud/check_realmap.txt" 2>&1; then
        echo "FAIL: real map (tools/saigon/realmap/check_realmap.py):"
        head -20 "$ud/check_realmap.txt"
        fail=1
    fi
fi
[ $fail -eq 0 ] && echo "OK: ${mods[*]}"
exit $fail
