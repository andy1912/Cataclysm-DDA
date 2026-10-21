"""Saigon home fittings that replace American furniture: 32x32, UltimateCataclysm 3/4 view.

UltimateCataclysm furniture shows the top surface in the upper part of the tile and
the front face below it, outlined and with a soft shadow to the bottom right.
These replace the dda ids directly, because a Saigon world uses them in every house:
  f_oven    US range with an oven  -> two-burner gas stove (bếp ga đôi) on a tiled counter
  f_toilet  western toilet         -> squat toilet (bồn cầu xổm) with a bucket and dipper
"""
from draw import sprite, rgb, shade

OUTLINE = 0.4
TILE_WHITE = rgb( '#e6eaec' )
GROUT = rgb( '#b4bcc0' )


def finish( c ):
    c.outline( OUTLINE )
    c.drop_shadow( 2, 2, 70 )


@sprite( 'f_oven', 32, 32 )
def gas_stove( c ):
    # tiled concrete counter: grey top, white-tiled front
    c.rect( 1, 5, 30, 21, rgb( '#b8b4aa' ) )
    c.rect( 1, 5, 30, 5, rgb( '#d4d0c6' ) )
    c.rect( 1, 22, 30, 30, TILE_WHITE )
    for x in range( 1, 31, 5 ):
        c.line( x, 22, x, 30, GROUT )
    c.line( 1, 26, 30, 26, GROUT )
    c.line( 1, 22, 30, 22, shade( TILE_WHITE, 0.8 ) )
    # the stove body: steel top plate on a black enamel case
    c.rect( 4, 7, 27, 19, rgb( '#2c2e32' ) )
    c.rect( 5, 8, 26, 17, rgb( '#9aa2aa' ) )
    c.line( 5, 8, 26, 8, rgb( '#c8d0d6' ) )
    c.rect( 4, 18, 27, 20, rgb( '#202226' ) )
    for cx in ( 11, 21 ):                                     # two burners
        c.ellipse( cx, 12.5, 4.2, 3.6, rgb( '#3a3e44' ) )
        c.ellipse( cx, 12.5, 2.6, 2.2, rgb( '#5a6068' ) )
        c.ellipse( cx, 12.5, 1.3, 1.1, rgb( '#c89a3a' ) )      # brass cap
        for dx, dy in ( ( -4, 0 ), ( 4, 0 ), ( 0, -3 ) ):     # pot supports
            c.px( cx + dx, 12 + dy, rgb( '#121314' ) )
        c.ellipse( cx, 19, 1.2, 1, rgb( '#f08a2c' ) )          # knob
    c.line( 27, 15, 30, 21, rgb( '#d83a2a' ) )                # red gas hose to the cylinder below
    finish( c )


@sprite( 'f_toilet', 32, 32 )
def squat_toilet( c ):
    ceramic = rgb( '#eef2f2' )
    # the squat pan, set into the floor
    c.ellipse( 14, 16, 8, 12, shade( ceramic, 0.82 ) )
    c.ellipse( 14, 15.5, 7.5, 11.5, ceramic )
    c.ellipse( 14, 18, 4.5, 7, rgb( '#c8d2d6' ) )             # bowl
    c.ellipse( 14, 22, 2.4, 2.2, rgb( '#3a4448' ) )           # drain
    c.ellipse( 14, 21.5, 1.4, 1.2, rgb( '#5a7480' ) )         # water
    for side in ( 7, 19 ):                                    # ribbed footrests
        for y in range( 8, 15, 2 ):
            c.line( side, y, side + 3, y, rgb( '#c4ccd0' ) )
    c.line( 9, 5, 19, 5, rgb( '#ffffff' ) )
    # red plastic bucket with a blue dipper (gáo)
    c.ellipse( 26.5, 23, 4.5, 2, rgb( '#b82a2a' ) )
    c.polygon( [ ( 22, 18 ), ( 31, 18 ), ( 30, 24 ), ( 23, 24 ) ], rgb( '#d83a3a' ) )
    c.line( 22, 18, 23, 24, rgb( '#f06060' ) )
    c.ellipse( 26.5, 18, 4.5, 2, rgb( '#e85050' ) )
    c.ellipse( 26.5, 18, 3.5, 1.3, rgb( '#5a8ab0' ) )         # water
    c.ellipse( 25.5, 17.5, 1.6, 1, rgb( '#2f74c0' ) )         # dipper cup
    c.line( 26, 17, 30, 13, rgb( '#2f74c0' ) )                # its handle
    finish( c )
