#!/usr/bin/env python3
"""Apply include-what-you-use suggestions from a CI log to the fork's files.

Usage: tools/saigon/apply_iwyu.py <iwyu-log> [file ...]

The log is the text of the CI "iwyu" job with the runner's checkout prefix stripped, so paths read
"tests/saigon_x_test.cpp".  For each "<file> should add these lines:" / "should remove these lines:"
block it removes the listed lines and inserts the added includes into the file's include list:
<...> headers after the last angle-bracket include, "..." headers in sorted position among the
quoted ones.  Forward declarations are skipped (none were asked for).  Only files given on the
command line are changed (all files in the log if none are given).  Run astyle afterwards.
"""
import re
import sys


def parse( log ):
    out = {}
    cur = None
    mode = None
    for line in log.splitlines():
        m = re.match( r'^(\S+) should (add|remove) these lines:$', line )
        if m:
            cur = out.setdefault( m.group( 1 ), { 'add': [], 'remove': [] } )
            mode = m.group( 2 )
            continue
        if line.startswith( 'The full include-list' ) or line.startswith( '(' ) or not line.strip():
            mode = None
            continue
        if cur is None or mode is None:
            continue
        if mode == 'add':
            m = re.match( r'^(#include [<"][^>"]+[>"])', line )
            if m:
                cur['add'].append( m.group( 1 ) )
        else:
            m = re.match( r'^- (#include [<"][^>"]+[>"])\s+// lines (\d+)-(\d+)', line )
            if m:
                cur['remove'].append( ( m.group( 1 ), int( m.group( 2 ) ), int( m.group( 3 ) ) ) )
    return out


def apply( path, todo ):
    lines = open( path, encoding='utf-8' ).read().split( '\n' )
    drop = set()
    # match by text: the log's line numbers are for the pushed file, which may have moved since
    for inc, a, b in todo['remove']:
        hits = [ i for i, l in enumerate( lines ) if l.strip().split( '//' )[0].strip() == inc ]
        if not hits:
            sys.exit( '%s: %s not found' % ( path, inc ) )
        drop.add( hits[0] )
    lines = [ l for i, l in enumerate( lines ) if i not in drop ]
    present = { l.strip() for l in lines if l.startswith( '#include' ) }
    for inc in todo['add']:
        if inc in present:
            continue
        angle = inc.startswith( '#include <' )
        idx = [ i for i, l in enumerate( lines )
                if l.startswith( '#include <' if angle else '#include "' ) ]
        if not idx:
            # first <...> include: before every include; a lone "...": after the last include
            allinc = [ i for i, l in enumerate( lines ) if l.startswith( '#include' ) ]
            lines.insert( allinc[0] if angle else allinc[-1] + 1, inc )
            present.add( inc )
            continue
        pos = idx[-1] + 1
        for i in idx:
            if lines[i] > inc:
                pos = i
                break
        lines.insert( pos, inc )
        present.add( inc )
    open( path, 'w', encoding='utf-8' ).write( '\n'.join( lines ) )
    print( '%s: +%d -%d' % ( path, len( todo['add'] ), len( drop ) ) )


def main():
    todo = parse( open( sys.argv[1], encoding='utf-8' ).read() )
    only = set( sys.argv[2:] )
    for path, t in sorted( todo.items() ):
        if only and path not in only:
            continue
        apply( path, t )


if __name__ == '__main__':
    main()
