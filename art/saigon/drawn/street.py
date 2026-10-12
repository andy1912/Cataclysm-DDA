"""Saigon sidewalk furniture (G20): placed by mapgen/roads/street_life.json.

Tall objects are 32x64 (tall.png geometry, offset 0,-32), rooted in the bottom 32x32 cell
like UltimateCataclysm's poles and lamps; the rest is 32x32 in 3/4 view.  Sprites keep
the UltimateCataclysm look: soft dark outline, light from the top left, a soft shadow.
"""
import math

from draw import sprite, rgb, shade

OUTLINE = 0.42
CONCRETE = rgb( '#a8a49a' )
STEEL = rgb( '#c4ccd2' )
STEEL_DARK = rgb( '#7a8288' )
CABLE = rgb( '#1c1c20' )


def finish( c, shadow=( 2, 2 ), alpha=70 ):
    c.outline( OUTLINE )
    c.drop_shadow( shadow[0], shadow[1], alpha )


def ground_shadow( c, cx, cy, rx, ry ):
    c.ellipse( cx + 3, cy, rx, ry, ( 0, 0, 0, 70 ) )


@sprite( 'f_sgn_cot_dien', 32, 64 )
def cot_dien( c ):
    # tapered concrete pole, a crossarm with insulators, and the famous cable tangle
    ground_shadow( c, 16, 61, 6, 2 )
    c.polygon( [ ( 14, 62 ), ( 18, 62 ), ( 17, 4 ), ( 15, 4 ) ], CONCRETE )
    c.line( 15, 62, 15, 5, shade( CONCRETE, 1.2 ) )
    c.line( 17, 62, 17, 5, shade( CONCRETE, 0.75 ) )
    for y in range( 12, 60, 9 ):                                   # climbing-step holes
        c.px( 16, y, shade( CONCRETE, 0.55 ) )
    c.rect( 7, 7, 25, 8, rgb( '#8a8a82' ) )                         # crossarm
    for x in ( 8, 12, 20, 24 ):
        c.rect( x, 5, x, 6, rgb( '#e8e8e0' ) )                      # insulators
    c.rect( 18, 30, 21, 34, rgb( '#5a5e62' ) )                      # junction box
    c.outline( OUTLINE )
    # cables go on after the outline: an outline would thicken every 1 px cable into a blob
    for k, y0 in enumerate( ( 6, 9, 13 ) ):                       # lines sagging off both ways
        for side in ( -1, 1 ):
            prev = ( 16, y0 )
            for t in range( 1, 9 ):
                x = 16 + side * t * 2
                y = y0 + 3 * math.sin( t / 8 * math.pi ) + k * 0.5
                c.line( prev[0], prev[1], x, y, CABLE )
                prev = ( x, y )
    for k in range( 4 ):                                           # the tangle around the pole
        c.ring( 16 + c.rand.uniform( -1.5, 1.5 ), 24 + c.rand.uniform( -1, 2 ), c.rand.uniform( 3, 5 ),
                c.rand.uniform( 1.5, 3 ), rgb( '#2e2e34' ), 1 )
    c.line( 19, 34, 18, 44, CABLE )                                # drop cable


@sprite( 'f_sgn_loa_phuong', 32, 64 )
def loa_phuong( c ):
    # steel pole with a pair of horn loudspeakers and a ward notice board
    ground_shadow( c, 16, 61, 5, 2 )
    c.rect( 15, 8, 17, 62, STEEL_DARK )
    c.line( 15, 8, 15, 62, STEEL )
    for side in ( -1, 1 ):                                         # two horns, facing out
        c.polygon( [ ( 16, 6 ), ( 16, 11 ), ( 16 + side * 11, 14 ), ( 16 + side * 11, 3 ) ], rgb( '#d8dcd8' ) )
        c.ellipse( 16 + side * 11, 8.5, 1.4, 5.5, rgb( '#3a3e42' ) )
    c.rect( 14, 5, 18, 12, rgb( '#9aa0a4' ) )
    c.rect( 10, 30, 22, 38, rgb( '#c8262a' ) )                      # red notice board
    c.rect( 11, 31, 21, 32, rgb( '#f2c232' ) )
    for y in ( 34, 36 ):
        c.line( 12, y, 20, y, rgb( '#f4e2c0' ) )
    c.outline( OUTLINE )


@sprite( 'f_sgn_ban_inox', 32, 32 )
def ban_inox( c ):
    # low square stainless table, a caddy of chopsticks, chili and fish sauce on top
    c.polygon( [ ( 5, 12 ), ( 27, 12 ), ( 25, 22 ), ( 7, 22 ) ], STEEL )
    c.line( 5, 12, 27, 12, rgb( '#eef2f4' ) )
    c.polygon( [ ( 7, 22 ), ( 25, 22 ), ( 25, 24 ), ( 7, 24 ) ], STEEL_DARK )
    for x in ( 8, 23 ):
        c.rect( x, 24, x + 1, 28, STEEL_DARK )                      # legs
    c.rect( 13, 13, 19, 18, rgb( '#d8dcd8' ) )                      # caddy tray
    c.rect( 14, 10, 15, 16, rgb( '#d02a2a' ) )                      # chili sauce
    c.rect( 17, 11, 18, 16, rgb( '#b8762a' ) )                      # fish sauce
    for x in ( 20, 21 ):
        c.line( x, 10, x, 16, rgb( '#e8d8b0' ) )                    # chopsticks
    finish( c )


@sprite( 'f_sgn_xe_banh_mi', 32, 32 )
def xe_banh_mi( c ):
    # glass case on a blue cart, baguettes stacked inside, two wheels
    c.rect( 5, 15, 27, 26, rgb( '#2f6ab0' ) )                       # cabinet
    c.rect( 5, 15, 27, 16, rgb( '#5a90d0' ) )
    c.rect( 6, 4, 26, 14, rgb( '#c8262a' ) )                        # red frame
    c.rect( 7, 5, 25, 13, rgb( '#cfe4ec' ) )                        # glass
    for y in ( 7, 10 ):
        for x in ( 8, 15 ):
            c.capsule( x, y + 1, x + 5, y, 1.1, rgb( '#d79a45' ) )   # baguettes
    c.line( 8, 6, 12, 6, rgb( '#ffffff' ) )                         # glass glint
    c.rect( 11, 18, 21, 22, rgb( '#f2c232' ) )                      # painted sign panel
    for x in ( 9, 23 ):
        c.ellipse( x, 27, 2.6, 2.6, rgb( '#2a2a2e' ) )
        c.px( x, 27, rgb( '#9aa0a4' ) )
    finish( c )


@sprite( 'f_sgn_du', 32, 64 )
def du( c ):
    # big striped café umbrella on a weighted stand
    ground_shadow( c, 16, 61, 7, 2 )
    c.ellipse( 16, 61, 5, 2, rgb( '#4a4e52' ) )                     # stand
    c.rect( 15, 20, 16, 61, rgb( '#d8dcd8' ) )                      # pole
    for k in range( 8 ):                                           # canopy panels
        a0, a1 = math.pi * k / 8, math.pi * ( k + 1 ) / 8
        colour = rgb( '#d83a3a' ) if k % 2 else rgb( '#f4f0e8' )
        c.polygon( [ ( 16, 9 ), ( 16 - 15 * math.cos( a0 ), 22 ), ( 16 - 15 * math.cos( a1 ), 22 ) ], colour )
    c.line( 1, 22, 31, 22, rgb( '#8a2020' ) )                       # hem
    c.px( 16, 8, rgb( '#d8dcd8' ) )
    c.outline( OUTLINE )


def bang_hieu( c, board, text ):
    # A-frame sidewalk sign; the "lettering" is abstract stripes (sprites stay language-free)
    c.polygon( [ ( 9, 9 ), ( 23, 9 ), ( 25, 27 ), ( 7, 27 ) ], board )
    c.polygon( [ ( 23, 9 ), ( 25, 27 ), ( 26, 27 ), ( 24, 9 ) ], shade( board, 0.6 ) )
    c.rect( 10, 11, 22, 13, shade( board, 1.35 ) )
    for y in ( 16, 19, 22 ):
        c.line( 11, y, 21 - ( y - 16 ) // 2, y, text )
    finish( c )


@sprite( 'f_sgn_bang_hieu', 32, 32,
         fg=[ { 'weight': 1, 'sprite': '@f_sgn_bang_hieu' }, { 'weight': 1, 'sprite': '@f_sgn_bang_hieu__blue' },
              { 'weight': 1, 'sprite': '@f_sgn_bang_hieu__green' } ] )
def bang_hieu_red( c ):
    bang_hieu( c, rgb( '#c8262a' ), rgb( '#f2c232' ) )


@sprite( 'f_sgn_bang_hieu__blue', 32, 32 )
def bang_hieu_blue( c ):
    bang_hieu( c, rgb( '#2f5aa8' ), rgb( '#ffffff' ) )


@sprite( 'f_sgn_bang_hieu__green', 32, 32 )
def bang_hieu_green( c ):
    bang_hieu( c, rgb( '#2e8a4a' ), rgb( '#f4f0e0' ) )
