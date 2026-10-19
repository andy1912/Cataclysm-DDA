"""Shophouse businesses (B8h): gold-shop counter, internet-café PC, karaoke set.  32x32 3/4 view."""
from draw import sprite, rgb

OUTLINE = 0.42


def finish( c ):
    c.outline( OUTLINE )
    c.drop_shadow( 2, 2, 70 )


@sprite( 'f_sgn_quay_vang', 32, 32 )
def quay_vang( c ):
    # glass counter on a lacquered base, red velvet inside, gold leaves and chains on show
    c.rect( 3, 18, 28, 28, rgb( '#7a1a1a' ) )                      # base
    c.rect( 3, 18, 28, 19, rgb( '#a82a2a' ) )
    c.rect( 3, 6, 28, 17, rgb( '#c8262a' ) )                       # velvet
    for x in range( 6, 26, 5 ):
        c.rect( x, 9, x + 2, 11, rgb( '#f2c232' ) )                # gold leaves
        c.px( x, 9, rgb( '#ffe68a' ) )
    for x in range( 5, 27, 2 ):
        c.px( x, 14 + ( x % 4 ) // 2, rgb( '#f2c232' ) )            # a chain
    c.rect( 3, 5, 28, 5, rgb( '#e8f2f4' ) )                        # glass top edge
    c.line( 5, 7, 12, 7, rgb( '#ffffff', 160 ) )                   # glint
    finish( c )


@sprite( 'f_sgn_may_net', 32, 32 )
def may_net( c ):
    # beige CRT monitor and tower on a plywood desk, keyboard and a headset
    c.rect( 3, 17, 28, 20, rgb( '#b88a58' ) )                      # desk top
    c.rect( 4, 21, 5, 28, rgb( '#8a6440' ) )
    c.rect( 26, 21, 27, 28, rgb( '#8a6440' ) )
    c.rect( 8, 5, 21, 15, rgb( '#d8d0bc' ) )                       # monitor
    c.rect( 10, 7, 19, 13, rgb( '#2f5a8a' ) )
    c.line( 11, 8, 15, 8, rgb( '#7ab0e0' ) )
    c.rect( 23, 6, 27, 16, rgb( '#cfc6b0' ) )                      # tower
    c.px( 25, 8, rgb( '#5ad05a' ) )
    c.rect( 9, 17, 20, 18, rgb( '#e8e2d0' ) )                      # keyboard
    c.ring( 5, 13, 2.5, 2.5, rgb( '#2a2a2e' ), 1 )                 # headset
    finish( c )


@sprite( 'f_sgn_dan_karaoke', 32, 32 )
def dan_karaoke( c ):
    # big TV between two speaker towers, a disc player and two microphones
    for x in ( 2, 25 ):
        c.rect( x, 6, x + 5, 27, rgb( '#2a2a2e' ) )                # speaker towers
        c.ellipse( x + 2.5, 12, 2, 2, rgb( '#5a5e62' ) )
        c.ellipse( x + 2.5, 21, 2.4, 2.4, rgb( '#5a5e62' ) )
    c.rect( 8, 7, 23, 19, rgb( '#3a3c40' ) )                       # TV
    c.rect( 9, 8, 22, 17, rgb( '#c85a9a' ) )                       # lyrics screen
    for y in ( 11, 14 ):
        c.line( 11, y, 20, y, rgb( '#f4e2f0' ) )
    c.rect( 9, 21, 22, 23, rgb( '#5a5e62' ) )                      # disc player
    c.px( 20, 22, rgb( '#5ad05a' ) )
    c.line( 11, 26, 13, 24, rgb( '#c8ccd0' ) )                     # microphones
    c.line( 19, 26, 17, 24, rgb( '#c8ccd0' ) )
    finish( c )
