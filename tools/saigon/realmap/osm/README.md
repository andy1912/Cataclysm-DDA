# OpenStreetMap data for the real-map Saigon

The real-map street network, water, land use and places come from OpenStreetMap.

**Data © OpenStreetMap contributors, available under the Open Database Licence (ODbL 1.0):**
<https://www.openstreetmap.org/copyright>. The overmap files made from it
(`data/mods/saigon_2000s/realmap_2009/`) are a Produced Work and carry this attribution in the mod's
credits.

- `query_roads.overpassql`, `query_land.overpassql`, `query_places.overpassql`: what is fetched, for the box
  S 10.729, W 106.624, N 10.886, E 106.821.
- `fetch_osm.sh`: fetches them from overpass-api.de (about 34 MB, not committed).
- Extract used so far: OSM data of 2026-10-05.

Today's map is turned into 2009 by `../corrections_2009.json` (each entry says why), checked against the
2000s tourist map kept locally in `../source/`.
