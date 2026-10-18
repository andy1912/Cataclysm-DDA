#!/usr/bin/env python3
"""Real-map stage 1: read a map image drawn to doc/saigon/REALMAP_IMAGE_SPEC.md and turn it into
a grid of map classes, one cell per game map tile (24 m).

  python3 tools/saigon/realmap/classify.py IMAGE.png POINTS.json OUT_PREFIX

POINTS.json lists the reference points marked on the image in black (#000000 squares):
  [ { "name": "Bến Thành clock tower", "lat": 10.7725, "lon": 106.6980 }, ... ]
in any order: the assignment of points to marks that fits best is kept.
The image is fitted onto real coordinates with an affine transform (3+ points; with 4+ the
residuals are reported, so a misplaced mark shows up).

Writes OUT_PREFIX.grid.json (classes per tile over the whole 5 x 4 overmap area, plus the
pixel position of every landmark and place marker) and OUT_PREFIX.preview.png (one pixel per
tile, coloured by class).
"""
import itertools
import json
import math
import os
import sys

sys.path.insert( 0, os.path.join( os.path.dirname( __file__ ), '..', 'art' ) )
import pngio  # noqa: E402

# Area: 5 x 4 overmaps of 180 tiles, 24 m each; north-west corner (REALMAP_IMAGE_SPEC.md §5)
AREA_W, AREA_H = 5 * 180, 4 * 180
ORIGIN_LAT, ORIGIN_LON = 10.8856, 106.6237
M_PER_DEG_LAT = 110600.0
M_PER_DEG_LON = 111320.0 * math.cos( math.radians( 10.8 ) )
TILE_M = 24.0

# REALMAP_IMAGE_SPEC.md §3
CLASSES = {
    'river': '#1F4FB0', 'canal': '#3AA6F0', 'lake': '#2A7AD0',
    'boulevard': '#E0302A', 'main_street': '#F28C1E', 'street': '#FFFFFF', 'hem': '#B4B4B4',
    'bridge': '#9B3FC8', 'railway': '#3C3C3C',
    'residential': '#E6C89A', 'downtown': '#E89AA0', 'cholon': '#EBB54A', 'villa': '#C9DFA0',
    'apartments': '#D8A0D8', 'industrial': '#9A9A9A', 'government': '#6E80A8', 'park': '#3FA548',
    'cemetery': '#6B8A22', 'farmland': '#D4EA9A', 'marsh': '#7AB8A0', 'open': '#F2EDDC',
}
MARKERS = {
    'landmark': '#FF00FF', 'reference': '#000000', 'fuel': '#FFF000', 'market': '#FF7F00',
    'pagoda': '#C00000', 'church': '#FFB0C8', 'school': '#0050FF', 'hospital': '#00E0E0',
    'police': '#202080', 'supermarket': '#00A050',
}
# When classes compete inside one tile, the narrow linear ones win so they stay connected.
PRIORITY = [ 'bridge', 'river', 'canal', 'boulevard', 'main_street', 'railway', 'street', 'lake' ]
TOLERANCE = 40      # squared-distance threshold is TOLERANCE**2 * 3 in RGB


def hexrgb( h ):
    return tuple( int( h[i:i + 2], 16 ) for i in ( 1, 3, 5 ) )


PALETTE = [ ( k, hexrgb( v ) ) for k, v in CLASSES.items() ]
MARKS = [ ( k, hexrgb( v ) ) for k, v in MARKERS.items() ]


_cache = {}


def nearest( rgb, table ):
    """Closest entry of table to rgb -> ( name, squared distance ); memoised, flat maps have few colours."""
    key = ( rgb, id( table ) )
    if key in _cache:
        return _cache[key]
    best, bd = None, 1e9
    for k, c in table:
        d = ( rgb[0] - c[0] ) ** 2 + ( rgb[1] - c[1] ) ** 2 + ( rgb[2] - c[2] ) ** 2
        if d < bd:
            best, bd = k, d
    _cache[key] = ( best, bd )
    return best, bd


def latlon_to_tile( lat, lon ):
    return ( ( lon - ORIGIN_LON ) * M_PER_DEG_LON / TILE_M, ( ORIGIN_LAT - lat ) * M_PER_DEG_LAT / TILE_M )


def find_markers( img ):
    """Connected blobs of each marker colour -> list of ( kind, cx, cy, size )."""
    w, h = img.width, img.height
    kind_at = {}
    for y in range( h ):
        for x in range( w ):
            p = img.get( x, y )
            k, d = nearest( tuple( p[:3] ), MARKS )
            if d <= 20 ** 2 * 3:
                kind_at[( x, y )] = k
    seen, blobs = set(), []
    for start, k in kind_at.items():
        if start in seen:
            continue
        stack, pts = [ start ], []
        seen.add( start )
        while stack:
            q = stack.pop()
            pts.append( q )
            for d in ( ( 1, 0 ), ( -1, 0 ), ( 0, 1 ), ( 0, -1 ) ):
                n = ( q[0] + d[0], q[1] + d[1] )
                if n not in seen and kind_at.get( n ) == k:
                    seen.add( n )
                    stack.append( n )
        if len( pts ) >= 9:                            # ignore stray anti-aliased pixels
            blobs.append( ( k, sum( p[0] for p in pts ) / len( pts ), sum( p[1] for p in pts ) / len( pts ), len( pts ) ) )
    return blobs


def solve_affine( src, dst ):
    """Least-squares affine: dst = A * [x, y, 1].  Returns ( a, b, c, d, e, f )."""
    n = len( src )
    # normal equations for x' = a x + b y + c and y' = d x + e y + f
    sxx = sum( x * x for x, _ in src ); sxy = sum( x * y for x, y in src ); syy = sum( y * y for _, y in src )
    sx = sum( x for x, _ in src ); sy = sum( y for _, y in src )
    m = [ [ sxx, sxy, sx ], [ sxy, syy, sy ], [ sx, sy, n ] ]

    def solve( rhs ):
        a = [ row[:] + [ r ] for row, r in zip( m, rhs ) ]
        for i in range( 3 ):
            piv = max( range( i, 3 ), key=lambda r: abs( a[r][i] ) )
            a[i], a[piv] = a[piv], a[i]
            for r in range( 3 ):
                if r != i:
                    f = a[r][i] / a[i][i]
                    a[r] = [ vr - f * vi for vr, vi in zip( a[r], a[i] ) ]
        return [ a[i][3] / a[i][i] for i in range( 3 ) ]
    X = solve( [ sum( x * u for ( x, _ ), ( u, _ ) in zip( src, dst ) ), sum( y * u for ( _, y ), ( u, _ ) in zip( src, dst ) ), sum( u for u, _ in dst ) ] )
    Y = solve( [ sum( x * v for ( x, _ ), ( _, v ) in zip( src, dst ) ), sum( y * v for ( _, y ), ( _, v ) in zip( src, dst ) ), sum( v for _, v in dst ) ] )
    return X + Y


def main():
    image, points, out = sys.argv[1], sys.argv[2], sys.argv[3]
    img = pngio.read( image )
    refs = json.load( open( points ) )
    blobs = find_markers( img )
    marks = [ ( b[1], b[2] ) for b in blobs if b[0] == 'reference' ]
    if len( marks ) < 3 or len( refs ) < 3:
        sys.exit( 'need 3+ black reference marks and 3+ points in %s (found %d marks)' % ( points, len( marks ) ) )
    # match: try every assignment of the listed points to marks and keep the best upright fit
    tiles = [ latlon_to_tile( r['lat'], r['lon'] ) for r in refs ]
    best = None
    for perm in itertools.permutations( range( len( marks ) ), len( refs ) ):
        src = [ marks[i] for i in perm ]
        t = solve_affine( src, tiles )
        err = sum( ( t[0] * x + t[1] * y + t[2] - u ) ** 2 + ( t[3] * x + t[4] * y + t[5] - v ) ** 2
                   for ( x, y ), ( u, v ) in zip( src, tiles ) )
        # the spec asks for north up: penalise rotated, skewed or mirrored fits so that with only
        # 3 points (which any assignment fits exactly) the upright one wins
        tilt = ( abs( t[1] ) + abs( t[3] ) ) / max( 1e-9, abs( t[0] ) + abs( t[4] ) )
        score = err + 1000 * tilt + ( 1e9 if t[0] <= 0 or t[4] <= 0 else 0 )
        if best is None or score < best[0]:
            best = ( score, perm, t, err )
    _, perm, t, err = best
    print( 'fit: %d points, rms error %.2f tiles (%.0f m)' % ( len( refs ), math.sqrt( err / len( refs ) ),
                                                             TILE_M * math.sqrt( err / len( refs ) ) ) )
    for r, i in zip( refs, perm ):
        print( '  %-30s mark at pixel (%.0f, %.0f)' % ( r['name'], marks[i][0], marks[i][1] ) )
    # pixel -> tile and its inverse (tile centre -> pixel) for sampling
    a, b, c, d, e, f = t
    det = a * e - b * d
    inv = ( e / det, -b / det, ( b * f - c * e ) / det, -d / det, a / det, ( c * d - a * f ) / det )
    m_per_px = TILE_M * math.sqrt( abs( det ) )
    print( 'scale: %.1f m per pixel (%.1f pixels per tile)' % ( m_per_px, TILE_M / m_per_px ) )
    # classify: sample each tile's pixel footprint, priority classes win over area classes
    k = max( 1, int( round( TILE_M / m_per_px ) ) )
    grid = []
    counts = {}
    for ty in range( AREA_H ):
        row = []
        for tx in range( AREA_W ):
            votes = {}
            for sy in range( k ):
                for sx in range( k ):
                    u, v = tx + ( sx + 0.5 ) / k, ty + ( sy + 0.5 ) / k
                    px = int( inv[0] * u + inv[1] * v + inv[2] )
                    py = int( inv[3] * u + inv[4] * v + inv[5] )
                    if 0 <= px < img.width and 0 <= py < img.height:
                        cls, dist = nearest( tuple( img.get( px, py )[:3] ), PALETTE )
                        if dist <= TOLERANCE ** 2 * 3:
                            votes[cls] = votes.get( cls, 0 ) + 1
            cls = 'outside'
            if votes:
                linear = [ p for p in PRIORITY if votes.get( p, 0 ) * 4 >= k * k ]   # covers 1/4 of the tile
                cls = linear[0] if linear else max( votes, key=votes.get )
            row.append( cls )
            counts[cls] = counts.get( cls, 0 ) + 1
        grid.append( row )
    places = []
    for kind, x, y, size in blobs:
        if kind != 'reference':
            places.append( { 'kind': kind, 'tile': [ round( a * x + b * y + c, 1 ), round( d * x + e * y + f, 1 ) ] } )
    with open( out + '.grid.json', 'w' ) as fo:
        json.dump( { 'width': AREA_W, 'height': AREA_H, 'origin': [ ORIGIN_LAT, ORIGIN_LON ], 'tile_m': TILE_M,
                     'grid': [ ''.join( chr( 65 + list( CLASSES ).index( c ) ) if c in CLASSES else '.' for c in row ) for row in grid ],
                     'legend': { chr( 65 + i ): k for i, k in enumerate( CLASSES ) }, 'places': places }, fo )
    prev = pngio.Image( AREA_W, AREA_H )
    for y, row in enumerate( grid ):
        for x, cls in enumerate( row ):
            prev.set( x, y, hexrgb( CLASSES[cls] ) + ( 255, ) if cls in CLASSES else ( 20, 20, 24, 255 ) )
    pngio.write( out + '.preview.png', prev )
    total = AREA_W * AREA_H
    print( 'classes: ' + ', '.join( '%s %.1f%%' % ( k, 100 * v / total ) for k, v in sorted( counts.items(), key=lambda kv: -kv[1] ) ) )
    print( 'markers: %d landmarks, %d places' % ( sum( p['kind'] == 'landmark' for p in places ), sum( p['kind'] != 'landmark' for p in places ) ) )


if __name__ == '__main__':
    main()
