#!/usr/bin/env python3
"""Generate everyday Saigon places that every city has more than one of (unit P2):
the petrol station, the Co.op Mart supermarket, the district hospital, the ward police
station, the cemetery, the bookstore and the motorbike dealer.

Built with the landmark generator's tools (gen_saigon_landmarks.py: Level grids, roofs,
vehicles, animals, the shared sgn_lm palette).  Each place adds its own symbols as mapgen
object keys, which override the palette.  Unlike the landmarks these are not unique: a city
can have several.  Local frame: the street is to the north.

Run from the repo root:  python3 tools/saigon/gen_places.py
"""
import json
import os
import sys

sys.path.insert( 0, os.path.dirname( __file__ ) )
import gen_saigon_landmarks as lm  # noqa: E402
from gen_saigon_landmarks import Level, roof_over  # noqa: E402

INDOOR = lm.INDOOR | set( '(@$);' )


# --- cây xăng ---------------------------------------------------------------------------------
def cay_xang():
    # a petrol station: four pumps under a canopy on the forecourt, the kiosk behind
    z0 = Level( 1, 1, ',' )
    z0.rect( 0, 0, 23, 1, 'S' )
    z0.rect( 3, 4, 20, 11, ':' )                       # under the canopy
    for x in ( 3, 20 ):
        for y in ( 4, 11 ):
            z0.at( x, y, 'P' )
    for x in ( 6, 10, 14, 18 ):
        z0.at( x, 8, '1' )                             # the pumps
    z0.box( 4, 14, 19, 21, 'C', '.' )                  # the kiosk
    for x in ( 7, 8 ):
        z0.at( x, 14, 'D' )
    z0.rect( 6, 17, 11, 17, 'j' )                      # the till
    for y in ( 16, 19 ):
        z0.at( 15, y, '$' )
        z0.at( 17, y, '$' )
    z0.vehicle( 2, 13, 'sgn_vg_sidewalk_parked', 90, 60 )
    z0.vehicle( 21, 13, 'sgn_vg_sidewalk_parked', 90, 40 )
    z1 = roof_over( z0, INDOOR )
    return { 0: z0, 1: z1 }


# --- Co.op Mart -------------------------------------------------------------------------------
def coopmart():
    # the supermarket that came in the late nineties: tills at the front, aisles of dry
    # goods and household things, a wall of fridges at the back
    z0 = Level( 2, 2, ',' )
    z0.rect( 0, 0, 47, 1, 'S' )
    z0.box( 2, 4, 45, 45, 'C', '.' )
    for x in range( 6, 42, 3 ):
        z0.at( x, 4, 'W' )
    for x in range( 21, 27 ):
        z0.at( x, 4, 'D' )
    for x in range( 8, 41, 5 ):                        # the tills
        z0.rect( x, 9, x + 1, 9, 'j' )
    for i, y in enumerate( range( 14, 40, 4 ) ):       # aisles: food on the left, goods on the right
        z0.rect( 5, y, 22, y, '(' )
        z0.rect( 26, y, 42, y, '@' )
    z0.rect( 4, 43, 43, 43, '$' )                      # the fridges
    z0.at( 44, 30, '+' )                               # stock room door
    z1 = roof_over( z0, INDOOR )
    return { 0: z0, 1: z1 }


# --- Bệnh viện quận ---------------------------------------------------------------------------
def benh_vien():
    # the district hospital: a waiting hall with benches and a registration desk, wards of
    # beds down both sides, a pharmacy, an operating room; more wards upstairs
    z0 = Level( 2, 2, ',' )
    z0.rect( 0, 0, 47, 1, 'S' )
    z0.rect( 20, 2, 27, 5, ',' )                       # ambulance bay
    z0.box( 2, 6, 45, 45, 'C', '.' )
    for x in range( 21, 27 ):
        z0.at( x, 6, 'D' )
    z0.rect( 18, 10, 29, 10, 'j' )                     # registration desk
    for y in ( 14, 17, 20 ):
        z0.rect( 17, y, 30, y, 'b' )                   # waiting benches
    for wall, bed in ( ( 14, 4 ), ( 33, 43 ) ):        # a ward down each side, beds along the outer wall
        z0.rect( wall, 7, wall, 44, 'C' )
        z0.at( wall, 26, '+' )
        for y in range( 9, 43, 3 ):
            z0.at( bed, y, '(' )
    z0.box( 16, 32, 31, 44, 'C', '.' )                 # pharmacy and operating room
    z0.rect( 23, 33, 23, 43, 'C' )
    z0.at( 20, 32, '+' )
    z0.at( 27, 32, '+' )
    for y in range( 34, 43, 2 ):
        z0.at( 17, y, '$' )                            # pharmacy shelves
    z0.rect( 26, 37, 28, 38, 't' )                     # operating table
    z0.at( 24, 24, '<' )
    z1 = Level( 2, 2, ' ' )
    z1.box( 2, 6, 45, 45, 'C', '.' )
    for x in range( 4, 44, 3 ):
        z1.at( x, 6, 'w' )
    for x in range( 5, 43, 3 ):                        # an open ward upstairs
        for y in ( 9, 15, 30, 36, 42 ):
            z1.at( x, y, '(' )
    z1.at( 24, 24, '>' )
    z2 = roof_over( z1, INDOOR )
    return { 0: z0, 1: z1, 2: z2 }


# --- Đồn công an phường -----------------------------------------------------------------------
def cong_an():
    # the ward police station: a yellow front office with a desk, offices, the equipment
    # lockers and a barred holding cell at the back
    z0 = Level( 1, 1, ',' )
    z0.rect( 0, 0, 23, 1, 'S' )
    z0.box( 2, 5, 21, 21, '#', '.' )
    for x in ( 11, 12 ):
        z0.at( x, 5, '+' )
    z0.rect( 7, 8, 16, 8, 'j' )                        # front desk
    for x in ( 5, 9 ):
        z0.at( x, 11, 'd' )
        z0.at( x, 12, 'c' )
    z0.rect( 3, 14, 20, 14, '#' )
    z0.at( 7, 14, '+' )
    for x in range( 4, 11, 2 ):
        z0.at( x, 16, '$' )                            # lockers
    z0.rect( 13, 15, 20, 20, ')' )                     # the holding cell: bars
    z0.rect( 14, 16, 19, 19, '.' )
    z0.at( 16, 15, ';' )                               # cell door
    z1 = roof_over( z0, INDOOR )
    return { 0: z0, 1: z1 }


# --- Nghĩa trang ------------------------------------------------------------------------------
def nghia_trang():
    # a cemetery: a low wall, a gate with a small shrine, rows of tiled tombs between paths,
    # frangipani trees
    z0 = Level( 2, 2, 'g' )
    z0.rect( 0, 0, 47, 1, 'S' )
    z0.rect( 1, 2, 46, 2, '#' )
    z0.rect( 1, 2, 1, 46, '#' )
    z0.rect( 46, 2, 46, 46, '#' )
    z0.rect( 1, 46, 46, 46, '#' )
    z0.rect( 21, 2, 26, 2, 'o' )                       # the gate
    z0.rect( 22, 3, 25, 44, 'o' )
    z0.box( 30, 4, 36, 9, '#', 'n' )                   # the miếu shrine
    z0.at( 30, 6, '+' )
    z0.at( 34, 6, 'E' )
    for y in range( 6, 44, 4 ):                        # rows of tombs
        for x in range( 4, 20, 3 ):
            z0.at( x, y, '*' )
        for x in range( 28, 44, 3 ):
            if not ( 4 <= y <= 10 and x >= 28 ):
                z0.at( x, y, '*' )
    for x, y in ( ( 3, 4 ), ( 20, 24 ), ( 44, 20 ), ( 27, 40 ), ( 10, 44 ) ):
        z0.at( x, y, 'T' )
    z1 = roof_over( z0, INDOOR, 'l' )
    return { 0: z0, 1: z1 }


# --- Nhà sách ---------------------------------------------------------------------------------
def nha_sach():
    # a bookstore: shelves in rows, a stationery counter, glass front
    z0 = Level( 1, 1, ',' )
    z0.rect( 0, 0, 23, 1, 'S' )
    z0.box( 2, 4, 21, 21, 'C', '.' )
    for x in range( 4, 20, 3 ):
        z0.at( x, 4, 'W' )
    for x in ( 11, 12 ):
        z0.at( x, 4, 'D' )
    z0.rect( 4, 7, 9, 7, 'j' )
    for y in range( 10, 20, 3 ):
        z0.rect( 4, y, 9, y, '$' )
        z0.rect( 14, y, 19, y, '$' )
    z1 = roof_over( z0, INDOOR )
    return { 0: z0, 1: z1 }


# --- Cửa hàng xe máy --------------------------------------------------------------------------
def xe_may():
    # a motorbike dealer: new bikes lined up behind the glass, a counter, a service bay
    z0 = Level( 1, 1, ',' )
    z0.rect( 0, 0, 23, 1, 'S' )
    z0.box( 2, 4, 21, 21, 'C', ':' )
    for x in range( 3, 21 ):
        z0.at( x, 4, 'W' )
    for x in ( 11, 12 ):
        z0.at( x, 4, 'D' )
    for x in ( 5, 9, 14, 18 ):                         # the new bikes
        z0.vehicle( x, 9, 'sgn_vg_new_motorbikes', 90, 80 )
    z0.rect( 4, 14, 9, 14, 'j' )
    z0.rect( 13, 15, 20, 15, 'C' )                     # service bay
    z0.at( 16, 15, '+' )
    z0.rect( 14, 18, 19, 18, 'j' )
    z1 = roof_over( z0, INDOOR )
    return { 0: z0, 1: z1 }


PLACES = {
    # id: ( builder, w, h, name, colour, weight, pool, extra flags, local symbols )
    'sgn_pl_cay_xang': ( cay_xang, 1, 1, 'cây xăng', 'red', 10, 'shops', [],
                         { 'terrain': { '1': 't_gas_pump', '$': 't_sgn_gach_men' },
                           'furniture': { '$': 'f_rack' },
                           'gaspumps': { '1': { 'fuel': 'gasoline' } },
                           'items': { '$': { 'item': 'sgn_petrol_kiosk', 'chance': 60, 'repeat': [ 1, 2 ] } } } ),
    'sgn_pl_coopmart': ( coopmart, 2, 2, 'Co.op Mart', 'light_blue', 4, 'shops', [ 'CITY_UNIQUE' ],
                         { 'terrain': { '(': 't_sgn_gach_men', '@': 't_sgn_gach_men', '$': 't_sgn_gach_men' },
                           'furniture': { '(': 'f_rack', '@': 'f_rack', '$': 'f_display_fridge' },
                           'items': { '(': { 'item': 'sgn_supermarket_food', 'chance': 60, 'repeat': [ 1, 3 ] },
                                      '@': { 'item': 'sgn_supermarket_goods', 'chance': 50, 'repeat': [ 1, 2 ] },
                                      '$': { 'item': 'sgn_supermarket_drinks', 'chance': 50, 'repeat': [ 1, 3 ] } } } ),
    'sgn_pl_benh_vien': ( benh_vien, 2, 2, 'bệnh viện quận', 'white', 3, 'shops', [ 'CITY_UNIQUE' ],
                          { 'terrain': { '(': 't_sgn_gach_men', '$': 't_sgn_gach_men' },
                            'furniture': { '(': 'f_bed', '$': 'f_rack' },
                            'items': { '(': { 'item': 'sgn_hospital', 'chance': 25 },
                                       '$': { 'item': 'sgn_hospital', 'chance': 70, 'repeat': [ 1, 3 ] } } } ),
    'sgn_pl_cong_an': ( cong_an, 1, 1, 'đồn công an phường', 'yellow', 5, 'shops', [],
                        { 'terrain': { '$': 't_sgn_gach_men', ')': 't_bars', ';': 't_door_bar_c' },
                          'furniture': { '$': 'f_locker' },
                          'items': { '$': { 'item': 'sgn_police_station', 'chance': 60, 'repeat': [ 1, 2 ] } } } ),
    'sgn_pl_nghia_trang': ( nghia_trang, 2, 2, 'nghĩa trang', 'light_gray', 6, 'parks', [],
                            { 'terrain': { '*': 't_grass' }, 'furniture': { '*': 'f_sgn_mo' } } ),
    'sgn_pl_nha_sach': ( nha_sach, 1, 1, 'nhà sách', 'light_green', 5, 'shops', [],
                         { 'terrain': { '$': 't_sgn_gach_men' }, 'furniture': { '$': 'f_bookcase' },
                           'items': { '$': { 'item': 'sgn_bookstore', 'chance': 70, 'repeat': [ 1, 3 ] } } } ),
    'sgn_pl_xe_may': ( xe_may, 1, 1, 'cửa hàng xe máy', 'light_cyan', 5, 'shops', [],
                       {} ),
}


def generate():
    mapgens, terrains, buildings = [], [], []
    for pid, ( build, w, h, name, colour, _weight, _pool, flags, local ) in PLACES.items():
        levels = build()
        overmaps = []
        for z, lv in sorted( levels.items() ):
            rows = lv.rows()
            assert len( rows ) == h * 24 and all( len( r ) == w * 24 for r in rows ), ( pid, z )
            grid = [ [ lm.oter( pid, x, y, z ) for x in range( w ) ] for y in range( h ) ]
            obj = { 'fill_ter': 't_concrete' if z == 0 else 't_open_air', 'rows': rows, 'palettes': [ 'sgn_lm' ] }
            if z == 0:
                obj['flags'] = lm.CLEARING
                obj['place_monster'] = [ dict( m, x=[ ox * 24, ox * 24 + 23 ], y=[ oy * 24 + ( 6 if oy == 0 else 0 ), oy * 24 + 23 ] )
                                         for oy in range( h ) for ox in range( w ) for m in lm.MONSTERS ]
            if lv.monsters:
                obj['place_monster'] = obj.get( 'place_monster', [] ) + lv.monsters
            for key, table in local.items():
                obj[key] = table
            if lv.vehicles:
                obj['place_vehicles'] = [ { 'vehicle': g, 'x': x, 'y': y, 'rotation': r, 'chance': ch }
                                          for x, y, g, r, ch in lv.vehicles ]
            mapgens.append( { 'type': 'mapgen', 'om_terrain': grid, 'object': obj } )
            for y in range( h ):
                for x in range( w ):
                    tid = lm.oter( pid, x, y, z )
                    terrains.append( { 'type': 'overmap_terrain', 'id': tid,
                                       'copy-from': 'generic_city_building' if z == 0 else 'generic_city_building_roof',
                                       'name': name if z == 0 else name + ' (roof)', 'sym': '&' if z == 0 else '#',
                                       'color': colour, 'looks_like': 'house' if ( x, y, z ) == ( 0, 0, 0 )
                                       else lm.oter( pid, 0, 0, 0 ) } )
                    overmaps.append( { 'point': [ x, y, z ], 'overmap': tid + '_north' } )
        buildings.append( { 'type': 'city_building', 'id': pid, 'locations': [ 'land' ],
                            'flags': [ 'SAIGON' ] + flags, 'city_sizes': [ 4, -1 ], 'overmaps': overmaps } )
    return mapgens, terrains + buildings


def main():
    mg, om = generate()
    root = lm.ROOT
    os.makedirs( os.path.join( root, 'mapgen', 'places' ), exist_ok=True )
    with open( os.path.join( root, 'mapgen', 'places', 'places.json' ), 'w' ) as f:
        json.dump( mg, f, ensure_ascii=False, indent=2 )
    with open( os.path.join( root, 'overmap', 'places.json' ), 'w' ) as f:
        json.dump( om, f, ensure_ascii=False, indent=2 )
    print( 'wrote %d places: %s' % ( len( PLACES ), ', '.join( PLACES ) ) )
    print( 'region weights: ' + ', '.join( '%s %s %d' % ( p[6], k, p[5] ) for k, p in PLACES.items() ) )


if __name__ == '__main__':
    main()
