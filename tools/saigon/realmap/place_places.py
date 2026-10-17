"""Real-map unit R4: everyday places from OpenStreetMap on their real sites.

Each place (osm_to_grid.py's "places") becomes the mod's building of that kind, on the nearest
free tile within SEARCH tiles that faces a street, turned to face it.  Supermarkets are kept only
for the chains open in 2009 (the minimarts in today's data came later).  Cemetery land is filled
with nghĩa trang blocks.
"""
import math
import re

SEARCH = 3
# W3: a military compound is mapped as one big area whose centre is often deep inside it, far
# from any street; its guard post may stand anywhere up to its gate
SEARCH_KIND = { 'military': 8 }
LANDMARK_RADIUS = 3            # a place this close to a landmark is that landmark
DIRS = [ ( 0, -1 ), ( 1, 0 ), ( 0, 1 ), ( -1, 0 ) ]          # the side a building faces: n e s w
WATER = ( 'river', 'canal', 'lake' )
KIND = {
    'fuel': 'sgn_pl_cay_xang', 'market': 'sgn_cho_1', 'pagoda': 'sgn_chua_1', 'church': 'sgn_nha_tho_1',
    'school': 'sgn_truong_1', 'hospital': 'sgn_pl_benh_vien', 'police': 'sgn_pl_cong_an',
    'supermarket': 'sgn_pl_coopmart',
    # W3: the district police headquarters and an army guard post on each OSM military site
    'police_hq': 'sgn_pa_cong_an_quan', 'military': 'sgn_pa_don_quan_su',
}
CHAINS_2009 = re.compile( r'co\.?\s?op|big ?c|maximark|metro|citimart|lotte', re.I )


def size( parts, r ):
    w = max( p[0] for p in parts ) + 1
    h = max( p[1] for p in parts ) + 1
    return ( w, h ) if r % 2 == 0 else ( h, w )


def front( x0, y0, w, h, r ):
    if r == 0:
        return [ ( x, y0 - 1 ) for x in range( x0, x0 + w ) ]
    if r == 1:
        return [ ( x0 + w, y ) for y in range( y0, y0 + h ) ]
    if r == 2:
        return [ ( x, y0 + h ) for x in range( x0, x0 + w ) ]
    return [ ( x0 - 1, y ) for y in range( y0, y0 + h ) ]


def free( world, terrain, road_tiles, tiles, W, H ):
    return all( 0 <= x < W and 0 <= y < H and ( x, y ) not in world.used and ( x, y ) not in road_tiles and
                terrain[y][x] not in WATER for x, y in tiles )


def place( world, terrain, road_tiles, buildings, places, W, H ):
    placed = {}
    missed = {}
    represented = 0
    for p in places:
        kind = p['kind']
        # the real Bến Thành, Đức Bà, Thiên Hậu ... are in the data too: their landmark stands for them
        if any( abs( p['tile'][0] - t[0] ) <= LANDMARK_RADIUS and abs( p['tile'][1] - t[1] ) <= LANDMARK_RADIUS
                for t in world.landmark_tiles ):
            represented += 1
            continue
        if kind == 'supermarket' and not CHAINS_2009.search( p.get( 'name', '' ) ):
            continue
        parts = buildings[KIND[kind]]
        ax, ay = p['tile']
        best = None
        reach = SEARCH_KIND.get( kind, SEARCH )
        for r in range( 4 ):
            w, h = size( parts, r )
            for oy in range( -reach, reach + 1 ):
                for ox in range( -reach, reach + 1 ):
                    x0, y0 = ax - w // 2 + ox, ay - h // 2 + oy
                    tiles = [ ( x, y ) for y in range( y0, y0 + h ) for x in range( x0, x0 + w ) ]
                    if not free( world, terrain, road_tiles, tiles, W, H ):
                        continue
                    f = sum( 1 for t in front( x0, y0, w, h, r ) if t in road_tiles )
                    if not f:
                        continue
                    score = 10 * f - 4 * math.hypot( ox, oy )
                    if best is None or score > best[0]:
                        best = ( score, x0, y0, r )
        if best is None:
            missed[kind] = missed.get( kind, 0 ) + 1
            continue
        _, x0, y0, r = best
        world.place( parts, x0, y0, r )
        placed[kind] = placed.get( kind, 0 ) + 1
    # cemeteries: 2 x 2 nghĩa trang blocks wherever cemetery land has room
    parts = buildings['sgn_pl_nghia_trang']
    for y in range( H - 1 ):
        for x in range( W - 1 ):
            tiles = [ ( x, y ), ( x + 1, y ), ( x, y + 1 ), ( x + 1, y + 1 ) ]
            if all( terrain[q][p] == 'cemetery' for p, q in tiles ) and free( world, terrain, road_tiles, tiles, W, H ):
                world.place( parts, x, y, ( x // 2 + y // 2 ) % 4 )
                placed['cemetery'] = placed.get( 'cemetery', 0 ) + 1
    return [ 'places: %d already stood for by a landmark; ' % represented +
             ', '.join( '%s %d' % kv for kv in sorted( placed.items() ) ) +
             ( '; no room for ' + ', '.join( '%s %d' % kv for kv in sorted( missed.items() ) ) if missed else '' ) ]
