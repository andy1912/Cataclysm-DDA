#!/usr/bin/env python3
"""Replace dda road/bridge traffic with Saigon traffic (d4_r3 §2.2 route (c)).

Reads data/json/mapgen/nested/road_vehicles_nested.json and writes Saigon copies of
every nested chunk in it, keeping dda's lane geometry (positions, rotations, chances)
but swapping every vehicle group for sgn_vg_street_traffic (sgn_vg_city_traffic where dda
parked its city_vehicles, the only spots sized for dda's ambulances and fire engines).  The 8 entry ids that the
road and bridge mapgens reference are then redefined at weight 1,000,000 pointing at
the copies, so dda traffic is left at 1000/1,001,000 ≈ 0.1% per id.
Re-run after upstream changes to the dda file.

Run from the repo root:  python3 tools/saigon/gen_road_traffic.py
"""
import json
import os

HERE = os.path.dirname( __file__ )
DDA = os.path.join( HERE, '..', '..', 'data', 'json', 'mapgen', 'nested', 'road_vehicles_nested.json' )
OUT = os.path.join( HERE, '..', '..', 'data', 'mods', 'saigon_2000s', 'mapgen', 'roads', 'road_traffic.json' )
ENTRY_IDS = [
    '24x24_road_end_vehicles', '24x24_road_straight_vehicles', '24x24_road_curved_vehicles',
    '24x24_road_curved_layby_vehicles', '24x24_road_tee_vehicles', '24x24_road_four_way_crossroad_vehicles',
    '24x24_bridge_road_vehicles', '24x24_bridgehead_ground_vehicles' ]
WEIGHT = 1000000
GROUP = 'sgn_vg_street_traffic'
CITY_GROUP = 'sgn_vg_city_traffic'
# per mille; two- and three-wheelers 890, the garbage handcart 10, four-wheelers 100 (L-loc5)
STREET = [ [ 'sgn_veh_underbone', 400 ], [ 'sgn_veh_xe_tay_ga', 160 ], [ 'sgn_veh_xe_dap', 75 ],
           [ 'sgn_veh_ba_gac_may', 65 ], [ 'sgn_veh_xich_lo', 40 ],
           # V4: the older bikes, the 2008-2009 electric bicycle, the disabled rider's trike, the last
           # (abandoned) xe lam and the ward's garbage handcart
           [ 'sgn_veh_underbone_100', 70 ], [ 'sgn_veh_xe_50', 45 ], [ 'sgn_veh_xe_dap_dien', 20 ],
           [ 'sgn_veh_xe_ba_banh', 10 ], [ 'sgn_veh_xe_lam', 5 ], [ 'sgn_veh_xe_rac', 10 ],
           # L-loc5: a few taxis, cars, minibuses and light trucks, as in 2009
           [ 'sgn_veh_taxi', 40 ], [ 'sgn_veh_xe_hoi', 30 ], [ 'sgn_veh_xe_tai_nhe', 20 ],
           [ 'sgn_veh_xe_16_cho', 10 ] ]
# V4: the 115 ambulance and the fire engine, rare, only in dda's city parking spots
CITY = STREET + [ [ 'sgn_veh_xe_cuu_thuong', 4 ], [ 'sgn_veh_xe_cuu_hoa', 2 ] ]


def rename( nid ):
    return 'sgn_' + nid


def transform( value, local_ids ):
    """Swap vehicle groups and re-point chunk references at the Saigon copies."""
    if isinstance( value, dict ):
        out = {}
        for k, v in value.items():
            if k == 'vehicle' and isinstance( v, str ):
                out[k] = CITY_GROUP if v == 'city_vehicles' else GROUP
            else:
                out[k] = transform( v, local_ids )
        return out
    if isinstance( value, list ):
        return [ transform( v, local_ids ) for v in value ]
    if isinstance( value, str ) and value in local_ids:
        return rename( value )
    return value


def main():
    with open( DDA ) as f:
        dda = json.load( f )
    chunks = [ o for o in dda if isinstance( o, dict ) and o.get( 'type' ) == 'mapgen' and 'nested_mapgen_id' in o ]
    local_ids = { o['nested_mapgen_id'] for o in chunks }
    missing = set( ENTRY_IDS ) - local_ids
    assert not missing, 'dda file changed, missing entry ids: %s' % missing
    out = [ { 'type': 'vehicle_group', 'id': GROUP,
              '//': 'Saigon street traffic for the road/bridge nested chunks.',
              'vehicles': STREET },
            { 'type': 'vehicle_group', 'id': CITY_GROUP,
              '//': 'Street traffic plus a rare ambulance or fire engine, for the city parking chunks.',
              'vehicles': CITY } ]
    for o in chunks:
        copy = transform( o, local_ids )
        copy['nested_mapgen_id'] = rename( o['nested_mapgen_id'] )
        copy.pop( 'weight', None )
        out.append( copy )
    for nid in ENTRY_IDS:
        out.append( { 'type': 'mapgen', 'nested_mapgen_id': nid, 'weight': WEIGHT,
                      'object': { 'mapgensize': [ 24, 24 ],
                                  'place_nested': [ { 'chunks': [ rename( nid ) ], 'x': 0, 'y': 0 } ] } } )
    os.makedirs( os.path.dirname( OUT ), exist_ok=True )
    with open( OUT, 'w' ) as f:
        json.dump( out, f, ensure_ascii=False, indent=2 )


if __name__ == '__main__':
    main()
