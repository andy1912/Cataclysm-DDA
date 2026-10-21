#!/usr/bin/env python3
"""Sân bay Tân Sơn Nhất for the real map: the airfield's ground tiles.  Writes three overmap
terrains and their mapgen; the real map places them from the OSM runways, taxiways and aprons
(tools/saigon/realmap), the terminal is the landmark sgn_lm_san_bay.

  sgn_sb_runway    tarmac with the centre-line dashes and threshold bars (runways run about
                   east-west, so the markings do too; NO_ROTATE)
  sgn_sb_taxiway   tarmac with a yellow centre cross
  sgn_sb_apron     tarmac with yellow stand lines, an abandoned apron bus or tug now and then,
                   luggage that fell off a cart

  data/mods/saigon_2000s/overmap/san_bay.json
  data/mods/saigon_2000s/mapgen/san_bay.json

  python3 tools/saigon/gen_san_bay.py
"""
import json
import os

ROOT = os.path.join( os.path.dirname( os.path.abspath( __file__ ) ), '..', '..' )
MOD = os.path.join( ROOT, 'data', 'mods', 'saigon_2000s' )


def grid( fill='.' ):
    return [ [ fill ] * 24 for _ in range( 24 ) ]


def runway():
    g = grid()
    for x in range( 0, 24 ):                     # centre-line dashes: 6 on, 6 off
        if x % 12 < 6:
            g[11][x] = 'y'
            g[12][x] = 'y'
    for x in range( 2, 22, 4 ):                  # touchdown bars either side
        for y in ( 4, 5, 18, 19 ):
            g[y][x] = 'y'
            g[y][x + 1] = 'y'
    return g


def taxiway():
    g = grid()
    for i in range( 24 ):
        g[11][i] = 'y'
        g[i][11] = 'y'
    return g


def apron():
    g = grid()
    for x in ( 0, 23 ):                          # stand edge lines
        for y in range( 24 ):
            g[y][x] = 'y'
    for x in range( 24 ):
        g[2][x] = 'y'
    for y in range( 4, 22 ):                     # lead-in line to the stand
        g[y][12] = 'y'
    return g


def main():
    common = { "see_cost": "none", "travel_cost_type": "road", "flags": [ "NO_ROTATE" ] }
    oters = [
        dict( { "type": "overmap_terrain", "id": "sgn_sb_runway", "name": "runway", "sym": "=",
                "color": "light_gray", "looks_like": "road" }, **common ),
        dict( { "type": "overmap_terrain", "id": "sgn_sb_taxiway", "name": "taxiway", "sym": "+",
                "color": "yellow", "looks_like": "sgn_sb_runway" }, **common ),
        dict( { "type": "overmap_terrain", "id": "sgn_sb_apron", "name": "airport apron", "sym": "#",
                "color": "light_gray", "looks_like": "sgn_sb_runway" }, **common ),
    ]
    terrain = { ".": "t_pavement", "y": "t_pavement_y" }
    mapgen = [
        { "type": "mapgen", "om_terrain": "sgn_sb_runway", "weight": 100,
          "object": { "fill_ter": "t_pavement", "rows": [ ''.join( r ) for r in runway() ], "terrain": terrain } },
        { "type": "mapgen", "om_terrain": "sgn_sb_taxiway", "weight": 100,
          "object": { "fill_ter": "t_pavement", "rows": [ ''.join( r ) for r in taxiway() ], "terrain": terrain } },
        { "type": "mapgen", "om_terrain": "sgn_sb_apron", "weight": 100,
          "object": { "fill_ter": "t_pavement", "rows": [ ''.join( r ) for r in apron() ], "terrain": terrain,
                      "place_vehicles": [ { "vehicle": "sgn_vg_coach", "x": 12, "y": 12, "rotation": 90, "chance": 8 } ],
                      "place_items": [ { "item": "sgn_tourist", "x": [ 2, 21 ], "y": [ 3, 21 ], "chance": 25,
                                         "repeat": [ 1, 2 ] } ],
                      "place_monster": [ { "group": "sgn_GROUP_SAIGON_AWAKE", "x": [ 1, 22 ], "y": [ 1, 22 ],
                                           "chance": 15 } ] } },
    ]
    with open( os.path.join( MOD, 'overmap', 'san_bay.json' ), 'w' ) as f:
        json.dump( oters, f, ensure_ascii=False, indent=2 )
        f.write( '\n' )
    with open( os.path.join( MOD, 'mapgen', 'san_bay.json' ), 'w' ) as f:
        json.dump( mapgen, f, ensure_ascii=False, indent=2 )
        f.write( '\n' )
    print( 'wrote overmap/ and mapgen/san_bay.json' )


if __name__ == '__main__':
    main()
