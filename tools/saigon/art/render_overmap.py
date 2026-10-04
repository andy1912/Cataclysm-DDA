#!/usr/bin/env python3
"""Render one generated Saigon overmap with the real overmap tilesets, without the game window.

Input is the dump written by the hidden test saigon_overmap_dump (tests/saigon_scene_dump_test.cpp):
  SAIGON_OVERMAP_OUT=om.json tests/cata_test --mods=dda,saigon_2000s "[saigon_overmap]"
  python3 tools/saigon/art/render_overmap.py om.json OUT.png [--scale 0.5] [--crop x0,y0,x1,y1]
      [--landmarks LIST.md] [--no-outline] [--zoom 3]

Sprite lookup mirrors cata_tiles for OVERMAP_TERRAIN: the oter type id (with the season
suffix first), then the type's looks_like list, recursively.  The Saigon mod's
derived_overmap_tileset.json overrides Larwick Overmap id by id.  Connected and water
terrain get their subtile from the S/E/W/N bits (get_rotation_and_subtile with rot_to -1);
other terrain is rotated by its direction.  Ids with no sprite fall back to a flat colour
and are listed.

Every District 1 landmark (sgn_lm_*) gets a coloured outline around its footprint;
--landmarks writes a markdown table of colour, landmark and OMT position.
"""

import argparse
import json
import os
import sys

sys.path.insert( 0, os.path.dirname( __file__ ) )
import pngio  # noqa: E402
from derive_sprites import BaseTileset, ROOT, GFX, sheet_path  # noqa: E402
from render_scene import Source, rotation_and_subtile, pick, rotated, blit, downscale  # noqa: E402

TILE = 16
COMPAT = 'Larwick Overmap'

# outline colours for the landmarks (RGB), in the order they are first found
LANDMARK_COLOURS = [ ( 'red', ( 255, 64, 64 ) ), ( 'yellow', ( 255, 220, 0 ) ), ( 'blue', ( 64, 160, 255 ) ),
                     ( 'purple', ( 200, 80, 255 ) ), ( 'green', ( 0, 230, 120 ) ), ( 'orange', ( 255, 128, 0 ) ),
                     ( 'white', ( 255, 255, 255 ) ), ( 'pink', ( 255, 105, 180 ) ), ( 'lime', ( 170, 255, 60 ) ),
                     ( 'cyan', ( 0, 220, 255 ) ) ]

LANDMARK_NAMES = {
    'ben_thanh': 'Chợ Bến Thành', 'duc_ba': 'Nhà thờ Đức Bà', 'buu_dien': 'Bưu điện Thành phố',
    'nha_hat': 'Nhà hát Thành phố', 'ubnd_tp': 'UBND Thành phố', 'dinh_doc_lap': 'Dinh Độc Lập',
    'thien_hau': 'Chùa Bà Thiên Hậu', 'ngoc_hoang': 'Chùa Ngọc Hoàng', 'binh_tay': 'Chợ Bình Tây',
}


def load_tilesets():
    tiles = {}  # id -> ( entry, Source, offset )
    base = BaseTileset( os.path.join( ROOT, 'gfx', 'Larwick_Overmap' ) )
    src = Source( [ ( s['start'], s['count'], os.path.join( base.base, s['file'] ), s['w'], s['h'], s['ox'], s['oy'],
                      s['cols'] ) for s in base.sheets ] )
    for sheet in base.config['tiles-new']:
        offset = ( sheet.get( 'sprite_offset_x', 0 ), sheet.get( 'sprite_offset_y', 0 ) )
        for t in sheet.get( 'tiles', [] ):
            for i in t['id'] if isinstance( t['id'], list ) else [ t['id'] ]:
                tiles[i] = ( t, src, offset )
    for name in ( 'derived_overmap_tileset.json', 'mod_overmap_tileset.json' ):  # hand art wins
        path = os.path.join( GFX, name )
        if not os.path.exists( path ):
            continue
        with open( path ) as f:
            for obj in json.load( f ):
                if COMPAT not in obj.get( 'compatibility', [] ):
                    continue
                sheets = []
                start = 0
                for sheet in obj['tiles-new']:
                    w, h = sheet.get( 'sprite_width', TILE ), sheet.get( 'sprite_height', TILE )
                    p = sheet_path( sheet )
                    pw, ph = BaseTileset._dims( p )
                    sheets.append( ( start, ( pw // w ) * ( ph // h ), p, w, h, sheet.get( 'sprite_offset_x', 0 ),
                                     sheet.get( 'sprite_offset_y', 0 ), pw // w ) )
                    start += ( pw // w ) * ( ph // h )
                msrc = Source( sheets )
                for sheet in obj['tiles-new']:
                    offset = ( sheet.get( 'sprite_offset_x', 0 ), sheet.get( 'sprite_offset_y', 0 ) )
                    for t in sheet.get( 'tiles', [] ):
                        for i in t['id'] if isinstance( t['id'], list ) else [ t['id'] ]:
                            tiles[i] = ( t, msrc, offset )
    return tiles


class Renderer:
    def __init__( self, dump, season ):
        self.tiles = load_tilesets()
        self.looks_like = dump['looks_like']
        self.season = season
        self.missing = set()
        self.cache = {}

    def find( self, tid, depth=10 ):
        if depth <= 0:
            return None
        for c in ( tid + '_season_' + self.season, tid ):
            if c in self.tiles:
                return self.tiles[c]
        for ll in self.looks_like.get( tid, [] ):
            got = self.find( ll, depth - 1 )
            if got:
                return got
        return None

    def sprite( self, src, index, turn ):
        key = ( id( src ), index, turn % 4 )
        if key not in self.cache:
            got = src.sprite( index )
            self.cache[key] = rotated( got[0], turn ) if got else None
        return self.cache[key]

    def draw( self, canvas, tid, x, y, rot, conn ):
        found = self.find( tid )
        if not found:
            self.missing.add( tid )
            return False
        entry, src, ( ox, oy ) = found
        if conn >= 0:
            rota, sub = rotation_and_subtile( conn, -1 )
            if entry.get( 'multitile' ):
                for extra in entry.get( 'additional_tiles', [] ):
                    if extra.get( 'id' ) == sub:
                        entry = dict( extra, rotates=True )
                        break
        else:
            rota = rot
        rotates = entry.get( 'rotates', bool( entry.get( 'multitile' ) ) )
        for key in ( 'bg', 'fg' ):
            sprites = pick( entry.get( key ), x, y )
            if not sprites:
                continue
            if len( sprites ) > 1:
                index, turn = sprites[rota % len( sprites )], 0
            else:
                index, turn = sprites[0], ( rota if rotates and key == 'fg' else 0 )
            img = self.sprite( src, index, turn )
            if img:
                blit( canvas, img, x * TILE + ox, y * TILE + oy )
        return True


def outline( canvas, x0, y0, x1, y1, rgb, width=2 ):
    for t in range( width ):
        for x in range( x0 + t, x1 - t + 1 ):
            for y in ( y0 + t, y1 - t ):
                if 0 <= x < canvas.width and 0 <= y < canvas.height:
                    canvas.set( x, y, rgb + ( 255, ) )
        for y in range( y0 + t, y1 - t + 1 ):
            for x in ( x0 + t, x1 - t ):
                if 0 <= x < canvas.width and 0 <= y < canvas.height:
                    canvas.set( x, y, rgb + ( 255, ) )


def landmarks( dump ):
    """sgn_lm_<name>_<x><y>[_z..|_b] footprints at z0 -> { name: ( x0, y0, x1, y1 ) } in OMT."""
    w = dump['width']
    found = {}
    for i, ( tid, _rot, _conn ) in enumerate( dump['tiles'] ):
        if not tid.startswith( 'sgn_lm_' ):
            continue
        name = tid[len( 'sgn_lm_' ):].rsplit( '_', 1 )[0]
        x, y = i % w, i // w
        x0, y0, x1, y1 = found.get( name, ( x, y, x, y ) )
        found[name] = ( min( x0, x ), min( y0, y ), max( x1, x ), max( y1, y ) )
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument( 'dump' )
    ap.add_argument( 'out' )
    ap.add_argument( '--scale', type=float, default=1.0, help='1, 0.5 or 0.25' )
    ap.add_argument( '--crop', help='OMT rectangle x0,y0,x1,y1 (inclusive)' )
    ap.add_argument( '--season', default='summer' )
    ap.add_argument( '--landmarks', help='write a markdown table of the outlined landmarks here' )
    ap.add_argument( '--no-outline', action='store_true', help='do not outline the landmarks' )
    ap.add_argument( '--zoom', type=int, default=1, help='enlarge N times, nearest neighbour' )
    args = ap.parse_args()
    with open( args.dump ) as f:
        dump = json.load( f )
    w, h = dump['width'], dump['height']
    x0, y0, x1, y1 = 0, 0, w - 1, h - 1
    if args.crop:
        x0, y0, x1, y1 = map( int, args.crop.split( ',' ) )
    r = Renderer( dump, args.season )
    canvas = pngio.Image( ( x1 - x0 + 1 ) * TILE, ( y1 - y0 + 1 ) * TILE )
    for i in range( canvas.width * canvas.height ):
        canvas.pixels[i * 4:i * 4 + 4] = bytes( ( 20, 20, 24, 255 ) )
    for y in range( y0, y1 + 1 ):
        for x in range( x0, x1 + 1 ):
            tid, rot, conn = dump['tiles'][y * w + x]
            r.draw( canvas, tid, x - x0, y - y0, rot, conn )
    rows = []
    for n, ( name, ( lx0, ly0, lx1, ly1 ) ) in enumerate( sorted( landmarks( dump ).items() ) ):
        colour, rgb = LANDMARK_COLOURS[n % len( LANDMARK_COLOURS )]
        if not args.no_outline:
                outline( canvas, ( lx0 - x0 ) * TILE, ( ly0 - y0 ) * TILE, ( lx1 - x0 + 1 ) * TILE - 1,
                     ( ly1 - y0 + 1 ) * TILE - 1, rgb, 3 )
        rows.append( '| %s | %s | %d,%d | %d×%d |' % ( colour, LANDMARK_NAMES.get( name, name ), lx0, ly0,
                                                     lx1 - lx0 + 1, ly1 - ly0 + 1 ) )
    if args.scale < 1:
        canvas = downscale( canvas, args.scale )
    if args.zoom > 1:
        k = args.zoom
        big = pngio.Image( canvas.width * k, canvas.height * k )
        for y in range( big.height ):
            row = canvas.pixels[( y // k ) * canvas.width * 4:( y // k + 1 ) * canvas.width * 4]
            big.pixels[y * big.width * 4:( y + 1 ) * big.width * 4] = bytes(
                b for x in range( canvas.width ) for _ in range( k ) for b in row[x * 4:x * 4 + 4] )
        canvas = big
    pngio.write( args.out, canvas )
    print( '%s (%dx%d)' % ( args.out, canvas.width, canvas.height ) )
    if r.missing:
        print( 'no sprite: ' + ' '.join( sorted( r.missing ) ) )
    if args.landmarks:
        with open( args.landmarks, 'w' ) as f:
            f.write( '| Outline | Landmark | OMT x,y (north-west) | Size |\n|---|---|---|---|\n' )
            f.write( '\n'.join( rows ) + '\n' )


if __name__ == '__main__':
    main()
