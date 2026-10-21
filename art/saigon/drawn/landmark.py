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


@sprite( 'f_sgn_buong_dien_thoai', 32, 32 )
def buong_dien_thoai( c ):
    # varnished wooden phone cabinet, glazed folding door, numbered brass plate
    c.rect( 7, 3, 24, 29, rgb( '#7a4a24' ) )
    c.rect( 7, 3, 24, 5, rgb( '#9a6434' ) )
    c.rect( 10, 8, 21, 26, rgb( '#b8d4dc', 200 ) )                  # glass door
    c.line( 15, 8, 15, 26, rgb( '#7a4a24' ) )                       # folding frame
    c.rect( 13, 5, 18, 6, rgb( '#e8c040' ) )                        # number plate
    c.rect( 17, 14, 19, 18, rgb( '#2a2a2e' ) )                      # the phone inside
    c.outline( 0.42 )
    c.drop_shadow( 2, 2, 70 )


@sprite( 'f_sgn_dong_ho', 32, 32 )
def dong_ho( c ):
    # the tower clock: white enamel face in a stone surround, black iron hands
    c.rect( 4, 4, 27, 27, rgb( '#c8b890' ) )
    c.ellipse( 16, 16, 10, 10, rgb( '#f4f2ea' ) )
    c.ring( 16, 16, 10, 10, rgb( '#2a2a2e' ), 1.2 )
    for dx, dy in ( ( 0, -8 ), ( 8, 0 ), ( 0, 8 ), ( -8, 0 ) ):
        c.px( 16 + dx, 16 + dy, rgb( '#2a2a2e' ) )                  # hour marks
    c.line( 16, 16, 16, 9, rgb( '#1a1a1e' ) )                       # minute hand
    c.line( 16, 16, 21, 18, rgb( '#1a1a1e' ) )                      # hour hand
    c.outline( 0.42 )
