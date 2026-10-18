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
  {"op": "recolor", "hue": [h0, h1], "min_sat": s, "max_sat": s, "max_val": v, "to_hue": h | null,
   "sat_mul": m | "sat_set": s, "val_mul": m, "val_add": a}
  {"op": "tint", "rgb": [r, g, b], "strength": 0..1}
  {"op": "desaturate", "sat_mul": m, "val_mul": m}
  {"op": "cap", "rows": n, "rgb": [r, g, b]}     colour the top n opaque rows (helmets)
  Per-pixel ops (recolor, tint, desaturate) accept "rows": [y0, y1] to touch only those
  rows of the sprite, e.g. the hair on a 32x48 monster.
  {"op": "flatten", "k": 0.3, "min_val": v}      pull brightness towards the sprite's median
      (pixels darker than min_val, i.e. outlines and shadows, keep theirs): turns brick
      courses into a smooth rendered wall while keeping the tile's shading and edges

Sprites that have a hand-drawn PNG (art/saigon/tiles) or a code-drawn one
(art/saigon/generated, from draw_sprites.py) are skipped, so drawn art always wins.  Output: data/mods/saigon_2000s/gfx/derived_*.png + derived_tileset.json
(a mod_tileset compatible with UltimateCataclysm), art/saigon/SOURCES_DERIVED.md and
doc/saigon/art/derived_preview.png (before/after contact sheet).

Run from the repo root:  python3 tools/saigon/art/derive_sprites.py [tiles] [overmap]
(no argument: both sets; "overmap" derives Larwick Overmap icons with
art/saigon/derive_overmap_recipes.json)
"""
import colorsys
import copy
import json
import os
import re
import sys

sys.path.insert( 0, os.path.dirname( __file__ ) )
import pngio  # noqa: E402

ROOT = os.path.join( os.path.dirname( __file__ ), '..', '..', '..' )
MOD = os.path.join( ROOT, 'data', 'mods', 'saigon_2000s' )
GFX = os.path.join( MOD, 'gfx' )


def sheet_path( sheet ):
    """Where the engine opens a mod tileset sheet: <mod root>/<file>."""
    return os.path.join( MOD, sheet['file'] )
ACROSS = 16
# One derivation set per base tileset; a mod tileset only applies over its base.
SETS = {
    'tiles': { 'base': 'gfx/UltimateCataclysm', 'compat': [ 'UltimateCataclysm' ],
               'recipes': 'art/saigon/derive_recipes.json', 'hand': [ 'art/saigon/tiles', 'art/saigon/generated' ],
               'prefix': 'derived', 'json': 'derived_tileset.json',
               'preview': 'doc/saigon/art/derived_preview.png', 'provenance': 'art/saigon/SOURCES_DERIVED.md',
               'source_name': 'UltimateCataclysm' },
    'overmap': { 'base': 'gfx/Larwick_Overmap', 'compat': [ 'Larwick Overmap' ],
                 'recipes': 'art/saigon/derive_overmap_recipes.json', 'hand': [ 'art/saigon/overmap16' ],
                 'prefix': 'derived_om', 'json': 'derived_overmap_tileset.json',
                 'preview': 'doc/saigon/art/derived_overmap_preview.png',
                 'provenance': 'art/saigon/SOURCES_DERIVED_OVERMAP.md', 'source_name': 'Larwick Overmap' },
}


class BaseTileset:
    def __init__( self, base ):
        self.base = base
        with open( os.path.join( base, 'tile_config.json' ) ) as f:
            self.config = json.load( f )
        info = self.config['tile_info'][0]
        self.sheets = []
        start = 0
        for sheet in self.config['tiles-new']:
            w = sheet.get( 'sprite_width', info['width'] )
            h = sheet.get( 'sprite_height', info['height'] )
            width, height = self._dims( os.path.join( base, sheet['file'] ) )
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
                    s['img'] = pngio.read( os.path.join( self.base, s['file'] ) )
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
        if kind == 'flatten':
            lo = op.get( 'min_val', 0.0 )
            vals = sorted( max( out.get( x, y )[:3] ) / 255 for y in range( out.height ) for x in range( out.width )
                           if out.get( x, y )[3] > 0 and max( out.get( x, y )[:3] ) / 255 >= lo )
            if not vals:
                continue
            median = vals[len( vals ) // 2]
            for y in range( out.height ):
                for x in range( out.width ):
                    r, g, b, a = out.get( x, y )
                    h, s, v = colorsys.rgb_to_hsv( r / 255, g / 255, b / 255 )
                    if a == 0 or v < lo:
                        continue
                    v = median + ( v - median ) * op['k']
                    nr, ng, nb = colorsys.hsv_to_rgb( h, s, v )
                    out.set( x, y, ( int( nr * 255 ), int( ng * 255 ), int( nb * 255 ), a ) )
            continue
        y0, y1 = op.get( 'rows', [ 0, out.height - 1 ] )
        for y in range( max( 0, y0 ), min( out.height - 1, y1 ) + 1 ):
            for x in range( out.width ):
                r, g, b, a = out.get( x, y )
                if a == 0:
                    continue
                h, s, v = colorsys.rgb_to_hsv( r / 255, g / 255, b / 255 )
                if kind == 'recolor':
                    h0, h1 = op['hue']
                    deg = h * 360
                    inside = h0 <= deg <= h1 if h0 <= h1 else ( deg >= h0 or deg <= h1 )
                    if not inside or s < op.get( 'min_sat', 0.0 ) or s > op.get( 'max_sat', 1.0 ) or v > op.get( 'max_val', 1.0 ):
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

    def __init__( self, prefix ):
        self.prefix = prefix
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
            name = '%s_%d_%dx%d.png' % ( self.prefix, n, w, h )
            pngio.write( os.path.join( GFX, name ), sheet )
            # relative to the MOD ROOT (tileset_loader.cpp: tileset_root = mts.get_base_path())
            sheets.append( { 'file': 'gfx/' + name, 'sprite_width': w, 'sprite_height': h,
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


def geometries_of( value ):
    """Geometries of every ( geometry, local ) sprite key inside an unresolved entry."""
    if isinstance( value, tuple ):
        yield value[0]
    elif isinstance( value, list ):
        for v in value:
            yield from geometries_of( v )
    elif isinstance( value, dict ):
        for v in value.values():
            yield from geometries_of( v )


def resolve( value, index ):
    if isinstance( value, tuple ):
        return index[value]
    if isinstance( value, list ):
        return [ resolve( v, index ) for v in value ]
    if isinstance( value, dict ):
        return { k: resolve( v, index ) for k, v in value.items() }
    return value


def hand_drawn_ids( roots ):
    ids = set()
    for root in roots:
        for dirpath, _, files in os.walk( os.path.join( ROOT, root ) ):
            ids.update( f[:-4] for f in files if f.endswith( '.png' ) )
    return ids


def derive( cfg ):
    base_dir = os.path.join( ROOT, cfg['base'] )
    if not os.path.isdir( base_dir ):
        sys.exit( '%s is not installed; see doc/saigon/art/UPDATING_SPRITES.md' % cfg['base'] )
    base = BaseTileset( base_dir )
    with open( os.path.join( ROOT, cfg['recipes'] ) ) as f:
        recipes = json.load( f )
    skip = hand_drawn_ids( cfg['hand'] )
    out = Output( cfg['prefix'] )
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
            print( 'warning: source %s not in %s, skipping %s' % ( source, cfg['source_name'], target ) )
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
    own = re.compile( r'^%s_\d+_\d+x\d+\.png$' % re.escape( cfg['prefix'] ) )
    for name in os.listdir( GFX ):
        if own.match( name ):
            os.remove( os.path.join( GFX, name ) )
    index, sheets = out.finalize()
    # Indices are mod-global, but the engine gives a tile the sprite offset of the sheet it
    # is declared under (tileset_loader parse_atlases): declare each entry under the sheet
    # of its sprites' geometry.
    sheet_of = { geometry: n for n, geometry in enumerate( out.order ) }
    for e in entries:
        geometries = set( geometries_of( e ) )
        if len( geometries ) != 1:
            sys.exit( '%s mixes sprite geometries %s' % ( e.get( 'id' ), sorted( geometries ) ) )
        sheets[sheet_of[geometries.pop()]]['tiles'].append( resolve( e, index ) )
    obj = [ { 'type': 'mod_tileset', 'compatibility': cfg['compat'], 'tiles-new': sheets } ]
    with open( os.path.join( GFX, cfg['json'] ), 'w', encoding='utf-8' ) as f:
        json.dump( obj, f, ensure_ascii=False, indent=1 )

    with open( os.path.join( ROOT, cfg['provenance'] ), 'w', encoding='utf-8' ) as f:
        f.write( '# Derived sprite provenance (%s)\n\nGenerated by `tools/saigon/art/derive_sprites.py`. Every '
                 'sprite below is a modified copy of %s art (CC-BY-SA 3.0, its contributors) and is '
                 'distributed under CC-BY-SA 3.0.\n\n| Saigon tile id | %s source | Edit |\n|---|---|---|\n' %
                 ( cfg['source_name'], cfg['source_name'], cfg['source_name'] ) )
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
        pngio.write( os.path.join( ROOT, cfg['preview'] ), sheet )
    print( '%s: derived %d tile entries from %d sprites in %d sheets' %
           ( cfg['source_name'], len( entries ), sum( len( v ) for v in out.groups.values() ), len( sheets ) ) )


def main():
    names = sys.argv[1:] or list( SETS )
    for name in names:
        derive( SETS[name] )


if __name__ == '__main__':
    main()
