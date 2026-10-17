#!/usr/bin/env python3
"""Check that every item_group reference in a mod JSON file resolves.

Walks the files, collecting every `"item": "x"` and `"group": "x"` (plus the
`"items": [["x", w]]` and `"groups": [[...]]` shorthand forms) and checks each
against the union of dda's and the mod's own item and item_group definitions.
An id that is only a group but is written under `"item"` (or the reverse) is
reported too: the engine will not load it, and the loot audit silently treats
the string as an item id, so the mistake hides.

Run from the repo root:
  python3 tools/saigon/check_refs.py data/mods/saigon_2000s/itemgroups/*.json
Exits 1 when anything does not resolve.
"""
import glob
import json
import sys

ITEM_TYPES = { 'ITEM', 'GENERIC', 'TOOL', 'COMESTIBLE', 'ARMOR', 'BOOK', 'AMMO', 'GUN', 'MAGAZINE', 'GUNMOD',
               'TOOL_ARMOR', 'BIONIC_ITEM', 'PET_ARMOR', 'ENGINE', 'WHEEL', 'TOOLMOD', 'BATTERY' }
# ids that are spelled as items in the JSON but are item groups in the data
KNOWN_GROUP_IDS = { 'shoes', 'shirts', 'pants', 'coats', 'underwear', 'clothing' }


def load_definitions():
    items, groups = set(), set()
    npcs = set()
    for path in glob.glob( 'data/json/**/*.json', recursive=True ) + \
                glob.glob( 'data/mods/saigon_2000s/**/*.json', recursive=True ):
        try:
            data = json.load( open( path ) )
        except ValueError:
            continue
        for o in data if isinstance( data, list ) else [ data ]:
            if not isinstance( o, dict ) or 'id' not in o:
                continue
            ids = o['id'] if isinstance( o['id'], list ) else [ o['id'] ]
            if o.get( 'type' ) in ITEM_TYPES:
                items.update( ids )
            elif o.get( 'type' ) in ( 'item_group', 'monstergroup' ):
                groups.update( ids )
            elif o.get( 'type' ) == 'npc':
                npcs.update( ids )
    return items, groups, npcs


def refs( node, item_refs, group_refs ):
    """Collect ( "item", id ) and ( "group", id ) pairs, all shorthand forms."""
    if isinstance( node, list ):
        for x in node:
            refs( x, item_refs, group_refs )
        return
    if not isinstance( node, dict ):
        return
    for key, val in node.items():
        if key == 'item' and isinstance( val, str ):
            item_refs.add( val )
        elif key == 'group' and isinstance( val, str ):
            group_refs.add( val )
        elif key == 'items':
            # [ "id", weight ] / [ [ "id", weight ], ... ] / [ { "item": ... } ]
            for x in val if isinstance( val, list ) else []:
                if isinstance( x, str ):
                    item_refs.add( x )
                elif isinstance( x, list ) and x and isinstance( x[0], str ):
                    item_refs.add( x[0] )
                else:
                    refs( x, item_refs, group_refs )
        elif key == 'groups':
            # [ "id" ] / [ [ "id", weight ] ] / [ { "group": ... } ]
            for x in val if isinstance( val, list ) else []:
                if isinstance( x, str ):
                    group_refs.add( x )
                elif isinstance( x, list ) and x and isinstance( x[0], str ):
                    group_refs.add( x[0] )
                else:
                    refs( x, item_refs, group_refs )
        else:
            refs( val, item_refs, group_refs )


def place_npcs( node, out ):
    """Collect the "class" ids of every place_npcs entry: mapgen wants an npc template."""
    if isinstance( node, list ):
        for x in node:
            place_npcs( x, out )
        return
    if not isinstance( node, dict ):
        return
    for key, val in node.items():
        if key == 'place_npcs' and isinstance( val, list ):
            for e in val:
                if isinstance( e, dict ) and isinstance( e.get( 'class' ), str ):
                    out.add( e['class'] )
        else:
            place_npcs( val, out )


def unstaffed_buildings( data ):
    """The mod's own landmark and place mapgens that put nobody inside (N6).

    A building is identified by the sgn_lm_*/sgn_pl_* terrain it draws on; only its
    north-west tile at ground level is required to be staffed (upper floors and roofs
    legitimately are not).
    """
    missing = []
    for o in data if isinstance( data, list ) else []:
        if not isinstance( o, dict ) or o.get( 'type' ) != 'mapgen':
            continue
        grid = o.get( 'om_terrain' )
        if not isinstance( grid, list ) or not grid or not isinstance( grid[ 0 ], list ):
            continue
        tiles = [ t for row in grid for t in row ]
        first = tiles[ 0 ] if tiles else None
        if not isinstance( first, str ):
            continue
        stem = first[ :-len( '_north' ) ] if first.endswith( '_north' ) else first
        if not stem.startswith( ( 'sgn_lm_', 'sgn_pl_' ) ) or not stem.endswith( '_00' ):
            continue
        ids = set()
        place_npcs( o.get( 'object', {} ), ids )
        if not ids:
            missing.append( stem )
    return missing


def main( argv ):
    paths = argv or sorted( glob.glob( 'data/mods/saigon_2000s/**/*.json', recursive=True ) )
    items, groups, npcs = load_definitions()
    # mapgen's "item" field and place_items entries accept an item_group id as well
    # (spawn_items resolves both), so an id that is a group is only reported when
    # the file is a pure item_group.
    in_mapgen = lambda p: '/mapgen/' in p or '/overmap/' in p or p.endswith( ( 'nha_ong.json', 'cho.json' ) )
    bad = 0
    for path in paths:
        try:
            data = json.load( open( path ) )
        except ValueError as err:
            print( '%s: not valid JSON: %s' % ( path, err ) )
            bad += 1
            continue
        item_refs, group_refs = set(), set()
        refs( data, item_refs, group_refs )
        npc_refs = set()
        place_npcs( data, npc_refs )
        missing_npc = sorted( n for n in npc_refs if n not in npcs )
        empty = unstaffed_buildings( data )
        missing_item = sorted( i for i in item_refs if i not in items )
        missing_group = sorted( g for g in group_refs if g not in groups )
        shadow_item = sorted( i for i in item_refs if i in groups and i not in items )
        shadow_group = sorted( g for g in group_refs if g in items and g not in groups )
        if in_mapgen( path ):
            # mapgen may name a group under "item"; only an unresolvable id matters
            missing_item = [ i for i in missing_item if i not in groups ]
            shadow_item = []
        if not ( missing_item or missing_group or shadow_item or shadow_group or missing_npc
                 or empty ):
            print( '%-62s %3d items, %2d groups, %2d npcs, all resolve' % (
                path, len( item_refs ), len( group_refs ), len( npc_refs ) ) )
            continue
        bad += 1
        if missing_item:
            print( '%s: no such item: %s' % ( path, ', '.join( missing_item ) ) )
        if missing_group:
            print( '%s: no such item_group: %s' % ( path, ', '.join( missing_group ) ) )
        if shadow_item:
            print( '%s: written as "item" but it is an item_group: %s' % ( path, ', '.join( shadow_item ) ) )
        if shadow_group:
            print( '%s: written as "group" but it is an item: %s' % ( path, ', '.join( shadow_group ) ) )
        if missing_npc:
            print( '%s: place_npcs names no such npc: %s' % ( path, ', '.join( missing_npc ) ) )
        if empty:
            print( '%s: N6, these buildings put nobody inside: %s' % ( path, ', '.join( empty ) ) )
    bad += check_vitamins()
    return 1 if bad else 0


def check_vitamins():
    """A food's "vitamins" must name vitamins that exist: the engine only notices a bad id
    when the item spawns (nước mắm named fish_allergen, which dda never had, and the suite
    logged it at random)."""
    known = set()
    for path in glob.glob( 'data/json/**/*.json', recursive=True ) + \
            glob.glob( 'data/mods/saigon_2000s/**/*.json', recursive=True ):
        try:
            data = json.load( open( path ) )
        except ValueError:
            continue
        for o in data if isinstance( data, list ) else [ data ]:
            if isinstance( o, dict ) and o.get( 'type' ) == 'vitamin':
                known.add( o.get( 'id' ) )
    bad = 0
    for path in sorted( glob.glob( 'data/mods/saigon_2000s/**/*.json', recursive=True ) ):
        try:
            data = json.load( open( path ) )
        except ValueError:
            continue
        for o in data if isinstance( data, list ) else [ data ]:
            if not isinstance( o, dict ):
                continue
            listed = ( o.get( 'vitamins' ) or [] ) + ( ( o.get( 'extend' ) or {} ).get( 'vitamins' ) or [] )
            unknown = [ v[0] for v in listed if isinstance( v, list ) and v and v[0] not in known ]
            if unknown:
                print( '%s: %s names no such vitamin: %s' % ( path, o.get( 'id' ), ', '.join( unknown ) ) )
                bad += 1
    return bad


if __name__ == '__main__':
    sys.exit( main( sys.argv[1:] ) )