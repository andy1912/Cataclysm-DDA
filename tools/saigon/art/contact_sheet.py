#!/usr/bin/env python3
"""Labelled contact sheet of sprites, for reviewing art (no dependencies).

  python3 tools/saigon/art/contact_sheet.py OUT.png ID [ID ...]
      first sprite of each id from the installed UltimateCataclysm tileset, with the
      Saigon mod's override (derived or hand-drawn/generated) beside it when one exists
  python3 tools/saigon/art/contact_sheet.py OUT.png --files A.png [B.png ...]
      arbitrary PNG files, labelled with their file names

Sprites are scaled 3x on a mid-grey checker so transparent edges stay visible.
"""
import json
import os
import sys

sys.path.insert( 0, os.path.dirname( __file__ ) )
import pngio  # noqa: E402
from derive_sprites import BaseTileset, ROOT, GFX, sheet_path  # noqa: E402

SCALE = int( os.environ.get( "SCALE", 3 ) )
CELL_W = int( os.environ.get( "CELL", 2 * 32 ) ) * SCALE + 12
# 3x5 font: each glyph is 5 rows of 3 bits
FONT = {
    'a': '010101111101101', 'b': '110101110101110', 'c': '011100100100011', 'd': '110101101101110',
    'e': '111100110100111', 'f': '111100110100100', 'g': '011100101101011', 'h': '101101111101101',
    'i': '111010010010111', 'j': '001001001101010', 'k': '101101110101101', 'l': '100100100100111',
    'm': '101111111101101', 'n': '110101101101101', 'o': '010101101101010', 'p': '110101110100100',
    'q': '010101101110011', 'r': '110101110101101', 's': '011100010001110', 't': '111010010010010',
    'u': '101101101101111', 'v': '101101101101010', 'w': '101101111111101', 'x': '101101010101101',
    'y': '101101010010010', 'z': '111001010100111', '0': '111101101101111', '1': '010110010010111',
    '2': '110001010100111', '3': '110001010001110', '4': '101101111001001', '5': '111100110001110',
    '6': '011100111101111', '7': '111001010010010', '8': '111101111101111', '9': '111101111001110',
    '_': '000000000000111', '.': '000000000000010', '-': '000000111000000', ' ': '000000000000000',
}


def text( img, x, y, s, rgba=( 20, 20, 20, 255 ) ):
    for ch in s.lower():
        glyph = FONT.get( ch, FONT['.'] )
        for i, bit in enumerate( glyph ):
            if bit == '1':
                px, py = x + i % 3, y + i // 3
                if 0 <= px < img.width and 0 <= py < img.height:
                    img.set( px, py, rgba )
        x += 4


def blit_scaled( dst, src, ox, oy ):
    for y in range( src.height ):
        for x in range( src.width ):
            r, g, b, a = src.get( x, y )
            if a == 0:
                continue
            for dy in range( SCALE ):
                for dx in range( SCALE ):
                    px, py = ox + x * SCALE + dx, oy + y * SCALE + dy
                    if 0 <= px < dst.width and 0 <= py < dst.height:
                        br, bg, bb, _ = dst.get( px, py )
                        k = a / 255
                        dst.set( px, py, ( int( r * k + br * ( 1 - k ) ), int( g * k + bg * ( 1 - k ) ),
                                           int( b * k + bb * ( 1 - k ) ), 255 ) )


def checker( img, ox, oy, w, h ):
    for y in range( h ):
        for x in range( w ):
            c = 150 if ( ( x // 8 ) + ( y // 8 ) ) % 2 else 170
            img.set( ox + x, oy + y, ( c, c, c, 255 ) )


def first_index( entry ):
    fg = entry.get( 'fg', entry.get( 'bg' ) )
    while isinstance( fg, list ) and fg:
        fg = fg[0]
    if isinstance( fg, dict ):
        fg = fg.get( 'sprite' )
        while isinstance( fg, list ) and fg:
            fg = fg[0]
    return fg if isinstance( fg, int ) else None


class ModTileset:
    """Sprites of the Saigon mod tilesets that target UltimateCataclysm."""

    def __init__( self ):
        self.tiles = {}
        self.sheets = []
        for name in sorted( os.listdir( GFX ) ):
            if not name.endswith( '.json' ):
                continue
            with open( os.path.join( GFX, name ) ) as f:
                data = json.load( f )
            for obj in data:
                if obj.get( 'type' ) != 'mod_tileset' or 'UltimateCataclysm' not in obj['compatibility']:
                    continue
                start = 0
                sheets = []
                for sheet in obj['tiles-new']:
                    w, h = sheet.get( 'sprite_width', 32 ), sheet.get( 'sprite_height', 32 )
                    path = sheet_path( sheet )
                    pw, ph = BaseTileset._dims( path )
                    count = ( pw // w ) * ( ph // h )
                    sheets.append( ( start, count, path, w, h, pw // w ) )
                    start += count
                for sheet in obj['tiles-new']:
                    for t in sheet.get( 'tiles', [] ):
                        for i in t['id'] if isinstance( t['id'], list ) else [ t['id'] ]:
                            self.tiles[i] = ( t, sheets )
        self.cache = {}

    def sprite( self, sid ):
        if sid not in self.tiles:
            return None
        entry, sheets = self.tiles[sid]
        idx = first_index( entry )
        for start, count, path, w, h, cols in sheets:
            if idx is not None and start <= idx < start + count:
                if path not in self.cache:
                    self.cache[path] = pngio.read( path )
                sheet = self.cache[path]
                local = idx - start
                img = pngio.Image( w, h )
                for y in range( h ):
                    for x in range( w ):
                        img.set( x, y, sheet.get( ( local % cols ) * w + x, ( local // cols ) * h + y ) )
                return img
        return None


def main():
    if len( sys.argv ) < 3:
        sys.exit( __doc__ )
    out = sys.argv[1]
    cells = []  # ( label, [images] )
    if sys.argv[2] == '--files':
        for path in sys.argv[3:]:
            cells.append( ( os.path.basename( path )[:-4], [ pngio.read( path ) ] ) )
    else:
        base = BaseTileset( os.path.join( ROOT, 'gfx', 'UltimateCataclysm' ) )
        mod = ModTileset()
        for sid in sys.argv[2:]:
            imgs = []
            if sid in base.tiles and first_index( base.tiles[sid] ) is not None:
                imgs.append( base.sprite( first_index( base.tiles[sid] ) )[0] )
            override = mod.sprite( sid )
            if override is not None:
                imgs.append( override )
            cells.append( ( sid, imgs ) )
    cols = 6
    cell_h = int( os.environ.get( "CELLH", 64 ) ) * SCALE + 14
    rows = ( len( cells ) + cols - 1 ) // cols
    sheet = pngio.Image( cols * CELL_W, max( 1, rows ) * cell_h )
    for i in range( sheet.width * sheet.height ):
        sheet.pixels[i * 4:i * 4 + 4] = bytes( ( 235, 235, 235, 255 ) )
    for n, ( label, imgs ) in enumerate( cells ):
        ox, oy = ( n % cols ) * CELL_W, ( n // cols ) * cell_h
        text( sheet, ox + 2, oy + 2, label[:CELL_W // 4 - 1] )
        x = ox + 2
        for img in imgs:
            checker( sheet, x, oy + 10, img.width * SCALE, img.height * SCALE )
            blit_scaled( sheet, img, x, oy + 10 )
            x += img.width * SCALE + 4
        if not imgs:
            text( sheet, ox + 2, oy + 14, 'no sprite', ( 200, 0, 0, 255 ) )
    pngio.write( out, sheet )
    print( 'wrote %s (%d cells)' % ( out, len( cells ) ) )


if __name__ == '__main__':
    main()
