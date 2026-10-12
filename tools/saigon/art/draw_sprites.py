#!/usr/bin/env python3
"""Run the code-drawn sprite programs and write their PNGs.

Every art/saigon/drawn/*.py registers sprites with draw.sprite(); this writes each one to
art/saigon/generated/<program>/<id>.png (plus <id>.json when it has extra tile keys),
then build_sprites.py packs them.  The PNGs are committed so art changes show up in
review.  A hand-drawn PNG of the same id under art/saigon/tiles always wins at pack time.

20x20 item icons are auto-fitted to the UltimateCataclysm size budget (review R5: the
original icons measure about 11x9 px, median): each is drawn once to measure it, then
redrawn through a scaling transform so its bounding box, outline and shadow included,
fits FIT_BOX, centred like the originals.  Pass fit=None to @sprite to opt out, or
fit=( w, h ) for another box.

overmap=True sends a sprite to art/saigon/overmap16/<program>/ instead: a 16x16 overmap
icon (oter type id) that build_sprites.py packs for Larwick Overmap.

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
OUT_OVERMAP = os.path.join( ROOT, 'art', 'saigon', 'overmap16' )
FIT_BOX = ( 13, 11 )        # w, h incl. 1 px outline + 1 px shadow; UltimateCataclysm median is 11x9
FIT_CENTRE = ( 10.0, 10.0 )  # where the originals sit in the 20x20 cell


def bbox( img ):
    xs = [ x for y in range( img.height ) for x in range( img.width ) if img.get( x, y )[3] > 0 ]
    ys = [ y for y in range( img.height ) for x in range( img.width ) if img.get( x, y )[3] > 0 ]
    return ( min( xs ), min( ys ), max( xs ), max( ys ) ) if xs else None


def render( sid, width, height, fn, fit ):
    seed = sum( map( ord, sid ) )
    canvas = draw.Canvas( width, height, seed=seed )
    fn( canvas )
    box = bbox( canvas ) if fit else None
    if box is None:
        return canvas
    x0, y0, x1, y1 = box
    w, h = x1 - x0 + 1, y1 - y0 + 1
    # outline + shadow stay ~3 px whatever the scale, so fit the body, not the border
    scale = min( 1.0, ( fit[0] - 3 ) / max( 1, w - 3 ), ( fit[1] - 3 ) / max( 1, h - 3 ) )
    centre = ( ( x0 + x1 + 1 ) / 2, ( y0 + y1 + 1 ) / 2 )
    if scale >= 1.0 and abs( centre[0] - FIT_CENTRE[0] ) < 1.5 and abs( centre[1] - FIT_CENTRE[1] ) < 2.5:
        return canvas
    canvas = draw.Canvas( width, height, seed=seed )
    canvas.set_transform( scale, centre, FIT_CENTRE )
    fn( canvas )
    return canvas


def run( program ):
    name = os.path.basename( program )[:-3]
    draw.REGISTRY.clear()
    spec = importlib.util.spec_from_file_location( 'drawn_' + name, program )
    module = importlib.util.module_from_spec( spec )
    spec.loader.exec_module( module )
    targets = { False: os.path.join( OUT, name ), True: os.path.join( OUT_OVERMAP, name ) }
    for target in targets.values():
        shutil.rmtree( target, ignore_errors=True )
    used = set()
    for sid, width, height, fn, extra in draw.REGISTRY:
        extra = dict( extra )
        fit = extra.pop( 'fit', FIT_BOX if ( width, height ) == ( 20, 20 ) else None )
        target = targets[bool( extra.pop( 'overmap', False ) )]
        if target not in used:
            os.makedirs( target )
            used.add( target )
        canvas = render( sid, width, height, fn, fit )
        pngio.write( os.path.join( target, sid + '.png' ), canvas )
        if extra:
            with open( os.path.join( target, sid + '.json' ), 'w' ) as f:
                json.dump( extra, f, indent=1 )
    print( '%s: %d sprites -> %s' % ( name, len( draw.REGISTRY ),
                                      ', '.join( os.path.relpath( t, ROOT ) for t in sorted( used ) ) ) )
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
