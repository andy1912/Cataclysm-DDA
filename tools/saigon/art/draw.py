"""Small pixel-art drawing kit for code-drawn Saigon sprites (no dependencies).

Sprite programs in art/saigon/drawn/*.py use it like this:

    from draw import Canvas, sprite, rgb
    @sprite( 'f_sgn_toilet_squat', 32, 32 )
    def squat_toilet( c ):
        c.ellipse( 16, 16, 9, 12, rgb( '#e8ecee' ) )
        ...
        c.outline()

Conventions follow STYLE_GUIDE.md and UltimateCataclysm: light from the top left,
soft dark outlines (a darkened copy of the neighbouring colour, not pure black),
3-4 tones per material, transparent background.  Everything is deterministic:
`Canvas.noise` uses a seeded generator so re-running gives identical PNGs.
"""
import random

import pngio

REGISTRY = []  # ( id, width, height, function, extra tile keys )


def sprite( sid, width, height, **extra ):
    """Register a function that draws sprite `sid` on a width x height canvas."""
    def wrap( fn ):
        REGISTRY.append( ( sid, width, height, fn, extra ) )
        return fn
    return wrap


def rgb( value, alpha=255 ):
    value = value.lstrip( '#' )
    return ( int( value[0:2], 16 ), int( value[2:4], 16 ), int( value[4:6], 16 ), alpha )


def shade( colour, k ):
    """k < 1 darkens, k > 1 lightens towards white."""
    r, g, b, a = colour
    if k <= 1:
        return ( int( r * k ), int( g * k ), int( b * k ), a )
    t = min( 1.0, k - 1 )
    return ( int( r + ( 255 - r ) * t ), int( g + ( 255 - g ) * t ), int( b + ( 255 - b ) * t ), a )


def mix( c1, c2, t ):
    return tuple( int( a + ( b - a ) * t ) for a, b in zip( c1, c2 ) )


class Canvas( pngio.Image ):
    """Drawing surface.  Shape calls take "design" coordinates; an optional transform
    (set_transform) maps them onto pixels, so one drawing can be rasterised smaller (the
    auto-fit of item icons) and still come out crisp: shapes are rasterised at the final
    size, 1 px lines stay 1 px, and outline/drop_shadow work on final pixels."""

    def __init__( self, width, height, seed=0 ):
        super().__init__( width, height )
        self.rand = random.Random( seed )
        self.tf = None  # ( scale, from_x, from_y, to_x, to_y )

    def set_transform( self, scale, from_xy, to_xy ):
        self.tf = ( scale, from_xy[0], from_xy[1], to_xy[0], to_xy[1] )

    # --- coordinate mapping ---------------------------------------------------------------
    def _c( self, x, y ):
        """Continuous design point -> continuous pixel point."""
        if self.tf is None:
            return x, y
        s, fx, fy, tx, ty = self.tf
        return tx + ( x - fx ) * s, ty + ( y - fy ) * s

    def _p( self, x, y ):
        """Design pixel (integer cell) -> pixel cell, through its centre."""
        if self.tf is None:
            return int( round( x ) ), int( round( y ) )
        cx, cy = self._c( x + 0.5, y + 0.5 )
        return int( cx // 1 ), int( cy // 1 )

    def _r( self, r ):
        return r if self.tf is None else r * self.tf[0]

    # --- pixel level (no transform) -------------------------------------------------------
    def inside( self, x, y ):
        return 0 <= x < self.width and 0 <= y < self.height

    def _px( self, x, y, colour ):
        if self.inside( x, y ) and colour is not None:
            if colour[3] == 255 or self.get( x, y )[3] == 0:
                self.set( x, y, colour )
            else:
                self.set( x, y, mix( self.get( x, y ), colour[:3] + ( 255, ), colour[3] / 255 ) )

    def _opaque( self, x, y ):
        return self.inside( x, y ) and self.get( x, y )[3] > 0

    def _line( self, x0, y0, x1, y1, colour ):
        dx, dy = abs( x1 - x0 ), -abs( y1 - y0 )
        sx, sy = ( 1 if x0 < x1 else -1 ), ( 1 if y0 < y1 else -1 )
        err = dx + dy
        while True:
            self._px( x0, y0, colour )
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def _ellipse( self, cx, cy, rx, ry, colour, light=None, dark=None ):
        for y in range( int( cy - ry ) - 1, int( cy + ry ) + 2 ):
            for x in range( int( cx - rx ) - 1, int( cx + rx ) + 2 ):
                nx, ny = ( x + 0.5 - cx ) / max( rx, 0.5 ), ( y + 0.5 - cy ) / max( ry, 0.5 )
                d = nx * nx + ny * ny
                if d > 1:
                    continue
                c = colour
                if dark is not None and nx + ny > 0.75 and d > 0.35:
                    c = dark
                elif light is not None and nx + ny < -0.75 and d > 0.25:
                    c = light
                self._px( x, y, c )

    # --- design level ---------------------------------------------------------------------
    def px( self, x, y, colour ):
        self._px( *self._p( x, y ), colour )

    def opaque( self, x, y ):
        return self._opaque( *self._p( x, y ) )

    def rect( self, x0, y0, x1, y1, colour ):
        """Filled rectangle, inclusive corners."""
        ( a, b ), ( c, d ) = self._p( x0, y0 ), self._p( x1, y1 )
        for y in range( min( b, d ), max( b, d ) + 1 ):
            for x in range( min( a, c ), max( a, c ) + 1 ):
                self._px( x, y, colour )

    def erase( self, x0, y0, x1, y1 ):
        """Make a rectangle transparent again, inclusive corners."""
        ( a, b ), ( c, d ) = self._p( x0, y0 ), self._p( x1, y1 )
        for y in range( max( 0, b ), min( self.height - 1, d ) + 1 ):
            for x in range( max( 0, a ), min( self.width - 1, c ) + 1 ):
                self.set( x, y, ( 0, 0, 0, 0 ) )

    def frame( self, x0, y0, x1, y1, colour ):
        self.line( x0, y0, x1, y0, colour )
        self.line( x0, y1, x1, y1, colour )
        self.line( x0, y0, x0, y1, colour )
        self.line( x1, y0, x1, y1, colour )

    def line( self, x0, y0, x1, y1, colour ):
        self._line( *self._p( x0, y0 ), *self._p( x1, y1 ), colour )

    def ellipse( self, cx, cy, rx, ry, colour, light=None, dark=None ):
        """Filled ellipse; optional top-left highlight and bottom-right shadow tones."""
        ccx, ccy = self._c( cx, cy )
        self._ellipse( ccx, ccy, self._r( rx ), self._r( ry ), colour, light, dark )

    def capsule( self, x0, y0, x1, y1, r0, colour, r1=None ):
        """Thick stroke with round ends, radius tapering from r0 to r1 (baguettes, stems, blades)."""
        r1 = r0 if r1 is None else r1
        steps = max( 1, int( max( abs( x1 - x0 ), abs( y1 - y0 ) ) * 2 ) )
        for i in range( steps + 1 ):
            t = i / steps
            r = r0 + ( r1 - r0 ) * t
            self.ellipse( x0 + ( x1 - x0 ) * t, y0 + ( y1 - y0 ) * t, r, r, colour )

    def ring( self, cx, cy, rx, ry, colour, width=1.0 ):
        cx, cy = self._c( cx, cy )
        rx, ry = self._r( rx ), self._r( ry )
        for y in range( int( cy - ry ) - 1, int( cy + ry ) + 2 ):
            for x in range( int( cx - rx ) - 1, int( cx + rx ) + 2 ):
                nx, ny = ( x + 0.5 - cx ) / max( rx, 0.5 ), ( y + 0.5 - cy ) / max( ry, 0.5 )
                d = ( nx * nx + ny * ny ) ** 0.5
                if 1 - width / max( 1.0, min( rx, ry ) ) <= d <= 1:
                    self._px( x, y, colour )

    def polygon( self, points, colour ):
        """Filled polygon (even-odd rule, pixel centres)."""
        points = [ self._c( x, y ) for x, y in points ]
        ys = [ p[1] for p in points ]
        for y in range( int( min( ys ) ), int( max( ys ) ) + 1 ):
            yc = y + 0.5
            xs = []
            for ( x0, y0 ), ( x1, y1 ) in zip( points, points[1:] + points[:1] ):
                if ( y0 <= yc < y1 ) or ( y1 <= yc < y0 ):
                    xs.append( x0 + ( yc - y0 ) * ( x1 - x0 ) / ( y1 - y0 ) )
            xs.sort()
            for a, b in zip( xs[::2], xs[1::2] ):
                for x in range( int( round( a ) ), int( round( b ) ) ):
                    self._px( x, y, colour )

    def noise( self, x0, y0, x1, y1, colours, density=0.3, only_opaque=True ):
        """Sprinkle pixels from `colours` over a rectangle (texture, grain, dirt)."""
        ( a, b ), ( c, d ) = self._p( x0, y0 ), self._p( x1, y1 )
        for y in range( b, d + 1 ):
            for x in range( a, c + 1 ):
                if self.rand.random() < density and ( not only_opaque or self._opaque( x, y ) ):
                    self._px( x, y, self.rand.choice( colours ) )

    def outline( self, k=0.45, diagonal=False ):
        """Soft outline: transparent pixels touching the sprite get a darkened neighbour colour."""
        add = []
        steps = [ ( 1, 0 ), ( -1, 0 ), ( 0, 1 ), ( 0, -1 ) ]
        if diagonal:
            steps += [ ( 1, 1 ), ( -1, -1 ), ( 1, -1 ), ( -1, 1 ) ]
        for y in range( self.height ):
            for x in range( self.width ):
                if self._opaque( x, y ):
                    continue
                near = [ self.get( x + dx, y + dy ) for dx, dy in steps if self._opaque( x + dx, y + dy ) ]
                if near:
                    r = sum( c[0] for c in near ) // len( near )
                    g = sum( c[1] for c in near ) // len( near )
                    b = sum( c[2] for c in near ) // len( near )
                    add.append( ( x, y, ( int( r * k ), int( g * k ), int( b * k ), 255 ) ) )
        for x, y, c in add:
            self.set( x, y, c )

    def drop_shadow( self, dx=2, dy=2, alpha=70 ):
        """Soft shadow to the bottom right under the sprite (UltimateCataclysm style)."""
        mask = [ ( x, y ) for y in range( self.height ) for x in range( self.width ) if self._opaque( x, y ) ]
        for x, y in mask:
            sx, sy = x + dx, y + dy
            if self.inside( sx, sy ) and not self._opaque( sx, sy ):
                self.set( sx, sy, ( 0, 0, 0, alpha ) )

    def flip_h( self ):
        out = Canvas( self.width, self.height )
        for y in range( self.height ):
            for x in range( self.width ):
                out.set( self.width - 1 - x, y, self.get( x, y ) )
        self.pixels = out.pixels


_BASE = {}


def base_sprite( tile_id, key='fg', tileset='gfx/UltimateCataclysm' ):
    """First `key` sprite of a base-tileset tile, as a Canvas (e.g. a grass ground tile to put
    under a code-drawn tree).  The copy is original tileset art: name it in the program's
    docstring so provenance stays visible."""
    import os
    from derive_sprites import BaseTileset, ROOT
    if tileset not in _BASE:
        _BASE[tileset] = BaseTileset( os.path.join( ROOT, tileset ) )
    base = _BASE[tileset]
    value = base.tiles[tile_id][key]
    while isinstance( value, list ):
        value = value[0]
    if isinstance( value, dict ):
        value = value['sprite']
        while isinstance( value, list ):
            value = value[0]
    img, _ = base.sprite( value )
    out = Canvas( img.width, img.height )
    out.pixels = bytearray( img.pixels )
    return out


def foliage( c, clumps, dark, mid, light, radius=( 3, 5 ), light_from=( -1, -1 ) ):
    """Leafy canopy in the UltimateCataclysm manner: every clump gets a dark underside,
    a mid body and a highlight towards the light, drawn back to front."""
    lx, ly = light_from
    rng = c.rand
    sized = [ ( x, y, rng.uniform( *radius ) ) for x, y in clumps ]
    sized.sort( key=lambda t: t[1] )
    for x, y, r in sized:
        c.ellipse( x + 1, y + 1, r + 0.6, r * 0.85 + 0.6, dark )
    for x, y, r in sized:
        c.ellipse( x, y, r, r * 0.85, mid )
        c.ellipse( x + lx * r * 0.35, y + ly * r * 0.35, r * 0.45, r * 0.4, light )
        # a few dark leaf gaps keep it from looking like blobs
        for _ in range( 2 ):
            gx, gy = x + rng.uniform( -r, r ) * 0.7, y + rng.uniform( -r, r ) * 0.6
            if c.opaque( int( gx ), int( gy ) ):
                c.px( gx, gy, dark )


def cast_shadow( c, dx, dy, alpha=60 ):
    """Long soft shadow of the whole sprite (trees throw theirs to the upper right)."""
    mask = [ ( x, y ) for y in range( c.height ) for x in range( c.width ) if c._opaque( x, y ) ]
    for x, y in mask:
        sx, sy = x + dx, y + dy
        if c.inside( sx, sy ) and not c._opaque( sx, sy ):
            c.set( sx, sy, ( 0, 0, 0, alpha ) )
