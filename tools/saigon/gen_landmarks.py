#!/usr/bin/env python3
"""Generate Saigon landmark buildings for the saigon_2000s mod (unit B8h-2).

CONTENT_BIBLE.md §3 landmarks with their own overmap tile (the shophouse businesses are
nhà ống lot variants in gen_nha_ong.py):
  sgn_nha_tho   Catholic church: pink stucco nave, forecourt with a statue, pews, altar
  sgn_ubnd      ward People's Committee office: yard with flagpole and loudspeaker,
                reception counter, offices, meeting room
  sgn_truong    primary school: schoolyard with a bàng tree and flagpole, two classrooms
Each is one OMT at z0 (local frame: street to the north) with its roof at z1.  Layouts
are built from rectangles so every row is exactly 24 wide.

Run from the repo root:  python3 tools/saigon/gen_landmarks.py
"""
import json
import os

ROOT = os.path.join( os.path.dirname( __file__ ), '..', '..', 'data', 'mods', 'saigon_2000s' )
CLEARING = [ 'ERASE_FURNITURE_BEFORE_PLACING_TERRAIN', 'ERASE_TRAP_BEFORE_PLACING_TERRAIN',
             'ALLOW_TERRAIN_UNDER_ITEMS' ]
# characters that are inside a building and so get a roof at z1
INDOOR = set( '#H.+DwpazCdcxtB' )


class Grid:
    def __init__( self, fill=',' ):
        self.g = [ [ fill ] * 24 for _ in range( 24 ) ]

    def rect( self, x0, y0, x1, y1, ch ):
        for y in range( y0, y1 + 1 ):
            for x in range( x0, x1 + 1 ):
                self.g[y][x] = ch

    def box( self, x0, y0, x1, y1, wall, floor ):
        self.rect( x0, y0, x1, y1, wall )
        self.rect( x0 + 1, y0 + 1, x1 - 1, y1 - 1, floor )

    def at( self, x, y, ch ):
        self.g[y][x] = ch

    def frontage( self, gate ):
        """Sidewalk rows 0-1, breeze-block fence round the lot with a gate on the street."""
        self.rect( 0, 0, 23, 1, 'S' )
        self.rect( 0, 2, 23, 2, 'o' )
        self.rect( 0, 2, 0, 23, 'o' )
        self.rect( 23, 2, 23, 23, 'o' )
        self.rect( gate[0], 2, gate[1], 2, ',' )

    def rows( self ):
        return [ ''.join( r ) for r in self.g ]


def church():
    g = Grid()
    g.frontage( ( 10, 13 ) )
    for x, y in ( ( 2, 3 ), ( 3, 3 ), ( 20, 3 ), ( 21, 3 ), ( 2, 5 ), ( 21, 5 ) ):
        g.at( x, y, 'f' )
    g.at( 11, 4, 'Z' )                                  # statue of Mary in the forecourt
    g.box( 2, 6, 21, 21, 'H', '.' )                     # pink stucco nave
    g.at( 11, 6, 'D' )
    g.at( 12, 6, 'D' )
    for y in ( 9, 12, 15, 18 ):
        g.at( 2, y, 'w' )
        g.at( 21, y, 'w' )
    for y in range( 9, 18, 2 ):                         # pews either side of the aisle
        g.rect( 4, y, 9, y, 'p' )
        g.rect( 14, y, 19, y, 'p' )
    g.rect( 10, 19, 13, 19, 'a' )                       # altar
    g.at( 11, 20, 'z' )                                 # crucifix
    g.at( 20, 21, '+' )                                 # sacristy door to the back yard
    return g.rows()


def ubnd():
    g = Grid()
    g.frontage( ( 9, 14 ) )
    g.at( 5, 4, 'F' )                                   # flagpole
    g.at( 18, 4, 'L' )                                  # ward loudspeaker
    for x in ( 3, 4, 19, 20 ):
        g.at( x, 6, 'f' )
    g.box( 2, 7, 21, 21, '#', '.' )
    g.at( 11, 7, 'D' )
    g.at( 12, 7, 'D' )
    for x in ( 5, 8, 15, 18 ):
        g.at( x, 7, 'w' )
    g.rect( 5, 10, 18, 10, 'C' )                        # reception counter with a pass-through
    g.rect( 11, 10, 12, 10, '.' )
    g.rect( 2, 13, 21, 13, '#' )                        # offices behind
    g.at( 6, 13, '+' )
    g.at( 17, 13, '+' )
    g.rect( 11, 13, 11, 21, '#' )
    for x, y in ( ( 4, 15 ), ( 8, 15 ), ( 4, 18 ), ( 8, 18 ) ):
        g.at( x, y, 'd' )
        g.at( x, y + 1, 'c' )
    g.rect( 3, 20, 4, 20, 'x' )                         # filing cabinets
    g.rect( 14, 16, 18, 17, 't' )                       # meeting table
    for x in ( 14, 16, 18 ):
        g.at( x, 15, 'c' )
        g.at( x, 18, 'c' )
    g.at( 5, 21, '+' )
    return g.rows()


def school():
    g = Grid()
    g.frontage( ( 10, 13 ) )
    g.at( 5, 5, 'T' )                                   # the schoolyard bàng tree
    g.at( 18, 4, 'F' )
    g.box( 2, 9, 21, 21, '#', '.' )
    g.at( 11, 9, 'D' )
    g.at( 12, 9, 'D' )
    for x in ( 4, 7, 16, 19 ):
        g.at( x, 9, 'w' )
    g.rect( 2, 11, 21, 11, '#' )                        # corridor y10, classrooms behind
    g.at( 6, 11, '+' )
    g.at( 17, 11, '+' )
    g.rect( 11, 11, 12, 21, '#' )
    for ox in ( 3, 13 ):                                # two classrooms
        for y in ( 13, 15, 17 ):
            for x in ( ox + 1, ox + 3, ox + 5 ):
                g.at( x, y, 'd' )
                g.at( x, y + 1, 'c' )
        g.at( ox + 3, 19, 't' )                         # teacher's desk
        g.rect( ox + 2, 20, ox + 5, 20, 'B' )           # blackboard on the back wall
    return g.rows()


def roof( rows ):
    return [ ''.join( '_' if ch in INDOOR else ' ' for ch in r ) for r in rows ]


def palette():
    return {
        'type': 'palette', 'id': 'sgn_landmark',
        'terrain': {
            'S': 't_sidewalk', ',': 't_concrete', 'o': 't_sgn_tuong_bong_gio', 'g': 't_grass', 'f': 't_grass',
            '#': 't_brick_wall', 'H': 't_sgn_tuong_hong', '.': 't_sgn_gach_men', '+': 't_door_c', 'D': 't_door_c',
            'w': 't_window_domestic', 'T': 't_sgn_tree_bang',
            'F': 't_concrete', 'L': 't_concrete', 'Z': 't_concrete',
            'p': 't_sgn_gach_men', 'a': 't_sgn_gach_men', 'z': 't_sgn_gach_men', 'C': 't_sgn_gach_men',
            'd': 't_sgn_gach_men', 'c': 't_sgn_gach_men', 'x': 't_sgn_gach_men', 't': 't_sgn_gach_men',
            'B': 't_sgn_gach_men' },
        'furniture': {
            'f': 'f_sgn_van_tho', 'F': 'f_flagpole', 'L': 'f_sgn_loa_phuong', 'Z': 'f_statue', 'p': 'f_bench',
            'a': 'f_table', 'z': 'f_statue', 'C': 'f_counter', 'd': 'f_desk', 'c': 'f_chair', 'x': 'f_filing_cabinet',
            't': 'f_table', 'B': 'f_sgn_bang_den' } }


def mapgens():
    out = []
    for oter, rows, roof_ter, items, monsters in (
        ( 'sgn_nha_tho', church(), 't_sgn_mai_ngoi',
          { 'a': { 'item': 'sgn_church', 'chance': 80, 'repeat': [ 1, 3 ] },
            'p': { 'item': 'sgn_church', 'chance': 8 } },
          [ { 'group': 'sgn_GROUP_ZOMBIE_DORMANT', 'x': [ 4, 19 ], 'y': [ 8, 18 ], 'chance': 70, 'repeat': [ 2, 5 ] },
            { 'group': 'sgn_GROUP_SAIGON_AWAKE', 'x': [ 3, 20 ], 'y': [ 3, 5 ], 'chance': 40 } ] ),
        ( 'sgn_ubnd', ubnd(), 't_concrete_roof',
          { 'C': { 'item': 'sgn_ward_office', 'chance': 50 }, 'd': { 'item': 'sgn_ward_office', 'chance': 50 },
            'x': { 'item': 'sgn_ward_office', 'chance': 70, 'repeat': [ 1, 3 ] } },
          [ { 'group': 'sgn_GROUP_SAIGON_AWAKE', 'x': [ 3, 20 ], 'y': [ 8, 20 ], 'chance': 50, 'repeat': [ 1, 2 ] } ] ),
        ( 'sgn_truong', school(), 't_sgn_mai_ngoi',
          { 'd': { 'item': 'sgn_school', 'chance': 25 }, 't': { 'item': 'sgn_school', 'chance': 60, 'repeat': [ 1, 2 ] } },
          [ { 'group': 'sgn_GROUP_ZOMBIE_DORMANT', 'x': [ 4, 19 ], 'y': [ 12, 18 ], 'chance': 50, 'repeat': [ 1, 3 ] },
            { 'group': 'sgn_GROUP_SAIGON_ANIMALS', 'x': [ 3, 20 ], 'y': [ 3, 8 ], 'chance': 30 } ] ) ):
        out.append( { 'type': 'mapgen', 'om_terrain': [ oter ],
                      'object': { 'fill_ter': 't_concrete', 'rows': rows, 'palettes': [ 'sgn_landmark' ],
                                  'items': items, 'place_monster': monsters, 'flags': CLEARING } } )
        out.append( { 'type': 'mapgen', 'om_terrain': [ oter + '_roof' ],
                      'object': { 'fill_ter': 't_open_air', 'rows': roof( rows ), 'terrain': { '_': roof_ter } } } )
    return out


NAMES = { 'sgn_nha_tho': ( 'nhà thờ', 'light_red' ), 'sgn_ubnd': ( 'UBND phường', 'yellow' ),
          'sgn_truong': ( 'trường học', 'light_blue' ) }


def overmap():
    out = []
    for oter, ( name, colour ) in NAMES.items():
        out.append( { 'type': 'overmap_terrain', 'id': oter, 'copy-from': 'generic_city_building',
                      'name': name, 'sym': '^', 'color': colour, 'looks_like': 'house' } )
        out.append( { 'type': 'overmap_terrain', 'id': oter + '_roof', 'copy-from': 'generic_city_building_roof',
                      'name': name + ' roof', 'sym': '#', 'color': colour, 'looks_like': 'house' } )
        out.append( { 'type': 'city_building', 'id': oter + '_1', 'locations': [ 'land' ], 'flags': [ 'SAIGON' ],
                      'overmaps': [ { 'point': [ 0, 0, 0 ], 'overmap': oter + '_north' },
                                    { 'point': [ 0, 0, 1 ], 'overmap': oter + '_roof_north' } ] } )
    return out


def main():
    mg = os.path.join( ROOT, 'mapgen', 'landmarks' )
    os.makedirs( mg, exist_ok=True )
    with open( os.path.join( mg, 'landmarks.json' ), 'w' ) as f:
        json.dump( [ palette() ] + mapgens(), f, ensure_ascii=False, indent=2 )
    with open( os.path.join( ROOT, 'overmap', 'landmarks.json' ), 'w' ) as f:
        json.dump( overmap(), f, ensure_ascii=False, indent=2 )
    for name, rows in ( ( 'church', church() ), ( 'ubnd', ubnd() ), ( 'school', school() ) ):
        assert all( len( r ) == 24 for r in rows ) and len( rows ) == 24, name
    print( 'wrote mapgen/landmarks/landmarks.json and overmap/landmarks.json' )


if __name__ == '__main__':
    main()
