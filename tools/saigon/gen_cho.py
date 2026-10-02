#!/usr/bin/env python3
"""Generate the chợ (covered wet market) for the saigon_2000s mod.

Design: doc/saigon/analysis/d2_r3.md §4.c.  A 2x2-OMT city building (48x48 tiles,
street to the local north) in the city "shops" pool.  Covered hall with entrances on
all four sides, a grid of stalls zoned like a real chợ: produce at the front, the wet
fish and meat hall in the middle, dry goods and garments at the back, an ice store
(thùng xốp coolers) in one corner and the market management office in another.

Run from the repo root:  python3 tools/saigon/gen_cho.py
"""
import json
import os

ROOT = os.path.join( os.path.dirname( __file__ ), '..', '..', 'data', 'mods', 'saigon_2000s' )
N = 48


def build_rows():
    g = [ [ '.' for _ in range( N ) ] for _ in range( N ) ]
    # perimeter wall with 4-wide entrances centred on each side
    for i in range( N ):
        for x, y in ( ( i, 0 ), ( i, N - 1 ), ( 0, i ), ( N - 1, i ) ):
            g[y][x] = '#'
    for i in range( 22, 26 ):
        g[0][i] = g[N - 1][i] = ','
        g[i][0] = g[i][N - 1] = ','
    # stall blocks: 4 wide x 2 deep counters, separated by 2-tile aisles
    zone_rows = [ ( 3, 'P' ), ( 7, 'P' ), ( 11, 'P' ), ( 16, 'F' ), ( 20, 'F' ), ( 26, 'M' ),
                  ( 30, 'M' ), ( 35, 'D' ), ( 39, 'G' ), ( 43, 'D' ) ]
    for y0, sym in zone_rows:
        for x0 in range( 3, N - 6, 6 ):
            if 20 <= x0 <= 25:
                continue  # keep the central north-south aisle clear
            if y0 == 7 and x0 in ( 3, 39 ):
                continue  # keep the office and ice-store doorways (x 5 and 41, row 6) clear
            for dy in range( 2 ):
                for dx in range( 4 ):
                    g[y0 + dy][x0 + dx] = sym
    # ice store (NE corner) and management office (NW corner), each with a door
    for y in range( 1, 6 ):
        for x in range( 38, 47 ):
            g[y][x] = 'I' if ( y in ( 2, 4 ) and x % 2 == 0 ) else '_'
    for x in range( 37, 47 ):
        g[6][x] = '#'
    for y in range( 1, 7 ):
        g[y][37] = '#'
    g[6][41] = '+'
    for y in range( 1, 6 ):
        for x in range( 1, 9 ):
            g[y][x] = '_'
    for x in range( 1, 10 ):
        g[6][x] = '#'
    for y in range( 1, 7 ):
        g[y][9] = '#'
    g[6][5] = '+'
    g[2][3] = 'd'
    g[2][6] = 'd'
    g[4][4] = 'A'
    return [ ''.join( r ) for r in g ]


def palette():
    return {
        'type': 'palette', 'id': 'sgn_cho',
        'terrain': {
            '#': 't_brick_wall', '.': 't_thconc_floor', ',': 't_thconc_floor', '_': 't_thconc_floor',
            '+': 't_door_c', 'P': 't_thconc_floor', 'F': 't_thconc_floor', 'M': 't_thconc_floor',
            'D': 't_thconc_floor', 'G': 't_thconc_floor', 'I': 't_thconc_floor', 'd': 't_thconc_floor',
            'A': 't_thconc_floor' },
        'furniture': {
            'P': 'f_counter', 'F': 'f_counter', 'M': 'f_counter', 'D': 'f_rack', 'G': 'f_clothing_rail',
            'd': 'f_desk', 'A': 'f_sgn_ban_tho' },
        'items': {
            'P': { 'item': 'sgn_cho_stall_produce', 'chance': 45 },
            'F': { 'item': 'sgn_cho_stall_meat_fish', 'chance': 45 },
            'M': { 'item': 'sgn_cho_stall_meat_fish', 'chance': 35 },
            'D': { 'item': 'sgn_shophouse_kitchen', 'chance': 50 },
            'G': { 'item': 'default_zombie_clothes', 'chance': 40 },
            'd': { 'item': 'sgn_shophouse_living', 'chance': 50 },
            'A': { 'item': 'sgn_pagoda', 'chance': 50 } },
        'item': { 'I': { 'item': 'sgn_thung_xop', 'chance': 80 } } }


def mapgen():
    return { 'type': 'mapgen',
             'om_terrain': [ [ 'sgn_cho_nw', 'sgn_cho_ne' ], [ 'sgn_cho_sw', 'sgn_cho_se' ] ],
             'object': { 'fill_ter': 't_thconc_floor', 'rows': build_rows(), 'palettes': [ 'sgn_cho' ],
                         # d3_r3 §6.2 chợ hot-spot tier, per 4-OMT hall: ~10 awake, ~30 dormant
                         # (ranges may not cross OMT boundaries, so one entry per quarter)
                         'place_monster': [ m for xr in ( [ 2, 21 ], [ 26, 45 ] ) for yr in ( [ 7, 22 ], [ 26, 45 ] )
                                            for m in (
                             { 'group': 'sgn_GROUP_SAIGON_AWAKE', 'x': xr, 'y': yr, 'repeat': [ 1, 4 ] },
                             { 'group': 'sgn_GROUP_ZOMBIE_DORMANT', 'x': xr, 'y': yr, 'repeat': [ 5, 10 ] } ) ],
                         # B9b: Cô Ba and Chú Tư hold out in the office of roughly one chợ in nine
                         # (true uniqueness needs a global flag: follow-up).
                         'place_nested': [ { 'chunks': [ [ 'sgn_cho_npcs', 1 ], [ 'null', 8 ] ], 'x': 1, 'y': 1 } ] } }


def roof_mapgen():
    rows = [ '_' * N ] * N
    return { 'type': 'mapgen',
             'om_terrain': [ [ 'sgn_cho_roof_nw', 'sgn_cho_roof_ne' ], [ 'sgn_cho_roof_sw', 'sgn_cho_roof_se' ] ],
             'object': { 'fill_ter': 't_open_air', 'rows': rows, 'terrain': { '_': 't_metal_flat_roof' } } }


def overmap():
    out = []
    for part in ( 'nw', 'ne', 'sw', 'se' ):
        out.append( { 'type': 'overmap_terrain', 'id': 'sgn_cho_' + part, 'copy-from': 'generic_city_building',
                      'name': 'chợ', 'sym': 'M', 'color': 'yellow', 'looks_like': 'grocery' } )
        out.append( { 'type': 'overmap_terrain', 'id': 'sgn_cho_roof_' + part,
                      'copy-from': 'generic_city_building_roof', 'name': 'chợ roof', 'sym': 'M',
                      'color': 'yellow', 'looks_like': 'grocery' } )
    out.append( { 'type': 'city_building', 'id': 'sgn_cho_1', 'locations': [ 'land' ], 'flags': [ 'SAIGON' ],
                  'overmaps': [
                      { 'point': [ 0, 0, 0 ], 'overmap': 'sgn_cho_nw_north' },
                      { 'point': [ 1, 0, 0 ], 'overmap': 'sgn_cho_ne_north' },
                      { 'point': [ 0, 1, 0 ], 'overmap': 'sgn_cho_sw_north' },
                      { 'point': [ 1, 1, 0 ], 'overmap': 'sgn_cho_se_north' },
                      { 'point': [ 0, 0, 1 ], 'overmap': 'sgn_cho_roof_nw_north' },
                      { 'point': [ 1, 0, 1 ], 'overmap': 'sgn_cho_roof_ne_north' },
                      { 'point': [ 0, 1, 1 ], 'overmap': 'sgn_cho_roof_sw_north' },
                      { 'point': [ 1, 1, 1 ], 'overmap': 'sgn_cho_roof_se_north' } ] } )
    return out


def main():
    rows = build_rows()
    assert len( rows ) == N and all( len( r ) == N for r in rows )
    mg = os.path.join( ROOT, 'mapgen', 'cho' )
    os.makedirs( mg, exist_ok=True )
    with open( os.path.join( mg, 'cho.json' ), 'w' ) as f:
        json.dump( [ palette(), mapgen(), roof_mapgen() ], f, ensure_ascii=False, indent=2 )
    with open( os.path.join( ROOT, 'overmap', 'cho.json' ), 'w' ) as f:
        json.dump( overmap(), f, ensure_ascii=False, indent=2 )


if __name__ == '__main__':
    main()
