#!/usr/bin/env python3
"""Derive Saigon sprites from the installed UltimateCataclysm tileset.

Original art stays consistent because every Saigon sprite starts from an original
UltimateCataclysm sprite (CC-BY-SA 3.0) and applies recorded, re-runnable edits
(recolours, tints, small overlays) from art/saigon/derive_recipes.json:

  {"target": "f_sgn_ban_tho", "source": "f_table", "ops": [ ... ]}
      copies the whole tile entry of <source> (fg/bg, variants, rotations, multitile
      additional_tiles) under the id <target>, transforming every sprite it uses
  {"tropical_seasons": ["_season_winter", "_season_autumn"]}
      for every base id ending in one of the suffixes, emits that id with the sprites
      of its "_season_summer" counterpart (or the plain id): no snow, no autumn
      foliage in Saigon (src/cata_tiles.cpp:378-396 picks season variants first)

Ops (applied in order to opaque pixels; hues in degrees):
  {"op": "recolor", "hue": [h0, h1], "min_sat": s, "max_val": v, "to_hue": h | null,
   "sat_mul": m | "sat_set": s, "val_mul": m, "val_add": a}
  {"op": "tint", "rgb": [r, g, b], "strength": 0..1}
  {"op": "desaturate", "sat_mul": m, "val_mul": m}
  {"op": "cap", "rows": n, "rgb": [r, g, b]}     colour the top n opaque rows (helmets)

Sprites that have a hand-drawn PNG under art/saigon/tiles32 are skipped, so real art
always wins.  Output: data/mods/saigon_2000s/gfx/derived_*.png + derived_tileset.json
(a mod_tileset compatible with UltimateCataclysm), art/saigon/SOURCES_DERIVED.md and
doc/saigon/art/derived_preview.png (before/after contact sheet).

Run from the repo root:  python3 tools/saigon/art/derive_sprites.py
"""
import colorsys
import copy
import json
import os
import sys

sys.path.insert( 0, os.path.dirname( __file__ ) )
import pngio  # noqa: E402

ROOT = os.path.join( os.path.dirname( __file__ ), '..', '..', '..' )
BASE = os.path.join( ROOT, 'gfx', 'UltimateCataclysm' )
RECIPES = os.path.join( ROOT, 'art', 'saigon', 'derive_recipes.json' )
HAND = os.path.join( ROOT, 'art', 'saigon', 'tiles32' )
GFX = os.path.join( ROOT, 'data', 'mods', 'saigon_2000s', 'gfx' )
ACROSS = 16


class BaseTileset:
    def __init__( self ):
        with open( os.path.join( BASE, 'tile_config.json' ) ) as f:
            self.config = json.load( f )
        info = self.config['tile_info'][0]
        self.sheets = []
        start = 0
        for sheet in self.config['tiles-new']:
            w = sheet.get( 'sprite_width', info['width'] )
            h = sheet.get( 'sprite_height', info['height'] )
            width, height = self._dims( os.path.join( BASE, sheet['file'] ) )
            cols = width // w
            count = cols * ( height // h )  # full grid capacity (src/tileset_loader.cpp:319)
            self.sheets.append( { 'file': sheet['file'], 'w': w, 'h': h,
                                  'ox': sheet.get( 'sprite_offset_x', 0 ), 'oy': sheet.get( 'sprite_offset_y', 0 ),
                                  'start': start, 'count': count, 'cols': cols, 'img': None } )
            start += count
        self.tiles = {}
        for sheet in self.config['tiles-new']:
            for t in sheet.get( 'tiles', [] ):
                for i in t['id'] if isinstance( t['id'], list ) else [ t['id'] ]:
                    self.tiles[i] = t

    @staticmethod
    def _dims( path ):
        with open( path, 'rb' ) as f:
            head = f.read( 24 )
        return int.from_bytes( head[16:20], 'big' ), int.from_bytes( head[20:24], 'big' )

    def sprite( self, index ):
        for s in self.sheets:
            if s['start'] <= index < s['start'] + s['count']:
                if s['img'] is None:
                    s['img'] = pngio.read( os.path.join( BASE, s['file'] ) )
                local = index - s['start']
                x0 = ( local % s['cols'] ) * s['w']
                y0 = ( local // s['cols'] ) * s['h']
                img = pngio.Image( s['w'], s['h'] )
                for y in range( s['h'] ):
                    src = ( ( y0 + y ) * s['img'].width + x0 ) * 4
                    img.pixels[y * s['w'] * 4:( y + 1 ) * s['w'] * 4] = s['img'].pixels[src:src + s['w'] * 4]
                return img, ( s['w'], s['h'], s['ox'], s['oy'] )
        raise KeyError( 'sprite index %d outside the base tileset' % index )


def apply_ops( img, ops ):
    out = pngio.Image( img.width, img.height, img.pixels )
    for op in ops:
        kind = op['op']
        if kind == 'cap':
            rows_done = 0
            for y in range( out.height ):
                if rows_done >= op['rows']:
                    break
                xs = [ x for x in range( out.width ) if out.get( x, y )[3] > 0 ]
                if not xs:
                    continue
                for x in xs[1:-1] if len( xs ) > 2 else xs:
                    out.set( x, y, tuple( op['rgb'] ) + ( 255, ) )
                rows_done += 1
            continue
        for y in range( out.height ):
            for x in range( out.width ):
                r, g, b, a = out.get( x, y )
                if a == 0:
                    continue
                h, s, v = colorsys.rgb_to_hsv( r / 255, g / 255, b / 255 )
                if kind == 'recolor':
                    h0, h1 = op['hue']
                    deg = h * 360
                    inside = h0 <= deg <= h1 if h0 <= h1 else ( deg >= h0 or deg <= h1 )
                    if not inside or s < op.get( 'min_sat', 0.0 ) or v > op.get( 'max_val', 1.0 ):
                        continue
                    if op.get( 'to_hue' ) is not None:
                        h = ( op['to_hue'] % 360 ) / 360
                    s = op['sat_set'] if 'sat_set' in op else min( 1.0, s * op.get( 'sat_mul', 1.0 ) )
                    v = min( 1.0, v * op.get( 'val_mul', 1.0 ) + op.get( 'val_add', 0.0 ) )
                    nr, ng, nb = colorsys.hsv_to_rgb( h, s, v )
                    out.set( x, y, ( int( nr * 255 ), int( ng * 255 ), int( nb * 255 ), a ) )
                elif kind == 'desaturate':
                    s = s * op.get( 'sat_mul', 0.0 )
                    v = min( 1.0, v * op.get( 'val_mul', 1.0 ) )
                    nr, ng, nb = colorsys.hsv_to_rgb( h, s, v )
                    out.set( x, y, ( int( nr * 255 ), int( ng * 255 ), int( nb * 255 ), a ) )
                elif kind == 'tint':
                    k = op['strength']
                    lum = ( 0.299 * r + 0.587 * g + 0.114 * b ) / 255
                    tr, tg, tb = [ c * lum * 1.4 for c in op['rgb'] ]
                    out.set( x, y, ( int( min( 255, r + ( tr - r ) * k ) ), int( min( 255, g + ( tg - g ) * k ) ),
                                     int( min( 255, b + ( tb - b ) * k ) ), a ) )
                else:
                    raise ValueError( 'unknown op %s' % kind )
    return out


class Output:
    """Collects derived sprites grouped by sheet geometry and assigns mod indices."""

    def __init__( self ):
        self.groups = {}  # geometry -> list of images
        self.order = []

    def add( self, img, geometry ):
        if geometry not in self.groups:
            self.groups[geometry] = []
            self.order.append( geometry )
        self.groups[geometry].append( img )
        return ( geometry, len( self.groups[geometry] ) - 1 )

    def finalize( self ):
        """Write sheets; return {(geometry, local): mod index} and tiles-new skeletons."""
        index = {}
        sheets = []
        offset = 0
        for n, geometry in enumerate( self.order ):
            w, h, ox, oy = geometry
            imgs = self.groups[geometry]
            rows = ( len( imgs ) + ACROSS - 1 ) // ACROSS
            sheet = pngio.Image( ACROSS * w, rows * h )
            for i, img in enumerate( imgs ):
                sheet.paste( img, ( i % ACROSS ) * w, ( i // ACROSS ) * h )
                index[( geometry, i )] = offset + i
            name = 'derived_%d_%dx%d.png' % ( n, w, h )
            pngio.write( os.path.join( GFX, name ), sheet )
            sheets.append( { 'file': name, 'sprite_width': w, 'sprite_height': h,
                             'sprite_offset_x': ox, 'sprite_offset_y': oy, 'tiles': [] } )
            offset += ACROSS * rows  # full grid capacity, like the engine
        return index, sheets


def remap_entry( entry, base, out, ops, cache ):
    """Deep-copy a tile entry, replacing every sprite index with a derived copy."""
    geometry_of_entry = []

    def remap( value ):
        if isinstance( value, int ):
            key = ( value, json.dumps( ops, sort_keys=True ) )
            if key not in cache:
                img, geometry = base.sprite( value )
                cache[key] = out.add( apply_ops( img, ops ), geometry )
            geometry_of_entry.append( cache[key][0] )
            return cache[key]
        if isinstance( value, list ):
            return [ remap( v ) for v in value ]
        if isinstance( value, dict ):
            return { k: ( remap( v ) if k == 'sprite' else v ) for k, v in value.items() }
        return value

    new = copy.deepcopy( entry )
    for key in ( 'fg', 'bg' ):
        if key in new:
            new[key] = remap( new[key] )
    for sub in new.get( 'additional_tiles', [] ):
        for key in ( 'fg', 'bg' ):
            if key in sub:
                sub[key] = remap( sub[key] )
    return new, geometry_of_entry


def resolve( value, index ):
    if isinstance( value, tuple ):
        return index[value]
    if isinstance( value, list ):
        return [ resolve( v, index ) for v in value ]
    if isinstance( value, dict ):
        return { k: resolve( v, index ) for k, v in value.items() }
    return value


def hand_drawn_ids():
    ids = set()
    for dirpath, _, files in os.walk( HAND ):
        ids.update( f[:-4] for f in files if f.endswith( '.png' ) )
    return ids


def main():
    if not os.path.isdir( BASE ):
        sys.exit( 'UltimateCataclysm is not installed in gfx/; see doc/saigon/art/UPDATING_SPRITES.md' )
    base = BaseTileset()
    with open( RECIPES ) as f:
        recipes = json.load( f )
    skip = hand_drawn_ids()
    out = Output()
    cache = {}
    entries = []      # ( target id, remapped entry )
    provenance = []
    previews = []     # ( source image, derived image ) for the contact sheet
    for rule in recipes:
        if 'tropical_seasons' in rule:
            suffixes = rule['tropical_seasons']
            for sid in sorted( base.tiles ):
                for suffix in suffixes:
                    if not sid.endswith( suffix ) or sid in skip:
                        continue
                    stem = sid[:-len( suffix )]
                    source = stem + '_season_summer' if stem + '_season_summer' in base.tiles else stem
                    if source not in base.tiles:
                        continue
                    new, _ = remap_entry( base.tiles[source], base, out, [], cache )
                    new['id'] = sid
                    entries.append( new )
                    provenance.append( ( sid, source, 'tropical season: summer art for %s' % suffix ) )
            continue
        target, source, ops = rule['target'], rule['source'], rule.get( 'ops', [] )
        if target in skip:
            continue
        if source not in base.tiles:
            print( 'warning: source %s not in UltimateCataclysm, skipping %s' % ( source, target ) )
            continue
        new, _ = remap_entry( base.tiles[source], base, out, ops, cache )
        new['id'] = target
        entries.append( new )
        provenance.append( ( target, source, json.dumps( ops ) ) )
        fg = base.tiles[source].get( 'fg' )
        first = fg if isinstance( fg, int ) else ( fg[0] if isinstance( fg, list ) and fg else None )
        if isinstance( first, dict ):
            first = first.get( 'sprite' )
            first = first[0] if isinstance( first, list ) else first
        if isinstance( first, int ):
            img, _ = base.sprite( first )
            previews.append( ( img, apply_ops( img, ops ) ) )

    os.makedirs( GFX, exist_ok=True )
    for name in os.listdir( GFX ):
        if name.startswith( 'derived_' ):
            os.remove( os.path.join( GFX, name ) )
    index, sheets = out.finalize()
    # every entry goes in the first sheet's "tiles"; indices are mod-global
    sheets[0]['tiles'] = [ resolve( e, index ) for e in entries ]
    obj = [ { 'type': 'mod_tileset', 'compatibility': [ 'UltimateCataclysm' ], 'tiles-new': sheets } ]
    with open( os.path.join( GFX, 'derived_tileset.json' ), 'w', encoding='utf-8' ) as f:
        json.dump( obj, f, ensure_ascii=False, indent=1 )

    with open( os.path.join( ROOT, 'art', 'saigon', 'SOURCES_DERIVED.md' ), 'w', encoding='utf-8' ) as f:
        f.write( '# Derived sprite provenance\n\nGenerated by `tools/saigon/art/derive_sprites.py`. Every sprite '
                 'below is a modified copy of UltimateCataclysm art (I-am-Erk/CDDA-Tilesets, CC-BY-SA 3.0, '
                 'UltimateCataclysm contributors) and is distributed under CC-BY-SA 3.0.\n\n'
                 '| Saigon tile id | UltimateCataclysm source | Edit |\n|---|---|---|\n' )
        for target, source, edit in provenance:
            f.write( '| `%s` | `%s` | %s |\n' % ( target, source, edit.replace( '|', '\\|' ) ) )

    if previews:
        cell = 96
        sheet = pngio.Image( cell * 2, cell * len( previews ) )
        for row, ( before, after ) in enumerate( previews ):
            for col, img in enumerate( ( before, after ) ):
                ox = col * cell + ( cell - img.width ) // 2
                oy = row * cell + ( cell - img.height ) // 2
                sheet.paste( img, ox, oy )
        pngio.write( os.path.join( ROOT, 'doc', 'saigon', 'art', 'derived_preview.png' ), sheet )
    print( 'derived %d tile entries from %d sprites in %d sheets' %
           ( len( entries ), sum( len( v ) for v in out.groups.values() ), len( sheets ) ) )


if __name__ == '__main__':
    main()
