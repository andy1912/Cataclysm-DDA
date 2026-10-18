#!/usr/bin/env python3
"""Generate the kênh (city canal) for the saigon_2000s mod (unit B8f).

Design: doc/saigon/analysis/d2_r3.md §4.d.  The river generator cannot draw a 10-30 m
canal, so canals are authored inside a city building: three canal cells in a row
(sgn_kenh_row_1), each a 24x24 OMT with the channel running local east-west so the
cells join into one continuous canal.  Local frame of a cell:
  rows 0-1    concrete embankment walk (north bank)
  rows 2-6    three tin-roofed shacks facing the walk, windows onto the water
  row  7      stone embankment edge (bờ kè), with plank landings between shacks
  rows 8-15   channel: 8 tiles of wadeable murky water (t_water_murky, SHALLOW_WATER)
  rows 16-23  the south bank, mirrored
Small boats are moored on the water as static vehicles.  Water exists at z0 only; the
shacks get tin roofs at z1 (sgn_kenh_roof).  Hẻm alleys may open onto canal cells.

Run from the repo root:  python3 tools/saigon/gen_kenh.py
"""
import json
import os

ROOT = os.path.join( os.path.dirname( __file__ ), '..', '..', 'data', 'mods', 'saigon_2000s' )
CLEARING = [ 'ERASE_FURNITURE_BEFORE_PLACING_TERRAIN', 'ERASE_TRAP_BEFORE_PLACING_TERRAIN',
             'ALLOW_TERRAIN_UNDER_ITEMS' ]

NORTH_BANK = [
    'aaaaaaaaaaaaaaaaaaaaaaaa',
    'aaaaaaaaaaaaaaaaaaaaaaaa',
    '##+###aa##+###aa##+###aa',
    '#b..A#aa#bk.A#aa#b.kA#aa',
    '#k...#aa#....#aa#.t.c#aa',
    '#tc..#aa#tc.b#aa#....#aa',
    '##o###aa###o##aa##o###aa',
    'eeeeeeddeeeeeeddeeeeeedd',
]
CHANNEL = [ '~' * 24 ] * 8
ROWS = NORTH_BANK + CHANNEL + NORTH_BANK[::-1]
HOUSE = set( '#b.Aktc+o' )


def roof_rows():
    return [ ''.join( '_' if ch in HOUSE else ' ' for ch in row ) for row in ROWS ]


def palette():
    return {
        'type': 'palette', 'id': 'sgn_kenh',
        'terrain': {
            'a': 't_sgn_hem_xi_mang', '#': 't_wall_wood', '.': 't_floor', '+': 't_door_c', 'o': 't_window_domestic',
            'e': 't_sgn_bo_ke', 'd': 't_floor', '~': 't_water_murky',
            'b': 't_floor', 'k': 't_floor', 'A': 't_floor', 't': 't_floor', 'c': 't_floor',
            '_': 't_sgn_mai_ton' },
        'furniture': { 'b': 'f_bed', 'k': 'f_counter', 'A': 'f_sgn_ban_tho', 't': 'f_table', 'c': 'f_stool' },
        'items': {
            'k': { 'item': 'sgn_shophouse_kitchen', 'chance': 40 },
            'b': { 'item': 'sgn_shophouse_living', 'chance': 30 },
            'A': { 'item': 'sgn_pagoda', 'chance': 30 },
            't': { 'item': 'sgn_cho_stall_meat_fish', 'chance': 20 },
            # W2: canal people kept a hoe or a dao rựa for the bank garden, and the boys a slingshot
            'c': { 'item': 'sgn_loot_country_tools', 'chance': 20 } },
        # water spinach gathered from the canal, left on the landings
        'item': { 'd': { 'item': 'sgn_rau_muong', 'chance': 25 } } }


def mapgen():
    return [
        { 'type': 'mapgen', 'om_terrain': [ 'sgn_kenh' ],
          'object': { 'fill_ter': 't_sgn_hem_xi_mang', 'rows': ROWS, 'palettes': [ 'sgn_kenh' ], 'flags': CLEARING,
                      # d2_r3 §4.d: boats moored on the water, wholly on water tiles
                      'place_vehicles': [ { 'vehicle': 'sgn_vg_canal_moored', 'x': 10, 'y': 11, 'rotation': 0,
                                            'chance': 45, 'status': 0 } ],
                      'place_monster': [
                          { 'group': 'sgn_GROUP_SAIGON_AWAKE', 'x': [ 0, 23 ], 'y': [ 0, 1 ], 'chance': 30 },
                          { 'group': 'sgn_GROUP_ZOMBIE_DORMANT', 'x': [ 0, 23 ], 'y': [ 22, 23 ], 'chance': 50,
                            'repeat': [ 1, 2 ] },
                          { 'group': 'sgn_GROUP_SAIGON_ANIMALS', 'x': [ 0, 23 ], 'y': [ 0, 23 ], 'chance': 30 } ] } },
        { 'type': 'mapgen', 'om_terrain': [ 'sgn_kenh_roof' ],
          'object': { 'fill_ter': 't_open_air', 'rows': roof_rows(), 'palettes': [ 'sgn_kenh' ] } },
    ]


def overmap():
    return [
        { 'type': 'overmap_terrain', 'id': 'sgn_kenh', 'copy-from': 'generic_city_building',
          'name': 'kênh', 'sym': '~', 'color': 'light_green', 'looks_like': 'river_center' },
        { 'type': 'overmap_terrain', 'id': 'sgn_kenh_roof', 'copy-from': 'generic_city_building_roof',
          'name': 'kênh shacks, rooftops', 'sym': '~', 'color': 'green', 'looks_like': 'river_center' },
        { 'type': 'vehicle_group', 'id': 'sgn_vg_canal_moored',
          '//': 'Small boats moored on a city canal (static, d2_r3 §4.d).',
          'vehicles': [ [ 'sgn_veh_xuong', 80 ], [ 'sgn_veh_ghe', 20 ] ] },
        { 'type': 'city_building', 'id': 'sgn_kenh_row_1', 'locations': [ 'land' ], 'flags': [ 'SAIGON' ],
          'overmaps': [ { 'point': [ x, 0, z ], 'overmap': ( 'sgn_kenh_north' if z == 0 else 'sgn_kenh_roof_north' ) }
                        for x in range( 3 ) for z in ( 0, 1 ) ] },
    ]


def main():
    mg = os.path.join( ROOT, 'mapgen', 'kenh' )
    os.makedirs( mg, exist_ok=True )
    with open( os.path.join( mg, 'kenh.json' ), 'w' ) as f:
        json.dump( [ palette() ] + mapgen(), f, ensure_ascii=False, indent=2 )
    with open( os.path.join( ROOT, 'overmap', 'kenh.json' ), 'w' ) as f:
        json.dump( overmap(), f, ensure_ascii=False, indent=2 )
    print( 'wrote mapgen/kenh/kenh.json and overmap/kenh.json' )


if __name__ == '__main__':
    main()
