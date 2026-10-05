"""Real-map unit R5: put the mod's 19 landmarks on their real sites (landmarks_2009.json).

Each landmark's footprint is centred on its anchor, then every shift of up to SEARCH tiles and all
four facings are scored: never on a boulevard or main street (except a roundabout landmark, which
replaces its road tile), as little water and minor street as possible, the front on as much street
as possible, as near the anchor as possible.  Minor streets under the chosen footprint are removed
and the links of their neighbours cut, so no road runs into a wall.
"""
import json
import math
import os

import classify as C

HERE = os.path.dirname( os.path.abspath( __file__ ) )
SEARCH = 3
DIRS = { 'n': ( 0, -1 ), 'e': ( 1, 0 ), 's': ( 0, 1 ), 'w': ( -1, 0 ) }
OPP = { 'n': 's', 's': 'n', 'e': 'w', 'w': 'e' }
WATER = ( 'river', 'canal', 'lake' )
MAJOR = ( 'boulevard', 'main_street' )


def footprint( parts, r ):
    w = max( p[0] for p in parts ) + 1
    h = max( p[1] for p in parts ) + 1
    return ( w, h ) if r % 2 == 0 else ( h, w )


def front_edge( x0, y0, w, h, r ):
    """The tiles just outside the side the landmark faces ( r: 0 north, 1 east, 2 south, 3 west )."""
    if r == 0:
        return [ ( x, y0 - 1 ) for x in range( x0, x0 + w ) ]
    if r == 1:
        return [ ( x0 + w, y ) for y in range( y0, y0 + h ) ]
    if r == 2:
        return [ ( x, y0 + h ) for x in range( x0, x0 + w ) ]
    return [ ( x0 - 1, y ) for y in range( y0, y0 + h ) ]


def remove_road( road_tiles, p ):
    for d in road_tiles.pop( p )[0]:
        q = ( p[0] + DIRS[d][0], p[1] + DIRS[d][1] )
        if q in road_tiles:
            c, cls, br = road_tiles[q]
            road_tiles[q] = ( c.replace( OPP[d], '' ), cls, br )


def place( world, terrain, road_tiles, buildings ):
    data = json.load( open( os.path.join( HERE, 'landmarks_2009.json' ) ) )['landmarks']
    report = []
    for lm in data:
        parts = buildings[lm['id']]
        ax, ay = C.latlon_to_tile( lm['lat'], lm['lon'] )
        on_road = lm.get( 'on_road', False )
        best = None
        facings = [ [ 'north', 'east', 'south', 'west' ].index( lm['facing'] ) ] if 'facing' in lm else range( 4 )
        for r in facings:
            w, h = footprint( parts, r )
            for oy in range( -SEARCH, SEARCH + 1 ):
                for ox in range( -SEARCH, SEARCH + 1 ):
                    x0, y0 = int( ax - w / 2 + 0.5 ) + ox, int( ay - h / 2 + 0.5 ) + oy
                    tiles = [ ( x, y ) for y in range( y0, y0 + h ) for x in range( x0, x0 + w ) ]
                    if any( t in world.used for t in tiles ):
                        continue
                    major = sum( 1 for t in tiles if t in road_tiles and road_tiles[t][1] in MAJOR )
                    if major and not on_road:
                        continue
                    water = sum( 1 for t in tiles if terrain[t[1]][t[0]] in WATER )
                    minor = sum( 1 for t in tiles if t in road_tiles ) - major
                    front = sum( 1 + ( road_tiles[t][1] in MAJOR ) for t in front_edge( x0, y0, w, h, r ) if t in road_tiles )
                    score = 10 * front - 15 * minor - 60 * water - 4 * math.hypot( ox, oy ) + ( 100 * major if on_road else 0 )
                    if best is None or score > best[0]:
                        best = ( score, x0, y0, r, tiles, minor, water )
        if best is None:
            report.append( '%s: no room near its site' % lm['id'] )
            continue
        _, x0, y0, r, tiles, minor, water = best
        for t in tiles:
            if t in road_tiles and not on_road:
                remove_road( road_tiles, t )
            elif t in road_tiles:
                road_tiles.pop( t )
        world.place( parts, x0, y0, r )
        cx, cy = x0 + footprint( parts, r )[0] / 2, y0 + footprint( parts, r )[1] / 2
        report.append( '%-22s at %3d,%3d facing %-5s %3.0f m from its site, %d minor street tiles removed%s'
                       % ( lm['id'], x0, y0, [ 'north', 'east', 'south', 'west' ][r],
                           C.TILE_M * math.hypot( cx - ax, cy - ay ), minor, ', %d water tiles' % water if water else '' ) )
    return report
