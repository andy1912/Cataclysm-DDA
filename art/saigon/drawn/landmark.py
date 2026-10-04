"""Landmark buildings (B8h-2): terracotta tile roofs and the classroom blackboard.
The church's pink stucco is derived from the brick wall (derive_recipes.json)."""
from draw import sprite, rgb, shade


def mai_ngoi( c, clay ):
    # overlapping courses of curved clay tiles, each course shading the one below
    c.rect( 0, 0, 31, 31, shade( clay, 0.7 ) )
    for row, y in enumerate( range( 0, 32, 6 ) ):
        for x in range( -4 + ( row % 2 ) * 4, 32, 8 ):
            c.ellipse( x + 4, y + 3, 4, 3.4, clay, light=shade( clay, 1.25 ), dark=shade( clay, 0.8 ) )
    c.noise( 0, 0, 31, 31, [ rgb( '#5a6a3a' ) ], 0.04 )   # moss in the gutters


@sprite( 't_sgn_mai_ngoi', 32, 32,
         fg=[ { 'weight': 3, 'sprite': '@t_sgn_mai_ngoi' }, { 'weight': 1, 'sprite': '@t_sgn_mai_ngoi__old' } ] )
def mai_ngoi_red( c ):
    mai_ngoi( c, rgb( '#b8502e' ) )


@sprite( 't_sgn_mai_ngoi__old', 32, 32 )
def mai_ngoi_old( c ):
    mai_ngoi( c, rgb( '#9a4a32' ) )


@sprite( 'f_sgn_bang_den', 32, 32 )
def bang_den( c ):
    # green-black chalkboard on a wooden frame, a date and a sum in chalk
    c.rect( 2, 6, 29, 22, rgb( '#8a5a32' ) )
    c.rect( 4, 8, 27, 20, rgb( '#2a4a3a' ) )
    c.line( 6, 10, 12, 10, rgb( '#e8ece8' ) )
    c.line( 6, 13, 18, 13, rgb( '#e8ece8' ) )
    c.line( 6, 16, 10, 16, rgb( '#e8ece8' ) )
    c.px( 12, 16, rgb( '#e8ece8' ) )
    c.line( 4, 21, 27, 21, rgb( '#a87a48' ) )             # chalk ledge
    c.px( 20, 20, rgb( '#ffffff' ) )
    c.rect( 4, 23, 5, 28, rgb( '#6a4428' ) )               # legs
    c.rect( 26, 23, 27, 28, rgb( '#6a4428' ) )
    c.outline( 0.42 )
    c.drop_shadow( 2, 2, 70 )
