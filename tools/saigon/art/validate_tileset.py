#!/usr/bin/env python3
"""Statically validate the Saigon mod tilesets against the engine's loader rules.

Mod tilesets only load together with a world (they are mod data), so a main-menu
launch cannot test them.  This mirrors src/tileset_loader.cpp instead:
  - each sheet's capacity is (W / sprite_width) * (H / sprite_height)   (:319)
  - sprite indices are global across one mod_tileset's sheets, in order,
    offset by a per-tileset sprite_id_offset                           (:421, :572, :966)
  - every fg/bg index (plain, rotation list, weighted variants, multitile
    additional_tiles) must fall inside that total capacity
  - "compatibility" must name an installed base tileset                 (:425)
  - "file" is opened relative to the MOD ROOT (tileset_root = mod base path), not to the
    JSON file: a missing image aborts loading the world
  - a tile is drawn with the sprite size and offset of the sheet it is declared under
    (parse_atlases), so every sprite it uses must come from a sheet of that same
    geometry, or it lands misplaced
Also warns (without failing) when a 20x20 item icon covers more than ICON_MAX_PX opaque
pixels: UltimateCataclysm's median icon covers about 60 (review R5).
Exit 1 on any problem.  Run from the repo root:
  python3 tools/saigon/art/validate_tileset.py
"""
import glob
import json
import os
import sys

ROOT = os.path.join( os.path.dirname( __file__ ), '..', '..', '..' )
MOD = os.path.join( ROOT, 'data', 'mods', 'saigon_2000s' )
GFX = os.path.join( MOD, 'gfx' )


ICON_MAX_PX = 150


def png_dims( path ):
    with open( path, 'rb' ) as f:
        head = f.read( 24 )
    return int.from_bytes( head[16:20], 'big' ), int.from_bytes( head[20:24], 'big' )


def installed_tilesets():
    names = set()
    for txt in glob.glob( os.path.join( ROOT, 'gfx', '*', 'tileset.txt' ) ):
        with open( txt, encoding='utf-8' ) as f:
            for line in f:
                if line.startswith( 'NAME:' ):
                    names.add( line.split( ':', 1 )[1].strip() )
    return names


def indices( value ):
    if isinstance( value, int ):
        yield value
    elif isinstance( value, list ):
        for v in value:
            yield from indices( v )
    elif isinstance( value, dict ) and 'sprite' in value:
        yield from indices( value['sprite'] )


def main():
    problems = []
    installed = installed_tilesets()
    checked_tiles = 0
    for path in sorted( glob.glob( os.path.join( GFX, '*.json' ) ) ):
        with open( path ) as f:
            data = json.load( f )
        for n, obj in enumerate( data ):
            if obj.get( 'type' ) != 'mod_tileset':
                continue
            where = '%s[%d]' % ( os.path.basename( path ), n )
            compat = obj.get( 'compatibility', [] )
            if not set( compat ) & installed:
                problems.append( '%s: compatibility %s matches no installed tileset %s' %
                                 ( where, compat, sorted( installed ) ) )
            capacity = 0
            ranges = []
            for sheet in obj['tiles-new']:
                # the engine opens <mod root>/<file> (tileset_loader.cpp: tileset_root is the
                # mod's base path), whatever folder the JSON file sits in
                png = os.path.join( MOD, sheet['file'] )
                if not os.path.exists( png ):
                    problems.append( '%s: sheet %s not found at <mod root>/%s; the game aborts loading the '
                                     'world ("Could not load image")' % ( where, sheet['file'], sheet['file'] ) )
                    continue
                w, h = png_dims( png )
                sw = sheet.get( 'sprite_width', 32 )
                sh = sheet.get( 'sprite_height', 32 )
                if w % sw or h % sh:
                    problems.append( '%s: %s is %dx%d, not a multiple of %dx%d' % ( where, sheet['file'], w, h, sw, sh ) )
                geometry = ( sw, sh, sheet.get( 'sprite_offset_x', 0 ), sheet.get( 'sprite_offset_y', 0 ) )
                ranges.append( ( capacity, capacity + ( w // sw ) * ( h // sh ), geometry ) )
                capacity += ( w // sw ) * ( h // sh )
            seen_ids = set()
            for sheet in obj['tiles-new']:
                declared = ( sheet.get( 'sprite_width', 32 ), sheet.get( 'sprite_height', 32 ),
                             sheet.get( 'sprite_offset_x', 0 ), sheet.get( 'sprite_offset_y', 0 ) )
                for tile in sheet.get( 'tiles', [] ):
                    checked_tiles += 1
                    tid = tile.get( 'id' )
                    for i in tid if isinstance( tid, list ) else [ tid ]:
                        if i in seen_ids:
                            problems.append( '%s: duplicate tile id %s' % ( where, i ) )
                        seen_ids.add( i )
                    parts = [ tile ] + tile.get( 'additional_tiles', [] )
                    if not any( 'fg' in p or 'bg' in p for p in parts ):
                        problems.append( '%s: %s has neither fg nor bg' % ( where, tid ) )
                    for p in parts:
                        for key in ( 'fg', 'bg' ):
                            for idx in indices( p.get( key ) ):
                                if not 0 <= idx < capacity:
                                    problems.append( '%s: %s %s index %d outside 0..%d' %
                                                     ( where, tid, key, idx, capacity - 1 ) )
                                    continue
                                geometry = next( g for a, b, g in ranges if a <= idx < b )
                                if geometry != declared:
                                    problems.append( '%s: %s declared under a %dx%d%+d%+d sheet but sprite %d '
                                                     'is %dx%d%+d%+d: drawn misplaced' %
                                                     ( ( where, tid ) + declared + ( idx, ) + geometry ) )
    warnings = []
    for path in sorted( glob.glob( os.path.join( GFX, '*20x20.png' ) ) ):
        sys.path.insert( 0, os.path.dirname( __file__ ) )
        import pngio
        sheet = pngio.read( path )
        for row in range( sheet.height // 20 ):
            for col in range( sheet.width // 20 ):
                n = sum( 1 for y in range( row * 20, row * 20 + 20 ) for x in range( col * 20, col * 20 + 20 )
                         if sheet.get( x, y )[3] > 0 )
                if n > ICON_MAX_PX:
                    warnings.append( '%s sprite %d covers %d px (> %d): oversized next to dda icons' %
                                     ( os.path.basename( path ), row * ( sheet.width // 20 ) + col, n, ICON_MAX_PX ) )
    for w in warnings[:20]:
        print( 'WARN', w )
    for p in problems[:40]:
        print( 'FAIL', p )
    print( 'checked %d tile entries in %s: %d problems' % ( checked_tiles, GFX, len( problems ) ) )
    sys.exit( 1 if problems else 0 )


if __name__ == '__main__':
    main()
