"""Saigon vehicle parts: 32x32 top-down, like UltimateCataclysm's vp_* sprites.

Vehicle parts are drawn from "vp_<part id>" tiles (src/cata_tiles.cpp:2096) and seen
from straight above, front of the vehicle towards the top of the tile.
"""
from draw import sprite, rgb, shade

OUTLINE = 0.4
STEEL = rgb( '#a8b0b8' )
CHROME = rgb( '#d8dee4' )
BLACK_VINYL = rgb( '#2a2a2e' )


def finish( c ):
    c.outline( OUTLINE )


@sprite( 'vp_sgn_engine_110cc', 32, 32 )
def engine_110cc( c ):
    # air-cooled single seen from above: wide crankcase, square finned cylinder leaning
    # forward, exhaust pipe sweeping back on the right, chain sprocket on the left
    c.capsule( 20, 12, 25, 28, 1.3, CHROME )                      # exhaust
    c.ellipse( 16, 21, 9, 5.5, STEEL, light=CHROME, dark=shade( STEEL, 0.7 ) )
    c.rect( 11, 7, 21, 16, rgb( '#7a8288' ) )
    for y in range( 7, 17, 2 ):
        c.line( 10, y, 22, y, rgb( '#c8d0d6' ) )                 # cooling fins
    c.rect( 14, 9, 18, 14, rgb( '#5a6268' ) )                     # cylinder head
    c.rect( 15, 5, 17, 6, rgb( '#3a3e44' ) )                      # spark plug cap
    c.ring( 9, 22, 3, 3, rgb( '#3a3e44' ), 1.2 )                  # sprocket
    c.px( 9, 22, rgb( '#3a3e44' ) )
    finish( c )


@sprite( 'vp_sgn_pillion', 32, 32 )
def pillion( c ):
    # long padded passenger seat with a chrome grab rail behind it
    c.ellipse( 16, 14, 5, 10, BLACK_VINYL, light=rgb( '#4a4a52' ) )
    for y in ( 9, 14, 19 ):
        c.line( 13, y, 19, y, rgb( '#1a1a1e' ) )                  # stitching
    c.ring( 16, 26, 6, 3, CHROME, 1.2 )
    finish( c )


@sprite( 'vp_sgn_tank_4l', 32, 32 )
def tank_4l( c ):
    # small pressed-steel tank under the seat, red paint, chrome filler cap
    c.ellipse( 16, 16, 6, 8, rgb( '#b82a2a' ), light=rgb( '#e86060' ), dark=rgb( '#7e1a1a' ) )
    c.ellipse( 16, 12, 2, 2, CHROME )
    c.px( 16, 12, rgb( '#6e767e' ) )
    finish( c )


@sprite( 'vp_sgn_longtail', 32, 32 )
def longtail( c ):
    # máy đuôi tôm: a small engine on a pivot with a long drive shaft and propeller trailing aft
    c.rect( 11, 3, 21, 13, rgb( '#c8a028' ) )                     # engine shroud
    c.rect( 12, 4, 20, 6, rgb( '#e8c450' ) )
    c.rect( 14, 8, 18, 11, rgb( '#3a3e44' ) )                     # air filter
    c.capsule( 16, 13, 16, 27, 1.0, STEEL )                       # drive shaft
    c.line( 13, 28, 19, 28, rgb( '#6e767e' ) )                    # propeller
    c.line( 16, 26, 16, 30, rgb( '#6e767e' ) )
    c.line( 21, 6, 27, 2, rgb( '#5a3a22' ) )                      # tiller
    finish( c )


@sprite( 'vp_sgn_oars', 32, 32 )
def oars( c ):
    # a pair of wooden oars shipped along the gunwale
    wood = rgb( '#a87a48' )
    for x in ( 11, 20 ):
        c.capsule( x, 4, x, 22, 0.8, wood )
        c.ellipse( x, 25, 2.2, 4.5, shade( wood, 0.85 ), light=shade( wood, 1.15 ) )   # blade
        c.rect( x - 1, 3, x + 1, 5, rgb( '#5a3a22' ) )                                # grip
    finish( c )
