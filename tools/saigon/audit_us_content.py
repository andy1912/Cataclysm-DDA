#!/usr/bin/env python3
"""B10: list dda items that Saigon content can spawn and that read as American.

Collects every item_group the saigon_2000s mod references (mapgen, monster drops,
professions, the landmark generator), walks those groups recursively through dda's
item_group definitions (the mod's own definitions override dda's by id), and flags reachable
non-Saigon items whose name or description matches US markers (dollars, US states and
institutions, US sports, US brands and holidays).

Exits 1 when anything is flagged (check_mod.sh runs it).  Deliberate exceptions live in ALLOWED.
Run from the repo root:  python3 tools/saigon/audit_us_content.py [--all]
(--all also prints how many items each referenced group reaches)
"""
import glob
import json
import re
import sys

ITEM_TYPES = { 'ITEM', 'GENERIC', 'TOOL', 'COMESTIBLE', 'ARMOR', 'BOOK', 'AMMO', 'GUN', 'MAGAZINE', 'GUNMOD',
               'TOOL_ARMOR', 'BIONIC_ITEM', 'PET_ARMOR', 'ENGINE', 'WHEEL', 'TOOLMOD', 'BATTERY' }
US = re.compile( r"\b(America\w*|U\.S\.A?\b|USA\b|United States|dollars?\b|Fort\b|New England|Maine|state trooper|"
                 r"county|Uncle Sam|Thanksgiving|football|baseball|hockey|NFL|NBA|MLB|Super Bowl|Fourth of July|"
                 r"bourbon|Hershey|Coca|Pepsi|Twinkie|Spam\b|pumpkin spice|Halloween|Christmas|Bible Belt|Yankee|"
                 r"Confederate|Texas|Florida|California|New York|Ohio|Boston)", re.I )


# Deliberate exceptions: ( group, item ) -> why it belongs in 2004 Saigon
ALLOWED = {
    ( 'sgn_tourist', 'money_twenty' ): 'backpackers on Bùi Viện carried US dollars',
    ( 'sgn_tourist', 'money_hundred' ): 'backpackers on Bùi Viện carried US dollars',
}


def tr( v ):
    if isinstance( v, dict ):
        return v.get( 'str', v.get( 'str_sp', v.get( 'str_pl', '' ) ) )
    return v or ''


def load( paths ):
    groups, items = {}, {}
    for path in paths:
        try:
            data = json.load( open( path ) )
        except Exception:
            continue
        for o in data if isinstance( data, list ) else [ data ]:
            if not isinstance( o, dict ):
                continue
            if o.get( 'type' ) == 'item_group':
                groups[o['id']] = o
            elif o.get( 'type' ) in ITEM_TYPES and 'id' in o:
                for i in o['id'] if isinstance( o['id'], list ) else [ o['id'] ]:
                    items[i] = o
    return groups, items


def walk( g, groups, items, seen, out ):
    if g in seen or g not in groups:
        return
    seen.add( g )
    o = groups[g]
    for e in o.get( 'entries', [] ) + o.get( 'items', [] ) + o.get( 'groups', [] ):
        entry( e, groups, items, seen, out )


def entry( e, groups, items, seen, out ):
    """One item_group entry, recursing into nested collection / distribution lists."""
    if isinstance( e, str ):
        out.add( e ) if e in items else walk( e, groups, items, seen, out )
        return
    if isinstance( e, list ):
        e = { 'item': e[0] }
    if not isinstance( e, dict ):
        return
    if 'item' in e:
        out.add( e['item'] )
    if 'group' in e:
        walk( e['group'], groups, items, seen, out )
    for k in ( 'contents-item', 'contents-group', 'container-item', 'container-group' ):
        v = e.get( k )
        for x in ( v if isinstance( v, list ) else [ v ] if isinstance( v, str ) else [] ):
            out.add( x ) if x in items else walk( x, groups, items, seen, out )
    for k in ( 'collection', 'distribution' ):
        if isinstance( e.get( k ), list ):
            for sub in e[k]:
                entry( sub, groups, items, seen, out )


def main():
    mod_files = glob.glob( 'data/mods/saigon_2000s/**/*.json', recursive=True )
    groups, items = load( glob.glob( 'data/json/**/*.json', recursive=True ) + mod_files )
    mod = ' '.join( open( f ).read() for f in mod_files ) + open( 'tools/saigon/gen_saigon_landmarks.py' ).read()
    # a group counts only where it is used as loot: after "group" / "item" / "death_drops" /
    # "contents-group" (JSON) or 'item' (the landmark generator), not as a terrain or season name
    used = set( re.findall( r'["\'](?:group|item|items|death_drops|contents-group|container-group)["\']\s*:\s*["\']([\w-]+)["\']',
                            mod ) )
    # an id that is also a real item is that item ("item": "pants" on a laundry line), not dda's group
    roots = sorted( g for g in groups if g in used and g not in items )
    reach, per_root = set(), {}
    for r in roots:
        out = set()
        walk( r, groups, items, set(), out )
        out -= { i for ( g, i ) in ALLOWED if g == r }
        per_root[r] = len( out )
        reach |= out
    print( '%d groups referenced by the mod reach %d items' % ( len( roots ), len( reach ) ) )
    if '--all' in sys.argv:
        for r in sorted( per_root, key=per_root.get, reverse=True ):
            print( '  %5d  %s' % ( per_root[r], r ) )
    hits = []
    for i in sorted( reach ):
        o = items.get( i )
        if not o or i.startswith( 'sgn_' ):
            continue
        text = tr( o.get( 'name' ) ) + ' | ' + tr( o.get( 'description' ) )
        m = US.search( text )
        if m:
            hits.append( ( i, m.group( 0 ), text ) )
    print( '%d flagged (%d allowed exceptions)' % ( len( hits ), len( ALLOWED ) ) )
    for i, word, text in hits:
        print( '  %-32s [%s] %s' % ( i, word, text[:120] ) )
    return 1 if hits else 0


if __name__ == '__main__':
    sys.exit( main() )
