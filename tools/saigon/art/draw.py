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
    def __init__( self, width, height, seed=0 ):
        super().__init__( width, height )
        self.rand = random.Random( seed )

    def inside( self, x, y ):
        return 0 <= x < self.width and 0 <= y < self.height

    def px( self, x, y, colour ):
        x, y = int( round( x ) ), int( round( y ) )
        if self.inside( x, y ) and colour is not None:
            if colour[3] == 255 or self.get( x, y )[3] == 0:
                self.set( x, y, colour )
            else:
                self.set( x, y, mix( self.get( x, y ), colour[:3] + ( 255, ), colour[3] / 255 ) )

    def opaque( self, x, y ):
        return self.inside( x, y ) and self.get( x, y )[3] > 0

    def rect( self, x0, y0, x1, y1, colour ):
        """Filled rectangle, inclusive corners."""
        for y in range( y0, y1 + 1 ):
            for x in range( x0, x1 + 1 ):
                self.px( x, y, colour )

    def frame( self, x0, y0, x1, y1, colour ):
        self.line( x0, y0, x1, y0, colour )
        self.line( x0, y1, x1, y1, colour )
        self.line( x0, y0, x0, y1, colour )
        self.line( x1, y0, x1, y1, colour )

    def line( self, x0, y0, x1, y1, colour ):
        x0, y0, x1, y1 = int( round( x0 ) ), int( round( y0 ) ), int( round( x1 ) ), int( round( y1 ) )
        dx, dy = abs( x1 - x0 ), -abs( y1 - y0 )
        sx, sy = ( 1 if x0 < x1 else -1 ), ( 1 if y0 < y1 else -1 )
        err = dx + dy
        while True:
            self.px( x0, y0, colour )
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def ellipse( self, cx, cy, rx, ry, colour, light=None, dark=None ):
        """Filled ellipse; optional top-left highlight and bottom-right shadow tones."""
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
                self.px( x, y, c )

    def capsule( self, x0, y0, x1, y1, r0, colour, r1=None ):
        """Thick stroke with round ends, radius tapering from r0 to r1 (baguettes, stems, blades)."""
        r1 = r0 if r1 is None else r1
        steps = max( 1, int( max( abs( x1 - x0 ), abs( y1 - y0 ) ) * 2 ) )
        for i in range( steps + 1 ):
            t = i / steps
            self.ellipse( x0 + ( x1 - x0 ) * t, y0 + ( y1 - y0 ) * t, r0 + ( r1 - r0 ) * t,
                          r0 + ( r1 - r0 ) * t, colour )

    def ring( self, cx, cy, rx, ry, colour, width=1.0 ):
        for y in range( int( cy - ry ) - 1, int( cy + ry ) + 2 ):
            for x in range( int( cx - rx ) - 1, int( cx + rx ) + 2 ):
                nx, ny = ( x + 0.5 - cx ) / rx, ( y + 0.5 - cy ) / ry
                d = ( nx * nx + ny * ny ) ** 0.5
                if 1 - width / min( rx, ry ) <= d <= 1:
                    self.px( x, y, colour )

    def polygon( self, points, colour ):
        """Filled polygon (even-odd rule, pixel centres)."""
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
                    self.px( x, y, colour )

    def noise( self, x0, y0, x1, y1, colours, density=0.3, only_opaque=True ):
        """Sprinkle pixels from `colours` over a rectangle (texture, grain, dirt)."""
        for y in range( y0, y1 + 1 ):
            for x in range( x0, x1 + 1 ):
                if self.rand.random() < density and ( not only_opaque or self.opaque( x, y ) ):
                    self.px( x, y, self.rand.choice( colours ) )

    def outline( self, k=0.45, diagonal=False ):
        """Soft outline: transparent pixels touching the sprite get a darkened neighbour colour."""
        add = []
        steps = [ ( 1, 0 ), ( -1, 0 ), ( 0, 1 ), ( 0, -1 ) ]
        if diagonal:
            steps += [ ( 1, 1 ), ( -1, -1 ), ( 1, -1 ), ( -1, 1 ) ]
        for y in range( self.height ):
            for x in range( self.width ):
                if self.opaque( x, y ):
                    continue
                near = [ self.get( x + dx, y + dy ) for dx, dy in steps if self.opaque( x + dx, y + dy ) ]
                if near:
                    r = sum( c[0] for c in near ) // len( near )
                    g = sum( c[1] for c in near ) // len( near )
                    b = sum( c[2] for c in near ) // len( near )
                    add.append( ( x, y, ( int( r * k ), int( g * k ), int( b * k ), 255 ) ) )
        for x, y, c in add:
            self.set( x, y, c )

    def drop_shadow( self, dx=2, dy=2, alpha=70 ):
        """Soft shadow to the bottom right under the sprite (UltimateCataclysm style)."""
        mask = [ ( x, y ) for y in range( self.height ) for x in range( self.width ) if self.opaque( x, y ) ]
        for x, y in mask:
            sx, sy = x + dx, y + dy
            if self.inside( sx, sy ) and not self.opaque( sx, sy ):
                self.set( sx, sy, ( 0, 0, 0, alpha ) )

    def flip_h( self ):
        out = Canvas( self.width, self.height )
        for y in range( self.height ):
            for x in range( self.width ):
                out.set( self.width - 1 - x, y, self.get( x, y ) )
        self.pixels = out.pixels
