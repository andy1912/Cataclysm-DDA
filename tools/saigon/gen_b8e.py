#!/usr/bin/env python3
"""Generate the chùa (pagoda) and chung cư (old apartment block) for saigon_2000s.

Both are 1-OMT city buildings, street to the local north.
  chùa:    walled compound with a three-arch gate (tam quan), a courtyard with a bodhi
           tree and incense burner, the main hall with Buddha statue and altars, monks'
           quarters and a vegetable garden.  Goes in the city "parks" pool.
  chung cư: a pre-1975 five-storey walk-up with open access corridors (hành lang) along
           the street side, a central stair core, four flats per floor (ground floor
           flats double as tiny shops), and a flat roof with water tanks.  Goes in the
           "houses" pool.  Stairs alternate columns per storey like the nhà ống.

Run from the repo root:  python3 tools/saigon/gen_b8e.py
"""
import json
import os

ROOT = os.path.join( os.path.dirname( __file__ ), '..', '..', 'data', 'mods', 'saigon_2000s' )
N = 24


def grid( fill ):
    return [ [ fill ] * N for _ in range( N ) ]


def rows_of( g ):
    out = [ ''.join( r ) for r in g ]
    assert len( out ) == N and all( len( r ) == N for r in out )
    return out


# ------------------------------------------------------------------ chùa -----
def pagoda_rows():
    g = grid( ',' )                                   # courtyard paving
    for i in range( N ):
        for x, y in ( ( i, 0 ), ( i, N - 1 ), ( 0, i ), ( N - 1, i ) ):
            g[y][x] = 'W'                             # compound wall
    for x in range( 9, 15 ):
        g[0][x] = ','                                 # tam quan gate opening
    g[0][10] = g[0][13] = 'P'                         # gate pillars
    # bodhi tree, incense burner and shrubs in the front courtyard
    g[5][5] = 'T'
    g[5][18] = 'T'
    g[6][11] = 'B'
    for x in ( 2, 3, 20, 21 ):
        g[2][x] = 's'
    # main hall: y 9-17, x 4-19
    for x in range( 4, 20 ):
        g[9][x] = '#'
        g[17][x] = '#'
    for y in range( 9, 18 ):
        g[y][4] = '#'
        g[y][19] = '#'
    for y in range( 10, 17 ):
        for x in range( 5, 19 ):
            g[y][x] = '.'
    g[9][11] = g[9][12] = '+'                         # double doors onto the courtyard
    g[9][7] = g[9][16] = 'w'
    for x in range( 8, 16 ):
        g[15][x] = 'A'                                # altar row
    g[16][11] = 'S'                                   # Buddha statue
    for y in ( 11, 13 ):
        for x in ( 7, 9, 14, 16 ):
            g[y][x] = 'm'                             # prayer mats (cushions)
    # monks' quarters (east) and kitchen (west) behind the hall: y 18-22
    for x in range( 1, 23 ):
        g[18][x] = '#'
    for y in range( 18, 23 ):
        g[y][11] = '#'
    for y in range( 19, 23 ):
        for x in range( 1, 11 ):
            g[y][x] = '.'
        for x in range( 12, 23 ):
            g[y][x] = '.'
    g[18][5] = '+'
    g[18][16] = '+'
    g[20][2] = 'k'
    g[20][3] = 'k'
    g[21][2] = 'O'
    for x in ( 13, 16, 19 ):
        g[20][x] = 'b'
    g[22][21] = 'd'
    # vegetable garden west of the hall
    for y in range( 10, 16 ):
        g[y][2] = 'g'
    return rows_of( g )


def pagoda_palette():
    return {
        'type': 'palette', 'id': 'sgn_chua',
        'terrain': {
            'W': 't_brick_wall', 'P': 't_brick_wall', ',': 't_concrete', '#': 't_brick_wall',
            '.': 't_thconc_floor', '+': 't_door_c', 'w': 't_window_domestic', 'T': 't_sgn_tree_bo_de',
            's': 't_region_shrub_decorative', 'g': 't_dirt', 'B': 't_concrete', 'A': 't_thconc_floor',
            'S': 't_thconc_floor', 'm': 't_thconc_floor', 'k': 't_thconc_floor',
            'O': 't_thconc_floor', 'b': 't_thconc_floor', 'd': 't_thconc_floor' },
        'furniture': {
            'B': 'f_brazier', 'A': 'f_sgn_ban_tho', 'S': 'f_statue',
            'k': 'f_counter', 'O': 'f_woodstove', 'b': 'f_bed', 'd': 'f_dresser' },
        'items': {
            'A': { 'item': 'sgn_pagoda', 'chance': 40 },
            'k': { 'item': 'sgn_pagoda', 'chance': 50 },
            'd': { 'item': 'sgn_pagoda', 'chance': 60 },
            'b': { 'item': 'sgn_shophouse_living', 'chance': 15 } } }


PAGODA_OUTDOOR = set( ',TsgBWP' )


def pagoda_roof_rows():
    return [ ''.join( ' ' if c in PAGODA_OUTDOOR else '_' for c in r ) for r in pagoda_rows() ]


# -------------------------------------------------------------- chung cư -----
TOP = 4                    # floors z0..z4, roof at z5
UNITS = ( 2, 6, 14, 18 )   # unit x origins (4 wide); stair core x 10-13


def up_col( z ):
    return 11 if z % 2 == 0 else 12


def chungcu_rows( z ):
    if z == TOP + 1:
        g = grid( ' ' )
        for y in range( 4, 20 ):
            for x in range( 2, 22 ):
                g[y][x] = '_'
        for x in range( 2, 22 ):
            g[4][x] = '='
            g[19][x] = '='
        for y in range( 4, 20 ):
            g[y][2] = '='
            g[y][21] = '='
        g[10][up_col( z - 1 )] = '>'
        g[15][5] = g[15][18] = 'K'
        return rows_of( g )
    g = grid( ' ' )
    if z == 0:
        for y in range( 0, 4 ):
            for x in range( N ):
                g[y][x] = 'S'                         # sidewalk / forecourt
        for y in range( 20, N ):
            for x in range( N ):
                g[y][x] = ','
    # access corridor (hành lang) along the street side, y 4-5
    for x in range( 2, 22 ):
        g[4][x] = '=' if z > 0 else ','
        g[5][x] = '.'
    # outer shell of the flats, y 6-19
    for x in range( 2, 22 ):
        g[6][x] = '#'
        g[19][x] = '#'
    for y in range( 6, 20 ):
        g[y][2] = '#'
        g[y][21] = '#'
    # stair core x 10-13
    for y in range( 6, 20 ):
        g[y][10] = '#'
        g[y][13] = '#'
        g[y][11] = g[y][12] = '.'
    g[6][11] = g[6][12] = '.'
    g[19][11] = g[19][12] = '#'
    if z < TOP + 1:
        g[10][up_col( z )] = '<'
    if z > 0:
        # directly above the up stair of the storey below; up_col alternates, so the
        # up and down stairs of one storey never share a tile
        g[10][up_col( z - 1 )] = '>'
    for ux in UNITS:
        x0 = ux
        door_x = x0 + 1 if ux < 10 else x0 + 2
        g[6][door_x] = '+'
        for y in range( 7, 19 ):
            for x in range( x0, x0 + 4 ):
                if g[y][x] == ' ':
                    g[y][x] = '.'
        # divider between paired flats
        if ux in ( 6, 18 ):
            for y in range( 6, 20 ):
                g[y][ux] = '#'
            g[6][ux + 1] = '+'
        # interior: front room, partition, back room
        for x in range( x0 + ( 1 if ux in ( 6, 18 ) else 0 ), x0 + 4 ):
            if g[12][x] == '.':
                g[12][x] = '#'
        g[12][x0 + 2] = '+'
        if z == 0:
            g[8][x0 + 2] = 'C'                        # ground-floor flats double as shops
            g[9][x0 + 2] = 'C'
        else:
            g[8][x0 + 2] = 't'
        g[14][x0 + 2] = 'b'
        g[16][x0 + 2] = 'k'
        g[18][x0 + 2] = 'd'
        g[17][x0 + 2] = 'A'
    # rear windows
    for ux in UNITS:
        g[19][ux + 2] = 'w'
    return rows_of( g )


def chungcu_palette():
    return {
        'type': 'palette', 'id': 'sgn_chungcu',
        'terrain': {
            '#': 't_brick_wall', '.': 't_thconc_floor', '+': 't_door_c', 'w': 't_window_bars',
            '=': 't_railing', ',': 't_concrete', 'S': 't_sidewalk', '_': 't_concrete_roof',
            '<': 't_stairs_up', '>': 't_stairs_down', 'K': 't_concrete_roof', 'C': 't_thconc_floor',
            't': 't_thconc_floor', 'b': 't_thconc_floor', 'k': 't_thconc_floor', 'd': 't_thconc_floor',
            'A': 't_thconc_floor' },
        'furniture': {
            'K': 'f_standing_tank', 'C': 'f_counter', 't': 'f_table', 'b': 'f_bed', 'k': 'f_counter',
            'd': 'f_dresser', 'A': 'f_sgn_ban_tho' },
        'liquids': { 'K': { 'liquid': 'water', 'amount': [ 120, 720 ] } },
        'items': {
            'C': { 'item': 'sgn_street_cart', 'chance': 30 },
            'k': { 'item': 'sgn_shophouse_kitchen', 'chance': 50 },
            'd': { 'item': 'sgn_shophouse_living', 'chance': 50 },
            # W2: and under the bed, what the flat kept to defend its door on the open corridor
            'b': [ { 'item': 'sgn_shophouse_living', 'chance': 20 }, { 'item': 'sgn_loot_home_weapon', 'chance': 15 } ],
            'A': { 'item': 'sgn_pagoda', 'chance': 20 } } }


def main():
    data = [ pagoda_palette(), chungcu_palette(),
             { 'type': 'mapgen', 'om_terrain': [ 'sgn_chua' ],
               'object': { 'fill_ter': 't_concrete', 'rows': pagoda_rows(), 'palettes': [ 'sgn_chua' ] } },
             { 'type': 'mapgen', 'om_terrain': [ 'sgn_chua_roof' ],
               'object': { 'fill_ter': 't_open_air', 'rows': pagoda_roof_rows(),
                           'terrain': { '_': 't_tile_flat_roof' } } } ]
    for z in range( TOP + 2 ):
        data.append( { 'type': 'mapgen', 'om_terrain': [ 'sgn_chungcu_z%d' % z ],
                       'object': { 'fill_ter': 't_concrete' if z == 0 else 't_open_air',
                                   'rows': chungcu_rows( z ), 'palettes': [ 'sgn_chungcu' ] } } )
    om = [ { 'type': 'overmap_terrain', 'id': 'sgn_chua', 'copy-from': 'generic_city_building',
             'name': 'chùa', 'sym': 'P', 'color': 'yellow', 'looks_like': 'church' },
           { 'type': 'overmap_terrain', 'id': 'sgn_chua_roof', 'copy-from': 'generic_city_building_roof',
             'name': 'chùa roof', 'sym': 'P', 'color': 'yellow', 'looks_like': 'church' },
           { 'type': 'city_building', 'id': 'sgn_chua_1', 'locations': [ 'land' ], 'flags': [ 'SAIGON' ],
             'overmaps': [ { 'point': [ 0, 0, 0 ], 'overmap': 'sgn_chua_north' },
                           { 'point': [ 0, 0, 1 ], 'overmap': 'sgn_chua_roof_north' } ] } ]
    for z in range( TOP + 2 ):
        om.append( { 'type': 'overmap_terrain', 'id': 'sgn_chungcu_z%d' % z,
                     'copy-from': 'generic_city_building' if z == 0 else 'generic_city_building_roof',
                     'name': 'chung cư' if z <= TOP else 'chung cư roof', 'sym': 'A', 'color': 'light_gray',
                     'looks_like': 'house' } )
    om.append( { 'type': 'city_building', 'id': 'sgn_chungcu_1', 'locations': [ 'land' ], 'flags': [ 'SAIGON' ],
                 'overmaps': [ { 'point': [ 0, 0, z ], 'overmap': 'sgn_chungcu_z%d_north' % z }
                               for z in range( TOP + 2 ) ] } )
    mg = os.path.join( ROOT, 'mapgen', 'b8e' )
    os.makedirs( mg, exist_ok=True )
    with open( os.path.join( mg, 'chua_chungcu.json' ), 'w' ) as f:
        json.dump( data, f, ensure_ascii=False, indent=2 )
    with open( os.path.join( ROOT, 'overmap', 'chua_chungcu.json' ), 'w' ) as f:
        json.dump( om, f, ensure_ascii=False, indent=2 )


if __name__ == '__main__':
    main()
