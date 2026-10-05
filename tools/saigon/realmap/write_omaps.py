#!/usr/bin/env python3
"""Real-map stage 2: turn the tile grid (osm_to_grid.py) into the overmap files the game loads.

  python3 tools/saigon/realmap/write_omaps.py GRID.json [OUT_FOLDER]

OUT_FOLDER defaults to data/mods/saigon_2000s/realmap_2009.  Writes overmap_<x>_<y>.omap.gz for the
5 x 4 overmaps (x -1..3, y -2..1: see ORIGIN_OM), every z level, marked "final" so the game adds nothing procedural on
top (doc/saigon/REALMAP_PLAN.md).  Overmaps beyond them are generated as usual (Vietmap).

v1 (unit R2b):
  roads      road pieces from the connections in the grid; bridges where a road crosses water
             (straight, north-south or east-west; the game adds the deck, supports and ramps)
  water      lake_surface: the game turns the edges into shores and adds the lake bed below
  blocks     tiles facing a street become nhà ống (5 storeys + roof) turned to face it; tiles
             inside blocks become hẻm blocks
  land use   parks, warehouses, fields, marsh; airport and cemeteries are open ground until R4
  landmarks  the 19 landmarks on their real sites (R5, place_landmarks.py, landmarks_2009.json)
Places come in R4.

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


class World:
    """The 5 x 4 overmaps as one big tile space."""

    def __init__( self, cols, rows ):
        self.cols, self.rows = cols, rows
        self.oms = { ( x, y ): Overmap( x + ORIGIN_OM[0], y + ORIGIN_OM[1] ) for x in range( cols ) for y in range( rows ) }
        self.used = set()

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


PREVIEW = [ ( 'sgn_lm_', ( 255, 0, 255 ) ), ( 'road', ( 70, 70, 70 ) ), ( 'bridge', ( 155, 63, 200 ) ),
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
    # ---- landmarks on their real sites (R5); minor streets under them are removed
    for line in place_landmarks.place( world, terrain, road_tiles, bld ):
        print( '  ' + line )
    bridges = 0
    for ( x, y ), ( c, cls, br ) in road_tiles.items():
        if ( x, y ) in world.used:
            continue
        if terrain[y][x] in WATER:
            # the game's bridges run straight: keep the axis with the most links
            ns = ( 'n' in c ) + ( 's' in c )
            ew = ( 'e' in c ) + ( 'w' in c )
            world.set( x, y, 0, 'bridge_north' if ns >= ew else 'bridge_east' )
            bridges += 1
        else:
            world.set( x, y, 0, 'road' + LINEAR_SUFFIX[c] )
        world.used.add( ( x, y ) )

    # ---- water and land use
    LAND = { 'park': 'park', 'industrial': 'warehouse', 'farmland': 'field', 'marsh': 'forest_water',
             'cemetery': 'field', 'government': 'field', 'open': 'field' }
    for y in range( H ):
        for x in range( W ):
            if ( x, y ) in world.used:
                continue
            t = terrain[y][x]
            if t in WATER:
                world.set( x, y, 0, 'lake_surface' )
                world.used.add( ( x, y ) )
            elif t in LAND:
                ter = LAND[t]
                world.set( x, y, 0, ter if ter in ( 'field', 'forest_water' ) else ter + '_' + ROT[rng.randrange( 4 )] )
                world.used.add( ( x, y ) )

    # ---- city blocks: frontage shophouses facing the best street, hẻm blocks inside
    rank = { 'boulevard': 3, 'main_street': 2, 'street': 1 }
    nha_ong, hem = bld['sgn_nhaong_row_1'], bld['sgn_hem_block_1']
    fronts = inner = 0
    for y in range( H ):
        for x in range( W ):
            if ( x, y ) in world.used:
                continue
            best = None
            for d, ( dx, dy ) in DIRS.items():
                q = ( x + dx, y + dy )
                if q in road_tiles and terrain[q[1]][q[0]] not in WATER:
                    score = rank[road_tiles[q][1]] + rng.random() * 0.1
                    if best is None or score > best[0]:
                        best = ( score, d )
            if best:
                world.place( nha_ong, x, y, FACING[best[1]] )
                fronts += 1
            else:
                world.place( hem, x, y, rng.randrange( 4 ) )
                inner += 1

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
    print( 'wrote %d overmaps to %s: %d road tiles (%d bridges), %d shophouse fronts, %d hẻm blocks'
           % ( len( world.oms ), os.path.relpath( out, ROOT ), len( road_tiles ), bridges, fronts, inner ) )


if __name__ == '__main__':
    main()
