#!/usr/bin/env bash
# Build "Cataclysm Saigon" for macOS on this Mac and package it as a dmg.
#
#   tools/saigon/package_macos.sh [version]          e.g. tools/saigon/package_macos.sh 0.1.0
#
# The package is for this Mac's architecture (Intel builds an x86_64 app, Apple Silicon an arm64
# one); the universal app comes from .github/workflows/saigon-release.yml.  Output goes to
# ~/code/cdda-saigon-logs/release/, outside the repo.
#
# Needs, as set up in doc/saigon/BUILD_PACKAGES.md: the SDL3, SDL3_image, SDL3_ttf and
# SDL3_mixer frameworks in ~/Library/Frameworks, the pkg-config shim for SDL3_mixer, glslang,
# Homebrew freetype and dylibbundler.  The CC-Sounds soundpack is taken from ./sound/CC-Sounds
# when present.
#
# What differs from the repo, inside the package only: dda + saigon_2000s are the default mods,
# the saigon_playtest cheat mod is left out, README.md is the player readme, saves go to
# ~/Library/Application Support/Cataclysm (USE_HOME_DIR=1).
set -euo pipefail
cd "$(dirname "$0")/../.."

VERSION="${1:-0.1.0}"
ARCH="$(uname -m)"
case "$ARCH" in
    x86_64) LABEL=macos-intel ;;
    arm64) LABEL=macos-apple-silicon ;;
    *) LABEL="macos-$ARCH" ;;
esac
LOGS="$HOME/code/cdda-saigon-logs"
OUT="$LOGS/release"
NAME="CataclysmSaigon-$VERSION-$LABEL"
FW="$HOME/Library/Frameworks"

for f in SDL3 SDL3_image SDL3_ttf SDL3_mixer; do
    if [ ! -d "$FW/$f.framework" ]; then
        echo "missing $FW/$f.framework (see doc/saigon/BUILD_PACKAGES.md)" >&2
        exit 1
    fi
done
command -v dylibbundler > /dev/null || { echo "missing dylibbundler: brew install dylibbundler" >&2; exit 1; }

export GLSLANG="${GLSLANG:-$LOGS/tools/glslang/bin/glslang}"
export PKG_CONFIG_PATH="$LOGS/tools/pkgconfig${PKG_CONFIG_PATH:+:$PKG_CONFIG_PATH}"
FLAGS=( TILES=1 FRAMEWORK=1 RELEASE=1 LOCALIZE=0 SOUND=1 USE_HOME_DIR=1 BUILD_SHADER_FORMATS=spv )

# main.cpp is the only file that reads USE_HOME_DIR; make does not notice a changed define
rm -f obj/tiles/main.o
echo "== building ($ARCH)"
nice make -j2 "${FLAGS[@]}" app > "$LOGS/package_macos_build.txt" 2>&1 || {
    grep -E 'error|Error' "$LOGS/package_macos_build.txt" | head -20
    exit 1
}
# (count, not grep -q: with pipefail an early grep exit makes nm's broken pipe fail the test)
if [ "$( nm -u Cataclysm.app/Contents/Resources/cataclysm-tiles | grep -c MIX_ )" -eq 0 ]; then
    echo "the binary has no sound (stale objects from a SOUND=0 build?): see BUILD_PACKAGES.md" >&2
    exit 1
fi

APP="$OUT/$NAME/Cataclysm Saigon.app"
rm -rf "$OUT/$NAME" "$OUT/$NAME.dmg"
mkdir -p "$OUT/$NAME"
mv Cataclysm.app "$APP"
R="$APP/Contents/Resources"

echo "== Saigon contents"
cp -R "$FW/SDL3_mixer.framework" "$R/"
rm -rf "$R/data/mods/saigon_playtest"
sed -i '' 's/"dependencies": \[.*\]/"dependencies": [ "dda", "saigon_2000s" ]/' "$R/data/mods/default.json"
grep -q '"saigon_2000s"' "$R/data/mods/default.json"
if [ -d sound/CC-Sounds ]; then
    cp -R sound/CC-Sounds "$R/data/sound/"
else
    echo "note: sound/CC-Sounds not found, packaging without a soundpack"
fi
cp doc/saigon/RELEASE_README.md "$OUT/$NAME/README.md"
cp LICENSE.txt LICENSE-OFL-Terminus-Font.txt "$OUT/$NAME/"
cat > "$R/VERSION.txt" << EOF
Cataclysm Saigon $VERSION ($LABEL)
commit sha: $(git rev-parse HEAD)
EOF
# the frameworks sit next to the binary; the launcher also sets DYLD_FRAMEWORK_PATH
install_name_tool -add_rpath "@executable_path/" "$R/cataclysm-tiles" 2> /dev/null || true

echo "== checking the package"
# 1. the game starts on the bundled libraries alone (~/Library/Frameworks hidden)
(
    cd "$R"
    DYLD_FRAMEWORK_PATH=. DYLD_LIBRARY_PATH=. DYLD_FALLBACK_FRAMEWORK_PATH=/nonexistent \
        DYLD_FALLBACK_LIBRARY_PATH=/nonexistent ./cataclysm-tiles --version
) | grep -q '+tiles, +sound' || { echo "the packaged binary does not start on its own libraries" >&2; exit 1; }
# 2. nothing links outside the app or the system
outside="$( otool -L "$R/cataclysm-tiles" "$R"/*.dylib | grep -E '^\s+/(usr/local|opt|Users)/' || true )"
if [ -n "$outside" ]; then
    echo "libraries linked from outside the app:" >&2
    echo "$outside" >&2
    exit 1
fi
# 3. the packaged data loads: the tiles build's --check-mods needs a window, so the curses build
#    (if built) checks the app's data folder instead
if [ -x ./cataclysm ]; then
    USERDIR="$( mktemp -d )"
    # --basepath, not --datadir: with --datadir the game looks for the tilesets in <datadir>/gfx/
    ./cataclysm --basepath "$R/" --userdir "$USERDIR/" --check-mods saigon_2000s \
        > "$LOGS/package_macos_check.txt" 2>&1 || {
        tail -20 "$LOGS/package_macos_check.txt"
        exit 1
    }
    rm -rf "$USERDIR"
else
    echo "note: no curses build (./cataclysm): skipped the data check"
fi
test -f "$R/data/mods/saigon_2000s/modinfo.json"

# sign last: the checks above can write into the bundle (the game creates data/ caches)
echo "== signing (ad hoc)"
bash build-scripts/codesign-macos.sh "$APP" > "$LOGS/package_macos_sign.txt" 2>&1 || {
    tail -5 "$LOGS/package_macos_sign.txt"
    exit 1
}

codesign --verify --deep --strict "$APP" || { echo "the signature does not verify" >&2; exit 1; }

echo "== dmg"
ln -s /Applications "$OUT/$NAME/Applications"
hdiutil create -quiet -volname "Cataclysm Saigon" -srcfolder "$OUT/$NAME" -ov -format UDZO "$OUT/$NAME.dmg"
shasum -a 256 "$OUT/$NAME.dmg" > "$OUT/$NAME.dmg.sha256"
du -h "$OUT/$NAME.dmg"
echo "done: $OUT/$NAME.dmg"
