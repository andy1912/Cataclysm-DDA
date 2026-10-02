#!/usr/bin/env python3
"""Mechanically verify path:line citations in a Saigon design document.

For every `path:N` or `path:N-M` reference (repo-relative paths under src/, tests/,
data/, doc/, tools/, lang/, build-scripts/), check that the file exists and the line
range is in bounds, at HEAD or at the base SHA (citations into src/game.cpp and
src/main.cpp may legitimately refer to either, since the C6 hunks shifted them).
Bare `:N` shorthand inherits the most recent path on the same line.

Usage: tools/saigon/check_citations.py doc/saigon/TDD.md [--base fe6a10c2b1]
Exit status 1 if any citation misses.
"""
import argparse
import re
import subprocess
import sys

PATH_RE = re.compile(
    r'((?:src|tests|data|doc|tools|lang|build-scripts)/[A-Za-z0-9_./+\-]+\.[A-Za-z0-9]+)'
    r'((?::\d+(?:-\d+)?)(?:,\s*:?\d+(?:-\d+)?)*)' )
LINES_RE = re.compile( r'(\d+)(?:-(\d+))?' )


def line_count( rev, path, cache ):
    key = ( rev, path )
    if key not in cache:
        try:
            if rev == 'HEAD':
                with open( path, 'rb' ) as f:
                    cache[key] = f.read().count( b'\n' ) + 1
            else:
                out = subprocess.run( [ 'git', 'show', '%s:%s' % ( rev, path ) ], capture_output=True )
                cache[key] = out.stdout.count( b'\n' ) + 1 if out.returncode == 0 else None
        except OSError:
            cache[key] = None
    return cache[key]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument( 'doc' )
    ap.add_argument( '--base', default='fe6a10c2b1' )
    args = ap.parse_args()
    cache = {}
    total = 0
    misses = []
    with open( args.doc, encoding='utf-8' ) as f:
        for lineno, text in enumerate( f, 1 ):
            for m in PATH_RE.finditer( text ):
                path = m.group( 1 ).rstrip( '.' )
                for rng in LINES_RE.finditer( m.group( 2 ) ):
                    lo = int( rng.group( 1 ) )
                    hi = int( rng.group( 2 ) or lo )
                    total += 1
                    ok = False
                    for rev in ( 'HEAD', args.base ):
                        n = line_count( rev, path, cache )
                        if n is not None and 1 <= lo <= hi <= n:
                            ok = True
                            break
                    if not ok:
                        misses.append( ( lineno, path, lo, hi ) )
    for lineno, path, lo, hi in misses:
        print( '%s:%d: miss %s:%d-%d' % ( args.doc, lineno, path, lo, hi ) )
    print( 'checked %d citations, %d misses' % ( total, len( misses ) ) )
    sys.exit( 1 if misses else 0 )


if __name__ == '__main__':
    main()
