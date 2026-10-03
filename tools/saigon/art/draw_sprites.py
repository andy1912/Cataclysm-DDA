#!/usr/bin/env python3
"""Run the code-drawn sprite programs and write their PNGs.

Every art/saigon/drawn/*.py registers sprites with draw.sprite(); this writes each one to
art/saigon/generated/<program>/<id>.png (plus <id>.json when it has extra tile keys),
then build_sprites.py packs them.  The PNGs are committed so art changes show up in
review.  A hand-drawn PNG of the same id under art/saigon/tiles always wins at pack time.

Run from the repo root:  python3 tools/saigon/art/draw_sprites.py [program ...]
"""
import importlib.util
import json
import os
import shutil
import sys

sys.path.insert( 0, os.path.dirname( __file__ ) )
import draw  # noqa: E402
import pngio  # noqa: E402

ROOT = os.path.join( os.path.dirname( __file__ ), '..', '..', '..' )
DRAWN = os.path.join( ROOT, 'art', 'saigon', 'drawn' )
OUT = os.path.join( ROOT, 'art', 'saigon', 'generated' )


def run( program ):
    name = os.path.basename( program )[:-3]
    draw.REGISTRY.clear()
    spec = importlib.util.spec_from_file_location( 'drawn_' + name, program )
    module = importlib.util.module_from_spec( spec )
    spec.loader.exec_module( module )
    target = os.path.join( OUT, name )
    shutil.rmtree( target, ignore_errors=True )
    os.makedirs( target )
    for sid, width, height, fn, extra in draw.REGISTRY:
        canvas = draw.Canvas( width, height, seed=sum( map( ord, sid ) ) )
        fn( canvas )
        pngio.write( os.path.join( target, sid + '.png' ), canvas )
        if extra:
            with open( os.path.join( target, sid + '.json' ), 'w' ) as f:
                json.dump( extra, f, indent=1 )
    print( '%s: %d sprites -> %s' % ( name, len( draw.REGISTRY ), os.path.relpath( target, ROOT ) ) )
    return len( draw.REGISTRY )


def main():
    wanted = set( sys.argv[1:] )
    total = 0
    for name in sorted( os.listdir( DRAWN ) ):
        if name.endswith( '.py' ) and ( not wanted or name[:-3] in wanted ):
            total += run( os.path.join( DRAWN, name ) )
    print( 'drew %d sprites' % total )


if __name__ == '__main__':
    main()
