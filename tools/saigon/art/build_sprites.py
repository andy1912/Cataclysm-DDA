#!/usr/bin/env python3
"""Pack hand-drawn and code-drawn Saigon sprites into the mod's mod_tileset (no Pillow needed).

Source layout (one PNG per game id, file name = id):
  art/saigon/tiles/<anything>/<id>.png       hand-drawn, for the UltimateCataclysm base
  art/saigon/generated/<program>/<id>.png    written by draw_sprites.py from art/saigon/drawn
  art/saigon/overmap16/<anything>/<id>.png   16x16 overmap icons (oter ids), Larwick Overmap

A hand-drawn PNG wins over a generated one with the same id.  Any size the base
tileset uses is accepted; the size picks the sheet and its offsets (GEOMETRY below,
the same as UltimateCataclysm's sheets), e.g. 20x20 items, 32x32 terrain, 32x64 tall
furniture, 32x36 worn overlays, 32x48 monsters.

<id>.json next to a PNG holds extra tile keys copied into the tile entry, e.g.
{"rotates": true}.  Inside it, "@name" refers to the sprite in name.png in the same
source root, so multi-sprite tiles work: a file with "__" in its name (t_foo__corner.png)
is such a helper sprite and gets no tile entry of its own.  Example sidecar for a
rotating fridge: {"rotates": true, "fg": ["@f_x", "@f_x__e", "@f_x__s", "@f_x__w"]}.

Overrides work for dda ids too: a mod tileset loads after the base tileset and
create_tile_type overwrites existing ids (src/cata_tiles.cpp:366-368).

Output: data/mods/saigon_2000s/gfx/saigon_<w>x<h>.png sheets, saigon_overmap16.png and
mod_tileset.json.  Run from the repo root:  python3 tools/saigon/art/build_sprites.py
"""
import json
import os
import re
import sys

sys.path.insert( 0, os.path.dirname( __file__ ) )
import pngio  # noqa: E402

ROOT = os.path.join( os.path.dirname( __file__ ), '..', '..', '..' )
SRC = os.path.join( ROOT, 'art', 'saigon' )
GFX = os.path.join( ROOT, 'data', 'mods', 'saigon_2000s', 'gfx' )
# ( width, height ) -> ( sprite_offset_x, sprite_offset_y ), from UltimateCataclysm/tile_config.json
GEOMETRY = {
    ( 32, 32 ): ( 0, 0 ), ( 20, 20 ): ( 6, 0 ), ( 32, 64 ): ( 0, -32 ), ( 32, 36 ): ( 0, -8 ),
    ( 32, 48 ): ( 0, -16 ), ( 64, 64 ): ( -16, -32 ), ( 64, 96 ): ( -16, -64 ), ( 96, 96 ): ( -32, -64 ),
}
SETS = [
    # source roots (later roots win), sheet prefix, allowed geometry, base tilesets this matches
    ( [ 'generated', 'tiles' ], 'saigon', GEOMETRY, [ 'UltimateCataclysm' ], 'mod_tileset.json' ),
    ( [ 'overmap16' ], 'saigon_overmap', { ( 16, 16 ): ( 0, 0 ) }, [ 'Larwick Overmap' ], 'mod_overmap_tileset.json' ),
]
ACROSS = 16


def collect( root ):
    found = {}
    base = os.path.join( SRC, root )
    for dirpath, _, files in os.walk( base ):
        for name in sorted( files ):
            if name.endswith( '.png' ):
                sid = name[:-4]
                if sid in found:
                    sys.exit( 'duplicate sprite %s in %s and %s' % ( sid, found[sid], dirpath ) )
                found[sid] = os.path.join( dirpath, name )
    return found


def pack( roots, prefix, geometry, compat ):
    sprites = {}
    for root in roots:
        sprites.update( collect( root ) )
    if not sprites:
        return None, 0
    groups = {}
    images = {}
    for sid in sorted( sprites ):
        img = pngio.read( sprites[sid] )
        size = ( img.width, img.height )
        if size not in geometry:
            sys.exit( '%s is %dx%d; supported sizes: %s' % ( sprites[sid], img.width, img.height,
                      ', '.join( '%dx%d' % s for s in sorted( geometry ) ) ) )
        groups.setdefault( size, [] ).append( sid )
        images[sid] = img
    index = {}
    sheets = []
    offset = 0
    for size in sorted( groups ):
        w, h = size
        ids = groups[size]
        rows = ( len( ids ) + ACROSS - 1 ) // ACROSS
        sheet = pngio.Image( ACROSS * w, rows * h )
        for i, sid in enumerate( ids ):
            sheet.paste( images[sid], ( i % ACROSS ) * w, ( i // ACROSS ) * h )
            index[sid] = offset + i
        name = '%s_%dx%d.png' % ( prefix, w, h )
        pngio.write( os.path.join( GFX, name ), sheet )
        ox, oy = geometry[size]
        # relative to the MOD ROOT, not to this JSON file: the loader opens
        # <mod base path>/<file> (tileset_loader.cpp: tileset_root = mts.get_base_path())
        sheets.append( { 'file': 'gfx/' + name, 'sprite_width': w, 'sprite_height': h,
                         'sprite_offset_x': ox, 'sprite_offset_y': oy, 'tiles': [] } )
        offset += ACROSS * rows  # full grid capacity, like the engine (src/tileset_loader.cpp:319)

    def resolve( value, where ):
        if isinstance( value, str ) and value.startswith( '@' ):
            if value[1:] not in index:
                sys.exit( '%s: no sprite %s.png for %s' % ( where, value[1:], value ) )
            return index[value[1:]]
        if isinstance( value, list ):
            return [ resolve( v, where ) for v in value ]
        if isinstance( value, dict ):
            return { k: resolve( v, where ) for k, v in value.items() }
        return value

    def refs( value ):
        if isinstance( value, str ) and value.startswith( '@' ):
            yield value[1:]
        elif isinstance( value, list ):
            for v in value:
                yield from refs( v )
        elif isinstance( value, dict ):
            for v in value.values():
                yield from refs( v )

    # The engine gives a tile the sprite offset of the sheet it is declared under
    # (tileset_loader parse_atlases), so each entry goes under the sheet of its size.
    sheet_of = { size: n for n, size in enumerate( sorted( groups ) ) }
    count = 0
    for sid in sorted( sprites ):
        if '__' in sid:
            continue
        entry = { 'id': sid, 'fg': index[sid] }
        used = { sid }
        sidecar = sprites[sid][:-4] + '.json'
        if os.path.exists( sidecar ):
            with open( sidecar ) as f:
                extra = json.load( f )
            extra.pop( 'id', None )
            used |= set( refs( extra ) )
            entry.update( resolve( extra, sidecar ) )
        sizes = { ( images[u].width, images[u].height ) for u in used if u in images }
        if len( sizes ) != 1:
            sys.exit( '%s mixes sprite sizes %s; one tile entry can only use one sheet geometry' %
                      ( sid, sorted( sizes ) ) )
        sheets[sheet_of[sizes.pop()]]['tiles'].append( entry )
        count += 1
    tiles = range( count )
    obj = { 'type': 'mod_tileset', 'compatibility': compat, 'tiles-new': sheets }
    print( '%s: %d tiles, %d sprites in %d sheets (for %s)' % ( '+'.join( roots ), len( tiles ), len( sprites ),
                                                              len( sheets ), ', '.join( compat ) ) )
    return obj, len( sprites )


def main():
    os.makedirs( GFX, exist_ok=True )
    own = re.compile( r'^saigon_(overmap_)?\d+x\d+\.png$|^saigon_tiles32\.png$|^saigon_overmap16\.png$' )
    for name in os.listdir( GFX ):
        if own.match( name ):
            os.remove( os.path.join( GFX, name ) )
    total = 0
    for roots, prefix, geometry, compat, out_name in SETS:
        obj, n = pack( roots, prefix, geometry, compat )
        out = os.path.join( GFX, out_name )
        if obj:
            with open( out, 'w', encoding='utf-8' ) as f:
                json.dump( [ obj ], f, ensure_ascii=False, indent=1 )
        elif os.path.exists( out ):
            os.remove( out )
        total += n
    print( 'packed %d sprites' % total )


if __name__ == '__main__':
    main()
