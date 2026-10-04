"""Wet-season floodwater (G30): flooded road, sidewalk and alley, plus rubber flood boots.

Flood terrain must read as the street *under* shallow brown water: the pattern of what
is underneath shows faintly through, and three weighted variants (calm, rain rings,
floating rubbish) keep a flooded street from tiling visibly.  Edges are seamless so
neighbouring flooded tiles join into one sheet of water.
"""
from draw import sprite, rgb, shade

WATER = rgb( '#7a6a48' )


def water( c, under, variant ):
    """under( c ) draws the submerged street; the water is a translucent wash over it."""
    under( c )
    c.rect( 0, 0, 31, 31, rgb( '#7a6a48', 170 ) )                   # muddy water
    c.noise( 0, 0, 31, 31, [ shade( WATER, 1.12 ), shade( WATER, 0.92 ) ], 0.25 )
    for _ in range( 3 ):                                             # glints on the surface
        x, y = c.rand.randint( 2, 28 ), c.rand.randint( 2, 28 )
        c.line( x, y, x + 3, y, rgb( '#b8a880' ) )
    if variant == 1:                                                 # rain rings
        for _ in range( 5 ):
            x, y = c.rand.uniform( 4, 28 ), c.rand.uniform( 4, 28 )
            c.ring( x, y, 3.2, 1.8, rgb( '#d8ccaa', 200 ), 0.8 )
            c.px( x, y, rgb( '#d8ccaa' ) )
    if variant == 2:                                                 # floating rubbish
        c.rect( 8, 10, 12, 12, rgb( '#e8e8e0' ) )                    # a styrofoam scrap
        c.ellipse( 21, 20, 2.4, 1.6, rgb( '#d83a5a' ) )              # a plastic bag
        c.line( 16, 6, 19, 8, rgb( '#4a6a2a' ) )                     # a leaf


def under_road( c ):
    c.rect( 0, 0, 31, 31, rgb( '#4a4a4c' ) )
    c.noise( 0, 0, 31, 31, [ rgb( '#5a5a5c' ), rgb( '#3a3a3c' ) ], 0.4 )


def under_sidewalk( c ):
    c.rect( 0, 0, 31, 31, rgb( '#a89a88' ) )
    for k in range( 0, 32, 8 ):
        c.line( k, 0, k, 31, rgb( '#8a7e6e' ) )
        c.line( 0, k, 31, k, rgb( '#8a7e6e' ) )


def under_alley( c ):
    c.rect( 0, 0, 31, 31, rgb( '#9c988e' ) )
    c.line( 14, 0, 16, 31, rgb( '#6a665e' ) )                        # the centre drain line


def flood_set( sid, under ):
    @sprite( sid, 32, 32, fg=[ { 'weight': 3, 'sprite': '@' + sid }, { 'weight': 3, 'sprite': '@%s__rain' % sid },
                               { 'weight': 1, 'sprite': '@%s__rubbish' % sid } ] )
    def calm( c ):
        water( c, under, 0 )

    @sprite( sid + '__rain', 32, 32 )
    def rain( c ):
        water( c, under, 1 )

    @sprite( sid + '__rubbish', 32, 32 )
    def rubbish( c ):
        water( c, under, 2 )


flood_set( 't_sgn_ngap_duong', under_road )
flood_set( 't_sgn_ngap_le', under_sidewalk )
flood_set( 't_sgn_ngap_hem', under_alley )


@sprite( 'sgn_ung_cao_su', 20, 20 )
def ung_cao_su( c ):
    # one tall black rubber boot in profile, toe to the right, a second one behind it
    for ox, tone in ( ( 2, rgb( '#1e1e22' ) ), ( 0, rgb( '#2e2e34' ) ) ):
        c.polygon( [ ( 6 + ox, 3 ), ( 11 + ox, 3 ), ( 11 + ox, 13 ), ( 16 + ox, 14 ), ( 16 + ox, 17 ), ( 6 + ox, 17 ) ], tone )
    c.line( 6, 3, 11, 3, rgb( '#6a6a72' ) )                            # rim
    c.line( 7, 5, 7, 15, rgb( '#5a5a62' ) )                            # shine down the shaft
    c.line( 6, 17, 16, 17, rgb( '#8a6a3a' ) )                          # tan sole
    c.outline( 0.45 )
    c.drop_shadow( 1, 1, 90 )
