#!/usr/bin/env python3
"""Check the written real-map overmap files for what makes the map unplayable on the ground
(found in the 2026-10-06 review: the player could not get anywhere):

  bridges   every bridge run is straight, at least 2 tiles long (the game only puts ramps on
            the end tiles of such runs) and lands on a road at both ends, along its axis
  hẻm       every hẻm network has a way in: a block touching a road or a canal (a hẻm block
            opens its alley mouths only towards those and other hẻm blocks)

  python3 tools/saigon/realmap/check_realmap.py [FOLDER]      (default: the mod's realmap_2009)

Exits 1 and lists the first problems when anything fails.
"""
import glob
import gzip
import json
import os
import sys

HERE = os.path.dirname( os.path.abspath( __file__ ) )
OM = 180


def load( folder ):
    tiles = {}
    for f in glob.glob( os.path.join( folder, 'overmap_*.omap.gz' ) ):
        for o in json.load( gzip.open( f, 'rt' ) ):
            if o['z'] != 0:
                continue
            ox, oy = o['om_pos']
            i = 0
            for t, n in o['layers']:
                for _ in range( n ):
                    tiles[( ox * OM + i % OM, oy * OM + i // OM )] = t
                    i += 1
    return tiles


def check_bridges( tiles ):
    problems, runs = [], 0
    seen = set()
    for p, t in tiles.items():
        if not t.startswith( 'bridge_' ) or p in seen:
            continue
        d = ( 0, 1 ) if t == 'bridge_north' else ( 1, 0 )
        a = p
        while tiles.get( ( a[0] - d[0], a[1] - d[1] ) ) == t:
            a = ( a[0] - d[0], a[1] - d[1] )
        run = [ a ]
        while tiles.get( ( run[-1][0] + d[0], run[-1][1] + d[1] ) ) == t:
            run.append( ( run[-1][0] + d[0], run[-1][1] + d[1] ) )
        seen.update( run )
        runs += 1
        before = tiles.get( ( run[0][0] - d[0], run[0][1] - d[1] ), 'edge' )
        after = tiles.get( ( run[-1][0] + d[0], run[-1][1] + d[1] ), 'edge' )
        if len( run ) < 2:
            problems.append( 'one-tile bridge at %s (no ramps)' % ( run[0], ) )
        for end, beyond in ( ( run[0], before ), ( run[-1], after ) ):
            if not beyond.startswith( 'road' ) and beyond != 'edge':
                problems.append( 'bridge at %s ends against %s' % ( end, beyond ) )
    return runs, problems


def check_hem( tiles ):
    hem = lambda t: t.startswith( 'sgn_hem' )
    way_in = lambda t: t.startswith( 'road' ) or t.startswith( 'sgn_kenh' )
    seen, problems, nets = set(), [], 0
    for p, t in tiles.items():
        if not hem( t ) or p in seen:
            continue
        stack, part, ok = [ p ], [], False
        seen.add( p )
        while stack:
            c = stack.pop()
            part.append( c )
            for dx, dy in ( ( 1, 0 ), ( -1, 0 ), ( 0, 1 ), ( 0, -1 ) ):
                q = ( c[0] + dx, c[1] + dy )
                tq = tiles.get( q )
                if tq is None:
                    continue
                ok = ok or way_in( tq )
                if hem( tq ) and q not in seen:
                    seen.add( q )
                    stack.append( q )
        nets += 1
        if not ok:
            problems.append( 'hẻm network of %d tiles at %s has no way in' % ( len( part ), part[0] ) )
    return nets, problems


def main():
    folder = sys.argv[1] if len( sys.argv ) > 1 else os.path.join( HERE, '..', '..', '..', 'data', 'mods',
                                                                    'saigon_2000s', 'realmap_2009' )
    tiles = load( folder )
    runs, bp = check_bridges( tiles )
    nets, hp = check_hem( tiles )
    print( 'bridges: %d runs, %d problems; hẻm: %d networks, %d without a way in' % ( runs, len( bp ), nets, len( hp ) ) )
    for line in ( bp + hp )[:20]:
        print( '  ' + line )
    sys.exit( 1 if bp or hp else 0 )


if __name__ == '__main__':
    main()
