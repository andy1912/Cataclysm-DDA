"""Blender script: render one Saigon asset to top-down and isometric sprites.

UNTESTED: Blender is not installed on the development machine yet.  Written against
the Blender 4.x Python API (bpy); see doc/saigon/art/PIPELINE.md and STYLE_GUIDE.md §1.

Usage:
  blender -b assets/<id>.blend -P tools/saigon/art/render_sprites.py -- --id <id> --out art_build
Expects a collection named exactly <id> containing the asset, modelled at 1 unit = 1 tile
with its pivot at the floor centre.  Writes:
  <out>/topdown/<id>.png                         32x32 colour (near-albedo, soft AO)
  <out>/iso/<id>_f{0..3}.png                     64 px wide iso colour, 4 facings
  <out>/iso/<id>_f{0..3}_{normal,height,emissive}.png   passes for per-pixel lighting (R4)
"""
import argparse
import math
import os
import sys

import bpy  # noqa: E0401  (only available inside Blender)

TOPDOWN_PX = 32
ISO_W_PX = 64
ISO_ELEVATION_DEG = 30.0   # 2:1 dimetric
ISO_AZIMUTH_DEG = 45.0


def parse_args():
    argv = sys.argv[sys.argv.index( '--' ) + 1:] if '--' in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument( '--id', required=True )
    ap.add_argument( '--out', required=True )
    ap.add_argument( '--tiles-high', type=float, default=1.0,
                     help='iso sprite height in tiles above the floor diamond (tall objects > 1)' )
    return ap.parse_args( argv )


def setup_scene():
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE_NEXT' if hasattr( bpy.types, 'SceneEEVEE' ) else 'BLENDER_EEVEE'
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    view_layer = scene.view_layers[0]
    view_layer.use_pass_normal = True
    view_layer.use_pass_z = True
    view_layer.use_pass_emit = True
    # neutral, shadowless key: sprites stay near-albedo, dynamic light comes later (R4)
    for obj in [ o for o in scene.objects if o.type == 'LIGHT' ]:
        bpy.data.objects.remove( obj, do_unlink=True )
    world = scene.world or bpy.data.worlds.new( 'World' )
    scene.world = world
    world.use_nodes = True
    world.node_tree.nodes['Background'].inputs[1].default_value = 1.0
    return scene


def make_camera( scene, name, location, rotation_euler, ortho_scale ):
    cam_data = bpy.data.cameras.new( name )
    cam_data.type = 'ORTHO'
    cam_data.ortho_scale = ortho_scale
    cam = bpy.data.objects.new( name, cam_data )
    scene.collection.objects.link( cam )
    cam.location = location
    cam.rotation_euler = rotation_euler
    scene.camera = cam
    return cam


def render_to( scene, path, width, height ):
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.filepath = path
    os.makedirs( os.path.dirname( path ), exist_ok=True )
    bpy.ops.render.render( write_still=True )


def render_passes( scene, base_path, width, height ):
    """Render colour plus normal / height / emissive passes via the compositor."""
    scene.use_nodes = True
    tree = scene.node_tree
    tree.nodes.clear()
    rl = tree.nodes.new( 'CompositorNodeRLayers' )
    outputs = {}
    for name in ( 'Normal', 'Depth', 'Emit' ):
        if name in rl.outputs:
            out = tree.nodes.new( 'CompositorNodeOutputFile' )
            out.base_path = os.path.dirname( base_path )
            out.file_slots[0].path = os.path.basename( base_path ) + '_' + {
                'Normal': 'normal', 'Depth': 'height', 'Emit': 'emissive' }[name] + '_'
            if name == 'Depth':
                norm = tree.nodes.new( 'CompositorNodeNormalize' )
                tree.links.new( rl.outputs[name], norm.inputs[0] )
                tree.links.new( norm.outputs[0], out.inputs[0] )
            else:
                tree.links.new( rl.outputs[name], out.inputs[0] )
            outputs[name] = out
    comp = tree.nodes.new( 'CompositorNodeComposite' )
    tree.links.new( rl.outputs['Image'], comp.inputs['Image'] )
    render_to( scene, base_path + '.png', width, height )


def main():
    args = parse_args()
    scene = setup_scene()
    if args.id not in bpy.data.collections:
        raise SystemExit( 'collection %s not found in the .blend' % args.id )
    asset = bpy.data.collections[args.id]
    pivot = bpy.data.objects.new( 'sgn_pivot', None )
    scene.collection.objects.link( pivot )
    for obj in asset.all_objects:
        if obj.parent is None:
            obj.parent = pivot

    # top-down: one tile seen from straight above
    make_camera( scene, 'cam_top', ( 0, 0, 10 ), ( 0, 0, 0 ), 1.0 )
    render_to( scene, os.path.join( args.out, 'topdown', args.id + '.png' ), TOPDOWN_PX, TOPDOWN_PX )

    # isometric: 2:1 dimetric, four facings by rotating the asset under a fixed camera
    elev = math.radians( ISO_ELEVATION_DEG )
    azim = math.radians( ISO_AZIMUTH_DEG )
    dist = 20.0
    loc = ( dist * math.cos( elev ) * math.sin( azim ), -dist * math.cos( elev ) * math.cos( azim ),
            dist * math.sin( elev ) )
    # a 1x1 tile's diamond is sqrt(2) units wide on screen
    make_camera( scene, 'cam_iso', loc, ( math.pi / 2 - elev, 0, azim ), math.sqrt( 2 ) )
    height_px = int( ISO_W_PX / 2 * ( 1 + args.tiles_high ) )
    for facing in range( 4 ):
        pivot.rotation_euler = ( 0, 0, math.radians( 90 * facing ) )
        render_passes( scene, os.path.join( args.out, 'iso', '%s_f%d' % ( args.id, facing ) ), ISO_W_PX,
                       height_px )


main()
