#!/usr/bin/env python3
"""Build the Saigon mod tileset from rendered top-down sprites.

UNTESTED end to end: the upstream composer (tools/gfx_tools/compose.py) needs pyvips,
which is not installed yet.  See doc/saigon/art/PIPELINE.md step 4.

  1. Lay out <render_dir>/topdown/*.png as a compositing tileset in <work>/src:
       tile_info.json, pngs_saigon_32x32/<id>.png + <id>.json ({"id": id, "fg": id})
  2. Run compose.py on it, producing <work>/out/tile_config.json and saigon.png
  3. Wrap tile_config["tiles-new"] in a mod_tileset object with the base tilesets'
     ids in "compatibility", and install sheet + JSON into data/mods/saigon_2000s/gfx/

Usage: tools/saigon/art/build_mod_tileset.py <render_dir> [--compat UltimateCataclysm ...]
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

ROOT = os.path.join( os.path.dirname( __file__ ), '..', '..', '..' )
COMPOSE = os.path.join( ROOT, 'tools', 'gfx_tools', 'compose.py' )
GFX = os.path.join( ROOT, 'data', 'mods', 'saigon_2000s', 'gfx' )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument( 'render_dir' )
    ap.add_argument( '--work', default=os.path.join( ROOT, '..', 'cdda-saigon-logs', 'art_work' ) )
    ap.add_argument( '--compat', nargs='+', default=[ 'UltimateCataclysm' ],
                     help='base tileset ids these sprites match (UNVERIFIED default)' )
    args = ap.parse_args()

    src = os.path.join( args.work, 'src' )
    out = os.path.join( args.work, 'out' )
    sheet_dir = os.path.join( src, 'pngs_saigon_32x32' )
    shutil.rmtree( args.work, ignore_errors=True )
    os.makedirs( sheet_dir )
    os.makedirs( out )
    with open( os.path.join( src, 'tile_info.json' ), 'w' ) as f:
        json.dump( [ { 'width': 32, 'height': 32, 'pixelscale': 1 }, { 'saigon.png': {} } ], f, indent=2 )
    count = 0
    for name in sorted( os.listdir( os.path.join( args.render_dir, 'topdown' ) ) ):
        if not name.endswith( '.png' ):
            continue
        sid = name[:-4]
        shutil.copy( os.path.join( args.render_dir, 'topdown', name ), os.path.join( sheet_dir, name ) )
        with open( os.path.join( sheet_dir, sid + '.json' ), 'w' ) as f:
            json.dump( { 'id': sid, 'fg': sid }, f )
        count += 1
    if count == 0:
        sys.exit( 'no top-down sprites in %s' % args.render_dir )

    subprocess.run( [ sys.executable, COMPOSE, src, out ], check=True )
    with open( os.path.join( out, 'tile_config.json' ) ) as f:
        config = json.load( f )
    mod_tileset = [ { 'type': 'mod_tileset', 'compatibility': args.compat, 'tiles-new': config['tiles-new'] } ]
    os.makedirs( GFX, exist_ok=True )
    for entry in config['tiles-new']:
        shutil.copy( os.path.join( out, entry['file'] ), os.path.join( GFX, entry['file'] ) )
    with open( os.path.join( GFX, 'mod_tileset.json' ), 'w' ) as f:
        json.dump( mod_tileset, f, indent=2 )
    print( 'installed %d sprites into %s' % ( count, GFX ) )


if __name__ == '__main__':
    main()
