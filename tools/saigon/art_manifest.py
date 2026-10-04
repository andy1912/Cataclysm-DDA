#!/usr/bin/env python3
"""Art manifest: every sprite id a Saigon 2000s world can show.

Walks references outward from the saigon_2000s mod (its mapgen and palettes, the dda
road/bridge mapgen it keeps, item groups, monster groups, vehicle groups and
prototypes, professions, recipes, monster death drops), recursing into dda content,
and lists each reachable id with:
  category   terrain / furniture / item / monster / vehicle_part / overmap_terrain / field
  source     mod or dda
  tier       T1 = on screen in every Saigon district (terrain, furniture, street traffic,
                  zombies, starting kit), T2 = common loot, T3 = everything else reachable
  facings    sprites needed per perspective (top-down / isometric), see FACINGS
  fallback   current looks_like chain end (what draws today without new art)
  refs       a few referencing objects, for context

Writes doc/saigon/art/manifest.csv and doc/saigon/art/manifest_summary.md.
Run from the repo root:  python3 tools/saigon/art_manifest.py
"""
import collections
import csv
import glob
import json
import os

ROOT = os.path.join( os.path.dirname( __file__ ), '..', '..' )
MOD = os.path.join( ROOT, 'data', 'mods', 'saigon_2000s' )
OUT = os.path.join( ROOT, 'doc', 'saigon', 'art' )
DDA_ROAD_MAPGEN = [ 'data/json/mapgen/road.json', 'data/json/mapgen/bridges.json',
                    'data/json/mapgen/nested/road_vehicles_nested.json' ]

ITEM_TYPES = { 'ITEM', 'AMMO', 'GUN', 'ARMOR', 'TOOL', 'COMESTIBLE', 'BOOK', 'GENERIC', 'MAGAZINE',
               'GUNMOD', 'TOOLMOD', 'BIONIC_ITEM', 'ENGINE', 'WHEEL', 'BATTERY', 'PET_ARMOR', 'TOOL_ARMOR' }
CATEGORY_OF_TYPE = { 'terrain': 'terrain', 'furniture': 'furniture', 'MONSTER': 'monster',
                     'vehicle_part': 'vehicle_part', 'overmap_terrain': 'overmap_terrain',
                     'field_type': 'field' }
# Sprites needed per id: (top-down, isometric).  Walls/fences connect (16 variants top-down,
# fewer distinct in iso but 2 faces); vehicle parts rotate (1 rotatable top-down sprite, 4 iso
# facings); creatures need 1 top-down and 4 iso facings; flat items 1/1.
FACINGS = { 'terrain': ( '1-16 (connecting)', '1-6 (2 faces if wall)' ), 'furniture': ( '1', '1-4' ),
            'item': ( '1', '1' ), 'monster': ( '1', '4' ), 'vehicle_part': ( '1 (rotates)', '4' ),
            'overmap_terrain': ( '1-4 (rotated)', '1-4' ), 'field': ( '1-3 (intensity)', '1-3' ) }


def load_all():
    objs = {}
    for base, source in ( ( os.path.join( ROOT, 'data', 'json' ), 'dda' ), ( MOD, 'mod' ) ):
        for f in glob.glob( os.path.join( base, '**', '*.json' ), recursive=True ):
            try:
                with open( f, encoding='utf-8' ) as fh:
                    data = json.load( fh )
            except ( json.JSONDecodeError, UnicodeDecodeError ):
                continue
            for o in data if isinstance( data, list ) else [ data ]:
                if not isinstance( o, dict ):
                    continue
                t = o.get( 'type' )
                key_id = o.get( 'id' ) or o.get( 'abstract' ) or o.get( 'nested_mapgen_id' )
                if t == 'mapgen' and 'nested_mapgen_id' in o:
                    key = ( 'nested_mapgen', o['nested_mapgen_id'] )
                elif t == 'MONSTER_FACTION':
                    continue
                elif isinstance( key_id, str ):
                    key = ( 'ITEM' if t in ITEM_TYPES else t, key_id )
                else:
                    continue
                # mod definitions override dda ones of the same type and id
                if key not in objs or source == 'mod':
                    objs[key] = ( o, source, os.path.relpath( f, ROOT ) )
    return objs


class Walker:
    def __init__( self, objs ):
        self.objs = objs
        self.found = {}          # ( category, id ) -> dict
        self.seen = set()

    def add( self, category, sid, tier, ref ):
        if not isinstance( sid, str ) or not sid or sid in ( 'null', 't_null', 'f_null' ):
            return
        sid = sid.split( '#' )[0]
        key = ( category, sid )
        e = self.found.get( key )
        if e is None:
            e = self.found[key] = { 'tier': tier, 'refs': [] }
        e['tier'] = min( e['tier'], tier )
        if len( e['refs'] ) < 3 and ref not in e['refs']:
            e['refs'].append( ref )

    def get( self, typ, sid ):
        return self.objs.get( ( typ, sid ) )

    # --- mapgen -----------------------------------------------------------
    def mapping_ids( self, value ):
        if isinstance( value, str ):
            yield value
        elif isinstance( value, list ):
            for v in value:
                if isinstance( v, list ) and v:
                    yield from self.mapping_ids( v[0] )
                else:
                    yield from self.mapping_ids( v )
        elif isinstance( value, dict ):
            # 'param' names a parameter, it is not an id: the ids come from the parameter's
            # default (walked with the 'parameters' block) and from 'fallback'
            for k in ( 'switch', 'fallback', 'distribution', 'cases', 'default' ):
                if k in value:
                    yield from self.mapping_ids( value[k] if k != 'cases' else list( value[k].values() ) )

    def walk_mapgen_object( self, obj, tier, ref ):
        if not isinstance( obj, dict ):
            return
        for k in ( 'fill_ter', ):
            if k in obj:
                for t in self.mapping_ids( obj[k] ):
                    self.add( 'terrain', t, tier, ref )
        for k, cat in ( ( 'terrain', 'terrain' ), ( 'furniture', 'furniture' ) ):
            for v in ( obj.get( k ) or {} ).values():
                for sid in self.mapping_ids( v ):
                    self.add( cat, sid, tier, ref )
        for v in ( obj.get( 'items' ) or {} ).values():
            for entry in v if isinstance( v, list ) else [ v ]:
                if isinstance( entry, dict ):
                    for g in self.mapping_ids( entry.get( 'item' ) ):
                        self.walk_item_group( g, max( tier, 2 ), ref )
        for v in ( obj.get( 'item' ) or {} ).values():
            for entry in v if isinstance( v, list ) else [ v ]:
                if isinstance( entry, dict ):
                    for i in self.mapping_ids( entry.get( 'item' ) ):
                        self.walk_item( i, max( tier, 2 ), ref )
        for pal in obj.get( 'palettes' ) or []:
            for pid in self.mapping_ids( pal ):
                p = self.get( 'palette', pid )
                if p and ( 'palette', pid ) not in self.seen:
                    self.seen.add( ( 'palette', pid ) )
                    self.walk_mapgen_object( p[0], tier, 'palette ' + pid )
        params = obj.get( 'parameters' ) or {}
        for pv in params.values():
            if not isinstance( pv, dict ):
                continue
            kind = pv.get( 'type' )
            for nid in self.mapping_ids( pv.get( 'default' ) ):
                if kind == 'ter_str_id':
                    self.add( 'terrain', nid, tier, ref )
                elif kind == 'furn_str_id':
                    self.add( 'furniture', nid, tier, ref )
                else:
                    self.walk_nested( nid, tier, ref )
        for pn in obj.get( 'place_nested' ) or []:
            for k in ( 'chunks', 'else_chunks' ):
                for nid in self.mapping_ids( pn.get( k ) ):
                    self.walk_nested( nid, tier, ref )
        for pm in obj.get( 'place_monster' ) or []:
            if 'group' in pm:
                self.walk_monster_group( pm['group'], tier, ref )
            if 'monster' in pm:
                for m in self.mapping_ids( pm['monster'] ):
                    self.walk_monster( m, tier, ref )
        for pm in obj.get( 'place_monsters' ) or []:
            self.walk_monster_group( pm.get( 'monster' ), tier, ref )
        for pv in obj.get( 'place_vehicles' ) or []:
            self.walk_vehicle_group( pv.get( 'vehicle' ), tier, ref )
        for pi in obj.get( 'place_loot' ) or []:
            if 'group' in pi:
                self.walk_item_group( pi['group'], max( tier, 2 ), ref )
            if 'item' in pi:
                self.walk_item( pi['item'], max( tier, 2 ), ref )
        for pi in obj.get( 'place_items' ) or []:
            self.walk_item_group( pi.get( 'item' ), max( tier, 2 ), ref )
        for pn in obj.get( 'place_npcs' ) or []:
            self.add( 'npc', pn.get( 'class' ), tier, ref )

    def walk_nested( self, nid, tier, ref ):
        if not isinstance( nid, str ) or ( 'nested', nid ) in self.seen:
            return
        self.seen.add( ( 'nested', nid ) )
        n = self.get( 'nested_mapgen', nid )
        if n:
            self.walk_mapgen_object( n[0].get( 'object' ), tier, 'nested ' + nid )

    # --- items --------------------------------------------------------------
    def walk_item( self, iid, tier, ref ):
        self.add( 'item', iid, tier, ref )

    def walk_group_entries( self, entries, tier, ref ):
        for e in entries or []:
            if isinstance( e, str ):
                self.walk_item( e, tier, ref )
            elif isinstance( e, list ) and e:
                self.walk_item( e[0], tier, ref )
            elif isinstance( e, dict ):
                if 'item' in e:
                    self.walk_item( e['item'], tier, ref )
                if 'group' in e:
                    self.walk_item_group( e['group'], tier, ref )
                for k in ( 'container-item', 'contents-item', 'ammo-item' ):
                    for v in e.get( k, [] ) if isinstance( e.get( k ), list ) else [ e.get( k ) ]:
                        if isinstance( v, str ):
                            self.walk_item( v, tier, ref )
                for k in ( 'distribution', 'collection', 'entries' ):
                    self.walk_group_entries( e.get( k ), tier, ref )

    def walk_item_group( self, gid, tier, ref ):
        if isinstance( gid, dict ):
            self.walk_group_entries( gid.get( 'entries' ) or gid.get( 'items' ), tier, ref )
            return
        if not isinstance( gid, str ) or ( 'item_group', gid ) in self.seen:
            return
        self.seen.add( ( 'item_group', gid ) )
        g = self.get( 'item_group', gid )
        if not g:
            return
        o = g[0]
        if g[1] == 'dda':
            # loot reached only through dda's deep group trees is "other reachable" content
            tier = max( tier, 3 )
        for k in ( 'entries', 'items' ):
            self.walk_group_entries( o.get( k ), tier, 'item_group ' + gid )
        for gg in o.get( 'groups' ) or []:
            self.walk_item_group( gg[0] if isinstance( gg, list ) else gg, tier, 'item_group ' + gid )
        if isinstance( o.get( 'container-item' ), str ):
            self.walk_item( o['container-item'], tier, 'item_group ' + gid )

    # --- monsters -----------------------------------------------------------
    def walk_monster( self, mid, tier, ref ):
        if not isinstance( mid, str ):
            return
        self.add( 'monster', mid, tier, ref )
        if ( 'monster', mid ) in self.seen:
            return
        self.seen.add( ( 'monster', mid ) )
        m = self.get( 'MONSTER', mid )
        if m and m[0].get( 'death_drops' ):
            self.walk_item_group( m[0]['death_drops'], max( tier, 2 ), 'drops of ' + mid )

    def walk_monster_group( self, gid, tier, ref ):
        if not isinstance( gid, str ) or ( 'monstergroup', gid ) in self.seen:
            return
        self.seen.add( ( 'monstergroup', gid ) )
        g = self.get( 'monstergroup', gid )
        if not g:
            return
        o = g[0]
        if isinstance( o.get( 'default' ), str ):
            self.walk_monster( o['default'], tier, 'monstergroup ' + gid )
        for e in o.get( 'monsters' ) or []:
            if 'monster' in e:
                self.walk_monster( e['monster'], tier, 'monstergroup ' + gid )
            if 'group' in e:
                self.walk_monster_group( e['group'], tier, 'monstergroup ' + gid )

    # --- vehicles -----------------------------------------------------------
    def walk_vehicle_group( self, gid, tier, ref ):
        if not isinstance( gid, str ) or ( 'vehicle_group', gid ) in self.seen:
            return
        self.seen.add( ( 'vehicle_group', gid ) )
        g = self.get( 'vehicle_group', gid )
        if g:
            for v in g[0].get( 'vehicles' ) or []:
                self.walk_vehicle( v[0] if isinstance( v, list ) else v, tier, 'vehicle_group ' + gid )
        else:
            self.walk_vehicle( gid, tier, ref )  # prototype ids double as singleton groups

    def walk_vehicle( self, vid, tier, ref ):
        if not isinstance( vid, str ) or ( 'vehicle', vid ) in self.seen:
            return
        self.seen.add( ( 'vehicle', vid ) )
        v = self.get( 'vehicle', vid )
        while v and 'parts' not in v[0] and v[0].get( 'copy-from' ):
            v = self.get( 'vehicle', v[0]['copy-from'] )
        if not v:
            return
        for tile in v[0].get( 'parts' ) or []:
            plist = tile.get( 'parts' ) or ( [ tile['part'] ] if 'part' in tile else [] )
            for p in plist:
                pid = p.get( 'part' ) if isinstance( p, dict ) else p
                self.add( 'vehicle_part', pid, tier, 'vehicle ' + vid )


def fallback_of( objs, category, sid ):
    typ = { 'terrain': 'terrain', 'furniture': 'furniture', 'item': 'ITEM', 'monster': 'MONSTER',
            'vehicle_part': 'vehicle_part', 'overmap_terrain': 'overmap_terrain' }.get( category )
    if category == 'monster' and sid.startswith( ( 'pseudo_dormant_', 'mon_pseudo_dormant_' ) ):
        # generated at runtime from the dda monster (MonsterGenerator::generate_fake_pseudo_dormant_monster)
        base = sid.replace( 'mon_pseudo_dormant_', 'mon_' ).replace( 'pseudo_dormant_', '' )
        return base
    chain = []
    cur = sid
    for _ in range( 8 ):
        o = objs.get( ( typ, cur ) ) if typ else None
        if not o:
            break
        nxt = o[0].get( 'looks_like' ) or o[0].get( 'copy-from' )
        if not isinstance( nxt, str ) or nxt == cur:
            break
        chain.append( nxt )
        cur = nxt
    return chain[-1] if chain else ''


def main():
    objs = load_all()
    w = Walker( objs )
    # Seeds: everything the mod defines, plus the mod's mapgen, plus the dda roads it keeps.
    for ( typ, sid ), ( o, source, path ) in objs.items():
        if source != 'mod':
            continue
        if typ == 'mapgen':
            w.walk_mapgen_object( o.get( 'object' ), 1, path )
        elif typ == 'nested_mapgen':
            w.walk_nested( sid, 1, path )
        elif typ == 'ITEM':
            w.walk_item( sid, 2, path )
        elif typ == 'MONSTER':
            w.walk_monster( sid, 1, path )
        elif typ == 'vehicle':
            w.walk_vehicle( sid, 1, path )
        elif typ == 'vehicle_group':
            w.walk_vehicle_group( sid, 1, path )
        elif typ == 'monstergroup':
            w.walk_monster_group( sid, 1, path )
        elif typ == 'item_group':
            w.walk_item_group( sid, 2, path )
        elif typ in ( 'terrain', 'furniture', 'overmap_terrain' ):
            w.add( CATEGORY_OF_TYPE[typ], sid, 1, path )
        elif typ == 'profession':
            for e in ( ( o.get( 'items' ) or {} ).get( 'both' ) or {} ).get( 'entries', [] ):
                if 'item' in e:
                    w.walk_item( e['item'], 1, 'profession ' + sid )
                if 'group' in e:
                    w.walk_item_group( e['group'], 1, 'profession ' + sid )
            if o.get( 'vehicle' ):
                w.walk_vehicle( o['vehicle'], 1, 'profession ' + sid )
        elif typ == 'recipe':
            w.walk_item( o.get( 'result' ), 2, 'recipe' )
    for f in DDA_ROAD_MAPGEN:
        with open( os.path.join( ROOT, f ) ) as fh:
            for o in json.load( fh ):
                if o.get( 'type' ) == 'mapgen' and 'om_terrain' in o:
                    w.walk_mapgen_object( o.get( 'object' ), 1, f )
    # city-ambient dda pieces always visible
    for t in ( 't_pavement', 't_pavement_y', 't_sidewalk', 't_concrete', 't_open_air', 't_dirt', 't_grass' ):
        w.add( 'terrain', t, 1, 'ambient' )

    rows = []
    for ( cat, sid ), e in sorted( w.found.items(), key=lambda kv: ( kv[1]['tier'], kv[0] ) ):
        if cat == 'npc':
            continue
        typ = { 'terrain': 'terrain', 'furniture': 'furniture', 'item': 'ITEM', 'monster': 'MONSTER',
                'vehicle_part': 'vehicle_part', 'overmap_terrain': 'overmap_terrain' }.get( cat )
        o = objs.get( ( typ, sid ) )
        source = o[1] if o else 'unknown'
        td, iso = FACINGS.get( cat, ( '1', '1' ) )
        rows.append( { 'tier': 'T%d' % min( e['tier'], 3 ), 'category': cat, 'id': sid, 'source': source,
                       'facings_topdown': td, 'facings_iso': iso,
                       'fallback': fallback_of( objs, cat, sid ), 'refs': '; '.join( e['refs'] ) } )
    os.makedirs( OUT, exist_ok=True )
    with open( os.path.join( OUT, 'manifest.csv' ), 'w', newline='', encoding='utf-8' ) as fh:
        wr = csv.DictWriter( fh, fieldnames=list( rows[0].keys() ), lineterminator='\n' )
        wr.writeheader()
        wr.writerows( rows )
    counts = collections.Counter( ( r['tier'], r['category'], r['source'] ) for r in rows )
    cats = sorted( { r['category'] for r in rows } )
    lines = [ '# Saigon art manifest: summary', '',
              'Generated by `tools/saigon/art_manifest.py`; full list in `manifest.csv` (%d ids).' % len( rows ),
              '', '| Tier | ' + ' | '.join( cats ) + ' | total |', '|---|' + '---|' * ( len( cats ) + 1 ) ]
    for tier in ( 'T1', 'T2', 'T3' ):
        cells = []
        for c in cats:
            m = counts[( tier, c, 'mod' )]
            d = counts[( tier, c, 'dda' )] + counts[( tier, c, 'unknown' )]
            cells.append( '%d (%d mod / %d dda)' % ( m + d, m, d ) )
        total = sum( v for ( t, _, _ ), v in counts.items() if t == tier )
        lines.append( '| %s | %s | %d |' % ( tier, ' | '.join( cells ), total ) )
    lines += [ '', 'T1 = on screen in every Saigon district; T2 = common loot; T3 = other reachable content.',
               'Facings per category (top-down / isometric) are listed per row in the CSV.' ]
    with open( os.path.join( OUT, 'manifest_summary.md' ), 'w', encoding='utf-8' ) as fh:
        fh.write( '\n'.join( lines ) + '\n' )
    print( '\n'.join( lines ) )


if __name__ == '__main__':
    main()
