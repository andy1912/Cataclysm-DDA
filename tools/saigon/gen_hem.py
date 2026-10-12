#!/usr/bin/env python3
"""Generate the hẻm (alley block) mapgen for the saigon_2000s mod.

Design: doc/saigon/analysis/d2_r3.md §4.b (critic PASS).  One 24x24 OMT:
  - a 2-tile alley spine: x = 11-12 over all y and y = 11-12 over all x;
  - four 11x11 quadrants of tiny homes, a hẻm café and a shrine (miếu), reached by
    1-tile sub-alleys.  One quadrant is authored (NW) and mirrored for NE/SW/SE, so
    every quadrant opens onto both spine arms it borders;
  - the arm ends are the only edge ports (rotation-invariant).  A port stays open when
    the neighbour is another hẻm block or a road, otherwise a wall caps it.
Deferred from the design: the closed_arm dead-end parameter (capped ports and
sub-alley spurs already make dead ends).

Run from the repo root:  python3 tools/saigon/gen_hem.py
"""
import json
import os

ROOT = os.path.join( os.path.dirname( __file__ ), '..', '..', 'data', 'mods', 'saigon_2000s' )
CLEARING = [ 'ERASE_FURNITURE_BEFORE_PLACING_TERRAIN', 'ERASE_TRAP_BEFORE_PLACING_TERRAIN',
             'ALLOW_TERRAIN_UNDER_ITEMS' ]

# NW quadrant variants (x 0-10, y 0-10).  Exits: east via the y=5 sub-alley at x=10,
# south via the x=5 sub-alley at y=10.  '#' wall, '.' floor, 'a' alley, '+' door,
# ',' outdoor courtyard, b bed, k kitchen counter, A ancestor altar, t table,
# T/C outdoor table/stool, S shrine altar, l laundry line over the alley,
# o breeze-block wall (tường bông gió).
NW = {
    'homes': [
        '###########',
        '#bkA###b.A#',
        '#...###...#',
        '#t..###.kt#',
        '##+#####+##',
        '#aalaaaalaa',
        '##+##a##+##',
        '#...#a#...#',
        '#bA.#l#tA.#',
        '#kt.#a#.bk#',
        '#####a#####' ],
    'cafe_shrine': [
        '###########',
        '#bkA#TC,TCo',
        '#...#,,,,,o',
        '#t..#TC,TCo',
        '##+##,,,,,#',
        '#aaaaaaaaaa',
        '##+##a#####',
        '#...#a#.S.#',
        '#bA.#a+...#',
        '#kt.#a#...#',
        '#####a#####' ],
}


def mirror_x( rows ):
    return [ r[::-1] for r in rows ]


def mirror_y( rows ):
    return rows[::-1]


QUADRANTS = {
    'nw': ( 0, 0, lambda r: r ),
    'ne': ( 13, 0, mirror_x ),
    'sw': ( 0, 13, mirror_y ),
    'se': ( 13, 13, lambda r: mirror_x( mirror_y( r ) ) ),
}


def pad( rows, size ):
    out = [ r.ljust( size ) for r in rows ]
    return out + [ ' ' * size ] * ( size - len( out ) )


def nested( nid, rows, size ):
    return { 'type': 'mapgen', 'nested_mapgen_id': nid,
             'object': { 'mapgensize': [ size, size ], 'palettes': [ 'sgn_hem' ],
                         'rows': pad( rows, size ), 'flags': CLEARING } }


FLOOR_PARAM = { 'param': 'floor', 'fallback': 't_thconc_floor' }


def palette():
    return {
        'type': 'palette', 'id': 'sgn_hem',
        # G21: one floor per quadrant chunk (scope nest)
        'parameters': { 'floor': { 'type': 'ter_str_id', 'scope': 'nest', 'default': { 'distribution': [
            [ 't_sgn_gach_bong_1', 1 ], [ 't_sgn_gach_bong_3', 1 ], [ 't_sgn_gach_men', 2 ], [ 't_thconc_floor', 3 ] ] } } },
        'terrain': {
            '_': 't_concrete_roof', '#': 't_brick_wall', '.': FLOOR_PARAM, 'a': 't_sgn_hem_xi_mang',
            # G22: most hẻm homes close their doorway with a folding iron gate
            '+': [ [ 't_sgn_cua_sat_keo_c', 2 ], [ 't_door_c', 1 ] ],
            ',': 't_concrete', 'b': FLOOR_PARAM, 'k': FLOOR_PARAM, 'A': FLOOR_PARAM,
            't': FLOOR_PARAM, 'T': 't_concrete', 'C': 't_concrete', 'S': FLOOR_PARAM,
            'o': 't_sgn_tuong_bong_gio', 'l': 't_sgn_hem_xi_mang' },
        'furniture': {
            'b': 'f_bed', 'k': 'f_counter', 'A': 'f_sgn_ban_tho', 't': 'f_table', 'T': 'f_sgn_ban_inox',
            'C': 'f_stool', 'S': 'f_sgn_ban_tho', 'l': 'f_sgn_day_phoi' },
        'items': {
            'k': { 'item': 'sgn_shophouse_kitchen', 'chance': 50 },
            'b': { 'item': 'sgn_shophouse_living', 'chance': 35 },
            'A': { 'item': 'sgn_pagoda', 'chance': 25 },
            'T': { 'item': 'sgn_cafe', 'chance': 40 },
            'S': { 'item': 'sgn_pagoda', 'chance': 70, 'repeat': [ 1, 3 ] } } }


PORTS = {
    # direction: (x, y, rows of the 2x2 cap chunk)
    'north': ( 11, 0, [ '##', '  ' ] ),
    'south': ( 11, 22, [ '  ', '##' ] ),
    'west': ( 0, 11, [ '# ', '# ' ] ),
    'east': ( 22, 11, [ ' #', ' #' ] ),
}
OPEN_NEIGHBOURS = [ { 'om_terrain': 'sgn_hem', 'om_terrain_match_type': 'PREFIX' },
                    { 'om_terrain': 'road', 'om_terrain_match_type': 'TYPE' },
                    # B8f: a canal cell presents its embankment walk (d2_r3 §4.b, D8)
                    { 'om_terrain': 'sgn_kenh', 'om_terrain_match_type': 'TYPE' } ]


OUTDOOR = set( 'a,TCl ' )


def roof_of( rows ):
    return [ ''.join( ' ' if c in OUTDOOR else '_' for c in r ) for r in rows ]


def stack( nid, layout, roof ):
    """z0 layout and the matching z1 roof, chosen together once per OMT column."""
    return { 'type': 'mapgen', 'nested_mapgen_id': nid,
             'object': { 'mapgensize': [ 11, 11 ], 'flags': CLEARING, 'place_nested': [
                 { 'chunks': [ layout ], 'x': 0, 'y': 0, 'check_z': [ 0 ] },
                 { 'chunks': [ roof ], 'x': 0, 'y': 0, 'check_z': [ 1 ] } ] } }


def params():
    return { 'type': 'palette', 'id': 'sgn_hem_params', 'parameters': {
        'q_' + q: { 'type': 'nested_mapgen_id', 'scope': 'omt_stack',
                    'default': { 'distribution': [ [ 'sgn_hem_stack_%s_homes' % q, 3 ],
                                                   [ 'sgn_hem_stack_%s_cafe_shrine' % q, 1 ] ] } }
        for q in QUADRANTS } }


def roof_mapgen():
    nests = [ { 'chunks': [ { 'param': 'q_' + q, 'fallback': 'sgn_hem_stack_%s_homes' % q } ], 'x': x, 'y': y }
              for q, ( x, y, _ ) in QUADRANTS.items() ]
    return { 'type': 'mapgen', 'om_terrain': [ 'sgn_hem_block_roof' ],
             'object': { 'fill_ter': 't_open_air', 'palettes': [ 'sgn_hem', 'sgn_hem_params' ],
                         'place_nested': nests } }


def block_mapgen():
    rows = []
    for y in range( 24 ):
        if y in ( 11, 12 ):
            rows.append( 'a' * 24 )
        else:
            rows.append( ' ' * 11 + 'aa' + ' ' * 11 )
    nests = []
    for q, ( x, y, _ ) in QUADRANTS.items():
        nests.append( { 'chunks': [ { 'param': 'q_' + q, 'fallback': 'sgn_hem_stack_%s_homes' % q } ],
                        'x': x, 'y': y } )
    for d, ( x, y, _ ) in PORTS.items():
        nests.append( { 'chunks': [ 'null' ], 'else_chunks': [ 'sgn_hem_cap_' + d ], 'x': x, 'y': y,
                        'neighbors': { d: OPEN_NEIGHBOURS } } )
    return { 'type': 'mapgen', 'om_terrain': [ 'sgn_hem_block' ],
             'object': { 'fill_ter': 't_concrete', 'rows': rows, 'palettes': [ 'sgn_hem', 'sgn_hem_params' ],
                         'place_nested': nests,
                         # d3_r3 §6.2 shophouse-like tier: a few awake, more dormant on the spine
                         'place_monster': [
                             { 'group': 'sgn_GROUP_SAIGON_AWAKE', 'x': [ 11, 12 ], 'y': [ 0, 23 ], 'chance': 60,
                               'repeat': [ 1, 2 ] },
                             { 'group': 'sgn_GROUP_ZOMBIE_DORMANT', 'x': [ 0, 23 ], 'y': [ 11, 12 ], 'chance': 80,
                               'repeat': [ 2, 5 ] },
                             # G28: a stray dog, cat, chicken or rat in the alley now and then
                             { 'group': 'sgn_GROUP_SAIGON_ANIMALS', 'x': [ 0, 23 ], 'y': [ 11, 12 ], 'chance': 35 } ] } }


def overmap():
    return [
        { 'type': 'overmap_terrain', 'id': 'sgn_hem_block', 'copy-from': 'generic_city_building',
          'name': 'hẻm', 'sym': '%', 'color': 'brown', 'looks_like': 'house' },
        { 'type': 'overmap_terrain', 'id': 'sgn_hem_block_roof', 'copy-from': 'generic_city_building_roof',
          'name': 'hẻm rooftops', 'sym': '%', 'color': 'brown', 'looks_like': 'house' },
        { 'type': 'city_building', 'id': 'sgn_hem_block_1', 'locations': [ 'land' ], 'flags': [ 'SAIGON' ],
          'overmaps': [ { 'point': [ 0, 0, 0 ], 'overmap': 'sgn_hem_block_north' },
                        { 'point': [ 0, 0, 1 ], 'overmap': 'sgn_hem_block_roof_north' } ] } ]


def main():
    out = [ palette(), params() ]
    for q, ( _, _, fn ) in QUADRANTS.items():
        for v, rows in NW.items():
            assert all( len( r ) == 11 for r in rows ) and len( rows ) == 11, v
            layout = 'sgn_hem_q_%s_%s' % ( q, v )
            out.append( nested( layout, fn( rows ), 11 ) )
            out.append( nested( layout + '_roof', roof_of( fn( rows ) ), 11 ) )
            out.append( stack( 'sgn_hem_stack_%s_%s' % ( q, v ), layout, layout + '_roof' ) )
    for d, ( _, _, rows ) in PORTS.items():
        out.append( nested( 'sgn_hem_cap_' + d, rows, 2 ) )
    out.append( block_mapgen() )
    out.append( roof_mapgen() )
    mg = os.path.join( ROOT, 'mapgen', 'hem' )
    os.makedirs( mg, exist_ok=True )
    with open( os.path.join( mg, 'hem_block.json' ), 'w' ) as f:
        json.dump( out, f, ensure_ascii=False, indent=2 )
    with open( os.path.join( ROOT, 'overmap', 'hem.json' ), 'w' ) as f:
        json.dump( overmap(), f, ensure_ascii=False, indent=2 )


if __name__ == '__main__':
    main()
