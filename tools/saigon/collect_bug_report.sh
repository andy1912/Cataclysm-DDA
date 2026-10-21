#!/usr/bin/env bash
# Collect what a Saigon 2000s playtest bug report needs into one dated folder and zip
# under ~/code/cdda-saigon-logs/bug_reports/, and print the path (doc/saigon/BUG_REPORT.md).
# Nothing is uploaded or sent anywhere: the files stay on this Mac until you attach them.
#
# Collected:
#   build.txt         git HEAD (short and full), branch, git status --short, binaries present
#   system.txt        sw_vers, uname -a, CPU and memory
#   debug.log         the game's whole config/debug.log (and debug.log.prev, the run before);
#                     debug_tail.txt is its last N lines, debug_errors.txt its ERROR/WARNING lines
#   options.json      config/options.json (game options; no personal data)
#   world/            with -w: the world's mods.json (the mod list), worldoptions.json,
#                     world_timestamp.json, master.gsav and the newest character *.sav,
#                     plus save/<world>-trimmed.tar.gz when the in-game
#                     "Export save archive for github bug report" made one
#   world_full.tar.gz with -f: the whole world folder (can be large)
#   screenshots/      with -w: the world's screenshots folder, if any
#
# The game folder ("userdir") is the repo root, because tools/saigon/play_saigon.sh runs
# the game there without --userdir: config/ and save/ next to this repo's data/.
#
# Usage: tools/saigon/collect_bug_report.sh [-w "World name"] [-t PT-xx] [-n lines] [-u userdir] [-f]
#   -w  world to take the save from (a folder name under save/; omit to skip the save)
#   -t  playtest id or short label for the folder name, e.g. PT-21
#   -n  how many lines of debug.log go into debug_tail.txt (default 300)
#   -u  game userdir (default: the repo root)
#   -f  also pack the whole world folder
set -u
cd "$(dirname "$0")/../.."
repo=$(pwd)

world=""
tag=""
lines=300
userdir="$repo"
full=0
while getopts "w:t:n:u:fh" opt; do
    case "$opt" in
        w) world="$OPTARG" ;;
        t) tag="$OPTARG" ;;
        n) lines="$OPTARG" ;;
        u) userdir="$OPTARG" ;;
        f) full=1 ;;
        h) sed -n '2,27p' "$0"; exit 0 ;;
        *) echo "Usage: $0 [-w \"World name\"] [-t PT-xx] [-n lines] [-u userdir] [-f]" >&2; exit 2 ;;
    esac
done
case "$lines" in
    ''|*[!0-9]*) echo "collect_bug_report: -n needs a number of lines, got '$lines'" >&2; exit 2 ;;
esac
userdir="${userdir%/}"

stamp=$(date +%Y-%m-%d_%H%M%S)
name="$stamp"
if [ -n "$tag" ]; then
    # keep the folder name to letters, digits, dot, dash and underscore
    name="${stamp}_$(printf '%s' "$tag" | tr -c 'A-Za-z0-9._-' '_')"
fi
base="$HOME/code/cdda-saigon-logs/bug_reports"
out="$base/$name"
mkdir -p "$out"

missing=()

# build: which code the bug was seen on
{
    echo "collected: $(date '+%Y-%m-%d %H:%M:%S %z')"
    echo "repo:      $repo"
    echo "userdir:   $userdir"
    echo "commit:    $(git rev-parse --short HEAD 2>/dev/null || echo unknown)"
    echo "full:      $(git rev-parse HEAD 2>/dev/null || echo unknown)"
    echo "branch:    $(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"
    echo "last:      $(git log -1 --format='%h %ad %s' --date=short 2>/dev/null || echo unknown)"
    echo
    echo "binaries:"
    for b in cataclysm-tiles cataclysm; do
        if [ -x "$repo/$b" ]; then
            echo "  $b  $(stat -f '%Sm' -t '%Y-%m-%d %H:%M' "$repo/$b" 2>/dev/null || stat -c '%y' "$repo/$b" 2>/dev/null)"
        else
            echo "  $b  (not built)"
        fi
    done
    echo
    echo "git status --short:"
    git -c core.quotepath=off status --short 2>/dev/null || echo "  (git status failed)"
} > "$out/build.txt"

# system
{
    if command -v sw_vers > /dev/null 2>&1; then
        sw_vers
        echo
    fi
    uname -a
    if command -v sysctl > /dev/null 2>&1; then
        echo "cpu:    $(sysctl -n machdep.cpu.brand_string 2>/dev/null || echo unknown)"
        mem=$(sysctl -n hw.memsize 2>/dev/null || echo 0)
        echo "memory: $((mem / 1073741824)) GB"
    fi
} > "$out/system.txt" 2>&1

# the game's log and options
log="$userdir/config/debug.log"
if [ -f "$log" ]; then
    cp "$log" "$out/debug.log"
    tail -n "$lines" "$log" > "$out/debug_tail.txt"
    grep -nE "ERROR|WARNING" "$log" | grep -v backtrace > "$out/debug_errors.txt" || true
else
    missing+=("config/debug.log (no game has been run in $userdir?)")
fi
# the game moves the previous run's log here at launch: the crash log after one relaunch
if [ -f "$log.prev" ]; then
    cp "$log.prev" "$out/debug.log.prev"
fi
if [ -f "$userdir/config/options.json" ]; then
    cp "$userdir/config/options.json" "$out/options.json"
fi

# the world: mod list, options, newest character save, trimmed archive
if [ -n "$world" ]; then
    wdir="$userdir/save/$world"
    if [ -d "$wdir" ]; then
        mkdir -p "$out/world"
        for f in mods.json worldoptions.json world_timestamp.json master.gsav; do
            [ -f "$wdir/$f" ] && cp "$wdir/$f" "$out/world/"
        done
        # newest character save (one *.sav per character)
        newest=""
        for f in "$wdir"/*.sav; do
            [ -f "$f" ] || continue
            if [ -z "$newest" ] || [ "$f" -nt "$newest" ]; then
                newest="$f"
            fi
        done
        if [ -n "$newest" ]; then
            cp "$newest" "$out/world/"
        else
            missing+=("a character save in save/$world (the world has no saved character yet)")
        fi
        trimmed="$userdir/save/${world}-trimmed.tar.gz"
        if [ -f "$trimmed" ]; then
            cp "$trimmed" "$out/world/"
        else
            missing+=("save/${world}-trimmed.tar.gz (optional: in game, Esc > 'Export save archive for github bug report')")
        fi
        if [ -d "$wdir/screenshots" ]; then
            cp -R "$wdir/screenshots" "$out/screenshots"
        fi
        if [ $full -eq 1 ]; then
            tar -czf "$out/world_full.tar.gz" -C "$userdir/save" "$world"
        fi
        {
            echo "world: $world"
            echo "mods:"
            if [ -f "$wdir/mods.json" ]; then
                tr -d '[]",' < "$wdir/mods.json" | sed '/^[[:space:]]*$/d; s/^[[:space:]]*/  /'
            fi
        } > "$out/world/README.txt"
    else
        worlds=""
        for d in "$userdir"/save/*/; do
            [ -d "$d" ] || continue
            d="${d%/}"
            worlds="${worlds:+$worlds, }${d##*/}"
        done
        missing+=("world 'save/$world' (worlds here: ${worlds:-none})")
    fi
fi

{
    echo "Saigon 2000s bug report material, collected $(date '+%Y-%m-%d %H:%M')."
    echo "Attach this zip (or the files) to doc/saigon/playtest/${tag:-PT-xx}_<short>.md; see doc/saigon/BUG_REPORT.md."
    echo
    if [ ${#missing[@]} -gt 0 ]; then
        echo "Not collected:"
        printf '  - %s\n' "${missing[@]}"
    else
        echo "Everything requested was collected."
    fi
} > "$out/README.txt"

zip_path="$out.zip"
if command -v ditto > /dev/null 2>&1; then
    ditto -c -k --keepParent "$out" "$zip_path"
elif command -v zip > /dev/null 2>&1; then
    (cd "$base" && zip -qr "$name.zip" "$name")
else
    zip_path="$out.tar.gz"
    tar -czf "$zip_path" -C "$base" "$name"
fi

if [ ${#missing[@]} -gt 0 ]; then
    echo "Not collected:"
    printf '  - %s\n' "${missing[@]}"
fi
echo "Folder: $out"
echo "Zip:    $zip_path"
