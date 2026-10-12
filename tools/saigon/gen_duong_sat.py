#!/usr/bin/env python3
"""Đường sắt: the North-South railway into Ga Sài Gòn, for the real map (dda no longer has
railroad overmap terrain).  Writes a LINEAR overmap terrain, sgn_duong_sat, and the five mapgen
pieces the game rotates (end, straight, curved, tee, four-way):

  data/mods/saigon_2000s/overmap/duong_sat.json
  data/mods/saigon_2000s/mapgen/duong_sat.json
  data/mods/saigon_2000s/itemgroups/duong_sat.json   (the litter along the line)

The base pieces follow dda's linear terrain: end open to the south, straight north-south, curved
east-south, tee east-south-west.  One metre-gauge track on a ballast bed, sleepers every other
metre, weeds and rubbish either side.

  python3 tools/saigon/gen_duong_sat.py
"""
import json
import os

ROOT = os.path.join( os.path.dirname( os.path.abspath( __file__ ) ), '..', '..' )
MOD = os.path.join( ROOT, 'data', 'mods', 'saigon_2000s' )
LO, HI = 8, 15            # the ballast bed
RAILS = ( 10, 13 )        # the two rails
PIECES = { 'end': 's', 'straight': 'ns', 'curved': 'es', 'tee': 'esw', 'four_way': 'nesw' }


def piece( arms ):
    g = [ [ '.' ] * 24 for _ in range( 24 ) ]

    def bed( x, y, vertical ):
        a = x if vertical else y                   # across the track
        along = y if vertical else x
        if a in RAILS:
            g[y][x] = ( 'V' if vertical else 'H' ) if along % 2 else ( 'v' if vertical else 'h' )
        elif RAILS[0] < a < RAILS[1] and along % 2 == 0:
            g[y][x] = '|' if vertical else '-'
        elif LO <= a <= HI:
            g[y][x] = '#'
    for d in arms:
        for i in range( 12 ):
            for a in range( LO, HI + 1 ):
                if d == 'n':
                    bed( a, i, True )
                elif d == 's':
                    bed( a, 23 - i, True )
                elif d == 'w':
                    bed( i, a, False )
                elif d == 'e':
                    bed( 23 - i, a, False )
    # where the arms meet: ballast with plain rail across the junction
    for y in range( LO, HI + 1 ):
        for x in range( LO, HI + 1 ):
            if len( arms ) > 1 and ( ( x in RAILS and ( 'n' in arms or 's' in arms ) ) or
                                     ( y in RAILS and ( 'e' in arms or 'w' in arms ) ) ):
                g[y][x] = 'X'
            elif g[y][x] == '.':
                g[y][x] = '#'
    if arms == 's':                                 # end of the line: a buffer stop
        for x in range( RAILS[0], RAILS[1] + 1 ):
            g[LO][x] = 'B'
    return [ ''.join( r ) for r in g ]


def main():
    oter = [ {
        "type": "overmap_terrain",
        "id": "sgn_duong_sat",
        "name": "railway",
        "sym": "#",
        "color": "light_gray",
        "looks_like": "subway",
        "see_cost": "none",
        "travel_cost_type": "road",
        "flags": [ "LINEAR" ]
    } ]
    mapgen = []
    for name, arms in PIECES.items():
        mapgen.append( {
            "type": "mapgen",
            "om_terrain": "sgn_duong_sat_" + name,
            "weight": 100,
            "object": {
                "fill_ter": "t_grass",
                "rows": piece( arms ),
                "terrain": {
                    ".": [ [ "t_grass", 6 ], [ "t_grass_long", 3 ], [ "t_dirt", 1 ] ],
                    "#": "t_railroad_rubble",
                    "V": "t_railroad_track_v", "v": "t_railroad_track_v_on_tie",
                    "H": "t_railroad_track_h", "h": "t_railroad_track_h_on_tie",
                    "|": "t_railroad_tie_v", "-": "t_railroad_tie_h",
                    "X": "t_railroad_track", "B": "t_railroad_rubble"
                },
                "furniture": { "B": "f_rubble_rock" },
                "place_items": [ { "item": "sgn_trash_railside", "x": [ 0, 23 ], "y": [ 0, 23 ], "chance": 40, "repeat": [ 1, 3 ] } ]
            }
        } )
    litter = [ {
        "type": "item_group",
        "id": "sgn_trash_railside",
        "subtype": "distribution",
        "//": "What lies along the tracks: no dda roadside group (those carry American books and fliers).",
        "items": [ [ "bag_plastic", 30 ], [ "bottle_plastic", 20 ], [ "can_drink", 15 ], [ "wrapper", 15 ],
                   [ "cig_butt", 10 ], [ "plastic_chunk", 10 ], [ "glass_shard", 5 ], [ "scrap", 5 ],
                   [ "cardboard", 5 ], [ "withered", 10 ] ]
    } ]
    with open( os.path.join( MOD, 'itemgroups', 'duong_sat.json' ), 'w' ) as f:
        json.dump( litter, f, ensure_ascii=False, indent=2 )
        f.write( '\n' )
    os.makedirs( os.path.join( MOD, 'mapgen' ), exist_ok=True )
    with open( os.path.join( MOD, 'overmap', 'duong_sat.json' ), 'w' ) as f:
        json.dump( oter, f, ensure_ascii=False, indent=2 )
        f.write( '\n' )
    with open( os.path.join( MOD, 'mapgen', 'duong_sat.json' ), 'w' ) as f:
        json.dump( mapgen, f, ensure_ascii=False, indent=2 )
        f.write( '\n' )
    print( 'wrote overmap/, mapgen/ and itemgroups/duong_sat.json' )


if __name__ == '__main__':
    main()
