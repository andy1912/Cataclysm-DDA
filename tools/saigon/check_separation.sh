#!/usr/bin/env bash
# Check that the fork keeps to its own places (unit S1, doc/saigon/ENGINE_PATCHES.md).
# Lists every path that differs from the last upstream intake point
# (git merge-base HEAD upstream/master), counting committed changes, uncommitted
# changes and untracked files that are not ignored. Fails if any of them is outside
# the fork-owned places and not one of the documented engine files.
#   Fork-owned: data/mods/saigon_2000s/ data/mods/saigon_playtest/ .github/workflows/saigon-* tools/saigon/ art/saigon/ doc/saigon/ tests/saigon_*
#   Engine:     the "allowed-engine-files" block in doc/saigon/ENGINE_PATCHES.md
# Usage: tools/saigon/check_separation.sh [--committed]
#   --committed  check HEAD only (ignore the working tree), e.g. in CI.
# Exit: 0 clean, 1 offenders listed, 2 cannot check (no upstream/master, no allowed list).
set -u
cd "$(dirname "$0")/../.."

mode=tree
[ "${1:-}" = "--committed" ] && mode=committed

if ! git rev-parse --verify --quiet upstream/master > /dev/null; then
    echo "check_separation: upstream/master is missing." >&2
    echo "  Add and fetch the upstream remote first:" >&2
    echo "  git remote add upstream https://github.com/CleverRaven/Cataclysm-DDA.git && git fetch upstream" >&2
    exit 2
fi
base=$(git merge-base HEAD upstream/master) || {
    echo "check_separation: no merge-base between HEAD and upstream/master." >&2
    exit 2
}

doc=doc/saigon/ENGINE_PATCHES.md
if [ ! -f "$doc" ]; then
    echo "check_separation: $doc is missing; it holds the allowed engine file list." >&2
    exit 2
fi
allowed=$(awk '/^```allowed-engine-files/{f=1; next} /^```/{f=0} f && NF {print $1}' "$doc")
if [ -z "$allowed" ]; then
    echo "check_separation: no allowed-engine-files block found in $doc." >&2
    exit 2
fi

if [ "$mode" = committed ]; then
    changed=$(git -c core.quotepath=off diff --name-only --no-renames "$base" HEAD)
else
    # Working tree vs the base covers committed and uncommitted edits to tracked files;
    # untracked files are new paths too.
    changed=$( {
        git -c core.quotepath=off diff --name-only --no-renames "$base"
        git -c core.quotepath=off ls-files --others --exclude-standard
    } | sort -u)
fi

offenders=()
n_fork=0
n_engine=0
while IFS= read -r p; do
    [ -z "$p" ] && continue
    case "$p" in
        data/mods/saigon_2000s/*|data/mods/saigon_playtest/*|.github/workflows/saigon-*|tools/saigon/*|art/saigon/*|doc/saigon/*|tests/saigon_*)
            n_fork=$((n_fork + 1)); continue ;;
    esac
    if printf '%s\n' "$allowed" | grep -qxF -- "$p"; then
        n_engine=$((n_engine + 1))
        continue
    fi
    offenders+=("$p")
done <<< "$changed"

echo "check_separation: base $(git rev-parse --short "$base") ($mode): $n_fork fork-owned, $n_engine documented engine file(s) changed."
if [ ${#offenders[@]} -gt 0 ]; then
    echo "FAIL: ${#offenders[@]} changed path(s) outside the fork-owned places and not in $doc:"
    printf '  %s\n' "${offenders[@]}"
    echo "Move fork files into data/mods/saigon_2000s/, tools/saigon/, art/saigon/, doc/saigon/ or"
    echo "tests/saigon_*, or document an engine change in $doc and add it to its allowed list."
    exit 1
fi
echo "OK: the original game's files are untouched outside the documented engine patches."
exit 0
