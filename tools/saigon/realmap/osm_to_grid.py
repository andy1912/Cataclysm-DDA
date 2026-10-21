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
  places    fuel, markets, pagodas, churches, temples, schools, hospitals, police, supermarkets;
            W3: district police headquarters (police_hq) and army sites (military, from land use)
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
# classes the OSM converter adds to the image classes (classify.py), with their preview colours
EXTRA_CLASSES = { 'runway': '#4A4C52', 'taxiway': '#C8A030', 'apron': '#7C7E86' }
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


def area_m2( e ):
    """Area of a closed way (0 for anything else)."""
    g = e.get( 'geometry' ) or []
    if e['type'] != 'way' or len( g ) < 4 or g[0] != g[-1]:
        return float( 'inf' ) if e['type'] == 'relation' else 0.0
    pts = [ ( p['lon'] * C.M_PER_DEG_LON, p['lat'] * C.M_PER_DEG_LAT ) for p in g ]
    return abs( sum( a[0] * b[1] - b[0] * a[1] for a, b in zip( pts, pts[1:] ) ) ) / 2


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
    # R-fid: today's building sites were mostly built up in 2009 (old shophouses, factories, slums
    # cleared since), so they stay city; only greenfield sites are open land
    'cemetery': 'cemetery', 'religious': None, 'construction': None, 'brownfield': None, 'greenfield': 'open',
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
        elif t.get( 'aeroway' ) in ( 'runway', 'taxiway' ) and e['type'] == 'way' and e['geometry'][0] != e['geometry'][-1]:
            cls, order = t['aeroway'], 3 if t['aeroway'] == 'runway' else 2.5
        elif t.get( 'aeroway' ) == 'apron':
            cls, order = 'apron', 2
        elif t.get( 'natural' ) == 'water':
            w = t.get( 'water', '' )
            # R-fid: fountains, pools and ponds smaller than one tile are not water on a 24 m grid
            # (the fountain at Lê Lợi - Nguyễn Huệ cut both streets)
            if t.get( 'amenity' ) == 'fountain' or w in ( 'fountain', 'reflecting_pool', 'pool' ) or \
                    ( w not in ( 'river', 'canal', 'oxbow' ) and area_m2( e ) < C.TILE_M ** 2 ):
                continue
            cls = 'river' if w in ( 'river', 'oxbow' ) else 'canal' if w in ( 'canal', 'ditch', 'stream' ) else 'lake'
            order = 4
        if cls:
            layers.append( ( order, cls, e ) )
    layers.sort( key=lambda l: l[0] )
    for order, cls, e in layers:
        if cls in ( 'runway', 'taxiway' ):
            # a runway is ~46 m wide: two tiles across its (mostly east-west) line
            steep = abs( tile( e['geometry'][-1] )[1] - tile( e['geometry'][0] )[1] ) > \
                abs( tile( e['geometry'][-1] )[0] - tile( e['geometry'][0] )[0] )
            for p in walk( e['geometry'] ):
                for q in ( [ p, ( p[0] + 1, p[1] ) if steep else ( p[0], p[1] + 1 ) ] if cls == 'runway' else [ p ] ):
                    if inside( q ) and not ( cls == 'taxiway' and terrain[q[1]][q[0]] == 'runway' ):
                        terrain[q[1]][q[0]] = cls
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


def divided_segments( ways ):
    """Segments ( way id, index ) that are one carriageway of a divided road: a one-way segment with
    a same-named one-way segment within DIVIDED_M running the other way.  Only the carriageway
    heading east-south-east is kept, so the road is drawn once, not as two parallel lines."""
    cell = 60.0                                            # metres per hash cell
    hashed = {}
    segs = []
    for e in ways:
        t = e['tags']
        if t.get( 'oneway' ) != 'yes':
            continue
        name = nfc( t.get( 'name' ) ) or t.get( 'highway' )
        g = e['geometry']
        for i, ( a, b ) in enumerate( zip( g, g[1:] ) ):
            ax, ay = a['lon'] * C.M_PER_DEG_LON, -a['lat'] * C.M_PER_DEG_LAT
            bx, by = b['lon'] * C.M_PER_DEG_LON, -b['lat'] * C.M_PER_DEG_LAT
            n = math.hypot( bx - ax, by - ay )
            if n < 1:
                continue
            seg = ( e['id'], i, name, ( ax + bx ) / 2, ( ay + by ) / 2, ( bx - ax ) / n, ( by - ay ) / n, n )
            segs.append( seg )
            hashed.setdefault( ( int( seg[3] // cell ), int( seg[4] // cell ) ), [] ).append( seg )
    # R-fid: decided per way, not per segment: a carriageway whose line wobbles (a bend, a bus bay)
    # had single segments heading the 'wrong' way dropped, which broke the kept carriageway into
    # pieces touching only at corners.  Each way keeps or drops all its twinned segments, by the
    # length-weighted mean heading of those segments: the carriageway heading east-south-east (REF) is kept.  Both
    # carriageways of a road running across REF used to be dropped where single segments wobbled.
    REF = ( 0.894, 0.447 )
    twinned = {}
    for wid, i, name, mx, my, dx, dy, n in segs:
        cx, cy = int( mx // cell ), int( my // cell )
        twin = any( o[2] == name and o[0] != wid and o[5] * dx + o[6] * dy < -0.8 and
                    math.hypot( o[3] - mx, o[4] - my ) < DIVIDED_M
                    for gx in ( cx - 1, cx, cx + 1 ) for gy in ( cy - 1, cy, cy + 1 ) for o in hashed.get( ( gx, gy ), [] ) )
        if twin:
            twinned.setdefault( wid, [] ).append( ( i, n * ( dx * REF[0] + dy * REF[1] ) ) )
    drop = set()
    for wid, lst in twinned.items():
        if sum( d for _, d in lst ) < 0:
            drop.update( ( wid, i ) for i, _ in lst )
    return drop


DIVIDED_M = 45


def roads( terrain, corr ):
    conn = {}
    klass = {}
    bridge = set()
    rank = { 'boulevard': 3, 'main_street': 2, 'street': 1 }
    used = skipped = 0
    ways = load( 'roads' )
    divided = divided_segments( ways )
    for e in ways:
        t = e.get( 'tags', {} )
        hw = t.get( 'highway', '' ).replace( '_link', '' )
        name = nfc( t.get( 'name' ) )
        if e['id'] in corr['drop_ids'] or any( n in name.lower() for n in corr['drop_names'] ) or \
                t.get( 'highway' ) in corr['drop_classes']:
            skipped += 1
            continue
        # zones that did not have this street network yet (Thủ Thiêm before the new town); a zone
        # with keep_major_roads keeps its through roads and loses only the estate streets
        if any( z.get( 'drop_roads_inside' ) and name not in z.get( 'keep_road_names', [] ) and
                not ( z.get( 'keep_major_roads' ) and hw in MAJOR ) and
                all( point_in( z['polygon'], p['lat'], p['lon'] ) for p in e['geometry'] ) for z in corr.get( 'zones', [] ) ):
            skipped += 1
            continue
        if t.get( 'tunnel' ) in ( 'yes', 'building_passage' ) or t.get( 'area' ) == 'yes':
            continue
        if hw not in MAJOR and any( z.get( 'drop_minor_streets' ) and
                                    all( point_in( z['polygon'], p['lat'], p['lon'] ) for p in e['geometry'] )
                                    for z in corr.get( 'zones', [] ) ):
            skipped += 1
            continue
        if hw in MAJOR:
            cls = MAJOR[hw]
        elif hw in MINOR and name and not ALLEY_NAME.match( name ) and length_m( e['geometry'] ) >= MIN_STREET_M:
            cls = 'street'
        else:
            continue
        used += 1
        is_bridge = t.get( 'bridge' ) not in ( None, 'no' ) or t.get( 'layer', '0' ) not in ( '0', '-1', '-2' )
        # walk each run of kept segments (one carriageway of a divided road is left out)
        g = e['geometry']
        runs, run = [], [ g[0] ]
        for i in range( len( g ) - 1 ):
            if ( e['id'], i ) in divided:
                if len( run ) > 1:
                    runs.append( run )
                run = [ g[i + 1] ]
            else:
                run.append( g[i + 1] )
        if len( run ) > 1:
            runs.append( run )
        path = []
        for r in runs:
            steps = walk( r )
            path.extend( steps )
            for a, b in zip( steps, steps[1:] ):
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
    shifted = shift_canals( terrain, conn, bridge )
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
    print( 'roads: %d ways used, %d removed by the 2009 corrections, %d one-way segments left out as the second '
           'carriageway, %d tiles (%d bridges), %d bank tiles given to water, %d canal tiles moved off canal-side streets'
           % ( used, skipped, len( divided ), len( conn ), len( bridge ), dropped, shifted ) )
    return conn, klass, bridge


def shift_canals( terrain, conn, bridge ):
    """R-fid: a canal drawn from its centre line is one tile wide, and the street along its bank
    often falls on the same tiles: it then became a long 'bridge' running down the canal.  Where a
    street runs along a canal (a straight run of road tiles on canal tiles, linked along the canal's
    axis), the canal moves one tile aside onto free land, so both show: the street on the bank and
    the water beside it.  Returns the number of canal tiles moved."""
    W_, H_ = len( terrain[0] ), len( terrain )

    def wet( p ):
        return 0 <= p[0] < W_ and 0 <= p[1] < H_ and terrain[p[1]][p[0]] == 'canal'

    def free( p ):
        return 0 <= p[0] < W_ and 0 <= p[1] < H_ and p not in conn and \
            terrain[p[1]][p[0]] not in ( 'river', 'lake', 'canal' )
    along = {}
    for p, c in conn.items():
        if p in bridge or not wet( p ):
            continue
        for axis, d0, d1 in ( ( 'ns', 'n', 's' ), ( 'ew', 'w', 'e' ) ):
            if d0 in c and d1 in c:
                a = ( p[0] + DIRS[d0][0], p[1] + DIRS[d0][1] )
                b = ( p[0] + DIRS[d1][0], p[1] + DIRS[d1][1] )
                if wet( a ) or wet( b ):
                    along[p] = axis
    moved = 0
    seen = set()
    for p in sorted( along ):
        if p in seen:
            continue
        axis = along[p]
        step = DIRS['s'] if axis == 'ns' else DIRS['e']
        side = [ DIRS['e'], DIRS['w'] ] if axis == 'ns' else [ DIRS['s'], DIRS['n'] ]
        # the whole run along the axis
        start = p
        while along.get( ( start[0] - step[0], start[1] - step[1] ) ) == axis:
            start = ( start[0] - step[0], start[1] - step[1] )
        run, q = [], start
        while along.get( q ) == axis:
            run.append( q )
            seen.add( q )
            q = ( q[0] + step[0], q[1] + step[1] )
        if len( run ) < 2:
            continue
        for sd in side:
            dest = [ ( r[0] + sd[0], r[1] + sd[1] ) for r in run ]
            if not all( free( t ) for t in dest ):
                continue
            for r, t in zip( run, dest ):
                terrain[t[1]][t[0]], terrain[r[1]][r[0]] = 'canal', terrain[t[1]][t[0]]
            # join the moved stretch to the canal beyond each end (a corner tile, if free)
            for end, back in ( ( run[0], ( -step[0], -step[1] ) ), ( run[-1], step ) ):
                beyond = ( end[0] + back[0], end[1] + back[1] )
                corner = ( beyond[0] + sd[0], beyond[1] + sd[1] )
                if wet( beyond ) and free( corner ):
                    terrain[corner[1]][corner[0]] = 'canal'
            moved += len( run )
            break
    # canal tiles touching only at a corner (a line stepping diagonally, or a moved stretch) are
    # joined through a free corner tile, so the water runs on unbroken
    for y in range( H_ - 1 ):
        for x in range( W_ ):
            if not wet( ( x, y ) ):
                continue
            for dx in ( -1, 1 ):
                q = ( x + dx, y + 1 )
                if wet( q ) and not wet( ( x + dx, y ) ) and not wet( ( x, y + 1 ) ):
                    corner = next( ( c for c in ( ( x + dx, y ), ( x, y + 1 ) ) if free( c ) ), None )
                    if corner:
                        terrain[corner[1]][corner[0]] = 'canal'
    return moved


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


# W3: the district police headquarters among the police (a ward post is everything else), and the
# army's compounds from the land use: one guard post per military site that is a barracks, a
# command or a unit, not a hospital, a school, a company, a shipyard or an office
POLICE_HQ = re.compile( r'^(công an|trụ sở công an) (quận|huyện|thành phố)|cảnh sát cơ động', re.I )
NOT_A_POST = re.compile( r'bệnh viện|trường|đại học|công ty|xưởng|văn phòng|ban cơ yếu|bãi tập', re.I )
MILITARY_SPACING = 8            # tiles: one post for a compound mapped as several pieces


def centre( e ):
    if e['type'] == 'node':
        return e['lat'], e['lon']
    if 'bounds' in e:
        b = e['bounds']
        return ( b['minlat'] + b['maxlat'] ) / 2, ( b['minlon'] + b['maxlon'] ) / 2
    if e.get( 'geometry' ):
        return ( sum( p['lat'] for p in e['geometry'] ) / len( e['geometry'] ),
                 sum( p['lon'] for p in e['geometry'] ) / len( e['geometry'] ) )
    return None


def military( corr ):
    out = []
    for e in load( 'land' ):
        t = e.get( 'tags', {} )
        if t.get( 'landuse' ) != 'military' or e['id'] in corr['drop_ids'] or NOT_A_POST.search( nfc( t.get( 'name', '' ) ) ):
            continue
        c = centre( e )
        if not c:
            continue
        x, y = ( int( v ) for v in C.latlon_to_tile( *c ) )
        if inside( ( x, y ) ) and not any( abs( x - q['tile'][0] ) < MILITARY_SPACING and
                                           abs( y - q['tile'][1] ) < MILITARY_SPACING for q in out ):
            out.append( { 'kind': 'military', 'tile': [ x, y ], 'name': nfc( t.get( 'name', '' ) ) } )
    return out


def places( corr ):
    out = []
    hq_names = set()
    for e in load( 'places' ):
        t = e.get( 'tags', {} )
        if e['id'] in corr['drop_ids']:
            continue
        kind = next( ( k for f, k in PLACE_KIND if f( t ) ), None )
        if not kind:
            continue
        if kind == 'police' and POLICE_HQ.search( nfc( t.get( 'name', '' ) ) ):
            if nfc( t['name'] ).lower() in hq_names:
                continue            # one headquarters per name (Thủ Đức is mapped twice)
            hq_names.add( nfc( t['name'] ).lower() )
            kind = 'police_hq'
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
    return out + military( corr )


def main():
    out = sys.argv[1]
    corr = json.load( open( os.path.join( HERE, 'corrections_2009.json' ) ) )
    corr['drop_ids'] = set( corr.get( 'drop_way_ids', [] ) )
    corr['drop_names'] = [ nfc( n ).lower() for n in corr.get( 'drop_road_names', [] ) ]
    corr['drop_classes'] = set( corr.get( 'drop_highway_classes', [] ) )
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
        if z.get( 'drop_roads_inside' ) or z.get( 'repaint' ):
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
    legend = list( C.CLASSES ) + list( EXTRA_CLASSES )
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
        return C.hexrgb( C.CLASSES.get( terrain[y][x] ) or EXTRA_CLASSES[terrain[y][x]] )
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
