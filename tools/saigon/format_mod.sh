#!/usr/bin/env bash
# Format every JSON file of the Saigon mod with the upstream formatter.
# Build it once with: make RELEASE=1 LOCALIZE=0 TILES=0 tools/format/json_formatter.cgi
set -eu
cd "$(dirname "$0")/../.."
find data/mods/saigon_2000s -name '*.json' -print0 | xargs -0 -n1 tools/format/json_formatter.cgi | grep -v "^Please read" || true
