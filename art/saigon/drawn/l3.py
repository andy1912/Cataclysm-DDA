"""L3 landmarks (asset unit A5): the station and bus station, Tao Đàn park, Hồ Con Rùa, Saigon
Trade Center, Diamond Plaza and the Phạm Ngũ Lão – Bùi Viện backpacker street.
Definitions in data/mods/saigon_2000s/furniture/l3.json and items/gear/travel.json.  The
blue-green curtain wall is derived from t_wall_glass (derive_recipes.json).

Tall objects are 32x64 (tall.png geometry), rooted in the bottom 32x32 cell.  3/4 view,
light from the top left, soft dark outline and shadow, like UltimateCataclysm.
"""
import math

from draw import sprite, rgb, shade

OUTLINE = 0.42
STEEL = rgb( '#b8c0c6' )
RUBBER = rgb( '#24262a' )
GRANITE = rgb( '#a4a29c' )
BAMBOO = rgb( '#c8a660' )
CONCRETE = rgb( '#d8d4ca' )


def finish( c, shadow=( 2, 2 ), alpha=70 ):
    c.outline( OUTLINE )
    c.drop_shadow( shadow[0], shadow[1], alpha )


def ground_shadow( c, cx, cy, rx, ry ):
    c.ellipse( cx + 3, cy, rx, ry, ( 0, 0, 0, 70 ) )


# --- escalators: real stairs (copy-from t_stairs_up / t_stairs_down) -----------------------
def escalator( c, up ):
    c.rect( 0, 0, 31, 31, rgb( '#cfcac0' ) )                          # mall floor around it
    c.rect( 5, 0, 26, 31, rgb( '#8a9096' ) )                          # the balustrade
    c.rect( 8, 0, 23, 31, STEEL )
    for y in range( 1, 31, 3 ):                                       # grooved steps
        c.line( 8, y, 23, y, shade( STEEL, 0.62 ) )
        c.line( 8, y + 1, 23, y + 1, shade( STEEL, 1.18 ) )
    c.rect( 5, 0, 7, 31, RUBBER )                                     # handrails
    c.rect( 24, 0, 26, 31, RUBBER )
    comb = 0 if up else 28                                            # comb plate at the far end
    c.rect( 8, comb, 23, comb + 3, rgb( '#e0c040' ) )
    for x in range( 9, 23, 2 ):
        c.px( x, comb + 1, rgb( '#806a20' ) )
    # direction arrow on the first step
    # the arrow narrows towards where the steps go: up the screen for up, down for down
    ay, d = ( 20, -1 ) if up else ( 11, 1 )
    for i in range( 4 ):
        w = 3 - i
        c.line( 16 - w - 1, ay + d * i, 15 + w + 1, ay + d * i, rgb( '#2a8a4a' ) if up else rgb( '#c03030' ) )


@sprite( 't_sgn_thang_cuon_len', 32, 32 )
def thang_cuon_len( c ):
    escalator( c, True )


@sprite( 't_sgn_thang_cuon_xuong', 32, 32 )
def thang_cuon_xuong( c ):
    escalator( c, False )


# --- Ga Sài Gòn / Bến xe Miền Đông ---------------------------------------------------------
@sprite( 'f_sgn_bang_gio_tau', 32, 64 )
def bang_gio_tau( c ):
    # a black flip-slat departure board on two steel posts, rows of amber times and names
    ground_shadow( c, 16, 60, 12, 2.5 )
    for x in ( 5, 26 ):
        c.rect( x, 26, x + 1, 60, shade( STEEL, 0.8 ) )
    c.rect( 1, 8, 30, 36, rgb( '#1a1c20' ) )
    c.rect( 1, 8, 30, 11, rgb( '#2a5a9a' ) )                          # the blue header
    c.line( 4, 9, 20, 9, rgb( '#f0f0f0' ) )
    for i, y in enumerate( range( 14, 35, 4 ) ):
        c.line( 3, y, 8, y, rgb( '#f0b030' ) )                         # departure time
        c.line( 11, y, 11 + 6 + ( i * 5 ) % 12, y, rgb( '#f0b030' ) )  # destination
        c.line( 24, y, 28, y, rgb( '#e04030' ) if i % 3 == 0 else rgb( '#40c060' ) )   # status
        c.line( 2, y + 2, 29, y + 2, rgb( '#2a2c30' ) )                # slat gaps
    finish( c )


@sprite( 'f_sgn_quay_ve', 32, 32 )
def quay_ve( c ):
    # a ticket counter behind scratched glass, a speaking hole, a money slot, a taped sign
    ground_shadow( c, 16, 29, 14, 2.5 )
    c.rect( 1, 16, 30, 28, rgb( '#7a8a96' ) )                          # counter front
    c.rect( 1, 14, 30, 16, rgb( '#c8ccd0' ) )                          # counter top
    c.rect( 3, 2, 28, 14, rgb( '#b8d4dc', 150 ) )                      # the glass pane
    c.frame( 3, 2, 28, 14, rgb( '#5a6a76' ) )
    c.ring( 15.5, 8, 2.5, 2.5, rgb( '#5a6a76' ), 1 )                  # speaking hole
    c.rect( 11, 13, 20, 13, rgb( '#2a2e32' ) )                         # money slot
    c.rect( 20, 3, 26, 7, rgb( '#f4f0e0' ) )                           # "HẾT VÉ" sign
    c.line( 21, 5, 25, 5, rgb( '#d02020' ) )
    c.line( 5, 4, 9, 9, rgb( '#e8f0f4', 120 ) )                        # scratches
    finish( c )


# --- Tao Đàn park --------------------------------------------------------------------------
def cage( c, cx, top, bird=None ):
    c.line( cx, top - 4, cx, top, rgb( '#5a4630' ) )                   # hook
    c.ellipse( cx, top + 2, 4.5, 2.5, shade( BAMBOO, 1.1 ) )          # domed top
    for x in range( -4, 5, 2 ):                                        # bamboo bars
        c.line( cx + x, top + 2, cx + x, top + 10, BAMBOO )
    c.rect( cx - 5, top + 10, cx + 5, top + 11, shade( BAMBOO, 0.7 ) )   # base tray
    if bird:
        c.ellipse( cx, top + 7, 1.8, 1.4, rgb( bird ) )
        c.px( int( cx ) + 2, top + 6, rgb( '#f0a020' ) )


@sprite( 'f_sgn_long_chim', 32, 64 )
def long_chim( c ):
    # a wooden rack in the park café with songbird cages hanging from its crossbar
    ground_shadow( c, 16, 60, 13, 2.5 )
    c.rect( 3, 14, 4, 60, rgb( '#6a4a2a' ) )                           # posts
    c.rect( 27, 14, 28, 60, rgb( '#6a4a2a' ) )
    c.rect( 1, 12, 30, 14, rgb( '#7a5630' ) )                          # crossbar
    cage( c, 9, 18, '#c84a2a' )                                        # a red-whiskered bulbul
    cage( c, 22, 18 )
    cage( c, 15.5, 36, '#5a5a3a' )
    finish( c )


@sprite( 'f_sgn_ban_da', 32, 32 )
def ban_da( c ):
    # a round granite table with a carved xiangqi board, four drum stools
    for x, y in ( ( 3, 4 ), ( 28, 4 ), ( 3, 27 ), ( 28, 27 ) ):        # drum stools, set apart
        ground_shadow( c, x, y + 2, 2.6, 1.2 )
        c.ellipse( x, y, 2.6, 2.2, shade( GRANITE, 0.88 ), light=shade( GRANITE, 1.2 ) )
    c.outline( OUTLINE )
    ground_shadow( c, 16, 25, 9, 2.2 )
    c.rect( 14, 19, 18, 25, shade( GRANITE, 0.7 ) )                    # pedestal
    c.ellipse( 16, 15, 9.5, 6.5, GRANITE, light=shade( GRANITE, 1.25 ), dark=shade( GRANITE, 0.75 ) )
    for i in range( 4 ):                                               # the carved board
        c.line( 10, 12 + i * 2, 22, 12 + i * 2, shade( GRANITE, 0.7 ) )
    for x in range( 10, 23, 3 ):
        c.line( x, 12, x, 18, shade( GRANITE, 0.7 ) )
    c.line( 10, 15, 22, 15, rgb( '#7a9ab0' ) )                         # the river across the middle
    finish( c, alpha=55 )


# --- Hồ Con Rùa ----------------------------------------------------------------------------
@sprite( 'f_sgn_thap_rua', 32, 64 )
def thap_rua( c ):
    # the concrete monument: a ring of open lotus petals and a slender spire
    ground_shadow( c, 16, 60, 13, 3 )
    c.ellipse( 16, 56, 12, 4, shade( CONCRETE, 0.8 ) )                # plinth
    for i, a in enumerate( range( -70, 71, 28 ) ):                      # lotus petals
        x = 16 + 11 * math.sin( math.radians( a ) )
        c.polygon( [ ( 16, 56 ), ( x - 3, 44 - abs( a ) / 12 ), ( x + 3, 44 - abs( a ) / 12 ) ],
                   shade( CONCRETE, 1.0 + ( i % 2 ) * 0.08 ) )
        c.line( 16, 55, x, 45 - abs( a ) / 12, shade( CONCRETE, 0.78 ) )
    c.polygon( [ ( 13, 48 ), ( 19, 48 ), ( 16.5, 3 ), ( 15.5, 3 ) ], CONCRETE )   # the spire
    c.line( 14, 47, 16, 4, shade( CONCRETE, 1.12 ) )
    c.line( 18, 47, 16, 4, shade( CONCRETE, 0.75 ) )
    for y in ( 20, 30, 40 ):                                           # ribs
        c.line( 14 + ( 48 - y ) // 20, y, 18 - ( 48 - y ) // 20, y, shade( CONCRETE, 0.7 ) )
    finish( c )


# --- Phạm Ngũ Lão – Bùi Viện ---------------------------------------------------------------
@sprite( 'sgn_ho_chieu', 20, 20 )
def ho_chieu( c ):
    # a sun-faded passport, gold crest, a visa slip poking out
    c.rect( 4, 3, 15, 16, rgb( '#23305a' ) )
    c.line( 4, 3, 15, 3, rgb( '#33407a' ) )
    c.rect( 13, 2, 17, 6, rgb( '#e8e0c8' ) )                           # the visa slip
    c.ellipse( 9.5, 9, 2.5, 2.5, rgb( '#d8b048' ) )
    c.px( 9, 9, rgb( '#23305a' ) )
    c.line( 6, 13, 13, 13, rgb( '#d8b048' ) )
    c.outline( OUTLINE )
    c.drop_shadow( 1, 1, 60 )
