#!/usr/bin/env python3
"""Write pregenerated overmap files (overmap_<x>_<y>.omap.gz) for the real-map Saigon.

Format, as read by overmap::unserialize_omap (src/savegame.cpp): a JSON array with one object
per z level, each {"type": "overmap", "om_pos": [x, y], "z": z, "final": true,
"layers": [[oter_id, run_length], ...]} covering 180 x 180 tiles in row-major order
(x fastest).  "final": true (Saigon fork) tells overmap::generate() to keep this layout and
skip its procedural steps.  dda's own files (the MA mod) have one layer and no "final".
"""
import gzip
import json
import os

OMAPX = OMAPY = 180


class Overmap:
    """A sparse 180 x 180 x z grid of oter ids with a default per z level."""

    def __init__( self, x, y ):
        self.pos = ( x, y )
        self.cells = {}                                   # ( x, y, z ) -> oter id

    def set( self, x, y, z, oter ):
        assert 0 <= x < OMAPX and 0 <= y < OMAPY, ( x, y )
        self.cells[( x, y, z )] = oter

    def get( self, x, y, z, default ):
        return self.cells.get( ( x, y, z ), default )

    def layer( self, z, default ):
        runs = []
        for y in range( OMAPY ):
            for x in range( OMAPX ):
                t = self.get( x, y, z, default )
                if runs and runs[-1][0] == t:
                    runs[-1][1] += 1
                else:
                    runs.append( [ t, 1 ] )
        return runs

    def write( self, folder, ground='field', above='open_air', below='solid_earth' ):
        zs = sorted( { z for ( _, _, z ) in self.cells } | { 0 } )
        objs = []
        for z in zs:
            default = ground if z == 0 else ( above if z > 0 else below )
            objs.append( { 'type': 'overmap', 'om_pos': list( self.pos ), 'z': z, 'final': True,
                           'layers': self.layer( z, default ) } )
        os.makedirs( folder, exist_ok=True )
        path = os.path.join( folder, 'overmap_%d_%d.omap.gz' % self.pos )
        with gzip.open( path, 'wt', encoding='utf-8' ) as f:
            json.dump( objs, f, separators=( ',', ':' ) )
        return path
