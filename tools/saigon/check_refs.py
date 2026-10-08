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
    return items, groups


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


def main( argv ):
    paths = argv or sorted( glob.glob( 'data/mods/saigon_2000s/**/*.json', recursive=True ) )
    items, groups = load_definitions()
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
        missing_item = sorted( i for i in item_refs if i not in items )
        missing_group = sorted( g for g in group_refs if g not in groups )
        shadow_item = sorted( i for i in item_refs if i in groups and i not in items )
        shadow_group = sorted( g for g in group_refs if g in items and g not in groups )
        if in_mapgen( path ):
            # mapgen may name a group under "item"; only an unresolvable id matters
            missing_item = [ i for i in missing_item if i not in groups ]
            shadow_item = []
        if not ( missing_item or missing_group or shadow_item or shadow_group ):
            print( '%-62s %3d items, %2d groups, all resolve' % ( path, len( item_refs ), len( group_refs ) ) )
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
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit( main( sys.argv[1:] ) )