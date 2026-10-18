#!/usr/bin/env python3
"""Generate the police and army sites of unit W3 (2026-10 firearm policy): the places where the
mod's firearms are loot, guarded by the uniformed dead.

  sgn_pa_cong_an_quan  district police headquarters (công an quận): a walled front yard with a
                       flagpole, the reception hall, offices, holding cells, the riot unit's
                       lockers and a locked armory of gun safes and an ammunition shelf; a dormitory
                       and more offices upstairs.  City building, CITY_UNIQUE, in the shops pool.
  sgn_pa_don_quan_su   army guard post (đồn quân sự): a walled compound with a sandbagged post at
                       the gate, a barracks of bunks, a command hut with a locked armory, and a
                       parked army truck.  City building for the real map (place_places.py puts one
                       on OpenStreetMap's military sites) and, as overmap special
                       sgn_pa_don_quan_su_ngoai_o, on the city outskirts and in the countryside.

Built with the landmark generator's tools (Level grids, roofs, the shared sgn_lm palette); each
site adds its own symbols, which override the palette.  Local frame: the road is to the north.
Writes mapgen/police_army/police_army.json and overmap/sgn_police_army.json.

Run from the repo root:  python3 tools/saigon/gen_police_army.py
"""
import json
import os
import sys

sys.path.insert( 0, os.path.dirname( __file__ ) )
import gen_saigon_landmarks as lm  # noqa: E402
from gen_saigon_landmarks import Level, roof_over  # noqa: E402

INDOOR = lm.INDOOR | set( 'ALRMNHh' )

# symbols both sites share; they override the sgn_lm palette (f_null clears its furniture)
COMMON = {
    'terrain': { 'A': 't_thconc_floor', 'L': 't_door_metal_locked', 'R': 't_sgn_gach_men', 'M': 't_thconc_floor',
                 'N': 't_thconc_floor', 'H': 't_bars', 'h': 't_door_bar_c', 'G': 't_chaingate_c', 'F': 't_concrete',
                 'J': 't_dirt', 'K': 't_dirt' },
    'furniture': { 'A': 'f_gunsafe_ml', 'L': 'f_null', 'R': 'f_locker', 'M': 'f_rack', 'N': 'f_bunkbed',
                   'h': 'f_null', 'G': 'f_null', 'F': 'f_flagpole', 'J': 'f_sandbag_half', 'K': 'f_table' },
}


def local( items ):
    out = { k: dict( v ) for k, v in COMMON.items() }
    out['items'] = items
    return out


# --- Công an quận ---------------------------------------------------------------------------------
def cong_an_quan():
    z0 = Level( 2, 1, ',' )
    z0.rect( 0, 0, 47, 1, 'S' )
    z0.rect( 1, 2, 46, 2, 'I' )                        # the front railing
    for x in range( 22, 26 ):
        z0.at( x, 2, 'G' )                             # the gate
    z0.at( 10, 4, 'F' )                                # the flag
    z0.rect( 2, 3, 3, 6, 'g' )
    z0.rect( 44, 3, 45, 6, 'g' )
    z0.box( 2, 7, 45, 22, '#', '.' )
    for x in range( 4, 44, 3 ):
        z0.at( x, 7, 'w' )
    for x in ( 23, 24 ):
        z0.at( x, 7, '+' )
    z0.rect( 18, 10, 29, 10, 'j' )                     # reception counter
    for x in range( 17, 22 ):
        z0.at( x, 13, 'b' )                            # the waiting bench
    # west wing: offices, then the holding cells
    z0.rect( 14, 8, 14, 21, '#' )
    z0.at( 14, 12, '+' )
    for x in ( 4, 8, 11 ):
        z0.at( x, 10, 'd' )
        z0.at( x, 11, 'c' )
    z0.rect( 3, 8, 3, 9, 'x' )
    z0.rect( 3, 15, 13, 15, '#' )
    z0.at( 10, 15, '+' )
    z0.rect( 3, 17, 13, 17, 'H' )                      # the cells: bars, two cells
    z0.rect( 8, 18, 8, 21, 'H' )
    z0.at( 5, 17, 'h' )
    z0.at( 11, 17, 'h' )
    # east wing: the riot unit's lockers, then the armory behind a locked steel door
    z0.rect( 33, 8, 33, 21, '#' )
    z0.at( 33, 12, '+' )
    for x in range( 35, 44, 2 ):
        z0.at( x, 9, 'R' )
    z0.rect( 34, 15, 44, 15, 'C' )
    z0.at( 39, 15, 'L' )
    for x in ( 36, 38, 40, 42 ):
        z0.at( x, 17, 'A' )
        z0.at( x, 20, 'A' )
    z0.rect( 44, 17, 44, 20, 'M' )
    z0.at( 24, 19, '<' )
    z0.vehicle( 34, 4, 'sgn_vg_pa_police', 0, 70 )     # in the front yard
    z0.vehicle( 6, 5, 'sgn_vg_sidewalk_parked', 0, 60 )
    # the dead: awake in the yard and the hall, still in the cells and offices, and in the armory
    z0.monster( 2, 3, 23, 21, 'sgn_mon_zombie_cong_an_quan', 70, [ 1, 2 ] )
    z0.monster( 26, 3, 45, 14, 'sgn_mon_zombie_cong_an_quan', 60, [ 1, 2 ] )
    z0.monster( 34, 10, 44, 13, 'sgn_mon_zombie_co_dong', 50 )
    z0.monster( 4, 18, 13, 21, 'pseudo_dormant_sgn_mon_zombie_cong_an_quan', 70, [ 1, 2 ] )
    z0.monster( 34, 16, 43, 21, 'pseudo_dormant_sgn_mon_zombie_co_dong', 40 )
    z1 = Level( 2, 1, ' ' )
    z1.box( 2, 7, 45, 22, '#', '.' )
    for x in range( 4, 44, 3 ):
        z1.at( x, 7, 'w' )
    z1.rect( 14, 8, 14, 21, '#' )
    z1.at( 14, 14, '+' )
    for x in range( 4, 13, 3 ):                        # the duty officers' dormitory
        z1.at( x, 10, 'N' )
        z1.at( x, 19, 'N' )
    z1.rect( 33, 8, 33, 21, '#' )
    z1.at( 33, 14, '+' )
    for x in ( 35, 39, 43 ):                           # the commander's office and the records
        z1.at( x, 11, 'd' )
        z1.at( x, 12, 'c' )
    z1.rect( 35, 18, 43, 18, 'x' )
    z1.at( 24, 19, '>' )
    z1.monster( 3, 8, 13, 21, 'pseudo_dormant_sgn_mon_zombie_cong_an_quan', 60, [ 1, 2 ] )
    z1.monster( 34, 8, 44, 21, 'sgn_mon_zombie_cong_an_quan', 40 )
    z2 = roof_over( z1, INDOOR )
    return { 0: z0, 1: z1, 2: z2 }


# --- Đồn quân sự ----------------------------------------------------------------------------------
def don_quan_su():
    z0 = Level( 2, 1, ',' )
    z0.box( 0, 3, 47, 23, 'C', 'g' )                   # the compound wall
    z0.rect( 21, 4, 26, 11, ',' )                      # the drive from the gate
    for x in range( 21, 27 ):
        z0.at( x, 3, 'G' )
    for x, y in ( ( 16, 0 ), ( 17, 0 ), ( 18, 0 ), ( 19, 0 ), ( 16, 1 ), ( 16, 2 ) ):
        z0.at( x, y, 'J' )                             # the sandbagged post outside the gate
    z0.at( 18, 1, 'K' )
    z0.at( 24, 8, 'F' )
    for x, y in ( ( 3, 6 ), ( 44, 6 ), ( 44, 10 ), ( 3, 10 ) ):
        z0.at( x, y, 'T' )
    # the barracks
    z0.box( 2, 12, 20, 22, '#', ':' )
    for x in range( 4, 19, 3 ):
        z0.at( x, 12, 'w' )
    z0.at( 11, 12, '+' )
    for x in range( 4, 19, 3 ):
        z0.at( x, 14, 'N' )
        z0.at( x, 20, 'N' )
    # the command hut and the armory behind it
    z0.box( 28, 12, 45, 22, '#', ':' )
    for x in ( 30, 33, 39, 42 ):
        z0.at( x, 12, 'w' )
    z0.at( 36, 12, '+' )
    for x in ( 31, 35, 40 ):
        z0.at( x, 14, 'd' )
        z0.at( x, 15, 'c' )
    z0.rect( 29, 17, 44, 17, 'C' )
    z0.at( 36, 17, 'L' )
    for x in range( 31, 42, 2 ):
        z0.at( x, 19, 'A' )
    z0.rect( 30, 21, 35, 21, 'M' )
    z0.vehicle( 14, 7, 'sgn_vg_pa_army_truck', 0, 80 )
    # the dead: the sentries in the yard, the rest on their bunks
    z0.monster( 2, 4, 20, 11, 'sgn_mon_zombie_bo_doi', 60, [ 1, 2 ] )
    z0.monster( 27, 4, 46, 11, 'sgn_mon_zombie_bo_doi', 60, [ 1, 2 ] )
    z0.monster( 3, 15, 19, 19, 'pseudo_dormant_sgn_mon_zombie_bo_doi', 80, [ 1, 3 ] )
    z0.monster( 29, 13, 44, 16, 'sgn_mon_zombie_bo_doi', 40 )
    z0.monster( 29, 18, 44, 21, 'pseudo_dormant_sgn_mon_zombie_bo_doi', 40 )
    z1 = Level( 2, 1, ' ' )                            # roofs over the two buildings only
    z1.rect( 2, 12, 20, 22, '_' )
    z1.rect( 28, 12, 45, 22, '_' )
    return { 0: z0, 1: z1 }


SITES = {
    # id: ( builder, w, h, name, colour, looks_like, flags, local symbols )
    'sgn_pa_cong_an_quan': ( cong_an_quan, 2, 1, 'trụ sở công an quận', 'yellow', 'sgn_pl_cong_an_00',
                             [ 'CITY_UNIQUE' ],
                             local( { 'A': { 'item': 'sgn_pa_armory_police', 'chance': 80 },
                                      'M': { 'item': 'sgn_pa_ammo_police', 'chance': 70, 'repeat': [ 1, 2 ] },
                                      'R': { 'item': 'sgn_pa_riot_gear', 'chance': 70 } } ) ),
    'sgn_pa_don_quan_su': ( don_quan_su, 2, 1, 'đồn quân sự', 'green', 'sgn_pl_kho_cang_00', [],
                            local( { 'A': { 'item': 'sgn_pa_armory_army', 'chance': 80 },
                                     'M': { 'item': 'sgn_pa_ammo_army', 'chance': 70, 'repeat': [ 1, 2 ] },
                                     'N': { 'item': 'sgn_pa_army_barracks', 'chance': 40 },
                                     'K': { 'item': 'sgn_pa_guard_post', 'chance': 70 } } ) ),
}

EXTRA = [
    { 'type': 'vehicle_group', 'id': 'sgn_vg_pa_army_truck',
      '//': 'W3: the army post\'s truck.  The mod\'s light truck: a copy of a dda truck would bring dda\'s '
            'glovebox loot (tools, a nail gun) into the audit.',
      'vehicles': [ [ 'sgn_veh_xe_tai_nhe', 100 ] ] },
    { 'type': 'vehicle_group', 'id': 'sgn_vg_pa_police',
      '//': 'W3: the district police yard: the duty pickup or the officers\' motorbikes.',
      'vehicles': [ [ 'sgn_veh_xe_tai_nhe', 40 ], [ 'sgn_veh_underbone', 60 ] ] },
]


def generate():
    mapgens, terrains, buildings = [], [], []
    for pid, ( build, w, h, name, colour, looks, flags, loc ) in SITES.items():
        levels = build()
        overmaps = []
        for z, lv in sorted( levels.items() ):
            rows = lv.rows()
            assert len( rows ) == h * 24 and all( len( r ) == w * 24 for r in rows ), ( pid, z )
            grid = [ [ lm.oter( pid, x, y, z ) for x in range( w ) ] for y in range( h ) ]
            obj = { 'fill_ter': 't_concrete' if z == 0 else 't_open_air', 'rows': rows, 'palettes': [ 'sgn_lm' ] }
            if z == 0:
                obj['flags'] = lm.CLEARING
            if lv.monsters:
                obj['place_monster'] = lv.monsters
            for key, table in loc.items():
                obj[key] = table
            if lv.vehicles:
                obj['place_vehicles'] = [ { 'vehicle': g, 'x': x, 'y': y, 'rotation': r, 'chance': ch }
                                          for x, y, g, r, ch in lv.vehicles ]
            mapgens.append( { 'type': 'mapgen', 'om_terrain': grid, 'object': obj } )
            for y in range( h ):
                for x in range( w ):
                    tid = lm.oter( pid, x, y, z )
                    t = { 'type': 'overmap_terrain', 'id': tid,
                          'copy-from': 'generic_city_building' if z == 0 else 'generic_city_building_roof',
                          'name': name if z == 0 else name + ( ' (roof)' if z == max( levels ) else ' (upper floor)' ),
                          'sym': '&' if z == 0 else '#', 'color': colour,
                          'looks_like': looks if ( x, y, z ) == ( 0, 0, 0 ) else lm.oter( pid, 0, 0, 0 ) }
                    terrains.append( t )
                    overmaps.append( { 'point': [ x, y, z ], 'overmap': tid + '_north' } )
        buildings.append( { 'type': 'city_building', 'id': pid, 'locations': [ 'land' ],
                            'flags': [ 'SAIGON' ] + flags, 'city_sizes': [ 4, -1 ], 'overmaps': overmaps } )
        if pid == 'sgn_pa_don_quan_su':
            # the same post outside the cities: Vietmap's outskirts and the delta countryside
            buildings.append( { 'type': 'overmap_special', 'id': 'sgn_pa_don_quan_su_ngoai_o',
                                '//': 'W3: an army guard post on the edge of the city or out in the fields, '
                                      'one to three per overmap where there is room (city_distance 2+).',
                                'overmaps': overmaps,
                                'connections': [ { 'point': [ 0, -1, 0 ], 'terrain': 'road', 'connection': 'local_road' } ],
                                'locations': [ 'land' ], 'city_distance': [ 2, -1 ], 'occurrences': [ 1, 3 ],
                                'flags': [ 'SAIGON' ] } )
    return mapgens + EXTRA, terrains + buildings


def main():
    mg, om = generate()
    root = lm.ROOT
    os.makedirs( os.path.join( root, 'mapgen', 'police_army' ), exist_ok=True )
    with open( os.path.join( root, 'mapgen', 'police_army', 'police_army.json' ), 'w' ) as f:
        json.dump( mg, f, ensure_ascii=False, indent=2 )
    with open( os.path.join( root, 'overmap', 'sgn_police_army.json' ), 'w' ) as f:
        json.dump( om, f, ensure_ascii=False, indent=2 )
    print( 'wrote %d sites: %s' % ( len( SITES ), ', '.join( SITES ) ) )


if __name__ == '__main__':
    main()
