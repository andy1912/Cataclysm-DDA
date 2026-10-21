#!/usr/bin/env python3
"""Write doc/saigon/art/sprite_revision_list.csv: every manifest id with its sprite size,
image count and art status.

Status is one of
  Saigon art (drawn)     hand-drawn or code-drawn sprite in mod_tileset.json
  Saigon art (derived)   recipe-derived sprite in derived_tileset.json / derived_overmap_tileset.json
  keep original          dda (or engine-generated) id whose UltimateCataclysm art is universal (art/saigon/art_triage.json)
  to do                  needs Saigon art (a mod id without a sprite, or a dda id listed as todo)
  to do (no sprite)      nothing in the base tileset along its fallback chain: the game
                         draws an ASCII glyph, so it needs a sprite whatever its origin
  base tileset gap       the same for deep (T3) dda loot: UltimateCataclysm itself has no
                         sprite, the vanilla game shows the glyph too
Size and image count come from the sprite that draws today (Saigon sprite, else the base
tileset entry of the id or of its fallback).  Run from the repo root after build/derive:
  python3 tools/saigon/art/revision_list.py
"""
import collections
import csv
import json
import os
import sys

sys.path.insert( 0, os.path.dirname( __file__ ) )
from derive_sprites import BaseTileset, ROOT, GFX, sheet_path  # noqa: E402

ART = os.path.join( ROOT, 'doc', 'saigon', 'art' )


def indices( value ):
    if isinstance( value, int ):
        yield value
    elif isinstance( value, list ):
        for v in value:
            yield from indices( v )
    elif isinstance( value, dict ) and 'sprite' in value:
        yield from indices( value['sprite'] )


def entry_indices( entry ):
    found = []
    for part in [ entry ] + entry.get( 'additional_tiles', [] ):
        for key in ( 'fg', 'bg' ):
            found += list( indices( part.get( key ) ) )
    return found


class ModSets:
    """Saigon mod tilesets: id -> ( kind, size, image count )."""

    def __init__( self ):
        self.tiles = {}
        for name, kind in ( ( 'mod_tileset.json', 'drawn' ), ( 'mod_overmap_tileset.json', 'drawn' ),
                            ( 'derived_tileset.json', 'derived' ), ( 'derived_overmap_tileset.json', 'derived' ) ):
            path = os.path.join( GFX, name )
            if not os.path.exists( path ):
                continue
            with open( path ) as f:
                for obj in json.load( f ):
                    ranges = []
                    start = 0
                    for sheet in obj['tiles-new']:
                        w, h = sheet.get( 'sprite_width', 32 ), sheet.get( 'sprite_height', 32 )
                        pw, ph = BaseTileset._dims( sheet_path( sheet ) )
                        count = ( pw // w ) * ( ph // h )
                        ranges.append( ( start, start + count, '%dx%d' % ( w, h ) ) )
                        start += count
                    for sheet in obj['tiles-new']:
                        for t in sheet.get( 'tiles', [] ):
                            idx = entry_indices( t )
                            size = next( ( s for a, b, s in ranges if idx and a <= idx[0] < b ), '?' )
                            for i in t['id'] if isinstance( t['id'], list ) else [ t['id'] ]:
                                self.tiles.setdefault( i, ( kind, size, len( set( idx ) ) ) )


def looks_like_table():
    """id -> looks_like for every JSON object in dda and the Saigon mod, with copy-from
    inheritance, so a fallback chain can be followed as far as the game follows it."""
    own, parent = {}, {}
    for top in ( os.path.join( ROOT, 'data', 'json' ), os.path.join( ROOT, 'data', 'mods', 'saigon_2000s' ) ):
        for dirpath, _, files in os.walk( top ):
            for name in files:
                if not name.endswith( '.json' ) or '/gfx' in dirpath:
                    continue
                try:
                    with open( os.path.join( dirpath, name ), encoding='utf-8' ) as f:
                        data = json.load( f )
                except ( ValueError, UnicodeDecodeError ):
                    continue
                for obj in data if isinstance( data, list ) else [ data ]:
                    if not isinstance( obj, dict ):
                        continue
                    ids = obj.get( 'id' ) or obj.get( 'abstract' )
                    for i in ids if isinstance( ids, list ) else [ ids ]:
                        if not isinstance( i, str ):
                            continue
                        if 'looks_like' in obj:
                            own[i] = obj['looks_like']
                        if 'copy-from' in obj and obj['copy-from'] != i:
                            parent[i] = obj['copy-from']

    def resolve( i, depth=0 ):
        if i in own or depth > 10:
            return own.get( i, '' )
        return resolve( parent[i], depth + 1 ) if i in parent else ''
    return resolve


def main():
    base = BaseTileset( os.path.join( ROOT, 'gfx', 'UltimateCataclysm' ) )
    looks_like = looks_like_table()
    variant_prefixes = { t.rsplit( '_', 1 )[0] for t in base.tiles if t.startswith( 'vp_' ) }

    def has_sprite( sid, category ):
        """Does the game find any base sprite for sid along its looks_like chain?"""
        cur, seen = sid, set()
        while cur and cur not in seen and len( seen ) < 10:
            seen.add( cur )
            if cur in base.tiles:
                return True
            if category == 'vehicle_part':
                vp = cur if cur.startswith( 'vp_' ) else 'vp_' + cur
                if vp in base.tiles or any( p.startswith( vp ) for p in variant_prefixes if p == vp or
                                            p.startswith( vp + '_' ) ):
                    return True
            nxt = looks_like( cur[3:] if cur.startswith( 'vp_' ) else cur )
            cur = nxt
        return False
    mod = ModSets()
    with open( os.path.join( ROOT, 'art', 'saigon', 'art_triage.json' ) ) as f:
        todo_dda = json.load( f )['todo']

    def base_info( sid ):
        if sid in base.tiles:
            idx = entry_indices( base.tiles[sid] )
            if idx:
                w, h, _, _ = base.sprite( idx[0] )[1]
                return '%dx%d' % ( w, h ), len( set( idx ) )
        return None

    rows = []
    with open( os.path.join( ART, 'manifest.csv' ) ) as fh:
        for row in csv.DictReader( fh ):
            sid = 'vp_' + row['id'] if row['category'] == 'vehicle_part' else row['id']
            if sid in mod.tiles:
                kind, size, images = mod.tiles[sid]
                status = 'Saigon art (%s)' % kind
            else:
                info = base_info( sid ) or ( row['fallback'] and base_info( row['fallback'] ) )
                size, images = info or ( '20x20' if row['category'] == 'item' else '32x32', 1 )
                if row['category'] == 'overmap_terrain':
                    size = '16x16'
                pseudo = row['id'].startswith( ( 't_region_', 'f_region_' ) )
                # vehicle parts are checked by the scene render instead: most parts without a
                # sprite (alternators, horns, mounts) sit under the part the tile displays
                drawable = row['category'] in ( 'vehicle_part', 'overmap_terrain' ) or pseudo or \
                    has_sprite( sid, row['category'] ) or ( row['fallback'] and has_sprite( row['fallback'], row['category'] ) )
                if not drawable and row['tier'] == 'T3':
                    status = 'base tileset gap'
                elif not drawable:
                    # nothing in the base tileset along the fallback: the game draws an ASCII glyph
                    status = 'to do (no sprite)'
                elif row['source'] != 'mod' and sid not in todo_dda and row['id'] not in todo_dda:
                    status = 'keep original'
                else:
                    status = 'to do'
            rows.append( [ row['tier'], row['category'], row['id'], row['source'], size, images, status,
                           row['fallback'] ] )
    with open( os.path.join( ART, 'sprite_revision_list.csv' ), 'w', newline='' ) as fh:
        out = csv.writer( fh, lineterminator='\n' )
        out.writerow( [ 'tier', 'category', 'id', 'source', 'size', 'images', 'status', 'fallback' ] )
        out.writerows( rows )
    stats = collections.Counter( ( r[0], r[6] ) for r in rows )
    for tier in ( 'T1', 'T2', 'T3' ):
        print( tier, ', '.join( '%s: %d' % ( s, n ) for ( t, s ), n in sorted( stats.items() ) if t == tier ) )


if __name__ == '__main__':
    main()
