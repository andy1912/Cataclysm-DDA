#!/bin/sh
# Fetch the OpenStreetMap extract for the real-map Saigon (5 x 4 overmaps; see query_*.overpassql).
# About 34 MB from overpass-api.de; the files are not committed (.gitignore).
# Data © OpenStreetMap contributors, available under the Open Database Licence (ODbL 1.0).
cd "$(dirname "$0")" || exit 1
for part in roads land places; do
    for try in 1 2 3; do
        curl -sS -o "saigon_$part.osm.json" -A "cdda-saigon-realmap/1.0 (game map converter)" \
             -H "Accept: application/json, */*" --data-urlencode "data@query_$part.overpassql" \
             https://overpass-api.de/api/interpreter &&
            python3 -c "import json; d = json.load(open('saigon_$part.osm.json')); print('$part', len(d['elements']), 'elements, data of', d['osm3s']['timestamp_osm_base'])" &&
            break
        echo "$part: try $try failed, retrying"; sleep 20
    done
done
