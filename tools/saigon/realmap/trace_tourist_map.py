#!/usr/bin/env python3
"""Real-map stage 1 for an ordinary printed street map (not drawn to REALMAP_IMAGE_SPEC.md colours):
read roads, water and parks off the scan, per game map tile (24 m).

  python3 tools/saigon/realmap/trace_tourist_map.py GEOREF.json OUT_PREFIX

GEOREF.json (tools/saigon/realmap/georef/) names the image, its reference points (pixel position of
a known place and that place's real coordinates) and the boxes to ignore (title, legend, logos).
The image is fitted onto real coordinates with a least-squares affine transform; each point's
residual is printed, so a misread point shows up.

How a pixel is read:
  - water: clearly blue;  park: clearly green;
  - road: near white and brighter than its surroundings (the map's district fills are pale tints,
    so plain whiteness is not enough);
  - ink: dark or saturated red (labels, icons, the inset frame): unknown, filled from neighbours;
  - anything else: land.
A tile takes water or park when most of its pixels are, road when a third of them are.  Roads cut
by labels are rejoined across short unknown gaps, then thinned to one tile wide.

Writes OUT_PREFIX.grid.json in classify.py's format (only river, park, street and open land here;
land use comes from the zones file in the next stage) and OUT_PREFIX.preview.png: the source
resampled to tiles beside the result.
"""
import json
import math
import os
import sys

HERE = os.path.dirname( os.path.abspath( __file__ ) )
sys.path.insert( 0, os.path.join( HERE, '..', 'art' ) )
sys.path.insert( 0, HERE )
import pngio  # noqa: E402
import classify as C  # noqa: E402

ROAD_FRACTION = 0.33
CONTRAST_RADIUS = 9          # px; box for the local background brightness
CONTRAST = 8                 # a road is this much brighter than its surroundings
GAP = 3                      # tiles of unknown a road may jump
MIN_HALF_WIDTH = 3           # px; streets drawn narrower than twice this are alleys, left to the blocks


def fit( points ):
    src = [ tuple( p['px'] ) for p in points ]
    dst = [ C.latlon_to_tile( p['lat'], p['lon'] ) for p in points ]
    t = C.solve_affine( src, dst )
    print( 'reference points:' )
    for p, ( x, y ), ( u, v ) in zip( points, src, dst ):
        e = C.TILE_M * math.hypot( t[0] * x + t[1] * y + t[2] - u, t[3] * x + t[4] * y + t[5] - v )
        print( '  %-28s %4.0f m off' % ( p['name'], e ) )
    a, b, c, d, e, f = t
    det = a * e - b * d
    print( 'scale %.2f m per pixel, rotation %.1f deg' % ( C.TILE_M * math.sqrt( abs( det ) ), math.degrees( math.atan2( d, a ) ) ) )
    inv = ( e / det, -b / det, ( b * f - c * e ) / det, -d / det, a / det, ( c * d - a * f ) / det )
    return t, inv


def read_pixels( img, ignore ):
    """Per-pixel class codes: 0 land, 1 road, 2 water, 3 park, 4 ink/unknown, 5 ignored."""
    W, H = img.width, img.height
    lum = [ [ 0 ] * W for _ in range( H ) ]
    for y in range( H ):
        row = lum[y]
        for x in range( W ):
            p = img.get( x, y )
            row[x] = min( p[0], p[1], p[2] )
    integ = [ [ 0 ] * ( W + 1 ) for _ in range( H + 1 ) ]
    for y in range( H ):
        acc, cur, prev, row = 0, integ[y + 1], integ[y], lum[y]
        for x in range( W ):
            acc += row[x]
            cur[x + 1] = prev[x + 1] + acc
    R = CONTRAST_RADIUS
    out = [ bytearray( W ) for _ in range( H ) ]
    for y in range( H ):
        y0, y1 = max( 0, y - R ), min( H, y + R + 1 )
        I0, I1, o = integ[y0], integ[y1], out[y]
        for x in range( W ):
            r, g, b = img.get( x, y )[:3]
            lo, hi = min( r, g, b ), max( r, g, b )
            if b > r + 40 and b > g + 8 and b > 150:
                o[x] = 2
            elif g > r + 15 and g > b + 50 and hi - lo > 50:
                o[x] = 3
            elif hi < 120 or ( r > g + 90 and r > b + 90 ):
                o[x] = 4
            elif lo >= 228 and hi - lo <= 24:
                x0, x1 = max( 0, x - R ), min( W, x + R + 1 )
                mean = ( I1[x1] - I0[x1] - I1[x0] + I0[x0] ) / ( ( y1 - y0 ) * ( x1 - x0 ) )
                o[x] = 1 if lo >= mean + CONTRAST else 0
    for x0, y0, x1, y1 in ignore:
        for y in range( max( 0, y0 ), min( H, y1 ) ):
            for x in range( max( 0, x0 ), min( W, x1 ) ):
                out[y][x] = 5
    return out


def road_width( pix, W, H ):
    """Chamfer distance (in pixels) from each road or label pixel to the nearest other pixel: half the
    width the map draws that street.  Labels count as road, because they are printed on the street."""
    INF = 1 << 20
    d = [ [ 0 if pix[y][x] not in ( 1, 4 ) else INF for x in range( W ) ] for y in range( H ) ]
    for y in range( H ):
        row, up = d[y], d[y - 1] if y else None
        for x in range( W ):
            if row[x]:
                v = row[x]
                if x:
                    v = min( v, row[x - 1] + 3 )
                if up:
                    v = min( v, up[x] + 3 )
                    if x:
                        v = min( v, up[x - 1] + 4 )
                    if x + 1 < W:
                        v = min( v, up[x + 1] + 4 )
                row[x] = v
    for y in range( H - 1, -1, -1 ):
        row, dn = d[y], d[y + 1] if y + 1 < H else None
        for x in range( W - 1, -1, -1 ):
            if row[x]:
                v = row[x]
                if x + 1 < W:
                    v = min( v, row[x + 1] + 3 )
                if dn:
                    v = min( v, dn[x] + 3 )
                    if x + 1 < W:
                        v = min( v, dn[x + 1] + 4 )
                    if x:
                        v = min( v, dn[x - 1] + 4 )
                row[x] = v
    return d


def to_tiles( pix, W, H, inv, width=None, min_half_width=0 ):
    """Per-tile class: 'outside', 'river', 'park', 'street', 'open' or '?' (mostly ink)."""
    k = 5                                             # samples per tile side (≈ 1 per pixel at 5.6 m/px)
    grid = []
    for ty in range( C.AREA_H ):
        row = []
        for tx in range( C.AREA_W ):
            n = [ 0 ] * 6
            widest = 0
            for sy in range( k ):
                for sx in range( k ):
                    u, v = tx + ( sx + 0.5 ) / k, ty + ( sy + 0.5 ) / k
                    px = int( inv[0] * u + inv[1] * v + inv[2] )
                    py = int( inv[3] * u + inv[4] * v + inv[5] )
                    if 0 <= px < W and 0 <= py < H:
                        n[pix[py][px]] += 1
                        if width is not None:
                            widest = max( widest, width[py][px] )
                    else:
                        n[5] += 1
            tot = k * k
            if n[5] * 2 > tot:
                row.append( 'outside' )
            elif n[2] * 2 > tot:
                row.append( 'river' )
            elif n[3] * 2 > tot:
                row.append( 'park' )
            elif width is not None and widest >= min_half_width * 3 and n[1] + n[4] >= tot * ROAD_FRACTION:
                row.append( 'street' )
            elif width is None and n[1] >= tot * ROAD_FRACTION:
                row.append( 'street' )
            elif n[4] * 2 > tot:
                row.append( '?' )
            else:
                row.append( 'open' )
        grid.append( row )
    return grid


def bridge_gaps( grid ):
    """A run of up to GAP unknown or land tiles between two road tiles in a straight line becomes road
    (labels written along a street cut it into pieces)."""
    H, W = len( grid ), len( grid[0] )
    add = set()
    for y in range( H ):
        for x in range( W ):
            if grid[y][x] != 'street':
                continue
            for dx, dy in ( ( 1, 0 ), ( 0, 1 ), ( 1, 1 ), ( 1, -1 ) ):
                run = []
                for s in range( 1, GAP + 2 ):
                    nx, ny = x + dx * s, y + dy * s
                    if not ( 0 <= nx < W and 0 <= ny < H ):
                        break
                    if grid[ny][nx] == 'street':
                        if run and all( grid[q][p] == '?' for p, q in run ) or len( run ) == 1:
                            add.update( run )
                        break
                    if grid[ny][nx] not in ( '?', 'open' ):
                        break
                    run.append( ( nx, ny ) )
    for x, y in add:
        grid[y][x] = 'street'
    for y in range( H ):
        for x in range( W ):
            if grid[y][x] == '?':
                grid[y][x] = 'open'
    return len( add )


def thin( grid ):
    """Zhang–Suen thinning of the road tiles, so a street drawn 2–3 tiles wide becomes one tile."""
    H, W = len( grid ), len( grid[0] )
    on = [ [ grid[y][x] == 'street' for x in range( W ) ] for y in range( H ) ]
    changed = True
    while changed:
        changed = False
        for step in ( 0, 1 ):
            kill = []
            for y in range( 1, H - 1 ):
                for x in range( 1, W - 1 ):
                    if not on[y][x]:
                        continue
                    n = [ on[y - 1][x], on[y - 1][x + 1], on[y][x + 1], on[y + 1][x + 1],
                          on[y + 1][x], on[y + 1][x - 1], on[y][x - 1], on[y - 1][x - 1] ]
                    b = sum( n )
                    if b < 2 or b > 6:
                        continue
                    if sum( ( not n[i] ) and n[( i + 1 ) % 8] for i in range( 8 ) ) != 1:
                        continue
                    if step == 0 and ( n[0] and n[2] and n[4] or n[2] and n[4] and n[6] ):
                        continue
                    if step == 1 and ( n[0] and n[2] and n[6] or n[0] and n[4] and n[6] ):
                        continue
                    kill.append( ( x, y ) )
            for x, y in kill:
                on[y][x] = False
            changed = changed or bool( kill )
    removed = 0
    for y in range( H ):
        for x in range( W ):
            if grid[y][x] == 'street' and not on[y][x]:
                grid[y][x] = 'open'
                removed += 1
    return removed


def orthogonalise( grid ):
    """Overmap roads connect only north/east/south/west: where a thinned line steps diagonally, add the
    corner tile so it stays connected."""
    H, W = len( grid ), len( grid[0] )
    add = []
    for y in range( H - 1 ):
        for x in range( W - 1 ):
            a, b, c, d = ( grid[y][x] == 'street', grid[y][x + 1] == 'street',
                           grid[y + 1][x] == 'street', grid[y + 1][x + 1] == 'street' )
            if a and d and not b and not c:
                add.append( ( x + 1, y ) if grid[y][x + 1] == 'open' else ( x, y + 1 ) )
            elif b and c and not a and not d:
                add.append( ( x, y ) if grid[y][x] == 'open' else ( x + 1, y + 1 ) )
    for x, y in add:
        if grid[y][x] in ( 'open', 'park' ):
            grid[y][x] = 'street'
    return len( add )


N4 = ( ( 1, 0 ), ( -1, 0 ), ( 0, 1 ), ( 0, -1 ) )


def street_neighbours( grid, x, y ):
    H, W = len( grid ), len( grid[0] )
    return sum( 1 for dx, dy in N4 if 0 <= x + dx < W and 0 <= y + dy < H and grid[y + dy][x + dx] == 'street' )


def tidy( grid, spur=4, min_piece=20 ):
    """Remove what the scan's noise leaves: 2 x 2 blobs (keep the roads through them), dead ends shorter
    than `spur` tiles, and pieces of fewer than `min_piece` tiles not joined to anything."""
    H, W = len( grid ), len( grid[0] )
    blobs = 0
    for y in range( H - 1 ):
        for x in range( W - 1 ):
            sq = [ ( x, y ), ( x + 1, y ), ( x, y + 1 ), ( x + 1, y + 1 ) ]
            if all( grid[q][p] == 'street' for p, q in sq ):
                # drop the corner with the fewest other links
                p, q = min( sq, key=lambda t: street_neighbours( grid, *t ) )
                grid[q][p] = 'open'
                blobs += 1
    spurs = 0
    for _ in range( spur ):
        ends = [ ( x, y ) for y in range( H ) for x in range( W )
                 if grid[y][x] == 'street' and street_neighbours( grid, x, y ) <= 1 ]
        for x, y in ends:
            grid[y][x] = 'open'
        spurs += len( ends )
    seen = [ [ False ] * W for _ in range( H ) ]
    pieces = 0
    for y in range( H ):
        for x in range( W ):
            if grid[y][x] != 'street' or seen[y][x]:
                continue
            stack, part = [ ( x, y ) ], []
            seen[y][x] = True
            while stack:
                cx, cy = stack.pop()
                part.append( ( cx, cy ) )
                for dx, dy in N4:
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < W and 0 <= ny < H and not seen[ny][nx] and grid[ny][nx] == 'street':
                        seen[ny][nx] = True
                        stack.append( ( nx, ny ) )
            if len( part ) < min_piece:
                for cx, cy in part:
                    grid[cy][cx] = 'open'
                pieces += 1
    return blobs, spurs, pieces


def main():
    georef, out = sys.argv[1], sys.argv[2]
    g = json.load( open( georef ) )
    root = os.path.join( HERE, '..', '..', '..' )
    img = pngio.read( os.path.join( root, g['image'] ) )
    t, inv = fit( g['points'] )
    pix = read_pixels( img, g.get( 'ignore', [] ) )
    width = road_width( pix, img.width, img.height )
    grid = to_tiles( pix, img.width, img.height, inv, width, g.get( 'min_half_width', MIN_HALF_WIDTH ) )
    print( 'rejoined %d road tiles across labels' % bridge_gaps( grid ) )
    print( 'thinned away %d road tiles' % thin( grid ) )
    print( 'added %d corner tiles' % orthogonalise( grid ) )
    print( 'tidied: %d blobs, %d dead-end tiles, %d loose pieces' % tidy( grid ) )
    counts = {}
    for row in grid:
        for c in row:
            counts[c] = counts.get( c, 0 ) + 1
    inside = sum( v for k, v in counts.items() if k != 'outside' )
    print( 'covered %d tiles (%.0f%% of the area): ' % ( inside, 100 * inside / ( C.AREA_W * C.AREA_H ) ) +
           ', '.join( '%s %.1f%%' % ( k, 100 * v / inside ) for k, v in sorted( counts.items(), key=lambda kv: -kv[1] ) if k != 'outside' ) )
    legend = list( C.CLASSES )
    with open( out + '.grid.json', 'w' ) as fo:
        json.dump( { 'width': C.AREA_W, 'height': C.AREA_H, 'origin': [ C.ORIGIN_LAT, C.ORIGIN_LON ], 'tile_m': C.TILE_M,
                     'source': g['image'],
                     'grid': [ ''.join( chr( 65 + legend.index( c ) ) if c in legend else '.' for c in row ) for row in grid ],
                     'legend': { chr( 65 + i ): k for i, k in enumerate( legend ) }, 'places': [] }, fo )
    # preview: the bounding box of the covered tiles, source resampled on the left, result on the right
    ys = [ y for y, row in enumerate( grid ) if any( c != 'outside' for c in row ) ]
    xs = [ x for x in range( C.AREA_W ) if any( grid[y][x] != 'outside' for y in ys ) ]
    x0, x1, y0, y1 = min( xs ), max( xs ) + 1, min( ys ), max( ys ) + 1
    S = 2
    pw, ph = ( x1 - x0 ) * S, ( y1 - y0 ) * S
    prev = pngio.Image( pw * 2 + 8, ph )
    colour = { 'river': '#1F4FB0', 'park': '#3FA548', 'street': '#202020', 'open': '#F2EDDC', 'outside': '#606060' }
    for ty in range( y0, y1 ):
        for tx in range( x0, x1 ):
            for sy in range( S ):
                for sx in range( S ):
                    u, v = tx + ( sx + 0.5 ) / S, ty + ( sy + 0.5 ) / S
                    px = int( inv[0] * u + inv[1] * v + inv[2] )
                    py = int( inv[3] * u + inv[4] * v + inv[5] )
                    src = img.get( px, py )[:3] + ( 255, ) if 0 <= px < img.width and 0 <= py < img.height else ( 96, 96, 96, 255 )
                    X, Y = ( tx - x0 ) * S + sx, ( ty - y0 ) * S + sy
                    prev.set( X, Y, src )
                    prev.set( pw + 8 + X, Y, C.hexrgb( colour[grid[ty][tx]] ) + ( 255, ) )
    pngio.write( out + '.preview.png', prev )
    print( 'tiles x %d–%d, y %d–%d; preview %s.preview.png' % ( x0, x1 - 1, y0, y1 - 1, out ) )


if __name__ == '__main__':
    main()
