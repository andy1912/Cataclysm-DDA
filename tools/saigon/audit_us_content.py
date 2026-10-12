#!/usr/bin/env python3
"""B10: list dda items that Saigon content can spawn and that read as American.
L-loc7: the same for the animals Saigon's worlds can spawn (fauna()); N0: for its people (npcs()).

Collects every item_group the saigon_2000s mod references (mapgen, monster drops,
professions, the landmark generator), walks those groups recursively through dda's
item_group definitions (the mod's own definitions override dda's by id), and flags reachable
non-Saigon items whose name or description matches US markers (dollars, US states and
institutions, US sports, US brands and holidays).

Exits 1 when anything is flagged (check_mod.sh runs it).  Deliberate exceptions live in ALLOWED.
Run from the repo root:  python3 tools/saigon/audit_us_content.py [--all]
(--all also prints how many items each referenced group reaches, and every reachable animal)
"""
import glob
import gzip
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
        # "item" is one id: add_entry reads it with get_string, so a list here is a data error
        # the game rejects, not a way to take several items at once
        if isinstance( e['item'], str ):
            out.add( e['item'] )
    if 'group' in e and isinstance( e['group'], str ):
        walk( e['group'], groups, items, seen, out )
    for k in ( 'contents-item', 'contents-group', 'container-item', 'container-group' ):
        v = e.get( k )
        for x in ( v if isinstance( v, list ) else [ v ] if isinstance( v, str ) else [] ):
            out.add( x ) if x in items else walk( x, groups, items, seen, out )
    for k in ( 'collection', 'distribution' ):
        if isinstance( e.get( k ), list ):
            for sub in e[k]:
                entry( sub, groups, items, seen, out )


# L-loc2: dda items whose names pass the word list but are out of place in 2009 Saigon loot
OUT_OF_PLACE = {
    'mre_beef': 'American army ration (Saigon: lương khô)',
    'mre_veggy': 'American army ration (Saigon: lương khô)',
    'holybook_bible1': 'English King James Bible (Saigon parishes: Kinh Thánh)',
    'holybook_catechism': 'English catechism (Saigon parishes: sách kinh nguyện)',
    'guidebook': "dda's in-joke guide (Saigon: backpacker's guide to Vietnam)",
    'textbook_speech': 'American textbook (Saigon schools: Ngữ văn)',
    'textbook_firstaid': 'American textbook (Saigon: Red Cross first-aid handbook)',
    'corset': 'not worn on Saigon streets', 'corset_waist': 'not worn on Saigon streets',
    'long_undertop': 'thermal underwear in the tropics', 'long_underpants': 'thermal underwear in the tropics',
    'thermal_shirt': 'thermal underwear in the tropics',
    'engineering_robotics_kit': "dda's American gadget group", 'engineering_makerspace_kit': "dda's American gadget group",
    'engineering_engine_kit': "dda's American gadget group",
}


# L-loc7: animals.  The engine spawns GROUP_FISH when you fish and GROUP_RIVER along rivers and
# lakes; every overmap terrain's "spawns" group spawns on it; the mod's mapgen places its own.
# North American wildlife (by id) or a description that places an animal in North America is
# flagged; the mod redescribes dda species that have a close Vietnamese relative (wildlife.json).
HARDCODED_GROUPS = [ 'GROUP_FISH', 'GROUP_RIVER' ]
NA_FAUNA = re.compile( r"moose|zoose|reindeer|zeindeer|deer|zeer|elk\b|bobcat|cougar|zougar|coyote|wolf\b|fox_|raccoon|"
                       r"opossum|skunk|groundhog|chipmunk|beaver|muskrat|_mink\b|porcupine|lemming|turkey\b|goose_canadian|"
                       r"bear\b|bear_|zombear|bluejay|cardinal|chickadee|waxwing|hummingbird|trout|salmon|walleye|pike\b|"
                       r"perch|bass\b|sunfish|redbreast|warmouth|muskellunge|sucker|fallfish|burbot|sturgeon|whitefish|"
                       r"gar_|pickerel|kokanee|copperhead|rattlesnake|wormsnake|snapping|skink|weasel|hare\b|wild_rabbit|"
                       r"leo_|peeper|freedom_|gray_frog|wood_frog|mink_frog|spade_|ferret|raven|woodpecker|coot\b|"
                       r"duck\b|lynx|marten|vole" )
# deliberate: animals that are American but really live in the delta
ALLOWED_FAUNA = { 'mon_bullfrog_frog': 'ếch Mỹ: introduced, farmed in the delta since the 1990s' }
NA_TEXT = re.compile( r"North America|New England|American|U\.S\.|Canad|Appalach|Maine\b|Great Lakes", re.I )


def fauna():
    mod_files = glob.glob( 'data/mods/saigon_2000s/**/*.json', recursive=True )
    groups, mons, oters, redescribed = {}, {}, {}, set()
    for path in glob.glob( 'data/json/**/*.json', recursive=True ) + mod_files:
        try:
            data = json.load( open( path ) )
        except ValueError:
            continue
        for o in data if isinstance( data, list ) else [ data ]:
            if not isinstance( o, dict ):
                continue
            t = o.get( 'type' )
            if t == 'monstergroup' and 'id' in o:
                old = groups.get( o['id'] )
                if old and not o.get( 'override' ):        # a group without "override" extends
                    o = dict( old, monsters=old.get( 'monsters', [] ) + o.get( 'monsters', [] ) )
                groups[o['id']] = o
            elif t == 'MONSTER' and 'id' in o:
                parent = mons.get( o.get( 'copy-from' ) ) if o.get( 'copy-from' ) != o['id'] else mons.get( o['id'] )
                merged = dict( parent or {}, **o )
                merged['flags'] = list( o.get( 'flags', ( parent or {} ).get( 'flags', [] ) ) ) + \
                    ( o.get( 'extend' ) or {} ).get( 'flags', [] )
                mons[o['id']] = merged
                if path.startswith( 'data/mods/' ) and 'description' in o:
                    redescribed.add( o['id'] )
            elif t == 'overmap_terrain' and 'spawns' in o:
                for i in o['id'] if isinstance( o.get( 'id' ), list ) else [ o['id'] ] if 'id' in o else []:
                    oters[i] = o['spawns']['group']
    # terrains: the real map's, the mod's own, and dda's generated wilderness (forest, field, swamp)
    terrains = set()
    for f in glob.glob( 'data/mods/saigon_2000s/realmap_2009/*.omap.gz' ):
        for level in json.load( gzip.open( f ) ):
            for t, _ in level['layers']:
                terrains.add( t )
                terrains.add( re.sub( r'_(north|south|east|west)$', '', t ) )
    terrains |= { o for o, g in oters.items() if o.startswith( 'sgn_' ) or g in ( 'GROUP_FOREST', 'GROUP_SWAMP' ) }
    roots = set( HARDCODED_GROUPS ) | { oters[t] for t in terrains if t in oters }
    text = ' '.join( open( f ).read() for f in glob.glob( 'data/mods/saigon_2000s/mapgen/**/*.json', recursive=True ) )
    text += open( 'tools/saigon/gen_saigon_landmarks.py' ).read() + open( 'tools/saigon/gen_places.py' ).read()
    found = set( re.findall( r'["\'](?:group|monster)["\']\s*:\s*["\']([\w-]+)["\']', text ) )
    roots |= found & set( groups )
    start = found & set( mons )
    reach, seen, todo = set(), set(), list( roots )
    todo += [ ( 'm', m ) for m in start ]
    while todo:
        x = todo.pop()
        if isinstance( x, tuple ):
            m = x[1]
            if m in reach or m not in mons:
                continue
            reach.add( m )
            o = mons[m]
            up = o.get( 'upgrades' ) or {}
            if up.get( 'into' ):
                todo.append( ( 'm', up['into'] ) )
            if up.get( 'into_group' ):
                todo.append( up['into_group'] )
            bt = {} if 'NO_BREED' in o['flags'] else ( o.get( 'reproduction' ) or {} ).get( 'baby_type' ) or {}
            if bt.get( 'baby_monster' ):
                todo.append( ( 'm', bt['baby_monster'] ) )
            if bt.get( 'baby_monster_group' ):
                todo.append( bt['baby_monster_group'] )
            continue
        if x in seen or x not in groups:
            continue
        seen.add( x )
        for e in groups[x].get( 'monsters', [] ):
            todo.append( e['group'] if 'group' in e else ( 'm', e.get( 'monster' ) ) )
    print( '%d spawn groups reach %d animals and monsters' % ( len( seen ), len( reach ) ) )
    hits = []
    for m in sorted( reach ):
        o = mons[m]
        desc = tr( o.get( 'name' ) ) + ' | ' + tr( o.get( 'description' ) )
        if '--all' in sys.argv:
            print( '    %-34s %s' % ( m, desc[:90] ) )
        if m.startswith( 'sgn_' ) or m in ALLOWED_FAUNA:
            continue
        # an animal the mod redescribes is judged by its new text, not by dda's id
        hit = ( NA_FAUNA.search( m ) if m not in redescribed else None ) or NA_TEXT.search( desc )
        if hit:
            hits.append( ( m, hit.group( 0 ), desc ) )
    print( '%d North American animals' % len( hits ) )
    for m, word, desc in hits:
        print( '  %-32s [%s] %s' % ( m, word, desc[:110] ) )
    return len( hits )


# N0: people.  A random NPC (game::perhaps_add_random_npc, and the starting NPC) is classless:
# Character::randomize gives it a profession the scenario allows (Saigon's, settings/whitelists.json),
# then npc::starting_inv_passtime dresses and arms it from the item groups NC_NONE_<what> and
# NC_NONE_HARDENED_<what> (npc.cpp random_item_from); it gets one mission from the ORIGIN_ANY_NPC pool
# (a starting NPC: ORIGIN_OPENER_NPC; ORIGIN_SECONDARY missions are follow-ups only their own NPCs
# offer).  An npc_class's "common" only adds a hobby background; nothing picks classes at random.
# So: the wanderer groups reach no firearm and nothing American, dda's missions are out of those
# pools, and every Saigon class dresses and arms its people from Saigon item groups (firearms only
# for GUN_CLASSES: 2009 Saigon civilians had none).
# N4: the mod has exactly one firearm, sgn_sung_9x18, and it may be held by exactly one class.
# This set used to name sgn_class_cong_an, which N3 renamed to sgn_class_guard, so the exemption
# had been pointing at a class that no longer existed - and a guard carrying a gun would have been
# flagged by a rule that could not be satisfied.  Adding a class here owes CONTENT_BIBLE.md a
# sentence saying why that person is armed.
GUN_CLASSES = { 'sgn_class_guard' }
# the firearms the mod defines; only a GUN_CLASSES group may reach one
GUN_ITEMS = { 'sgn_sung_9x18', 'sgn_mag_9x18' }
WANDERER_PREFIXES = ( 'NC_NONE_', 'NC_NONE_HARDENED_' )
RANDOM_ORIGINS = ( 'ORIGIN_ANY_NPC', 'ORIGIN_OPENER_NPC' )


def npcs():
    # every group the mod uses as loot must be listed, so N4 can prove the pistol stays inside
    # the guard's hands and reaches nobody else - not a shophouse, not a corpse, not the world
    mod_files = glob.glob( 'data/mods/saigon_2000s/**/*.json', recursive=True )
    paths = glob.glob( 'data/json/**/*.json', recursive=True ) + mod_files
    groups, items = load( paths )
    classes, missions = {}, {}
    for path in paths:
        try:
            data = json.load( open( path ) )
        except ValueError:
            continue
        for o in data if isinstance( data, list ) else [ data ]:
            if not isinstance( o, dict ) or 'id' not in o:
                continue
            table = { 'npc_class': classes, 'mission_definition': missions }.get( o.get( 'type' ) )
            if table is not None:
                parent = table.get( o.get( 'copy-from' ) ) if o.get( 'copy-from' ) else None
                table[o['id']] = dict( parent or {}, **o )
    hits = []

    def check_gear( who, group, guns_ok ):
        out = set()
        walk( group, groups, items, set(), out )
        for i in sorted( out ):
            it = items.get( i ) or {}
            text = tr( it.get( 'name' ) ) + ' | ' + tr( it.get( 'description' ) )
            gun = it.get( 'type' ) == 'GUN' or 'GUN' in ( it.get( 'subtypes' ) or [] )
            if gun and not guns_ok:
                hits.append( ( who, 'firearm', i ) )
            elif not i.startswith( 'sgn_' ) and ( US.search( text ) or i in OUT_OF_PLACE ):
                hits.append( ( who, 'gear', i ) )
    wanderer = sorted( g for g in groups if g.startswith( WANDERER_PREFIXES ) )
    for g in wanderer:
        check_gear( g, g, False )
    for mid, o in sorted( missions.items() ):
        pool = [ x for x in o.get( 'origins' ) or [] if x in RANDOM_ORIGINS ]
        if pool and not mid.startswith( 'MISSION_SGN_' ):
            hits.append( ( mid, 'random mission', tr( o.get( 'name' ) ) ) )
    for cid, o in sorted( classes.items() ):
        if not cid.startswith( 'sgn_' ):
            continue
        for key in ( 'worn_override', 'carry_override', 'weapon_override' ):
            if not o.get( key ):
                hits.append( ( cid, 'no ' + key, "dda's default gear" ) )
            else:
                check_gear( cid, o[key], cid in GUN_CLASSES )
    print( '%d wanderer gear groups, %d Saigon NPC classes, %d missions; %d problems' % (
        len( wanderer ), sum( c.startswith( 'sgn_' ) for c in classes ), len( missions ), len( hits ) ) )
    for what, why, detail in hits:
        print( '  %-36s [%s] %s' % ( what, why, detail[:90] ) )
    return len( hits )


def main():
    mod_files = glob.glob( 'data/mods/saigon_2000s/**/*.json', recursive=True )
    groups, items = load( glob.glob( 'data/json/**/*.json', recursive=True ) + mod_files )
    mod = ' '.join( open( f ).read() for f in mod_files ) + open( 'tools/saigon/gen_saigon_landmarks.py' ).read() + \
        open( 'tools/saigon/gen_places.py' ).read()
    # a group counts only where it is used as loot: after "group" / "item" / "death_drops" /
    # "contents-group" (JSON) or 'item' (the landmark generator), not as a terrain or season name
    used = set( re.findall( r'["\'](?:group|item|items|death_drops|contents-group|container-group)["\']\s*:\s*["\']([\w-]+)["\']',
                            mod ) )
    # an id that is also a real item is that item ("item": "pants" on a laundry line), not dda's group
    # the mod's vehicles copied from dda ones carry their parents' glovebox and trunk groups
    vehicles = {}
    for f in glob.glob( 'data/json/vehicles/**/*.json', recursive=True ) + mod_files:
        try:
            data = json.load( open( f ) )
        except ValueError:
            continue
        for o in data if isinstance( data, list ) else []:
            if isinstance( o, dict ) and o.get( 'type' ) == 'vehicle':
                vehicles[o.get( 'id' ) or o.get( 'abstract' )] = o
    for o in list( vehicles.values() ):
        if not str( o.get( 'id', '' ) ).startswith( 'sgn_' ):
            continue
        v, hops = o, 0
        while v is not None and hops < 6:
            for it in v.get( 'items', [] ):
                g = it.get( 'item_groups' ) or []
                used.update( [ g ] if isinstance( g, str ) else g )
            v, hops = vehicles.get( v.get( 'copy-from' ) ), hops + 1
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
        elif i in OUT_OF_PLACE:
            hits.append( ( i, 'out of place', OUT_OF_PLACE[i] ) )
    print( '%d flagged (%d allowed exceptions)' % ( len( hits ), len( ALLOWED ) ) )
    for i, word, text in hits:
        print( '  %-32s [%s] %s' % ( i, word, text[:120] ) )
    leaked = firearms_escape( roots, groups, items )
    if leaked:
        for root, item in leaked:
            print( '  %-32s [gun leak] reaches %s, which only a %s may carry' % (
                root, item, ' or '.join( sorted( GUN_CLASSES ) ) ) )
    animals = fauna()
    people = npcs()
    return 1 if hits or animals or people or leaked else 0


def firearms_escape( roots, groups, items ):
    """N4: the mod's own firearms must be reachable only through a GUN_CLASSES weapon group.

    Every group the mod places as loot is a root here, so anything a shophouse, a corpse, a
    landmark or a mapgen tile can spawn is in `roots`.  A guard's weapon_override is one of
    those too, which is the point: the pistol has to come out of a guard and from nowhere
    else.  Removing the class from GUN_CLASSES, or adding the pistol to a loot group, trips
    this.
    """
    allowed_groups = set()
    for f in glob.glob( 'data/mods/saigon_2000s/npcs/*.json' ):
        try:
            data = json.load( open( f ) )
        except ValueError:
            continue
        for o in data if isinstance( data, list ) else [ data ]:
            if isinstance( o, dict ) and o.get( 'type' ) == 'npc_class' \
                    and o.get( 'id' ) in GUN_CLASSES and o.get( 'weapon_override' ):
                allowed_groups.add( o['weapon_override'] )
    bad = []
    for r in roots:
        if r in allowed_groups:
            continue
        out = set()
        walk( r, groups, items, set(), out )
        for i in sorted( out & GUN_ITEMS ):
            bad.append( ( r, i ) )
    return bad


if __name__ == '__main__':
    sys.exit( main() )
