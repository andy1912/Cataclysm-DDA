#!/usr/bin/env python3
"""Write doc/saigon/art/sprite_revision_list.csv: every manifest id with its sprite size,
image count and art status.

Status is one of
  Saigon art (drawn)     hand-drawn or code-drawn sprite in mod_tileset.json
  Saigon art (derived)   recipe-derived sprite in derived_tileset.json / derived_overmap_tileset.json
  keep original          dda (or engine-generated) id whose UltimateCataclysm art is universal (art/saigon/art_triage.json)
  to do                  needs Saigon art (a mod id without a sprite, or a dda id listed as todo)
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
from derive_sprites import BaseTileset, ROOT, GFX  # noqa: E402

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
                        pw, ph = BaseTileset._dims( os.path.join( GFX, sheet['file'] ) )
                        count = ( pw // w ) * ( ph // h )
                        ranges.append( ( start, start + count, '%dx%d' % ( w, h ) ) )
                        start += count
                    for sheet in obj['tiles-new']:
                        for t in sheet.get( 'tiles', [] ):
                            idx = entry_indices( t )
                            size = next( ( s for a, b, s in ranges if idx and a <= idx[0] < b ), '?' )
                            for i in t['id'] if isinstance( t['id'], list ) else [ t['id'] ]:
                                self.tiles.setdefault( i, ( kind, size, len( set( idx ) ) ) )


def main():
    base = BaseTileset( os.path.join( ROOT, 'gfx', 'UltimateCataclysm' ) )
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
                info = base_info( sid ) or ( row['fallback'] and base_info( row['fallback'] ) ) or ( '?', 1 )
                size, images = info
                if row['category'] == 'overmap_terrain':
                    size = '16x16'
                if row['source'] != 'mod' and sid not in todo_dda and row['id'] not in todo_dda:
                    status = 'keep original'
                else:
                    status = 'to do'
            rows.append( [ row['tier'], row['category'], row['id'], row['source'], size, images, status,
                           row['fallback'] ] )
    with open( os.path.join( ART, 'sprite_revision_list.csv' ), 'w', newline='' ) as fh:
        out = csv.writer( fh )
        out.writerow( [ 'tier', 'category', 'id', 'source', 'size', 'images', 'status', 'fallback' ] )
        out.writerows( rows )
    stats = collections.Counter( ( r[0], r[6] ) for r in rows )
    for tier in ( 'T1', 'T2', 'T3' ):
        print( tier, ', '.join( '%s: %d' % ( s, n ) for ( t, s ), n in sorted( stats.items() ) if t == tier ) )


if __name__ == '__main__':
    main()
