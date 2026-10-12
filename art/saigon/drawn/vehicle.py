"""Saigon vehicle parts: 32x32 top-down, like UltimateCataclysm's vp_* sprites.

Vehicle parts are drawn from "vp_<part id>" tiles (src/cata_tiles.cpp:2096) and seen
from straight above, front of the vehicle towards the top of the tile.  Every part is
"rotates": true: the engine only turns a tile with the vehicle when it is multitile or
says so (tileset_loader: "rotates" defaults to "multitile"), otherwise it stays upright.
"""
from draw import sprite, rgb, shade

OUTLINE = 0.4
STEEL = rgb( '#a8b0b8' )
CHROME = rgb( '#d8dee4' )
BLACK_VINYL = rgb( '#2a2a2e' )


def finish( c ):
    c.outline( OUTLINE )


@sprite( 'vp_sgn_engine_110cc', 32, 32, rotates=True )
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


@sprite( 'vp_sgn_pillion', 32, 32, rotates=True )
def pillion( c ):
    # long padded passenger seat with a chrome grab rail behind it
    c.ellipse( 16, 14, 5, 10, BLACK_VINYL, light=rgb( '#4a4a52' ) )
    for y in ( 9, 14, 19 ):
        c.line( 13, y, 19, y, rgb( '#1a1a1e' ) )                  # stitching
    c.ring( 16, 26, 6, 3, CHROME, 1.2 )
    finish( c )


@sprite( 'vp_sgn_tank_4l', 32, 32, rotates=True )
def tank_4l( c ):
    # small pressed-steel tank under the seat, red paint, chrome filler cap
    c.ellipse( 16, 16, 6, 8, rgb( '#b82a2a' ), light=rgb( '#e86060' ), dark=rgb( '#7e1a1a' ) )
    c.ellipse( 16, 12, 2, 2, CHROME )
    c.px( 16, 12, rgb( '#6e767e' ) )
    finish( c )


@sprite( 'vp_sgn_longtail', 32, 32, rotates=True )
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


@sprite( 'vp_sgn_oars', 32, 32, rotates=True )
def oars( c ):
    # a pair of wooden oars shipped along the gunwale
    wood = rgb( '#a87a48' )
    for x in ( 11, 20 ):
        c.capsule( x, 4, x, 22, 0.8, wood )
        c.ellipse( x, 25, 2.2, 4.5, shade( wood, 0.85 ), light=shade( wood, 1.15 ) )   # blade
        c.rect( x - 1, 3, x + 1, 5, rgb( '#5a3a22' ) )                                # grip
    finish( c )


@sprite( 'vp_sgn_xich_lo_seat', 32, 32, rotates=True )
def xich_lo_seat( c ):
    # the cyclo's front bucket seat in red vinyl, the folded black canopy behind it and
    # the steel bumper arc in front
    c.ring( 16, 10, 11, 7, CHROME, 1.3 )                               # bumper arc
    c.erase( 0, 10, 31, 31 )                                           # keep its front half
    c.rect( 7, 9, 24, 20, rgb( '#b8282a' ) )                           # seat
    c.rect( 8, 10, 23, 11, rgb( '#e05050' ) )
    for x in range( 10, 23, 4 ):
        c.line( x, 12, x, 19, rgb( '#8a1a1c' ) )                       # tufting
    c.rect( 6, 21, 25, 27, rgb( '#26262a' ) )                          # folded canopy
    for x in range( 8, 25, 4 ):
        c.line( x, 21, x, 27, rgb( '#4a4a50' ) )                       # canopy ribs
    c.line( 6, 21, 25, 21, rgb( '#5a5a62' ) )
    c.outline( OUTLINE )


@sprite( 'vp_sgn_ba_gac_bed', 32, 32, rotates=True )
def ba_gac_bed( c ):
    # rough plank deck running fore and aft; tiles seamlessly across the 3x3 bed
    planks = [ rgb( '#9a7048' ), rgb( '#8a6240' ), rgb( '#a47a50' ), rgb( '#946a44' ) ]
    for i, x0 in enumerate( range( 0, 32, 8 ) ):
        c.rect( x0, 0, x0 + 6, 31, planks[i % 4] )
        c.line( x0 + 7, 0, x0 + 7, 31, rgb( '#4a3424' ) )              # gaps
        c.noise( x0, 0, x0 + 6, 31, [ shade( planks[i % 4], 0.85 ), shade( planks[i % 4], 1.12 ) ], 0.18 )
        for y in ( 3, 28 ):
            c.px( x0 + 3, y, rgb( '#3a3a3a' ) )                        # bolts
    c.line( 0, 15, 31, 15, rgb( '#2f5aa8' ) )                          # painted cross member
    c.line( 0, 16, 31, 16, rgb( '#244a8a' ) )
