#!/usr/bin/env python3
"""Real-map stage 1 from OpenStreetMap: turn the OSM extract (tools/saigon/realmap/osm/, fetched by
fetch_osm.sh) into a per-tile map of the 5 x 4 overmap area, 24 m per tile.

  python3 tools/saigon/realmap/osm_to_grid.py OUT_PREFIX

Writes OUT_PREFIX.grid.json:
  terrain   one letter per tile (legend as classify.py: river, canal, lake, park, cemetery, industrial,
            government, downtown, residential, farmland, marsh, open ...)
  roads     {"x,y": [connections "nesw" string, class, bridge?]} built from the ways themselves, so two
            parallel streets in neighbouring tiles do not merge into one
  rail      the North-South railway tiles
  places    fuel, markets, pagodas, churches, temples, schools, hospitals, police, supermarkets
and OUT_PREFIX.preview.png (1 px per tile) plus OUT_PREFIX.core.png (D1-D5 at 3 px per tile).

Data © OpenStreetMap contributors, ODbL 1.0 (see tools/saigon/realmap/osm/README.md).
2009 corrections (things built later) are applied from corrections_2009.json.
"""
import json
import math
import os
import re
import sys
import unicodedata

HERE = os.path.dirname( os.path.abspath( __file__ ) )
sys.path.insert( 0, os.path.join( HERE, '..', 'art' ) )
sys.path.insert( 0, HERE )
import pngio  # noqa: E402
import classify as C  # noqa: E402

W, H = C.AREA_W, C.AREA_H
MAJOR = { 'motorway': 'boulevard', 'trunk': 'boulevard', 'primary': 'main_street',
          'secondary': 'main_street', 'tertiary': 'street' }
MINOR = ( 'residential', 'unclassified', 'living_street' )
ALLEY_NAME = re.compile( r'(hẻm|hẽm|kiệt|ngõ|ngách|hem)\b', re.I )
MIN_STREET_M = 150          # shorter named streets stay inside blocks as alleys
DIRS = { 'n': ( 0, -1 ), 'e': ( 1, 0 ), 's': ( 0, 1 ), 'w': ( -1, 0 ) }
OPP = { 'n': 's', 's': 'n', 'e': 'w', 'w': 'e' }


def nfc( s ):
    return unicodedata.normalize( 'NFC', s or '' )


def load( name ):
    return json.load( open( os.path.join( HERE, 'osm', 'saigon_%s.osm.json' % name ) ) )['elements']


def tile( p ):
    return C.latlon_to_tile( p['lat'], p['lon'] )


def length_m( geom ):
    return sum( math.hypot( ( b['lon'] - a['lon'] ) * C.M_PER_DEG_LON, ( b['lat'] - a['lat'] ) * C.M_PER_DEG_LAT )
                for a, b in zip( geom, geom[1:] ) )


def walk( geom ):
    """The tiles a polyline passes through, 4-connected (a diagonal step goes through the side tile
    nearer the true line), as a list of integer ( x, y ) with consecutive duplicates removed."""
    out = []
    for a, b in zip( geom, geom[1:] ):
        x0, y0 = tile( a )
        x1, y1 = tile( b )
        n = int( max( abs( x1 - x0 ), abs( y1 - y0 ) ) * 4 ) + 1
        for i in range( n + 1 ):
            t = i / n
            fx, fy = x0 + ( x1 - x0 ) * t, y0 + ( y1 - y0 ) * t
            p = ( int( math.floor( fx ) ), int( math.floor( fy ) ) )
            if out and p == out[-1]:
                continue
            if out and abs( p[0] - out[-1][0] ) == 1 and abs( p[1] - out[-1][1] ) == 1:
                # diagonal: pick the corner tile whose centre is nearer the line point
                c1, c2 = ( p[0], out[-1][1] ), ( out[-1][0], p[1] )
                d1 = math.hypot( c1[0] + 0.5 - fx, c1[1] + 0.5 - fy )
                d2 = math.hypot( c2[0] + 0.5 - fx, c2[1] + 0.5 - fy )
                out.append( c1 if d1 <= d2 else c2 )
            out.append( p )
    return out


def inside( p ):
    return 0 <= p[0] < W and 0 <= p[1] < H


# ---------------------------------------------------------------- polygons

def rings_of( e ):
    """Outer and inner rings ( lists of tile-space points ) of a closed way or multipolygon relation."""
    if e['type'] == 'way':
        g = e.get( 'geometry' ) or []
        return ( [ [ tile( p ) for p in g ] ], [] ) if len( g ) > 3 and g[0] == g[-1] else ( [], [] )
    outer, inner = [], []
    for role, dest in ( ( 'outer', outer ), ( 'inner', inner ) ):
        roles = ( 'outer', '' ) if role == 'outer' else ( 'inner', )
        parts = [ [ ( p['lat'], p['lon'] ) for p in m['geometry'] ]
                  for m in e.get( 'members', [] ) if m['type'] == 'way' and m.get( 'role', '' ) in roles and m.get( 'geometry' ) ]
        # join way pieces end to end into closed rings
        while parts:
            ring = parts.pop()
            changed = True
            while ring[0] != ring[-1] and changed:
                changed = False
                for i, q in enumerate( parts ):
                    if q[0] == ring[-1]:
                        ring += q[1:]
                    elif q[-1] == ring[-1]:
                        ring += q[-2::-1]
                    elif q[-1] == ring[0]:
                        ring = q[:-1] + ring
                    elif q[0] == ring[0]:
                        ring = q[:0:-1] + ring
                    else:
                        continue
                    parts.pop( i )
                    changed = True
                    break
            if len( ring ) > 3:
                dest.append( [ C.latlon_to_tile( lat, lon ) for lat, lon in ring ] )
    return outer, inner


def point_in( poly, lat, lon ):
    """Even-odd test of a ( lat, lon ) point against a polygon given as [ [ lat, lon ], ... ]."""
    hit = False
    for ( a0, o0 ), ( a1, o1 ) in zip( poly, poly[1:] + poly[:1] ):
        if ( a0 <= lat ) != ( a1 <= lat ) and lon < o0 + ( lat - a0 ) * ( o1 - o0 ) / ( a1 - a0 ):
            hit = not hit
    return hit


def fill( rings, mark ):
    """Even-odd scanline fill of tile-space rings; calls mark( x, y ) for every tile whose centre is inside."""
    if not rings:
        return
    ys = [ p[1] for r in rings for p in r ]
    for ty in range( max( 0, int( min( ys ) ) ), min( H, int( max( ys ) ) + 1 ) ):
        cy = ty + 0.5
        xs = []
        for r in rings:
            for ( x0, y0 ), ( x1, y1 ) in zip( r, r[1:] + r[:1] ):
                if ( y0 <= cy ) != ( y1 <= cy ):
                    xs.append( x0 + ( cy - y0 ) * ( x1 - x0 ) / ( y1 - y0 ) )
        xs.sort()
        for a, b in zip( xs[0::2], xs[1::2] ):
            for tx in range( max( 0, int( math.ceil( a - 0.5 ) ) ), min( W, int( math.floor( b - 0.5 ) ) + 1 ) ):
                mark( tx, ty )


# ---------------------------------------------------------------- stages

LANDUSE = {
    'industrial': 'industrial', 'military': 'government', 'railway': 'industrial', 'port': 'industrial',
    'commercial': 'downtown', 'retail': 'downtown', 'civic_admin': 'government',
    'cemetery': 'cemetery', 'religious': None, 'construction': 'open', 'brownfield': 'open', 'greenfield': 'open',
    'farmland': 'farmland', 'farmyard': 'farmland', 'orchard': 'farmland', 'meadow': 'farmland',
    'forest': 'park', 'grass': None, 'recreation_ground': 'park', 'residential': None,
}


def land( terrain, corr ):
    """Land use, then parks, airport, water on top (later wins)."""
    els = [ e for e in load( 'land' ) if e['id'] not in corr['drop_ids'] ]
    layers = []
    for e in els:
        t = e.get( 'tags', {} )
        cls = None
        if 'landuse' in t:
            cls = LANDUSE.get( t['landuse'] )
            order = 1
        elif t.get( 'leisure' ) in ( 'park', 'garden' ):
            cls, order = 'park', 2
        elif t.get( 'leisure' ) == 'stadium':
            cls, order = 'open', 2
        elif t.get( 'aeroway' ) in ( 'aerodrome', ):
            cls, order = 'government', 0
        elif t.get( 'aeroway' ) in ( 'runway', 'taxiway', 'apron' ) and e['type'] == 'way' and e['geometry'][0] != e['geometry'][-1]:
            cls, order = 'airstrip', 3
        elif t.get( 'natural' ) == 'water':
            w = t.get( 'water', '' )
            cls = 'river' if w in ( 'river', 'oxbow' ) else 'canal' if w in ( 'canal', 'ditch', 'stream' ) else 'lake'
            order = 4
        if cls:
            layers.append( ( order, cls, e ) )
    layers.sort( key=lambda l: l[0] )
    for order, cls, e in layers:
        if cls == 'airstrip':
            for p in walk( e['geometry'] ):
                if inside( p ):
                    terrain[p[1]][p[0]] = 'government'
            continue
        outer, inner = rings_of( e )

        def mark( x, y, cls=cls ):
            terrain[y][x] = cls
        fill( outer + inner, mark )
    # waterway lines: canals and long streams are at least one tile wide even where no polygon exists
    for e in els:
        t = e.get( 'tags', {} )
        ww = t.get( 'waterway' )
        if ww in ( 'canal', 'stream', 'river' ) and t.get( 'tunnel' ) not in ( 'yes', 'culvert' ):
            if ww == 'stream' and length_m( e['geometry'] ) < 300:
                continue
            for p in walk( e['geometry'] ):
                if inside( p ) and terrain[p[1]][p[0]] not in ( 'river', 'lake' ):
                    terrain[p[1]][p[0]] = 'river' if ww == 'river' else 'canal'
    # the railway into Ga Sài Gòn
    rail = set()
    for e in els:
        t = e.get( 'tags', {} )
        if t.get( 'railway' ) == 'rail' and t.get( 'service' ) not in ( 'yard', 'siding', 'spur' ) and not t.get( 'tunnel' ):
            rail.update( p for p in walk( e['geometry'] ) if inside( p ) )
    return rail


def roads( terrain, corr ):
    conn = {}
    klass = {}
    bridge = set()
    rank = { 'boulevard': 3, 'main_street': 2, 'street': 1 }
    used = skipped = 0
    for e in load( 'roads' ):
        t = e.get( 'tags', {} )
        hw = t.get( 'highway', '' ).replace( '_link', '' )
        name = nfc( t.get( 'name' ) )
        if e['id'] in corr['drop_ids'] or any( n in name for n in corr['drop_names'] ):
            skipped += 1
            continue
        # zones that did not have this street network yet (Thủ Thiêm before the new town)
        if any( z.get( 'drop_roads_inside' ) and name not in z.get( 'keep_road_names', [] ) and
                all( point_in( z['polygon'], p['lat'], p['lon'] ) for p in e['geometry'] ) for z in corr.get( 'zones', [] ) ):
            skipped += 1
            continue
        if t.get( 'tunnel' ) in ( 'yes', 'building_passage' ) or t.get( 'area' ) == 'yes':
            continue
        if hw in MAJOR:
            cls = MAJOR[hw]
        elif hw in MINOR and name and not ALLEY_NAME.match( name ) and length_m( e['geometry'] ) >= MIN_STREET_M:
            cls = 'street'
        else:
            continue
        used += 1
        is_bridge = t.get( 'bridge' ) not in ( None, 'no' ) or t.get( 'layer', '0' ) not in ( '0', '-1', '-2' )
        path = walk( e['geometry'] )
        for a, b in zip( path, path[1:] ):
            for d, ( dx, dy ) in DIRS.items():
                if ( a[0] + dx, a[1] + dy ) == b:
                    if inside( a ):
                        conn.setdefault( a, set() ).add( d )
                    if inside( b ):
                        conn.setdefault( b, set() ).add( OPP[d] )
        for p in path:
            if inside( p ):
                conn.setdefault( p, set() )
                if rank[cls] > rank.get( klass.get( p ), 0 ):
                    klass[p] = cls
                if is_bridge:
                    bridge.add( p )
    # a road on a narrow canal keeps the road (as a bridge); a road on the river or a lake without a
    # bridge tag is a bank road drawn a tile too far: the water wins
    dropped = 0
    for p in list( conn ):
        ter = terrain[p[1]][p[0]]
        if ter in ( 'river', 'lake', 'canal' ):
            if p in bridge or ter == 'canal':
                bridge.add( p )
            else:
                for d in conn.pop( p ):
                    q = ( p[0] + DIRS[d][0], p[1] + DIRS[d][1] )
                    if q in conn:
                        conn[q].discard( OPP[d] )
                klass.pop( p, None )
                dropped += 1
    # flyovers and interchange ramps over dry land are plain road on the overmap
    bridge = { p for p in bridge if p in conn and terrain[p[1]][p[0]] in ( 'river', 'lake', 'canal' ) }
    print( 'roads: %d ways used, %d removed by the 2009 corrections, %d tiles (%d bridges), %d bank tiles given to water'
           % ( used, skipped, len( conn ), len( bridge ), dropped ) )
    return conn, klass, bridge


PLACE_KIND = [
    ( lambda t: t.get( 'amenity' ) == 'fuel', 'fuel' ),
    ( lambda t: t.get( 'amenity' ) == 'marketplace', 'market' ),
    ( lambda t: t.get( 'amenity' ) == 'place_of_worship' and t.get( 'religion' ) == 'christian', 'church' ),
    ( lambda t: t.get( 'amenity' ) == 'place_of_worship' and t.get( 'religion' ) in ( 'buddhist', 'taoist', 'chinese_folk', 'vietnamese_folk', 'caodaism', None ), 'pagoda' ),
    ( lambda t: t.get( 'amenity' ) in ( 'school', 'university' ), 'school' ),
    ( lambda t: t.get( 'amenity' ) == 'hospital', 'hospital' ),
    ( lambda t: t.get( 'amenity' ) == 'police', 'police' ),
    ( lambda t: t.get( 'shop' ) == 'supermarket', 'supermarket' ),
]


def places( corr ):
    out = []
    for e in load( 'places' ):
        t = e.get( 'tags', {} )
        if e['id'] in corr['drop_ids']:
            continue
        kind = next( ( k for f, k in PLACE_KIND if f( t ) ), None )
        if not kind:
            continue
        if e['type'] == 'node':
            lat, lon = e['lat'], e['lon']
        elif 'bounds' in e:
            b = e['bounds']
            lat, lon = ( b['minlat'] + b['maxlat'] ) / 2, ( b['minlon'] + b['maxlon'] ) / 2
        elif e.get( 'geometry' ):
            lat = sum( p['lat'] for p in e['geometry'] ) / len( e['geometry'] )
            lon = sum( p['lon'] for p in e['geometry'] ) / len( e['geometry'] )
        else:
            continue
        x, y = C.latlon_to_tile( lat, lon )
        if inside( ( int( x ), int( y ) ) ):
            out.append( { 'kind': kind, 'tile': [ int( x ), int( y ) ], 'name': nfc( t.get( 'name', '' ) ) } )
    return out


def main():
    out = sys.argv[1]
    corr = json.load( open( os.path.join( HERE, 'corrections_2009.json' ) ) )
    corr['drop_ids'] = set( corr.get( 'drop_way_ids', [] ) )
    corr['drop_names'] = [ nfc( n ) for n in corr.get( 'drop_road_names', [] ) ]
    terrain = [ [ 'residential' ] * W for _ in range( H ) ]
    for z in corr.get( 'zones', [] ):
        rings = [ [ C.latlon_to_tile( lat, lon ) for lat, lon in z['polygon'] ] ]

        def mark( x, y, cls=z['class'] ):
            terrain[y][x] = cls
        fill( rings, mark )
    rail = land( terrain, corr )
    # zones that replace today's land use (Thủ Thiêm's new-town plots) are painted again on top,
    # keeping only the water
    for z in corr.get( 'zones', [] ):
        if z.get( 'drop_roads_inside' ):
            rings = [ [ C.latlon_to_tile( lat, lon ) for lat, lon in z['polygon'] ] ]

            def mark( x, y, cls=z['class'] ):
                if terrain[y][x] not in ( 'river', 'canal', 'lake' ):
                    terrain[y][x] = cls
            fill( rings, mark )
    conn, klass, bridge = roads( terrain, corr )
    pl = places( corr )
    counts = {}
    for row in terrain:
        for c in row:
            counts[c] = counts.get( c, 0 ) + 1
    print( 'terrain: ' + ', '.join( '%s %.1f%%' % ( k, 100 * v / ( W * H ) ) for k, v in sorted( counts.items(), key=lambda kv: -kv[1] ) ) )
    print( 'places: ' + ', '.join( '%s %d' % ( k, sum( p['kind'] == k for p in pl ) ) for k in sorted( { p['kind'] for p in pl } ) ) )
    legend = list( C.CLASSES )
    with open( out + '.grid.json', 'w' ) as fo:
        json.dump( { 'width': W, 'height': H, 'origin': [ C.ORIGIN_LAT, C.ORIGIN_LON ], 'tile_m': C.TILE_M,
                     'source': 'OpenStreetMap (ODbL) + corrections_2009.json',
                     'legend': { chr( 65 + i ): k for i, k in enumerate( legend ) },
                     'terrain': [ ''.join( chr( 65 + legend.index( c ) ) for c in row ) for row in terrain ],
                     'roads': { '%d,%d' % p: [ ''.join( d for d in 'nesw' if d in c ), klass.get( p, 'street' ), p in bridge ]
                                for p, c in sorted( conn.items() ) },
                     'rail': sorted( [ list( p ) for p in rail ] ),
                     'places': pl }, fo, ensure_ascii=False )
    # previews
    road_col = { 'boulevard': ( 224, 48, 42 ), 'main_street': ( 242, 140, 30 ), 'street': ( 40, 40, 40 ) }

    def colour( x, y ):
        p = ( x, y )
        if p in conn:
            return ( 155, 63, 200 ) if p in bridge else road_col[klass.get( p, 'street' )]
        if p in rail:
            return ( 60, 60, 60 )
        return C.hexrgb( C.CLASSES[terrain[y][x]] )
    img = pngio.Image( W, H )
    for y in range( H ):
        for x in range( W ):
            img.set( x, y, colour( x, y ) + ( 255, ) )
    pngio.write( out + '.preview.png', img )
    x0, y0, x1, y1, s = 230, 400, 470, 590, 3
    img = pngio.Image( ( x1 - x0 ) * s, ( y1 - y0 ) * s )
    for y in range( y0, y1 ):
        for x in range( x0, x1 ):
            c = colour( x, y ) + ( 255, )
            for sy in range( s ):
                for sx in range( s ):
                    img.set( ( x - x0 ) * s + sx, ( y - y0 ) * s + sy, c )
    pngio.write( out + '.core.png', img )


if __name__ == '__main__':
    main()
