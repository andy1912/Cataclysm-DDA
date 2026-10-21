"""Household and medicine items (G24): 20x20 icons, auto-fitted to the UltimateCataclysm budget."""
from draw import sprite, rgb

OUTLINE = 0.38


def finish( c ):
    c.outline( OUTLINE )
    c.drop_shadow( 1, 1, 90 )


@sprite( 'sgn_quat_may', 20, 20 )
def quat_may( c ):
    # pedestal fan: round blue grille on a pole and a weighted base
    c.ellipse( 10, 8, 5.5, 5.5, rgb( '#3f7ad0' ) )
    c.ring( 10, 8, 5.5, 5.5, rgb( '#9ac0f0' ), 1 )
    for dx, dy in ( ( -2, -2 ), ( 2, -1 ), ( 0, 2.5 ) ):
        c.ellipse( 10 + dx, 8 + dy, 1.6, 1.6, rgb( '#c8dcf4' ) )   # blades
    c.ellipse( 10, 8, 1, 1, rgb( '#2a2a2e' ) )
    c.rect( 9, 13, 10, 16, rgb( '#d8dcd8' ) )
    c.ellipse( 9.5, 17, 4, 1.4, rgb( '#2f5aa8' ) )
    finish( c )


@sprite( 'sgn_den_dau', 20, 20 )
def den_dau( c ):
    # kerosene lamp: glass chimney over a brass font
    c.ellipse( 10, 14, 4, 2.5, rgb( '#c89a3a' ), light=rgb( '#f2c860' ) )
    c.polygon( [ ( 8, 13 ), ( 12, 13 ), ( 11.5, 5 ), ( 8.5, 5 ) ], rgb( '#e8f2f4', 200 ) )
    c.ellipse( 10, 10, 1, 2, rgb( '#f2a02a' ) )                   # flame
    c.rect( 8, 4, 12, 4, rgb( '#d8e8ec' ) )
    finish( c )


@sprite( 'sgn_nen', 20, 20 )
def nen( c ):
    # thick red altar candle with gold characters
    c.rect( 8, 7, 12, 16, rgb( '#c8262a' ) )
    c.line( 8, 7, 8, 16, rgb( '#e85050' ) )
    for y in ( 9, 12 ):
        c.rect( 9, y, 11, y + 1, rgb( '#f2c232' ) )
    c.line( 10, 5, 10, 6, rgb( '#2a2a2a' ) )
    finish( c )


@sprite( 'sgn_dien_thoai', 20, 20 )
def dien_thoai( c ):
    # 2G brick phone: grey-blue body, green monochrome screen, keypad
    c.rect( 7, 3, 12, 16, rgb( '#3a4a5a' ) )
    c.rect( 8, 5, 11, 8, rgb( '#9ac87a' ) )
    for y in range( 10, 16, 2 ):
        for x in ( 8, 10 ):
            c.px( x, y, rgb( '#c8d0d8' ) )
            c.px( x + 1, y, rgb( '#c8d0d8' ) )
    c.line( 11, 2, 11, 3, rgb( '#2a2a2e' ) )                       # stub antenna
    finish( c )


@sprite( 'sgn_radio_cassette', 20, 20 )
def radio_cassette( c ):
    # silver boombox: twin speakers, tape deck, carrying handle
    c.rect( 3, 8, 16, 15, rgb( '#b8c0c8' ) )
    c.rect( 3, 8, 16, 8, rgb( '#e0e6ea' ) )
    for cx in ( 6, 13 ):
        c.ellipse( cx, 12, 2.2, 2.2, rgb( '#3a3e42' ) )
        c.px( cx, 12, rgb( '#7a8288' ) )
    c.rect( 8, 10, 11, 13, rgb( '#2a2e32' ) )                      # cassette window
    c.line( 5, 6, 14, 6, rgb( '#6e767e' ) )                        # handle
    c.line( 5, 6, 5, 7, rgb( '#6e767e' ) )
    c.line( 14, 6, 14, 7, rgb( '#6e767e' ) )
    finish( c )


@sprite( 'sgn_mung', 20, 20 )
def mung( c ):
    # folded white mosquito net, mesh texture and hanging strings
    c.rect( 4, 8, 15, 15, rgb( '#f2f4f2' ) )
    for x in range( 5, 15, 2 ):
        c.line( x, 8, x, 15, rgb( '#d8dcd8' ) )
    for y in range( 9, 15, 2 ):
        c.line( 4, y, 15, y, rgb( '#d8dcd8' ) )
    c.line( 4, 8, 2, 5, rgb( '#c8c8c8' ) )
    c.line( 15, 8, 17, 5, rgb( '#c8c8c8' ) )
    finish( c )


@sprite( 'sgn_dau_gio', 20, 20 )
def dau_gio( c ):
    # tiny glass bottle of green medicated oil with a red screw cap
    c.rect( 8, 8, 11, 15, rgb( '#2e9a52', 230 ) )
    c.line( 8, 8, 8, 15, rgb( '#7ad08a' ) )
    c.rect( 9, 5, 10, 7, rgb( '#c8262a' ) )
    c.rect( 8, 11, 11, 12, rgb( '#f2e6c8' ) )
    finish( c )


@sprite( 'sgn_oresol', 20, 20 )
def oresol( c ):
    # foil sachet with an orange stripe and a water drop
    c.rect( 5, 6, 14, 15, rgb( '#d8dee2' ) )
    c.line( 5, 6, 14, 6, rgb( '#f4f8fa' ) )
    c.rect( 5, 9, 14, 11, rgb( '#f08a2c' ) )
    c.ellipse( 9.5, 13, 1.4, 1.6, rgb( '#2f8ad8' ) )
    for x in range( 5, 15, 2 ):
        c.px( x, 15, rgb( '#a8b0b6' ) )                            # crimp
    finish( c )


@sprite( 'sgn_khau_trang', 20, 20 )
def khau_trang( c ):
    # flowery cotton face mask with ear loops
    c.polygon( [ ( 5, 8 ), ( 14, 8 ), ( 15, 13 ), ( 10, 15 ), ( 4, 13 ) ], rgb( '#f4a8c4' ) )
    for x, y in ( ( 7, 10 ), ( 11, 9 ), ( 9, 12 ), ( 13, 12 ) ):
        c.px( x, y, rgb( '#c8306a' ) )
        c.px( x + 1, y, rgb( '#f2f2f2' ) )
    c.ring( 3.5, 10.5, 2, 2.5, rgb( '#f2f2f2' ), 1 )
    c.ring( 15.5, 10.5, 2, 2.5, rgb( '#f2f2f2' ), 1 )
    finish( c )
