#!/usr/bin/env bash
# QA the real tiles game load path, which --check-mods never exercises (it loads no tilesets).
# Copies a Saigon world that has a saved character into a throwaway user folder, launches
# cataclysm-tiles straight into it, waits until both tilesets are loaded and the character is
# drawn (or an error appears), then closes the game.  The user's own saves are never touched.
# Opens a game window for 1-3 minutes.
# Usage: tools/saigon/qa_game_load.sh ["World Name"]   (default: McCredie Springs)
set -u
cd "$(dirname "$0")/../.."
world="${1:-McCredie Springs}"
qa="${SAIGON_QA_USERDIR:-$HOME/code/cdda-saigon-logs/qa_userdir}"
if [ ! -d "save/$world" ]; then
    echo "FAIL: no world 'save/$world' to copy (need a Saigon world with a saved character)"
    exit 2
fi
rm -rf "$qa" && mkdir -p "$qa/save" && cp -R config "$qa/config" && rm -f "$qa/config/debug.log"
cp -R "save/$world" "$qa/save/"
log="$qa/config/debug.log"
CATA_DISABLE_SPRITE_SHADERS=1 ./cataclysm-tiles --userdir "$qa/" --world "$world" > "$qa/stdout.txt" 2>&1 &
pid=$!
result="TIMEOUT"
for _ in $( seq 1 300 ); do
    sleep 1
    if ! kill -0 "$pid" 2>/dev/null; then result="EXITED"; break; fi
    [ -f "$log" ] || continue
    if grep -qE "Could not load image|Failed to open tile info|terminate called|Segmentation|Error loading data" "$log"; then
        result="ERROR"; break
    fi
    # both tilesets loaded, then the renderer sizes the character sprite: the map is on screen
    if grep -q "Loaded tileset: Larwick Overmap" "$log" && grep -q "tint mask reallocation" "$log"; then
        sleep 5; result="LOADED"; break
    fi
done
kill "$pid" 2>/dev/null
for _ in 1 2 3 4 5; do kill -0 "$pid" 2>/dev/null || break; sleep 1; done
kill -9 "$pid" 2>/dev/null
wait "$pid" 2>/dev/null
# expected noise: mod tilesets are checked against every tileset; the test portrait pack has no 'unknown'
unexpected=$( grep -E "ERROR|WARNING" "$log" 2>/dev/null | grep -vE "not compatible with|no 'unknown' tile|error message will follow|pack load time|opendir \[[^]]*cache\]" )
grep -E "Loaded tileset|atlas upload: tileset=UltimateCataclysm" "$log" | sed -E 's/ renderer=.*atlas_payload_bytes=/ bytes=/; s/ baked=.*//'
if [ "$result" = "LOADED" ] && [ -z "$unexpected" ]; then
    echo "OK: '$world' loads in cataclysm-tiles (tilesets loaded, character drawn)"
    exit 0
fi
echo "FAIL: $result"
[ -n "$unexpected" ] && echo "$unexpected" | grep -v "backtrace" | head -20
exit 1
