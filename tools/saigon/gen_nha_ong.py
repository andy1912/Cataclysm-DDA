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
        'WRRR', 'W..G', 'Wtc.', 'Wtc.', 'W...', 'Wtc.', 'W...', 'WCC.', 'WSO.',
        'W...', 'W...', 'W...', 'W...', 'W.A.', 'WF..', 'WTb.', 'W..L', 'WW+W' ],
    'taphoa': [
        'WRRR', 'W..G', 'Wrr.', 'W...', 'Wrr.', 'W...', 'Wrr.', 'WCC.', 'W...',
        'W...', 'W...', 'W...', 'W...', 'W.A.', 'WF..', 'WTb.', 'W..L', 'WW+W' ],
    'nhathuoc': [
        'WRRR', 'W..G', 'Wpp.', 'W...', 'Wpp.', 'W...', 'Wpp.', 'WCC.', 'W...',
        'W...', 'W...', 'W...', 'W...', 'W.A.', 'WF..', 'WTb.', 'W..L', 'WW+W' ],
    'moto': [
        'WRRR', 'W..G', 'W.m.', 'W.m.', 'W...', 'Wkk.', 'W...', 'WCC.', 'W...',
        'W...', 'W...', 'W...', 'W...', 'W.A.', 'WF..', 'WTb.', 'W..L', 'WW+W' ],
    # B8h shophouse businesses: gold shop, internet café, karaoke rooms
    'tiemvang': [
        'WRRR', 'W..G', 'Wgg.', 'W...', 'Wgg.', 'W...', 'W...', 'WCC.', 'W...',
        'W...', 'W...', 'W...', 'W...', 'W.A.', 'WF..', 'WTb.', 'W..L', 'WW+W' ],
    'net': [
        'WRRR', 'W..G', 'Wnc.', 'Wnc.', 'Wnc.', 'Wnc.', 'Wnc.', 'WCC.', 'W...',
        'W...', 'W...', 'W...', 'W...', 'W.A.', 'WF..', 'WTb.', 'W..L', 'WW+W' ],
    'karaoke': [
        'WRRR', 'W..G', 'W...', 'WCC.', 'W...', 'WQs.', 'W.s.', 'W+WW', 'WQs.',
        'W.s.', 'W...', 'W...', 'W...', 'W.A.', 'WF..', 'WTb.', 'W..L', 'WW+W' ],
    # P1 more shophouse businesses
    'hotoc': [                                       # barber: chairs facing mirrors, a sink
        'WRRR', 'W..G', 'Wih.', 'W...', 'Wih.', 'W...', 'Wih.', 'W.S.', 'Wcc.',
        'W...', 'W...', 'W...', 'W...', 'W.A.', 'WF..', 'WTb.', 'W..L', 'WW+W' ],
    'may': [                                         # tailor: treadle machines, cloth racks
        'WRRR', 'W..G', 'Wff.', 'W...', 'We..', 'We.c', 'W...', 'WCC.', 'Wff.',
        'W...', 'W...', 'W...', 'W...', 'W.A.', 'WF..', 'WTb.', 'W..L', 'WW+W' ],
    'suadien': [                                     # electronics repair: benches, TVs waiting
        'WRRR', 'W..G', 'WjV.', 'W.c.', 'WjV.', 'W.c.', 'WVV.', 'WCC.', 'W...',
        'W...', 'W...', 'W...', 'W...', 'W.A.', 'WF..', 'WTb.', 'W..L', 'WW+W' ],
    'thuocbac': [                                    # herbalist: walls of herb drawers
        'WRRR', 'W..G', 'Wuu.', 'W...', 'Wuu.', 'W...', 'W.c.', 'WCC.', 'Wuu.',
        'W...', 'W...', 'W...', 'W...', 'W.A.', 'WF..', 'WTb.', 'W..L', 'WW+W' ],
    'camdo': [                                       # pawn shop: glass cases, a safe
        'WRRR', 'W..G', 'Wyy.', 'W...', 'Wyy.', 'W...', 'Wx..', 'WCC.', 'W...',
        'W...', 'W...', 'W...', 'W...', 'W.A.', 'WF..', 'WTb.', 'W..L', 'WW+W' ],
    'photo': [                                       # photocopy shop
        'WRRR', 'W..G', 'Wz..', 'W...', 'Wz..', 'W...', 'Wqq.', 'WCC.', 'W...',
        'W...', 'W...', 'W...', 'W...', 'W.A.', 'WF..', 'WTb.', 'W..L', 'WW+W' ],
    'banhmi': [                                      # bakery: ovens and bread racks
        'WRRR', 'W..G', 'Waa.', 'W...', 'Woo.', 'W...', 'Wo..', 'WCC.', 'Waa.',
        'W...', 'W...', 'W...', 'W...', 'W.A.', 'WF..', 'WTb.', 'W..L', 'WW+W' ],
    'nhau': [                                        # quán nhậu: low tables, a grill, beer crates
        'WRRR', 'W..G', 'Wtc.', 'Wtc.', 'W...', 'Wtc.', 'W.l.', 'WBB.', 'Wtc.',
        'W...', 'W...', 'W...', 'W...', 'W.A.', 'WF..', 'WTb.', 'W..L', 'WW+W' ],
}
FLOOR = {
    'family': [
        'W#w#', 'Wb..', 'Wd..', 'W.v.', 'W+WW', 'Wb..', 'Wd..', 'W...', 'W...',
        'WV..', 'W.s.', 'W...', 'W...', 'W+WW', 'WbT.', 'W...', 'W.d.', 'W#w#' ],
    'rental': [
        'W#w#', 'Wbb.', 'W.v.', 'Wbb.', 'W...', 'W+WW', 'Wb..', 'W...', 'W...',
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
    r[6] = '=_P_'                        # G21: potted kumquat, and the AC units everyone bolts to the roof
    r[10] = '=M__'
    out.append( ( 'sgn_lot_z3_deck', with_stairs( r, 3, 3 ) ) )
    # h4/h5: setback room at z3 (+walk)
    r = rows_from( SETBACK_ROOM, 2 )
    r.update( rows_from( WALK, 16 ) )
    out.append( ( 'sgn_lot_z3_room', with_stairs( r, 3, 4 ) ) )
    # h4 top: deck at z4 over rows 2-15
    r = rows_from( SETBACK_DECK, 2 )
    r[3] = r[3][:2] + 'K' + r[3][3:]
    r[7] = '=P_='
    r[11] = '=M_='
    out.append( ( 'sgn_lot_z4_deck', with_stairs( r, 4, 4 ) ) )
    # h5: setback room at z4, deck at z5
    out.append( ( 'sgn_lot_z4_room', with_stairs( rows_from( SETBACK_ROOM, 2 ), 4, 5 ) ) )
    r = rows_from( SETBACK_DECK, 2 )
    r[3] = r[3][:2] + 'K' + r[3][3:]
    r[7] = '=P_='
    r[11] = '=M_='
    out.append( ( 'sgn_lot_z5_deck', with_stairs( r, 5, 5 ) ) )
    return out


# Monsters per lot (d3_r3 §6.2 shophouse tier: <= 4 awake and <= 20 dormant per OMT).
# mapgen rolls 'chance' on every 'repeat', so a lot holds 0.15 awake and 0.5 x 1.5 = 0.75
# dormant on the ground floor plus 0.08 awake on each of z1/z2: with six lots a row OMT expects
# about 1.9 awake and 4.5 dormant (6.4 in all).  D-fix (DIFFICULTY.md, side check): dormant
# repeat [1, 3] -> [1, 2]; it was 6 dormant (7.9 in all) per OMT, 4-6x a vanilla street.
GROUND_MONSTERS = [ { 'group': 'sgn_GROUP_SAIGON_AWAKE', 'x': [ 1, 3 ], 'y': [ 3, 18 ], 'chance': 15 },
                    { 'group': 'sgn_GROUP_ZOMBIE_DORMANT', 'x': [ 1, 3 ], 'y': [ 3, 18 ], 'chance': 50,
                      'repeat': [ 1, 2 ] } ]
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
                           [ 'sgn_lot_z0_nhathuoc', 1 ], [ 'sgn_lot_z0_tiemvang', 1 ], [ 'sgn_lot_z0_net', 1 ],
                           [ 'sgn_lot_z0_karaoke', 1 ], [ 'sgn_lot_z0_hotoc', 1 ], [ 'sgn_lot_z0_may', 1 ],
                           [ 'sgn_lot_z0_suadien', 1 ], [ 'sgn_lot_z0_thuocbac', 1 ], [ 'sgn_lot_z0_camdo', 1 ],
                           [ 'sgn_lot_z0_photo', 1 ], [ 'sgn_lot_z0_banhmi', 1 ], [ 'sgn_lot_z0_nhau', 1 ] ],
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


FLOOR_PARAM = { 'param': 'floor', 'fallback': 't_thconc_floor' }
FLOORS = { 'type': 'ter_str_id', 'scope': 'nest', 'default': { 'distribution': [
    # G21: one floor per house and storey (scope nest = per lot chunk)
    [ 't_sgn_gach_bong_1', 2 ], [ 't_sgn_gach_bong_2', 2 ], [ 't_sgn_gach_bong_3', 2 ], [ 't_sgn_gach_bong_4', 2 ],
    [ 't_sgn_gach_men', 3 ], [ 't_thconc_floor', 2 ] ] } }


def palette():
    return {
        'type': 'palette', 'id': 'sgn_nhaong',
        'parameters': { 'floor': FLOORS },
        'terrain': {
            'W': 't_brick_wall', '#': 't_brick_wall', 'w': 't_window_bars',
            # G22: shopfronts close with a roller shutter or a folding iron gate
            'R': [ [ 't_rdoor_c', 3 ], [ 't_sgn_cua_sat_keo_c', 2 ] ],
            '+': 't_door_c', '.': FLOOR_PARAM, 't': FLOOR_PARAM, 'c': FLOOR_PARAM,
            'C': FLOOR_PARAM, 'S': FLOOR_PARAM, 'O': FLOOR_PARAM, 'K': 't_concrete_roof',
            'A': FLOOR_PARAM, 'F': FLOOR_PARAM, 'T': FLOOR_PARAM, 'b': FLOOR_PARAM,
            'r': FLOOR_PARAM, 'm': FLOOR_PARAM, 'k': FLOOR_PARAM, 'd': FLOOR_PARAM,
            's': FLOOR_PARAM, 'p': FLOOR_PARAM,
            'G': FLOOR_PARAM, 'L': FLOOR_PARAM, 'V': FLOOR_PARAM, 'v': FLOOR_PARAM,
            'g': FLOOR_PARAM, 'n': FLOOR_PARAM, 'Q': FLOOR_PARAM,
            'h': FLOOR_PARAM, 'i': FLOOR_PARAM, 'e': FLOOR_PARAM, 'f': FLOOR_PARAM, 'j': FLOOR_PARAM,
            'u': FLOOR_PARAM, 'x': FLOOR_PARAM, 'y': FLOOR_PARAM, 'z': FLOOR_PARAM, 'q': FLOOR_PARAM,
            'o': FLOOR_PARAM, 'a': FLOOR_PARAM, 'l': FLOOR_PARAM, 'B': FLOOR_PARAM,
            'P': 't_concrete_roof', 'M': 't_concrete_roof',
            '<': 't_stairs_up', '>': 't_stairs_down', '_': 't_concrete_roof', '=': 't_railing' },
        'furniture': {
            't': 'f_table', 'c': 'f_stool', 'C': 'f_counter', 'S': 'f_sink', 'O': 'f_oven',
            'K': 'f_standing_tank', 'A': 'f_sgn_ban_tho', 'F': 'f_fridge', 'T': 'f_toilet',
            'b': 'f_bed', 'r': 'f_rack', 'm': 'f_rack', 'k': 'f_counter', 'd': 'f_dresser',
            's': 'f_sofa', 'p': 'f_rack',
            # G21 shophouse interior
            'G': 'f_sgn_ban_tho_than_tai', 'L': 'f_sgn_lu_nuoc', 'V': 'f_sgn_tivi_crt', 'v': 'f_sgn_vong',
            'P': 'f_sgn_chau_kieng', 'M': 'f_air_conditioner',
            # B8h businesses
            'g': 'f_sgn_quay_vang', 'n': 'f_sgn_may_net', 'Q': 'f_sgn_dan_karaoke',
            # P1 businesses
            'h': 'f_barber_chair', 'i': 'f_bigmirror', 'e': 'f_sgn_may_may', 'f': 'f_rack', 'j': 'f_workbench',
            'u': 'f_sgn_tu_thuoc_bac', 'x': 'f_safe_l', 'y': 'f_displaycase', 'z': 'f_sgn_may_photo', 'q': 'f_rack',
            'o': 'f_oven', 'a': 'f_rack', 'l': 'f_sgn_bep_nuong', 'B': 'f_crate_c' },
        'liquids': { 'K': { 'liquid': 'water', 'amount': [ 120, 720 ] },
                     'L': { 'liquid': 'water', 'amount': [ 40, 240 ] } },
        'items': {
            'G': { 'item': 'sgn_pagoda', 'chance': 60 },
            'g': { 'item': 'sgn_gold_shop', 'chance': 70, 'repeat': [ 1, 3 ] },
            'n': { 'item': 'sgn_net_cafe', 'chance': 35 },
            'Q': { 'item': 'sgn_karaoke', 'chance': 60, 'repeat': [ 1, 2 ] },
            'h': { 'item': 'sgn_barber', 'chance': 25 },
            'f': { 'item': 'sgn_tailor', 'chance': 60, 'repeat': [ 1, 3 ] },
            'e': { 'item': 'sgn_tailor', 'chance': 30 },
            'j': { 'item': 'sgn_electronics_repair', 'chance': 60, 'repeat': [ 1, 2 ] },
            'u': { 'item': 'sgn_herbalist', 'chance': 70, 'repeat': [ 1, 3 ] },
            'x': { 'item': 'sgn_pawn', 'chance': 80, 'repeat': [ 1, 3 ] },
            'y': { 'item': 'sgn_pawn', 'chance': 50, 'repeat': [ 1, 2 ] },
            'q': { 'item': 'sgn_photocopy', 'chance': 60, 'repeat': [ 1, 2 ] },
            'a': { 'item': 'sgn_bakery', 'chance': 60, 'repeat': [ 1, 3 ] },
            'B': { 'item': 'sgn_nhau', 'chance': 60, 'repeat': [ 1, 3 ] },
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
        # G28: strays in the back alley behind the row
        obj['place_monster'] = [ { 'group': 'sgn_GROUP_SAIGON_ANIMALS', 'x': [ 0, 23 ], 'y': [ 20, 23 ], 'chance': 30 } ]
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
