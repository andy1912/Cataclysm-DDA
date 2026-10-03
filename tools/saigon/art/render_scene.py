#!/usr/bin/env python3
"""Render a generated Saigon block with the real tilesets, without the game window.

Input is the dump written by the hidden test tests/saigon_scene_dump_test.cpp:
  SAIGON_SCENE_OUT=scene.json tests/cata_test --mods=dda,saigon_2000s "[saigon_scene]"
  python3 tools/saigon/art/render_scene.py scene.json OUT.png [--scale 0.5] [--crop x0,y0,x1,y1]

Sprite lookup mirrors src/cata_tiles.cpp: "<id>_season_<season>" first, then the id,
then its looks_like chain (vehicle parts: "vp_<id>_<variant>", "vp_<id>", then
"vp_<looks_like>" and "<looks_like>").  The Saigon mod tilesets override the base
UltimateCataclysm tileset id by id, as create_tile_type does.  Connected terrain and
furniture pick their subtile and rotation with the engine's rules
(get_rotation_and_subtile); weighted variants are picked per position.  Tiles are drawn
row by row, terrain then furniture, item, vehicle, so tall sprites overlap like in game.
Not modelled: lighting, fields, monsters, z-levels above 0, item stacks beyond the top item.
"""
import argparse
import json
import os
import sys
import zlib

sys.path.insert( 0, os.path.dirname( __file__ ) )
import pngio  # noqa: E402
from derive_sprites import BaseTileset, ROOT, GFX, sheet_path  # noqa: E402

TILE = 32
SUBTILES = [ 'center', 'corner', 'edge', 't_connection', 'end_piece', 'unconnected', 'open', 'broken' ]


class Source:
    """Sprites of one tileset (base or one mod_tileset object): index -> image + geometry."""

    def __init__( self, sheets ):
        self.sheets = sheets  # list of ( start, count, path, w, h, ox, oy, cols )
        self.cache = {}

    def sprite( self, index ):
        if index in self.cache:
            return self.cache[index]
        for start, count, path, w, h, ox, oy, cols in self.sheets:
            if start <= index < start + count:
                sheet = SHEETS.get( path )
                if sheet is None:
                    sheet = SHEETS[path] = pngio.read( path )
                local = index - start
                img = pngio.Image( w, h )
                x0, y0 = ( local % cols ) * w, ( local // cols ) * h
                for y in range( h ):
                    s = ( ( y0 + y ) * sheet.width + x0 ) * 4
                    img.pixels[y * w * 4:( y + 1 ) * w * 4] = sheet.pixels[s:s + w * 4]
                self.cache[index] = ( img, ox, oy )
                return self.cache[index]
        return None


SHEETS = {}


def load_tilesets():
    tiles = {}  # id -> ( entry, Source )
    base = BaseTileset( os.path.join( ROOT, 'gfx', 'UltimateCataclysm' ) )
    sheets = [ ( s['start'], s['count'], os.path.join( base.base, s['file'] ), s['w'], s['h'], s['ox'], s['oy'],
                 s['cols'] ) for s in base.sheets ]
    src = Source( sheets )
    for sheet in base.config['tiles-new']:
        offset = ( sheet.get( 'sprite_offset_x', 0 ), sheet.get( 'sprite_offset_y', 0 ) )
        for t in sheet.get( 'tiles', [] ):
            for i in t['id'] if isinstance( t['id'], list ) else [ t['id'] ]:
                tiles[i] = ( t, src, offset )
    for name in ( 'derived_tileset.json', 'mod_tileset.json' ):  # drawn art wins over derived
        path = os.path.join( GFX, name )
        if not os.path.exists( path ):
            continue
        with open( path ) as f:
            for obj in json.load( f ):
                if 'UltimateCataclysm' not in obj.get( 'compatibility', [] ):
                    continue
                sheets = []
                start = 0
                for sheet in obj['tiles-new']:
                    w, h = sheet.get( 'sprite_width', TILE ), sheet.get( 'sprite_height', TILE )
                    p = sheet_path( sheet )
                    pw, ph = BaseTileset._dims( p )
                    count = ( pw // w ) * ( ph // h )
                    sheets.append( ( start, count, p, w, h, sheet.get( 'sprite_offset_x', 0 ),
                                     sheet.get( 'sprite_offset_y', 0 ), pw // w ) )
                    start += count
                src = Source( sheets )
                for sheet in obj['tiles-new']:
                    offset = ( sheet.get( 'sprite_offset_x', 0 ), sheet.get( 'sprite_offset_y', 0 ) )
                    for t in sheet.get( 'tiles', [] ):
                        for i in t['id'] if isinstance( t['id'], list ) else [ t['id'] ]:
                            tiles[i] = ( t, src, offset )
    return tiles


def rotation_edge_ns( rot ):
    e, w = rot & 2, rot & 4
    return 2 if e and w else 1 if e else 0 if w else 3


def rotation_edge_ew( rot ):
    n, s = rot & 8, rot & 1
    return 2 if n and s else 1 if n else 0 if s else 3


UNCONNECTED = { 0: 15, 15: 12, 8: 2, 2: 1, 1: 0, 4: 3, 10: 6, 3: 5, 5: 4, 12: 7, 14: 10, 11: 9, 7: 8, 13: 11, 9: 14,
                6: 13 }


def rotation_and_subtile( val, rot ):
    """src/cata_tiles.cpp get_rotation_and_subtile; rot 127 means no rotation group."""
    none = rot == 127
    if val == 0:
        return ( 0 if none else UNCONNECTED.get( rot, 0 ) ), 'unconnected'
    if val == 15:
        return 0, 'center'
    ends = { 8: ( 2, rotation_edge_ns ), 4: ( 1, rotation_edge_ew ), 2: ( 3, rotation_edge_ew ),
             1: ( 0, rotation_edge_ns ) }
    if val in ends:
        r, fn = ends[val]
        return ( r if none else r + 4 * fn( rot ) ), 'end_piece'
    if val == 9:
        return ( 0 if none else 2 * rotation_edge_ns( rot ) ), 'edge'
    if val == 6:
        return ( 1 if none else 1 + 2 * rotation_edge_ew( rot ) ), 'edge'
    corners = { 12: 2, 10: 3, 3: 0, 5: 1 }
    if val in corners:
        return corners[val], 'corner'
    return { 14: 2, 11: 3, 7: 0, 13: 1 }[val], 't_connection'


def pick( value, x, y ):
    """A fg/bg value -> list of sprite indices (rotations), choosing a weighted variant by position."""
    if value is None:
        return []
    if isinstance( value, int ):
        return [ value ]
    if isinstance( value, list ) and value and isinstance( value[0], dict ):
        total = sum( v.get( 'weight', 1 ) for v in value )
        r = zlib.crc32( ( '%d,%d' % ( x, y ) ).encode() ) % max( 1, total )
        for v in value:
            r -= v.get( 'weight', 1 )
            if r < 0:
                s = v['sprite']
                return s if isinstance( s, list ) else [ s ]
        return []
    if isinstance( value, list ):
        return [ v for v in value if isinstance( v, int ) ]
    return []


def rotated( img, rota ):
    rota %= 4
    if rota == 0:
        return img
    w, h = img.width, img.height
    out = pngio.Image( h if rota % 2 else w, w if rota % 2 else h )
    for y in range( h ):
        for x in range( w ):
            px = img.get( x, y )
            if rota == 1:      # 90 degrees clockwise
                out.set( h - 1 - y, x, px )
            elif rota == 2:    # flip both ways
                out.set( w - 1 - x, h - 1 - y, px )
            else:              # 90 degrees counter-clockwise
                out.set( y, w - 1 - x, px )
    return out


def blit( canvas, img, ox, oy ):
    for y in range( img.height ):
        cy = oy + y
        if not 0 <= cy < canvas.height:
            continue
        for x in range( img.width ):
            cx = ox + x
            if not 0 <= cx < canvas.width:
                continue
            i = ( y * img.width + x ) * 4
            a = img.pixels[i + 3]
            if a == 0:
                continue
            j = ( cy * canvas.width + cx ) * 4
            if a == 255:
                canvas.pixels[j:j + 3] = img.pixels[i:i + 3]
            else:
                k = a / 255
                for c in range( 3 ):
                    canvas.pixels[j + c] = int( img.pixels[i + c] * k + canvas.pixels[j + c] * ( 1 - k ) )


class Renderer:
    def __init__( self, scene, season ):
        self.tiles = load_tilesets()
        self.looks_like = scene['looks_like']
        self.season = season
        self.missing = set()

    def find( self, tid, variant='', seasonal=True ):
        seen = set()
        candidates = []
        cur = tid
        for _ in range( 10 ):
            if not cur or cur in seen:
                break
            seen.add( cur )
            if variant:
                candidates.append( cur + '_' + variant )
            if seasonal:
                candidates.append( cur + '_season_' + self.season )
            candidates.append( cur )
            ll = self.looks_like.get( cur, '' )
            if cur.startswith( 'vp_' ) and ll:
                candidates.append( 'vp_' + ll )
            cur = ll
        for c in candidates:
            if c in self.tiles:
                return self.tiles[c]
        self.missing.add( tid )
        return self.tiles.get( 'unknown' )

    def draw( self, canvas, tid, x, y, conn=0, rot=127, variant='', vrota=None, seasonal=True ):
        found = self.find( tid, variant, seasonal )
        if not found:
            return
        entry, src, ( ox, oy ) = found
        rota = 0
        if entry.get( 'multitile' ) and vrota is None:
            rota, sub = rotation_and_subtile( conn, rot )
            for extra in entry.get( 'additional_tiles', [] ):
                if extra.get( 'id' ) == sub:
                    entry = dict( extra, rotates=True )
                    break
        elif vrota is not None:
            rota = vrota
        # like tileset_loader: "rotates" defaults to "multitile"; subtiles always rotate
        rotates = entry.get( 'rotates', bool( entry.get( 'multitile' ) ) )
        for key in ( 'bg', 'fg' ):
            sprites = pick( entry.get( key ), x, y )
            if not sprites:
                continue
            if len( sprites ) > 1:
                index, turn = sprites[rota % len( sprites )], 0
            else:
                index, turn = sprites[0], ( rota if rotates and key == 'fg' else 0 )
            got = src.sprite( index )
            if not got:
                continue
            img = got[0]   # the offset is the declaring sheet's (tileset_loader parse_atlases)
            blit( canvas, rotated( img, turn ), x * TILE + ox, y * TILE + oy )


def downscale( img, factor ):
    step = int( round( 1 / factor ) )
    out = pngio.Image( img.width // step, img.height // step )
    for y in range( out.height ):
        for x in range( out.width ):
            acc = [ 0, 0, 0 ]
            for dy in range( step ):
                for dx in range( step ):
                    p = img.get( x * step + dx, y * step + dy )
                    for c in range( 3 ):
                        acc[c] += p[c]
            n = step * step
            out.set( x, y, ( acc[0] // n, acc[1] // n, acc[2] // n, 255 ) )
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument( 'scene' )
    ap.add_argument( 'out' )
    ap.add_argument( '--scale', type=float, default=1.0, help='1, 0.5 or 0.25' )
    ap.add_argument( '--crop', help='tile rectangle x0,y0,x1,y1 (inclusive)' )
    ap.add_argument( '--season', default='winter', help='the Saigon scenario starts in CDDA winter' )
    args = ap.parse_args()
    with open( args.scene ) as f:
        scene = json.load( f )
    w, h = scene['width'], scene['height']
    x0, y0, x1, y1 = ( 0, 0, w - 1, h - 1 )
    if args.crop:
        x0, y0, x1, y1 = map( int, args.crop.split( ',' ) )
    r = Renderer( scene, args.season )
    canvas = pngio.Image( ( x1 - x0 + 1 ) * TILE, ( y1 - y0 + 1 ) * TILE )
    for i in range( canvas.width * canvas.height ):
        canvas.pixels[i * 4 + 3] = 255
    tiles = scene['tiles']
    for y in range( y0, y1 + 1 ):
        for x in range( x0, x1 + 1 ):
            ter, tc, tr, furn, fc, fr, item, vp, variant, vrota = tiles[y * w + x]
            lx, ly = x - x0, y - y0
            r.draw( canvas, ter, lx, ly, tc, tr )
            if furn:
                r.draw( canvas, furn, lx, ly, fc, fr )
            if item:
                r.draw( canvas, item, lx, ly, seasonal=False )
            if vp:
                r.draw( canvas, vp, lx, ly, variant=variant, vrota=vrota, seasonal=False )
    if args.scale < 1:
        canvas = downscale( canvas, args.scale )
    pngio.write( args.out, canvas )
    print( 'wrote %s (%dx%d)' % ( args.out, canvas.width, canvas.height ) )
    if r.missing:
        print( 'drawn as unknown:', ' '.join( sorted( r.missing ) ) )


if __name__ == '__main__':
    main()
