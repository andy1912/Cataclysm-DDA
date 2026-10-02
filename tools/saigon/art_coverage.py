#!/usr/bin/env python3
"""Art coverage: which manifest ids have a Saigon sprite, a fallback, or nothing.

Reads doc/saigon/art/manifest.csv (from art_manifest.py) and every mod_tileset in
data/mods/saigon_2000s/gfx/.  For each tier it reports how many ids have
  sprite    an entry in the Saigon mod tileset
  fallback  no sprite, but a looks_like chain to a vanilla id (draws with base art)
  missing   neither (draws as "unknown" or ASCII)
Exit status 1 if any T1 id is missing (the CI gate).

Run from the repo root:  python3 tools/saigon/art_coverage.py [--list T1]
"""
import argparse
import collections
import csv
import glob
import json
import os
import sys

ROOT = os.path.join( os.path.dirname( __file__ ), '..', '..' )


def sprite_ids():
    ids = set()
    for f in glob.glob( os.path.join( ROOT, 'data', 'mods', 'saigon_2000s', 'gfx', '*.json' ) ):
        with open( f ) as fh:
            for o in json.load( fh ):
                if o.get( 'type' ) != 'mod_tileset':
                    continue
                for sheet in o.get( 'tiles-new', [] ):
                    for t in sheet.get( 'tiles', [] ):
                        tid = t.get( 'id' )
                        ids.update( tid if isinstance( tid, list ) else [ tid ] )
    return ids


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument( '--list', choices=[ 'T1', 'T2', 'T3' ], help='print the ids still needing art in a tier' )
    args = ap.parse_args()
    have = sprite_ids()
    stats = collections.Counter()
    todo = []
    with open( os.path.join( ROOT, 'doc', 'saigon', 'art', 'manifest.csv' ) ) as fh:
        for row in csv.DictReader( fh ):
            # vehicle parts are drawn from "vp_<id>" tiles (src/cata_tiles.cpp:2096)
            sprite_id = 'vp_' + row['id'] if row['category'] == 'vehicle_part' else row['id']
            if sprite_id in have:
                state = 'sprite'
            elif row['fallback'] or row['source'] == 'dda':
                # dda ids are drawn by the base tileset; mod ids need a looks_like chain
                state = 'fallback'
            else:
                state = 'missing'
            stats[( row['tier'], state )] += 1
            if state != 'sprite' and args.list == row['tier']:
                todo.append( '%s\t%s\t%s\t%s' % ( row['category'], row['id'], row['source'], state ) )
    print( '| Tier | Saigon sprite | base-tileset art / fallback | missing |' )
    print( '|---|---|---|---|' )
    for tier in ( 'T1', 'T2', 'T3' ):
        print( '| %s | %d | %d | %d |' % ( tier, stats[( tier, 'sprite' )], stats[( tier, 'fallback' )],
                                          stats[( tier, 'missing' )] ) )
    if todo:
        print( '\n'.join( todo ) )
    sys.exit( 1 if stats[( 'T1', 'missing' )] else 0 )


if __name__ == '__main__':
    main()
