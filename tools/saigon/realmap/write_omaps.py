#!/usr/bin/env python3
"""Real-map stage 2: turn the tile grid (osm_to_grid.py) into the overmap files the game loads.

  python3 tools/saigon/realmap/write_omaps.py GRID.json [OUT_FOLDER]

OUT_FOLDER defaults to data/mods/saigon_2000s/realmap_2009.  Writes overmap_<x>_<y>.omap.gz for the
5 x 4 overmaps (x -1..3, y -2..1: see ORIGIN_OM), every z level, marked "final" so the game adds nothing procedural on
top (doc/saigon/REALMAP_PLAN.md).  Overmaps beyond them are generated as usual (Vietmap).

v1 (unit R2b):
  roads      road pieces from the connections in the grid; bridges where a road crosses water
             (straight, north-south or east-west; the game adds the deck, supports and ramps)
  railway    sgn_duong_sat pieces along the North-South line (level crossings stay street)
  water      lake_surface: the game turns the edges into shores and adds the lake bed below
  blocks     tiles facing a street become nhà ống (5 storeys + roof) turned to face it; tiles
             inside blocks become hẻm blocks, or fields where streets are sparse (R3); farmland
             along main roads gets village shophouses
  land use   parks, warehouses, fields, marsh; airport and cemeteries are open ground until R4
  districts  the 2009 districts as named cities (districts_2009.json): overmap labels and hordes
  landmarks  the 19 landmarks on their real sites (R5, place_landmarks.py, landmarks_2009.json)
  places     fuel, markets, pagodas, churches, schools, hospitals, police, supermarkets of 2009 and
             cemeteries from the data (R4, place_places.py)

Every terrain id written is checked against the overmap_terrain definitions of dda and the mod.
"""
import glob
import json
import os
import random
import sys

HERE = os.path.dirname( os.path.abspath( __file__ ) )
ROOT = os.path.join( HERE, '..', '..', '..' )
sys.path.insert( 0, HERE )
sys.path.insert( 0, os.path.join( HERE, '..', 'art' ) )
from omap import Overmap  # noqa: E402
import place_landmarks  # noqa: E402
import classify as C  # noqa: E402
import place_places  # noqa: E402

OM = 180
# The area's overmap (1, 2) - District 1 west, District 3, District 10, south Phú Nhuận - is the
# game's overmap (0, 0): a new game looks for its start there first (game::start_game spirals out
# from the world origin), so it begins in central Saigon. The area spans overmaps -1..3, -2..1.
ORIGIN_OM = ( -1, -2 )
ROT = [ 'north', 'east', 'south', 'west' ]
DIRS = { 'n': ( 0, -1 ), 'e': ( 1, 0 ), 's': ( 0, 1 ), 'w': ( -1, 0 ) }
FACING = { 'n': 0, 'e': 1, 's': 2, 'w': 3 }
LINEAR_SUFFIX = {
    '': '_isolated', 'n': '_end_south', 'e': '_end_west', 's': '_end_north', 'w': '_end_east',
    'ns': '_ns', 'ew': '_ew', 'ne': '_ne', 'es': '_es', 'sw': '_sw', 'nw': '_wn',
    'nes': '_nes', 'new': '_new', 'nsw': '_nsw', 'esw': '_esw', 'nesw': '_nesw',
}
WATER = ( 'river', 'canal', 'lake' )


def known_terrain():
    """Every valid overmap terrain id (with its rotations) from dda and the mod."""
    ids = set()
    files = glob.glob( os.path.join( ROOT, 'data/json/overmap/**/*.json' ), recursive=True ) + \
        glob.glob( os.path.join( ROOT, 'data/mods/saigon_2000s/**/*.json' ), recursive=True )
    for f in files:
        try:
            data = json.load( open( f ) )
        except ( ValueError, UnicodeDecodeError ):
            continue
        for o in data if isinstance( data, list ) else [ data ]:
            if not isinstance( o, dict ) or o.get( 'type' ) != 'overmap_terrain' or 'id' not in o:
                continue
            flags = o.get( 'flags', [] )
            for i in o['id'] if isinstance( o['id'], list ) else [ o['id'] ]:
                ids.add( i )
                if 'LINEAR' in flags:
                    ids.update( i + s for s in LINEAR_SUFFIX.values() )
                elif 'NO_ROTATE' not in flags:
                    ids.update( i + '_' + r for r in ROT )
    return ids


def buildings():
    """The mod's city buildings: id -> list of ( dx, dy, z, terrain_with_north_suffix )."""
    out = {}
    for f in glob.glob( os.path.join( ROOT, 'data/mods/saigon_2000s/overmap/*.json' ) ):
        for o in json.load( open( f ) ):
            if o.get( 'type' ) == 'city_building':
                out[o['id']] = [ ( e['point'][0], e['point'][1], e['point'][2], e['overmap'] ) for e in o['overmaps'] ]
    return out


def rotated( ter, r ):
    """A building tile's terrain turned r quarter turns clockwise ( '_north' -> '_east' ... )."""
    for i, name in enumerate( ROT ):
        if ter.endswith( '_' + name ):
            return ter[:-len( name )] + ROT[( i + r ) % 4]
    return ter


MIN_ISLAND = 8                 # road pieces smaller than this, away from the area's edge, are dropped


def components( road_tiles ):
    seen, parts = set(), []
    for p in road_tiles:
        if p in seen:
            continue
        stack, part = [ p ], []
        seen.add( p )
        while stack:
            c = stack.pop()
            part.append( c )
            for d in road_tiles[c][0]:
                q = ( c[0] + DIRS[d][0], c[1] + DIRS[d][1] )
                if q in road_tiles and q not in seen:
                    seen.add( q )
                    stack.append( q )
        parts.append( part )
    return parts


def heal( road_tiles, land_ok ):
    """Where two separate road pieces touch (a divided road's halves, a street ending one tile short
    of another), link them once: one link per pair of pieces, so parallel streets of the same
    network are not laddered together."""
    parent = {}

    def find( p ):
        while parent.get( p, p ) != p:
            parent[p] = parent.get( parent[p], parent[p] )
            p = parent[p]
        return p
    for part in components( road_tiles ):
        for p in part:
            parent[p] = part[0]
    links = 0
    OPP = { 'n': 's', 's': 'n', 'e': 'w', 'w': 'e' }
    # dead ends first: they are where a missing link most likely belongs
    order = sorted( road_tiles, key=lambda p: len( road_tiles[p][0] ) )
    for p in order:
        for d, ( dx, dy ) in DIRS.items():
            q = ( p[0] + dx, p[1] + dy )
            if q in road_tiles and find( p ) != find( q ) and land_ok( p ) and land_ok( q ):
                c, cls, br = road_tiles[p]
                road_tiles[p] = ( ''.join( x for x in 'nesw' if x in c + d ), cls, br )
                c, cls, br = road_tiles[q]
                road_tiles[q] = ( ''.join( x for x in 'nesw' if x in c + OPP[d] ), cls, br )
                parent[find( p )] = find( q )
                links += 1
    # a dead end one free land tile short of another piece: fill the gap
    for p in [ p for p in road_tiles if len( road_tiles[p][0] ) == 1 ]:
        for d, ( dx, dy ) in DIRS.items():
            gap, q = ( p[0] + dx, p[1] + dy ), ( p[0] + 2 * dx, p[1] + 2 * dy )
            if gap in road_tiles or q not in road_tiles or find( p ) == find( q ) or not land_ok( gap ):
                continue
            road_tiles[gap] = ( ''.join( x for x in 'nesw' if x in d + OPP[d] ), road_tiles[p][1], False )
            for a, b in ( ( p, d ), ( q, OPP[d] ) ):
                c, cls, br = road_tiles[a]
                road_tiles[a] = ( ''.join( x for x in 'nesw' if x in c + b ), cls, br )
            parent[gap] = find( p )
            parent[find( p )] = find( q )
            links += 1
            break
    return links


def link( road_tiles, a, b, cls='street' ):
    """Make a and b ( 4-adjacent ) road tiles linked to each other, creating them if needed."""
    OPP = { 'n': 's', 's': 'n', 'e': 'w', 'w': 'e' }
    d = next( k for k, ( dx, dy ) in DIRS.items() if ( a[0] + dx, a[1] + dy ) == b )
    for p, x in ( ( a, d ), ( b, OPP[d] ) ):
        c, k, br = road_tiles.get( p, ( '', cls, False ) )
        road_tiles[p] = ( ''.join( y for y in 'nesw' if y in c + x ), k, br )


def unlink_all( road_tiles, p ):
    OPP = { 'n': 's', 's': 'n', 'e': 'w', 'w': 'e' }
    for d in road_tiles.pop( p )[0]:
        q = ( p[0] + DIRS[d][0], p[1] + DIRS[d][1] )
        if q in road_tiles:
            c, k, br = road_tiles[q]
            road_tiles[q] = ( c.replace( OPP[d], '' ), k, br )


def fix_crossings( road_tiles, terrain, W, H ):
    """The game's bridges are straight decks with a ramp on each end tile, and it only adds the
    ramps where a run of at least two bridge tiles ends: a one-tile bridge, a crossing that bends
    or one that ends against water or a building cannot be walked.  So: a crossing of one or two
    water tiles becomes plain road (a culvert); a longer one is rebuilt as one straight bridge from
    bank to bank along its main direction, joined to the street on the far side over land."""
    wet = lambda p: terrain[p[1]][p[0]] in WATER
    inside = lambda p: 0 <= p[0] < W and 0 <= p[1] < H
    seen = set()
    crossings = [ p for p in road_tiles if wet( p ) ]
    culverts = rebuilt = dropped = 0
    for start in crossings:
        if start in seen or start not in road_tiles:
            continue
        comp, stack = [], [ start ]
        seen.add( start )
        while stack:                                   # the crossing: linked road tiles on water
            c = stack.pop()
            comp.append( c )
            for d in road_tiles[c][0]:
                q = ( c[0] + DIRS[d][0], c[1] + DIRS[d][1] )
                if q in road_tiles and wet( q ) and q not in seen:
                    seen.add( q )
                    stack.append( q )
        cls = max( ( road_tiles[p][1] for p in comp ), key=[ 'street', 'main_street', 'boulevard' ].index )
        entries = []                                   # ( land tile, direction from it into the water )
        for c in comp:
            for d in road_tiles[c][0]:
                q = ( c[0] + DIRS[d][0], c[1] + DIRS[d][1] )
                if q in road_tiles and not wet( q ):
                    entries.append( ( q, next( k for k, v in DIRS.items() if ( q[0] + v[0], q[1] + v[1] ) == c ) ) )
        if len( comp ) <= 2:
            for c in comp:                             # a culvert: the road runs over the canal
                terrain[c[1]][c[0]] = 'open'
            culverts += 1
            continue
        for c in comp:
            unlink_all( road_tiles, c )
        if not entries:
            dropped += 1
            continue
        # the bridge starts at the entry whose way into the water, followed straight, reaches the
        # farthest other entry
        best = None
        for a, d in entries:
            for b, _ in entries:
                along = ( b[0] - a[0] ) * DIRS[d][0] + ( b[1] - a[1] ) * DIRS[d][1]
                if along > 0 and ( best is None or along > best[0] ):
                    best = ( along, a, d, b )
        if best is None:
            dropped += 1
            continue
        _, a, d, b = best
        run, p = [], ( a[0] + DIRS[d][0], a[1] + DIRS[d][1] )
        while inside( p ) and wet( p ) and len( run ) < 400:
            run.append( p )
            p = ( p[0] + DIRS[d][0], p[1] + DIRS[d][1] )
        if not inside( p ) or len( run ) >= 400:
            dropped += 1
            continue
        if len( run ) <= 2:
            for c in run:
                terrain[c[1]][c[0]] = 'open'
        prev = a
        for c in run + [ p ]:
            link( road_tiles, prev, c, cls )
            c0, k, _ = road_tiles[c]
            road_tiles[c] = ( c0, k, len( run ) > 2 and c in run )
            prev = c
        # over land from the far bank to the street the crossing used to reach
        if p != b:
            path = land_path( p, b, lambda q: inside( q ) and not wet( q ), 40 )
            for x, y in zip( path, path[1:] ):
                link( road_tiles, x, y, cls )
        rebuilt += 1
    return 'crossings: %d short ones made culverts, %d rebuilt as straight bridges, %d dropped (no far bank)' % (
        culverts, rebuilt, dropped )


def settle_bridges( road_tiles, terrain, used ):
    """Every road tile on water must belong to a straight bridge run of 2+ tiles with a road tile
    beyond each end along its axis (where the game adds the ramps); anything else is a culvert."""
    wet = lambda p: terrain[p[1]][p[0]] in WATER
    good = set()
    for p, ( c, cls, br ) in road_tiles.items():
        if not wet( p ) or p in good or p in used:
            continue
        for axis, ( d0, d1 ) in ( ( 'ns', ( 'n', 's' ) ), ( 'ew', ( 'w', 'e' ) ) ):
            if not ( set( c ) <= set( axis ) and c ):
                continue
            run = [ p ]
            for d in ( d0, d1 ):
                q = p
                while True:
                    q = ( q[0] + DIRS[d][0], q[1] + DIRS[d][1] )
                    if q in road_tiles and wet( q ) and set( road_tiles[q][0] ) <= set( axis ):
                        run.append( q )
                    else:
                        break
            ends = [ ( min( run ), d0 ), ( max( run ), d1 ) ]
            if len( run ) >= 2 and all( ( e[0] + DIRS[d][0], e[1] + DIRS[d][1] ) in road_tiles and
                                        not wet( ( e[0] + DIRS[d][0], e[1] + DIRS[d][1] ) ) for e, d in ends ):
                good.update( run )
    n = 0
    for p in list( road_tiles ):
        if wet( p ) and p not in good and p not in used:
            terrain[p[1]][p[0]] = 'open'
            n += 1
    return n


def path_to_road( starts, road_tiles, ok, limit ):
    """Shortest 4-connected path from any of `starts` (ok() tiles) to the nearest road tile, over
    ok() tiles: [start, ..., road tile], or [] when none is within `limit` steps."""
    prev = { s: None for s in starts if ok( s ) }
    frontier = list( prev )
    for _ in range( limit ):
        nxt = []
        for c in frontier:
            for dx, dy in DIRS.values():
                q = ( c[0] + dx, c[1] + dy )
                if q in prev:
                    continue
                if q in road_tiles:
                    path = [ q, c ]
                    while prev[path[-1]] is not None:
                        path.append( prev[path[-1]] )
                    return path[::-1]
                if ok( q ):
                    prev[q] = c
                    nxt.append( q )
        frontier = nxt
    return []


def land_path( a, b, ok, limit ):
    """Shortest 4-connected path from a to b over tiles where ok() holds (both ends included), or
    [] when b is not within `limit` steps."""
    prev, frontier = { a: None }, [ a ]
    for _ in range( limit ):
        nxt = []
        for c in frontier:
            for dx, dy in DIRS.values():
                q = ( c[0] + dx, c[1] + dy )
                if q not in prev and ( q == b or ok( q ) ):
                    prev[q] = c
                    nxt.append( q )
        if b in prev:
            path = [ b ]
            while prev[path[-1]] is not None:
                path.append( prev[path[-1]] )
            return path[::-1]
        frontier = nxt
    return []


def prune_islands( road_tiles, W, H ):
    parts = components( road_tiles )
    dropped = 0
    for part in parts:
        edge = any( x in ( 0, W - 1 ) or y in ( 0, H - 1 ) for x, y in part )
        if len( part ) < MIN_ISLAND and not edge:
            for p in part:
                del road_tiles[p]
            dropped += 1
    biggest = max( len( p ) for p in components( road_tiles ) )
    if biggest < 0.93 * len( road_tiles ):
        sys.exit( 'road network broken: the largest piece holds only %d of %d road tiles' % ( biggest, len( road_tiles ) ) )
    return 'road network: %d small cut-off pieces dropped; the largest network holds %.1f %% of %d road tiles' % (
        dropped, 100 * biggest / len( road_tiles ), len( road_tiles ) )


MOUTH_EVERY = 6                # one street-front tile in this many becomes an alley mouth


def groups( tiles ):
    """4-connected groups of a set of tiles."""
    seen, out = set(), []
    for p in sorted( tiles ):
        if p in seen:
            continue
        stack, part = [ p ], []
        seen.add( p )
        while stack:
            c = stack.pop()
            part.append( c )
            for dx, dy in DIRS.values():
                q = ( c[0] + dx, c[1] + dy )
                if q in tiles and q not in seen:
                    seen.add( q )
                    stack.append( q )
        out.append( part )
    return out


DENSITY_RADIUS = 15            # tiles: a 31 x 31 window, about 750 m
RURAL_DENSITY = 0.06           # below this share of street tiles a block's inside is fields, not hẻm


def road_density( road_tiles, W, H, r ):
    """Share of road tiles in the ( 2r+1 )^2 window around a tile (summed-area table)."""
    I = [ [ 0 ] * ( W + 1 ) for _ in range( H + 1 ) ]
    for y in range( H ):
        acc, cur, prev = 0, I[y + 1], I[y]
        for x in range( W ):
            acc += ( x, y ) in road_tiles
            cur[x + 1] = prev[x + 1] + acc

    def at( x, y ):
        x0, x1, y0, y1 = max( 0, x - r ), min( W, x + r + 1 ), max( 0, y - r ), min( H, y + r + 1 )
        return ( I[y1][x1] - I[y0][x1] - I[y1][x0] + I[y0][x0] ) / ( ( x1 - x0 ) * ( y1 - y0 ) )
    return at


class World:
    """The 5 x 4 overmaps as one big tile space."""

    def __init__( self, cols, rows ):
        self.cols, self.rows = cols, rows
        self.oms = { ( x, y ): Overmap( x + ORIGIN_OM[0], y + ORIGIN_OM[1] ) for x in range( cols ) for y in range( rows ) }
        self.used = set()
        self.landmarks = []            # ( id, the tiles just outside its front ), set by place_landmarks

    def set( self, x, y, z, ter ):
        self.oms[( x // OM, y // OM )].set( x % OM, y % OM, z, ter )

    def place( self, parts, x, y, r ):
        """A city building's tiles, footprint top-left at ( x, y ) after rotation r."""
        w = max( p[0] for p in parts ) + 1
        h = max( p[1] for p in parts ) + 1
        for dx, dy, z, ter in parts:
            if r == 1:
                dx, dy = h - 1 - dy, dx
            elif r == 2:
                dx, dy = w - 1 - dx, h - 1 - dy
            elif r == 3:
                dx, dy = dy, w - 1 - dx
            self.set( x + dx, y + dy, z, rotated( ter, r ) )
            if z == 0:
                self.used.add( ( x + dx, y + dy ) )


PREVIEW = [ ( 'sgn_lm_', ( 255, 0, 255 ) ), ( 'sgn_sb_runway', ( 40, 40, 46 ) ), ( 'sgn_sb_', ( 120, 122, 130 ) ), ( 'sgn_duong_sat', ( 20, 20, 20 ) ), ( 'sgn_pl_', ( 0, 200, 220 ) ), ( 'sgn_cho', ( 255, 127, 0 ) ),
            ( 'sgn_chua', ( 192, 0, 0 ) ), ( 'sgn_nha_tho', ( 255, 176, 200 ) ), ( 'sgn_truong', ( 0, 80, 255 ) ), ( 'road', ( 70, 70, 70 ) ), ( 'bridge', ( 155, 63, 200 ) ),
            ( 'lake', ( 31, 79, 176 ) ), ( 'sgn_nh_', ( 232, 150, 60 ) ), ( 'sgn_hem', ( 230, 200, 154 ) ),
            ( 'park', ( 63, 165, 72 ) ), ( 'warehouse', ( 150, 150, 150 ) ), ( 'forest_water', ( 122, 184, 160 ) ),
            ( 'field', ( 242, 237, 220 ) ) ]


def preview( world, W, H, path ):
    """z 0 at one pixel per tile, coloured by kind (landmarks magenta)."""
    import pngio
    img = pngio.Image( W, H )
    for ( ox, oy ), om in world.oms.items():
        for y in range( OM ):
            for x in range( OM ):
                ter = om.get( x, y, 0, 'field' )
                c = next( ( col for pre, col in PREVIEW if ter.startswith( pre ) ), ( 0, 0, 0 ) )
                img.set( ox * OM + x, oy * OM + y, c + ( 255, ) )
    pngio.write( path, img )


def main():
    grid_path = sys.argv[1]
    out = sys.argv[2] if len( sys.argv ) > 2 else os.path.join( ROOT, 'data/mods/saigon_2000s/realmap_2009' )
    g = json.load( open( grid_path ) )
    W, H = g['width'], g['height']
    terrain = [ [ g['legend'][c] for c in row ] for row in g['terrain'] ]
    roads = { tuple( map( int, k.split( ',' ) ) ): v for k, v in g['roads'].items() }
    valid = known_terrain()
    bld = buildings()
    rng = random.Random( 2009 )
    world = World( W // OM, H // OM )

    # ---- roads and bridges; links to tiles that are not road are dropped, lone tiles removed
    road_tiles = {}
    for p, ( conn, cls, br ) in roads.items():
        c = ''.join( d for d in conn if ( p[0] + DIRS[d][0], p[1] + DIRS[d][1] ) in roads )
        if c:
            road_tiles[p] = ( c, cls, br )
    # ---- river and canal crossings the game can build (see fix_crossings)
    print( '  ' + fix_crossings( road_tiles, terrain, W, H ) )
    # ---- road network check (R9): pieces cut off from everything (gated compounds, streets whose
    # only link was an alley) are dropped when small; report how much is one network
    print( '  road network: %d links added where separate pieces touch or end one tile apart'
           % heal( road_tiles, lambda p: 0 <= p[0] < W and 0 <= p[1] < H and terrain[p[1]][p[0]] not in WATER ) )
    print( '  ' + prune_islands( road_tiles, W, H ) )

    # ---- landmarks on their real sites (R5); minor streets under them are removed
    for line in place_landmarks.place( world, terrain, road_tiles, bld ):
        print( '  ' + line )
    # a landmark whose front touches no street (Tân Sơn Nhất's terminal stands in its aprons: the
    # airport's own roads are service roads, not in the extract) gets an access road over open land
    for lid, front in world.landmarks:
        if any( t in road_tiles for t in front ):
            continue
        path = path_to_road( front, road_tiles, lambda q: 0 <= q[0] < W and 0 <= q[1] < H and
                             terrain[q[1]][q[0]] not in WATER and q not in world.used, 60 )
        for a, b in zip( path, path[1:] ):
            link( road_tiles, a, b, 'street' )
        print( '  %s: access road of %d tiles to the nearest street' % ( lid, max( 0, len( path ) - 1 ) )
               if path else '  %s: no street within reach of its front' % lid )
    # ---- everyday places from the data (R4)
    for line in place_places.place( world, terrain, road_tiles, bld, g['places'], W, H ):
        print( '  ' + line )
    # last check on the bridges: a straight run of 2+ landing on road at both ends, or a culvert
    culverts = settle_bridges( road_tiles, terrain, world.used )
    if culverts:
        print( '  %d leftover bridge tiles made culverts' % culverts )
    bridges = 0
    for ( x, y ), ( c, cls, br ) in road_tiles.items():
        if ( x, y ) in world.used:
            continue
        if terrain[y][x] in WATER:
            # fix_crossings left only straight runs of 3+: the axis is the one the tile links along
            world.set( x, y, 0, 'bridge_north' if 'n' in c or 's' in c else 'bridge_east' )
            bridges += 1
        else:
            world.set( x, y, 0, 'road' + LINEAR_SUFFIX[c] )
        world.used.add( ( x, y ) )

    # ---- the railway into Ga Sài Gòn (gen_duong_sat.py); a street it crosses stays a street (a level
    # crossing) and the rail pieces on either side join it
    rail = { tuple( p ) for p in g.get( 'rail', [] ) }
    rails = 0
    for ( x, y ) in sorted( rail ):
        if ( x, y ) in world.used or terrain[y][x] in WATER:
            continue
        c = ''.join( d for d in 'nesw' if ( x + DIRS[d][0], y + DIRS[d][1] ) in rail )
        world.set( x, y, 0, 'sgn_duong_sat' + LINEAR_SUFFIX[c] )
        world.used.add( ( x, y ) )
        rails += 1

    # ---- water and land use; farmland along a main road is left for the village shophouses below
    LAND = { 'park': 'park', 'industrial': 'warehouse', 'farmland': 'field', 'marsh': 'forest_water',
             'cemetery': 'field', 'government': 'field', 'open': 'field',
             'runway': 'sgn_sb_runway', 'taxiway': 'sgn_sb_taxiway', 'apron': 'sgn_sb_apron' }
    UNROTATED = ( 'field', 'forest_water', 'sgn_sb_runway', 'sgn_sb_taxiway', 'sgn_sb_apron' )
    rank = { 'boulevard': 3, 'main_street': 2, 'street': 1 }

    def best_street( x, y, minimum=1 ):
        best = None
        for d, ( dx, dy ) in DIRS.items():
            q = ( x + dx, y + dy )
            if q in road_tiles and terrain[q[1]][q[0]] not in WATER and rank[road_tiles[q][1]] >= minimum:
                score = rank[road_tiles[q][1]] + rng.random() * 0.1
                if best is None or score > best[0]:
                    best = ( score, d )
        return best
    for y in range( H ):
        for x in range( W ):
            if ( x, y ) in world.used:
                continue
            t = terrain[y][x]
            if t in WATER:
                world.set( x, y, 0, 'lake_surface' )
                world.used.add( ( x, y ) )
            elif t == 'farmland' and best_street( x, y, 2 ) and rng.random() < 0.6:
                continue
            elif t in LAND:
                ter = LAND[t]
                world.set( x, y, 0, ter if ter in UNROTATED else ter + '_' + ROT[rng.randrange( 4 )] )
                world.used.add( ( x, y ) )

    # ---- ferry landings (ferries_2009.json): a dock on the water tile nearest each anchor that
    # borders a street, the pier towards the land
    docks = 0
    for f in json.load( open( os.path.join( HERE, 'ferries_2009.json' ) ) )['ferries']:
        ax, ay = ( int( v ) for v in C.latlon_to_tile( f['lat'], f['lon'] ) )
        best = None
        for y in range( ay - 8, ay + 9 ):
            for x in range( ax - 8, ax + 9 ):
                if not ( 0 <= x < W and 0 <= y < H ) or terrain[y][x] not in WATER or ( x, y ) in road_tiles:
                    continue
                for d, ( dx, dy ) in DIRS.items():
                    q = ( x + dx, y + dy )
                    if not ( 0 <= q[0] < W and 0 <= q[1] < H ) or terrain[q[1]][q[0]] in WATER:
                        continue
                    # the bank tile is the street, or open ground left between the street and the pier
                    on_street = q in road_tiles
                    near_street = q not in world.used and any( ( q[0] + ex, q[1] + ey ) in road_tiles and
                                                               terrain[q[1] + ey][q[0] + ex] not in WATER
                                                               for ex, ey in DIRS.values() )
                    # with no street near (Thủ Thiêm's marsh bank in 2009) any open bank will do
                    open_bank = q not in world.used or world.oms[( q[0] // OM, q[1] // OM )].get(
                        q[0] % OM, q[1] % OM, 0, '' ) in ( 'field', 'forest_water' )
                    if on_street or near_street or open_bank:
                        dist = abs( x - ax ) + abs( y - ay ) + ( 0 if on_street else 1 if near_street else 20 )
                        if best is None or dist < best[0]:
                            best = ( dist, x, y, d, None if on_street or q in world.used else q )
        if best is None:
            print( '  no landing for %s' % f['name'] )
            continue
        _, x, y, d, bank = best
        world.set( x, y, 0, 'sgn_ben_pha_' + ROT[FACING[d]] )
        if bank:
            world.set( bank[0], bank[1], 0, 'field' )
            world.used.add( bank )
        docks += 1
    print( '  %d ferry landings' % docks )

    # ---- city blocks: frontage shophouses facing the best street; inside, hẻm blocks where the city
    # was dense in 2009 and fields where it was not (R3: few named streets within ~750 m)
    density = road_density( road_tiles, W, H, DENSITY_RADIUS )
    nha_ong, hem = bld['sgn_nhaong_row_1'], bld['sgn_hem_block_1']
    front, inside = {}, set()
    fields = 0
    for y in range( H ):
        for x in range( W ):
            if ( x, y ) in world.used:
                continue
            best = best_street( x, y )
            if best:
                front[( x, y )] = best[1]
            elif density( x, y ) < RURAL_DENSITY:
                world.set( x, y, 0, 'field' )
                world.used.add( ( x, y ) )
                fields += 1
            else:
                inside.add( ( x, y ) )
    # alley mouths (đầu hẻm): a hẻm block opens its alleys only towards roads, canals and other
    # hẻm blocks, so every network of inner hẻm blocks gets street-front tiles turned into hẻm
    # blocks: about one in MOUTH_EVERY of the frontage it touches, at least one
    mouths = set()
    sealed = 0
    for part in groups( set( inside ) ):
        touching = sorted( { q for p in part for q in ( ( p[0] + dx, p[1] + dy ) for dx, dy in DIRS.values() )
                             if q in front } )
        if not touching:
            # boxed in by parks, landmarks, places or water: an open lot, not a sealed alley maze
            for p in part:
                world.set( p[0], p[1], 0, 'field' )
                world.used.add( p )
                inside.discard( p )
            sealed += 1
            continue
        mouths.update( touching[::MOUTH_EVERY] )
    fronts = inner = 0
    for p, d in front.items():
        if p in mouths:
            world.place( hem, p[0], p[1], FACING[d] )
            inner += 1
        else:
            world.place( nha_ong, p[0], p[1], FACING[d] )
            fronts += 1
    for p in inside:
        world.place( hem, p[0], p[1], rng.randrange( 4 ) )
        inner += 1
    print( '  hẻm: %d alley mouths on the streets; %d boxed-in pieces with no street frontage left as open lots'
           % ( len( mouths ), sealed ) )

    # ---- the 2009 districts as the overmap's cities (names, hordes)
    for d in json.load( open( os.path.join( HERE, 'districts_2009.json' ) ) )['districts']:
        x, y = ( int( v ) for v in C.latlon_to_tile( d['lat'], d['lon'] ) )
        world.oms[( x // OM, y // OM )].cities.append( { 'name': d['name'], 'x': x % OM, 'y': y % OM,
                                                        'size': d['size'], 'population': d['population'] } )

    # ---- check and write
    bad = set()
    for om in world.oms.values():
        for ( x, y, z ), ter in om.cells.items():
            if ter not in valid:
                bad.add( ter )
    if bad:
        sys.exit( 'unknown terrain ids: %s' % ', '.join( sorted( bad )[:20] ) )
    os.makedirs( out, exist_ok=True )
    for om in world.oms.values():
        om.write( out )
    preview( world, W, H, os.path.splitext( grid_path )[0].replace( '.grid', '' ) + '.omap.png' )
    print( 'wrote %d overmaps to %s: %d road tiles (%d bridges), %d railway tiles, %d shophouse fronts, %d hẻm blocks, '
           '%d fields inside sparse blocks'
           % ( len( world.oms ), os.path.relpath( out, ROOT ), len( road_tiles ), bridges, rails, fronts, inner, fields ) )


if __name__ == '__main__':
    main()
