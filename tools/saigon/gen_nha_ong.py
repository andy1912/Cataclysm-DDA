#!/usr/bin/env python3
"""Generate the nhà ống (shophouse) row mapgen for the saigon_2000s mod.

Design: doc/saigon/analysis/d2_r3.md §4.a (critic PASS).  One 24x24 OMT holds six
4-tile lots (x = 4k..4k+3).  Local frame: street to the north.
  rows 0-1   sidewalk (z0), open air above
  row  2     shop front: roll-up shutter (z0) / front wall with barred windows (z1+)
  rows 3-15  house body
  rows 16-19 rear rooms at z0-z2, shared roof walk at z3
  rows 20-23 back alley (z0), open air above
Each lot picks a height h3/h4/h5 once per OMT column (omt_stack parameter) and its
chunk switches content by absolute z with check_z, so floors stay consistent.
Stairs alternate between lot-local (2,13) and (2,11) so no tile is both up and down.

Run from the repo root:  python3 tools/saigon/gen_nha_ong.py
"""
import json
import os

ROOT = os.path.join( os.path.dirname( __file__ ), '..', '..', 'data', 'mods', 'saigon_2000s' )
BLANK = ' ' * 24
CLEARING = [ 'ERASE_FURNITURE_BEFORE_PLACING_TERRAIN', 'ERASE_TRAP_BEFORE_PLACING_TERRAIN',
             'ALLOW_TERRAIN_UNDER_ITEMS' ]

# Stair rows: going up from an even storey uses row 13, from an odd storey row 11.
def up_row( z ):
    return 13 if z % 2 == 0 else 11


def down_row( z ):
    return up_row( z - 1 )


def chunk( rows_by_y ):
    """rows_by_y: {y: 4-char string}; returns 24 rows of 24 chars (cols 0-3 only)."""
    rows = []
    for y in range( 24 ):
        s = rows_by_y.get( y )
        rows.append( s.ljust( 24 ) if s else BLANK )
    return rows


def with_stairs( rows, z, top ):
    rows = dict( rows )
    if z > 0:
        y = down_row( z )
        rows[y] = rows[y][:2] + '>' + rows[y][3:]
    if z < top:
        y = up_row( z )
        rows[y] = rows[y][:2] + '<' + rows[y][3:]
    return rows


# --- lot templates (4 columns; column 0 is this lot's west party wall) ---------
GROUND = {
    'pho': [
        'WRRR', 'W...', 'Wtc.', 'Wtc.', 'W...', 'Wtc.', 'W...', 'WCC.', 'WSO.',
        'W...', 'W...', 'W...', 'W...', 'W.A.', 'WF..', 'WTb.', 'W...', 'WW+W' ],
    'taphoa': [
        'WRRR', 'W...', 'Wrr.', 'W...', 'Wrr.', 'W...', 'Wrr.', 'WCC.', 'W...',
        'W...', 'W...', 'W...', 'W...', 'W.A.', 'WF..', 'WTb.', 'W...', 'WW+W' ],
    'nhathuoc': [
        'WRRR', 'W...', 'Wpp.', 'W...', 'Wpp.', 'W...', 'Wpp.', 'WCC.', 'W...',
        'W...', 'W...', 'W...', 'W...', 'W.A.', 'WF..', 'WTb.', 'W...', 'WW+W' ],
    'moto': [
        'WRRR', 'W...', 'W.m.', 'W.m.', 'W...', 'Wkk.', 'W...', 'WCC.', 'W...',
        'W...', 'W...', 'W...', 'W...', 'W.A.', 'WF..', 'WTb.', 'W...', 'WW+W' ],
}
FLOOR = {
    'family': [
        'W#w#', 'Wb..', 'Wd..', 'W...', 'W+WW', 'Wb..', 'Wd..', 'W...', 'W...',
        'W...', 'W.s.', 'W...', 'W...', 'W+WW', 'WbT.', 'W...', 'W.d.', 'W#w#' ],
    'rental': [
        'W#w#', 'Wbb.', 'W...', 'Wbb.', 'W...', 'W+WW', 'Wb..', 'W...', 'W...',
        'W...', 'W...', 'W...', 'W...', 'W+WW', 'WbT.', 'W...', 'Wb..', 'W#w#' ],
}
# z3 roof walk (rows 16-19) shared by every lot; railing dividers on column 0.
WALK = [ '=___', '____', '____', '====' ]
DECK_FULL = [ 'WWWW' ] + [ '=___' ] * 13           # rows 2-15, h3 top deck
SETBACK_ROOM = [ 'W#w#' ] + [ 'W..W' ] * 12 + [ 'W+WW' ]  # rows 2-15, door onto walk at (1,15)
SETBACK_DECK = [ 'WWWW' ] + [ '=__=' ] * 13         # rows 2-15, top of a setback


def rows_from( lines, first_y ):
    return { first_y + i: line for i, line in enumerate( lines ) }


def lot_chunks():
    out = []
    # ground variants (z0)
    for name, lines in GROUND.items():
        out.append( ( 'sgn_lot_z0_' + name, with_stairs( rows_from( lines, 2 ), 0, 1 ) ) )
    # floors z1, z2 (always present: every lot has >= 3 storeys)
    for z in ( 1, 2 ):
        for name, lines in FLOOR.items():
            out.append( ( 'sgn_lot_z%d_%s' % ( z, name ), with_stairs( rows_from( lines, 2 ), z, 3 ) ) )
    # h3 top: full deck + walk at z3
    r = rows_from( DECK_FULL, 2 )
    r.update( rows_from( WALK, 16 ) )
    r[18] = r[18][:2] + 'K' + r[18][3:]  # rooftop water tank; column 3 is the end-cap column on lot 5
    out.append( ( 'sgn_lot_z3_deck', with_stairs( r, 3, 3 ) ) )
    # h4/h5: setback room at z3 (+walk)
    r = rows_from( SETBACK_ROOM, 2 )
    r.update( rows_from( WALK, 16 ) )
    out.append( ( 'sgn_lot_z3_room', with_stairs( r, 3, 4 ) ) )
    # h4 top: deck at z4 over rows 2-15
    r = rows_from( SETBACK_DECK, 2 )
    r[3] = r[3][:2] + 'K' + r[3][3:]
    out.append( ( 'sgn_lot_z4_deck', with_stairs( r, 4, 4 ) ) )
    # h5: setback room at z4, deck at z5
    out.append( ( 'sgn_lot_z4_room', with_stairs( rows_from( SETBACK_ROOM, 2 ), 4, 5 ) ) )
    r = rows_from( SETBACK_DECK, 2 )
    r[3] = r[3][:2] + 'K' + r[3][3:]
    out.append( ( 'sgn_lot_z5_deck', with_stairs( r, 5, 5 ) ) )
    return out


# Monsters per lot (d3_r3 §6.2 shophouse tier: <= 4 awake and <= 20 dormant per OMT).
GROUND_MONSTERS = [ { 'group': 'sgn_GROUP_SAIGON_AWAKE', 'x': [ 1, 3 ], 'y': [ 3, 18 ], 'chance': 15 },
                    { 'group': 'sgn_GROUP_ZOMBIE_DORMANT', 'x': [ 1, 3 ], 'y': [ 3, 18 ], 'chance': 50,
                      'repeat': [ 1, 3 ] } ]
FLOOR_MONSTERS = [ { 'group': 'sgn_GROUP_SAIGON_AWAKE', 'x': [ 1, 3 ], 'y': [ 3, 18 ], 'chance': 8 } ]


def nested( nid, rows ):
    monsters = GROUND_MONSTERS if nid.startswith( 'sgn_lot_z0_' ) else (
        FLOOR_MONSTERS if nid.startswith( ( 'sgn_lot_z1_', 'sgn_lot_z2_' ) ) else None )
    obj = nested_object( rows )
    if monsters:
        obj['object']['place_monster'] = monsters
    obj['nested_mapgen_id'] = nid
    return obj


def nested_object( rows ):
    return { 'type': 'mapgen',
             'object': { 'mapgensize': [ 24, 24 ], 'palettes': [ 'sgn_nhaong' ], 'rows': chunk( rows ),
                         # Lot chunks are z-exclusive (check_z) and replace whatever is below them.
                         'flags': CLEARING } }


def lot_height( nid, top ):
    ground = { 'chunks': [ [ 'sgn_lot_z0_pho', 3 ], [ 'sgn_lot_z0_taphoa', 4 ], [ 'sgn_lot_z0_moto', 2 ],
                           [ 'sgn_lot_z0_nhathuoc', 1 ] ],
               'x': 0, 'y': 0, 'check_z': [ 0 ] }
    floors = [ { 'chunks': [ [ 'sgn_lot_z%d_family' % z, 3 ], [ 'sgn_lot_z%d_rental' % z, 1 ] ],
                 'x': 0, 'y': 0, 'check_z': [ z ] } for z in ( 1, 2 ) ]
    tops = {
        3: [ ( 'sgn_lot_z3_deck', 3 ) ],
        4: [ ( 'sgn_lot_z3_room', 3 ), ( 'sgn_lot_z4_deck', 4 ) ],
        5: [ ( 'sgn_lot_z3_room', 3 ), ( 'sgn_lot_z4_room', 4 ), ( 'sgn_lot_z5_deck', 5 ) ],
    }[top]
    upper = [ { 'chunks': [ c ], 'x': 0, 'y': 0, 'check_z': [ z ] } for c, z in tops ]
    return { 'type': 'mapgen', 'nested_mapgen_id': nid,
             'object': { 'mapgensize': [ 24, 24 ], 'place_nested': [ ground ] + floors + upper,
                         'flags': CLEARING } }


def end_caps():
    """East outer wall at x=23 (z0-z2 rows 2-19, z3 rows 2-19), west cap at x=0 on z3."""
    out = []
    wall = { y: 'W' for y in range( 2, 20 ) }
    out.append( nested( 'sgn_nh_cap_wall', wall ) )
    return out


def palette():
    return {
        'type': 'palette', 'id': 'sgn_nhaong',
        'terrain': {
            'W': 't_brick_wall', '#': 't_brick_wall', 'w': 't_window_bars', 'R': 't_rdoor_c',
            '+': 't_door_c', '.': 't_thconc_floor', 't': 't_thconc_floor', 'c': 't_thconc_floor',
            'C': 't_thconc_floor', 'S': 't_thconc_floor', 'O': 't_thconc_floor', 'K': 't_concrete_roof',
            'A': 't_thconc_floor', 'F': 't_thconc_floor', 'T': 't_thconc_floor', 'b': 't_thconc_floor',
            'r': 't_thconc_floor', 'm': 't_thconc_floor', 'k': 't_thconc_floor', 'd': 't_thconc_floor',
            's': 't_thconc_floor', 'p': 't_thconc_floor',
            '<': 't_stairs_up', '>': 't_stairs_down', '_': 't_concrete_roof', '=': 't_railing' },
        'furniture': {
            't': 'f_table', 'c': 'f_stool', 'C': 'f_counter', 'S': 'f_sink', 'O': 'f_oven',
            'K': 'f_standing_tank', 'A': 'f_sgn_ban_tho', 'F': 'f_fridge', 'T': 'f_toilet',
            'b': 'f_bed', 'r': 'f_rack', 'm': 'f_rack', 'k': 'f_counter', 'd': 'f_dresser',
            's': 'f_sofa', 'p': 'f_rack' },
        'liquids': { 'K': { 'liquid': 'water', 'amount': [ 120, 720 ] } },
        'items': {
            'C': { 'item': 'sgn_street_cart', 'chance': 35 },
            'O': { 'item': 'sgn_shophouse_kitchen', 'chance': 50 },
            'F': { 'item': 'sgn_shophouse_kitchen', 'chance': 40 },
            'A': { 'item': 'sgn_pagoda', 'chance': 30 },
            'r': { 'item': 'sgn_shophouse_kitchen', 'chance': 45, 'repeat': [ 1, 3 ] },
            'm': { 'item': 'sgn_moto_shop', 'chance': 50, 'repeat': [ 1, 2 ] },
            'k': { 'item': 'sgn_moto_shop', 'chance': 40 },
            'p': { 'item': 'sgn_pharmacy', 'chance': 60, 'repeat': [ 1, 3 ] },
            'd': { 'item': 'sgn_shophouse_living', 'chance': 50, 'repeat': [ 1, 2 ] },
            'b': { 'item': 'sgn_shophouse_living', 'chance': 20 },
            's': { 'item': 'sgn_shophouse_living', 'chance': 30 } } }


def params_palette():
    dist = { 'distribution': [ [ 'sgn_lot_h3', 3 ], [ 'sgn_lot_h4', 4 ], [ 'sgn_lot_h5', 1 ] ] }
    return { 'type': 'palette', 'id': 'sgn_nhaong_row_params',
             'parameters': { 'lot%d' % k: { 'type': 'nested_mapgen_id', 'scope': 'omt_stack', 'default': dist }
                             for k in range( 6 ) } }


def row_mapgen( oters, z0 ):
    lots = [ { 'chunks': [ { 'param': 'lot%d' % k, 'fallback': 'sgn_lot_h3' } ], 'x': 4 * k, 'y': 0 }
             for k in range( 6 ) ]
    caps = [ { 'chunks': [ 'sgn_nh_cap_wall' ], 'x': 23, 'y': 0, 'check_z': [ 0, 1, 2, 3 ] },
             { 'chunks': [ 'sgn_nh_cap_wall' ], 'x': 0, 'y': 0, 'check_z': [ 3 ] } ]
    obj = { 'palettes': [ 'sgn_nhaong_row_params' ], 'place_nested': lots + caps }
    if z0:
        obj['fill_ter'] = 't_concrete'
        obj['rows'] = [ 'S' * 24, 'S' * 24 ] + [ ' ' * 24 ] * 18 + [ 'P' * 24 ] * 4
        obj['terrain'] = { 'S': 't_sidewalk', 'P': 't_concrete' }
    else:
        obj['fill_ter'] = 't_open_air'
    return { 'type': 'mapgen', 'om_terrain': oters, 'object': obj }


def overmap():
    out = []
    names = { 0: 'nhà ống row', 1: 'nhà ống row, upper floor', 2: 'nhà ống row, upper floor',
              3: 'nhà ống rooftops', 4: 'nhà ống rooftops', 5: 'nhà ống rooftops' }
    for z in range( 6 ):
        o = { 'type': 'overmap_terrain', 'id': 'sgn_nh_solo_z%d' % z,
              'copy-from': 'generic_city_building' if z == 0 else 'generic_city_building_roof',
              'name': names[z], 'sym': '^' if z == 0 else '#', 'color': 'light_red' if z == 0 else 'red',
              'looks_like': 'house' }
        out.append( o )
    out.append( { 'type': 'city_building', 'id': 'sgn_nhaong_row_1', 'locations': [ 'land' ],
                  'flags': [ 'SAIGON' ],
                  'overmaps': [ { 'point': [ 0, 0, z ], 'overmap': 'sgn_nh_solo_z%d_north' % z }
                                for z in range( 6 ) ] } )
    return out


def main():
    mg = os.path.join( ROOT, 'mapgen', 'nha_ong' )
    os.makedirs( mg, exist_ok=True )
    os.makedirs( os.path.join( ROOT, 'overmap' ), exist_ok=True )
    chunks = [ nested( nid, rows ) for nid, rows in lot_chunks() ]
    heights = [ lot_height( 'sgn_lot_h%d' % h, h ) for h in ( 3, 4, 5 ) ]
    data = [ palette(), params_palette() ] + chunks + heights + end_caps() + [
        row_mapgen( [ 'sgn_nh_solo_z0' ], True ),
        row_mapgen( [ 'sgn_nh_solo_z%d' % z for z in range( 1, 6 ) ], False ) ]
    with open( os.path.join( mg, 'nha_ong_row.json' ), 'w' ) as f:
        json.dump( data, f, ensure_ascii=False, indent=2 )
    with open( os.path.join( ROOT, 'overmap', 'nha_ong.json' ), 'w' ) as f:
        json.dump( overmap(), f, ensure_ascii=False, indent=2 )


if __name__ == '__main__':
    main()
