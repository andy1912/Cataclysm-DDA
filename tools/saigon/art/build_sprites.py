#!/usr/bin/env python3
"""Pack Saigon sprites into the mod's mod_tileset (no Pillow/pyvips needed).

Source layout (one PNG per game id, file name = id):
  art/saigon/tiles32/<anything>/<id>.png      32x32, for the top-down base tileset
  art/saigon/tiles32/<anything>/<id>.json     optional extra tile keys, e.g.
                                              {"rotates": true} or {"bg": ...}
  art/saigon/overmap16/<anything>/<id>.png    16x16 overmap icons (oter ids)

Overrides work for dda ids too: a mod tileset loads after the base tileset and
create_tile_type overwrites existing ids (src/cata_tiles.cpp:366-368), so drawing
t_sidewalk.png restyles the dda sidewalk.  Name a file <id>_season_winter.png to
replace a base tileset's winter variant (the Saigon scenario starts in CDDA winter).

Output: data/mods/saigon_2000s/gfx/saigon_tiles32.png, saigon_overmap16.png and
mod_tileset.json.  Run from the repo root:  python3 tools/saigon/art/build_sprites.py
"""
import json
import os
import sys

sys.path.insert( 0, os.path.dirname( __file__ ) )
import pngio  # noqa: E402

ROOT = os.path.join( os.path.dirname( __file__ ), '..', '..', '..' )
SRC = os.path.join( ROOT, 'art', 'saigon' )
GFX = os.path.join( ROOT, 'data', 'mods', 'saigon_2000s', 'gfx' )
SHEETS = [
    # source folder, sprite size, output sheet, base tilesets this matches
    ( 'tiles32', 32, 'saigon_tiles32.png', [ 'UltimateCataclysm' ] ),
    ( 'overmap16', 16, 'saigon_overmap16.png', [ 'Larwick Overmap' ] ),
]
ACROSS = 16


def collect( folder ):
    found = {}
    base = os.path.join( SRC, folder )
    for dirpath, _, files in os.walk( base ):
        for name in sorted( files ):
            if name.endswith( '.png' ):
                sid = name[:-4]
                if sid in found:
                    sys.exit( 'duplicate sprite id %s in %s and %s' % ( sid, found[sid], dirpath ) )
                found[sid] = os.path.join( dirpath, name )
    return found


def main():
    objects = []
    os.makedirs( GFX, exist_ok=True )
    total = 0
    for folder, size, sheet_name, compat in SHEETS:
        sprites = collect( folder )
        sheet_path = os.path.join( GFX, sheet_name )
        if not sprites:
            if os.path.exists( sheet_path ):
                os.remove( sheet_path )
            continue
        ids = sorted( sprites )
        rows = ( len( ids ) + ACROSS - 1 ) // ACROSS
        sheet = pngio.Image( ACROSS * size, rows * size )
        tiles = []
        for index, sid in enumerate( ids ):
            img = pngio.read( sprites[sid] )
            if ( img.width, img.height ) != ( size, size ):
                sys.exit( '%s is %dx%d, expected %dx%d' % ( sprites[sid], img.width, img.height, size, size ) )
            sheet.paste( img, ( index % ACROSS ) * size, ( index // ACROSS ) * size )
            entry = { 'id': sid, 'fg': index }
            sidecar = sprites[sid][:-4] + '.json'
            if os.path.exists( sidecar ):
                with open( sidecar ) as f:
                    extra = json.load( f )
                extra.pop( 'id', None )
                extra.pop( 'fg', None )
                entry.update( extra )
            tiles.append( entry )
        pngio.write( sheet_path, sheet )
        objects.append( { 'type': 'mod_tileset', 'compatibility': compat,
                          'tiles-new': [ { 'file': sheet_name, 'sprite_width': size, 'sprite_height': size,
                                           'tiles': tiles } ] } )
        total += len( ids )
        print( '%s: %d sprites -> %s (for %s)' % ( folder, len( ids ), sheet_name, ', '.join( compat ) ) )
    out = os.path.join( GFX, 'mod_tileset.json' )
    if objects:
        with open( out, 'w', encoding='utf-8' ) as f:
            json.dump( objects, f, ensure_ascii=False, indent=2 )
    elif os.path.exists( out ):
        os.remove( out )
    print( 'packed %d sprites' % total )


if __name__ == '__main__':
    main()
