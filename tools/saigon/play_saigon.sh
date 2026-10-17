#!/usr/bin/env bash
# Launch Cataclysm: Dark Days Ahead with the Saigon 2000s mod preselected.
# - Uses the graphical SDL3 build (cataclysm-tiles) with the original UltimateCataclysm
#   tileset and Larwick Overmap (engine defaults, src/options.cpp:2527,2580); falls back
#   to the terminal build if the tiles build is not there yet.
# - Writes config/user-default-mods.json so "Create World" starts with dda + saigon_2000s
#   (format: src/mod_manager.cpp:315-330).  An existing file is left alone.
# - CATA_DISABLE_SPRITE_SHADERS=1: shaders are built as SPIR-V, which Metal cannot use,
#   so sprites draw from pre-baked atlases instead (doc/c++/COMPILING.md, SDL builds).
set -eu
cd "$(dirname "$0")/../.."
mkdir -p config
if [ ! -f config/user-default-mods.json ]; then
    cat > config/user-default-mods.json <<'EOF'
{
  "type": "MOD_INFO",
  "id": "user:default",
  "conflicts": [  ],
  "dependencies": [ "dda", "saigon_2000s" ],
  "//": "Not really obsolete!  Marked as such to prevent it from showing in the main list",
  "obsolete": true
}
EOF
    echo "Saigon 2000s preselected for new worlds (config/user-default-mods.json)."
fi
if [ ! -d gfx/UltimateCataclysm ]; then
    echo "Note: gfx/UltimateCataclysm is missing; install it from I-am-Erk/CDDA-Tilesets releases."
fi
if [ -x ./cataclysm-tiles ]; then
    exec env CATA_DISABLE_SPRITE_SHADERS=1 ./cataclysm-tiles "$@"
fi
echo "cataclysm-tiles is not built yet; starting the terminal version."
exec ./cataclysm "$@"
