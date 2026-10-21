#!/bin/sh
# Rebuild the real-map Saigon 2009 from the OSM extract (fetch it first with osm/fetch_osm.sh):
#   1. osm_to_grid.py  OSM + corrections_2009.json -> build/realmap_2009.grid.json (+ previews)
#   2. write_omaps.py  grid -> data/mods/saigon_2000s/realmap_2009/overmap_<x>_<y>.omap.gz
#   3. check_realmap.py  walkable bridges, a way into every hẻm network
# Then check it: tests/cata_test --mods=dda,saigon_2000s "saigon_realmap*"
set -e
cd "$(dirname "$0")"
mkdir -p build
python3 osm_to_grid.py build/realmap_2009
python3 write_omaps.py build/realmap_2009.grid.json
python3 check_realmap.py
