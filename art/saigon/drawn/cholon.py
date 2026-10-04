"""Chợ Lớn landmarks (asset unit A2, doc/saigon/MAP.md): the Thiên Hậu and Ngọc Hoàng temples
and Chợ Bình Tây.  Definitions in data/mods/saigon_2000s/furniture/cholon.json.

Tall objects (statues, the pillar, the rice-sack stack) are 32x64 like UltimateCataclysm's
f_statue / t_column / f_crate_c, rooted in the bottom 32x32 cell.  3/4 view, light from
the top left, soft dark outline and shadow.
"""
import math

from draw import sprite, rgb, shade, mix

OUTLINE = 0.42
LACQUER = rgb( '#a81c1c' )
GOLD = rgb( '#e0b030' )
BRONZE = rgb( '#8a6430' )
GRANITE = rgb( '#a4a29c' )
CLAY = rgb( '#b45c3a' )
EMBER = rgb( '#ff6a20' )
SMOKE = rgb( '#e8e8f0', 70 )


def finish( c, shadow=( 2, 2 ), alpha=70 ):
    c.outline( OUTLINE )
    c.drop_shadow( shadow[0], shadow[1], alpha )


def ground_shadow( c, cx, cy, rx, ry ):
    c.ellipse( cx + 3, cy, rx, ry, ( 0, 0, 0, 70 ) )


# --- terrain ----------------------------------------------------------------------------------
@sprite( 't_sgn_gach_tau', 32, 32 )
def gach_tau( c ):
    # 8 px red clay tiles, each fired a little differently, dark joints with moss
    c.rect( 0, 0, 31, 31, rgb( '#5a3424' ) )
    for ty in range( 4 ):
        for tx in range( 4 ):
            k = c.rand.uniform( 0.86, 1.12 )
            x0, y0 = tx * 8, ty * 8
            c.rect( x0, y0, x0 + 6, y0 + 6, shade( CLAY, k ) )
            c.line( x0, y0, x0 + 6, y0, shade( CLAY, k * 1.15 ) )          # worn top edge
            c.line( x0 + 6, y0 + 1, x0 + 6, y0 + 6, shade( CLAY, k * 0.82 ) )
    c.noise( 0, 0, 31, 31, [ shade( CLAY, 0.7 ), shade( CLAY, 1.2 ) ], 0.06 )
    for _ in range( 6 ):                                               # moss in the joints
        j = c.rand.randrange( 4 ) * 8 + 7
        c.px( j if c.rand.random() < 0.5 else c.rand.randrange( 32 ),
              c.rand.randrange( 32 ) if c.rand.random() < 0.5 else j, rgb( '#4a6a32' ) )


@sprite( 't_sgn_ngoi_men_xanh', 32, 32 )
def ngoi_men_xanh( c ):
    # green glazed tubular tiles in columns, a bright glaze highlight down each tube
    green = rgb( '#2e8a4a' )
    c.rect( 0, 0, 31, 31, shade( green, 0.5 ) )
    for x in range( 0, 32, 6 ):
        c.rect( x + 1, 0, x + 4, 31, green )
        c.line( x + 2, 0, x + 2, 31, shade( green, 1.45 ) )
        c.line( x + 4, 0, x + 4, 31, shade( green, 0.75 ) )
        for y in range( 3, 32, 8 ):                                    # tube joints
            c.line( x + 1, y, x + 4, y, shade( green, 0.62 ) )
    c.noise( 0, 0, 31, 31, [ rgb( '#d8e8c0' ) ], 0.015 )


@sprite( 't_sgn_cot_son', 32, 64 )
def cot_son( c ):
    # a round red lacquered pillar on a stone base, a gilded couplet down its face
    ground_shadow( c, 16, 59, 9, 3 )
    c.ellipse( 16, 58, 10, 4, GRANITE )                                # stone base
    c.rect( 9, 6, 23, 57, LACQUER )
    c.line( 10, 6, 10, 57, shade( LACQUER, 1.35 ) )                    # round: lit left edge
    c.line( 11, 6, 11, 57, shade( LACQUER, 1.15 ) )
    c.line( 22, 6, 22, 57, shade( LACQUER, 0.7 ) )
    c.line( 23, 6, 23, 57, shade( LACQUER, 0.6 ) )
    c.rect( 14, 12, 17, 50, rgb( '#1e1a16' ) )                         # the black couplet board
    for y in range( 14, 49, 4 ):                                       # gilded characters
        c.rect( 15, y, 16, y + 1, GOLD )
        if y % 8 == 2:
            c.px( 14, y + 1, GOLD )
    c.ellipse( 16, 6, 7.5, 2.5, shade( LACQUER, 1.1 ) )               # top, into the beam
    c.rect( 8, 2, 24, 5, rgb( '#5a2a1a' ) )
    finish( c )


# --- the temples ------------------------------------------------------------------------------
def coil( c, cx, top, length, r ):
    # a hanging incense cone: a spiral that widens downwards, drawn as tilted turns
    # of brown-gold coil with the dark gaps between them showing
    turns = 6
    for i in range( turns ):
        t = ( i + 1 ) / turns
        y = top + t * length
        rx = 1.5 + t * ( r - 1.5 )
        c.ring( cx, y, rx, max( 1.0, rx * 0.35 ), rgb( '#9a7034' ) if i % 2 else rgb( '#b88a44' ), 1 )
    c.line( cx - r, top + length, cx + r, top + length, rgb( '#7a5628' ) )
    c.px( int( cx + r ), int( top + length ), EMBER )                  # the burning end


@sprite( 'f_sgn_nhang_vong', 32, 32 )
def nhang_vong( c ):
    # two big incense cones hanging from the rafters, red prayer tags below, a thread of smoke
    for cx, top, length, r in ( ( 10, 3, 13, 7 ), ( 23, 7, 11, 6 ) ):
        c.line( cx, 0, cx, top, rgb( '#5a4630' ) )                      # hanging wire
        coil( c, cx, top, length, r )
        y = top + length + 1
        c.line( cx, y, cx, y + 1, rgb( '#5a4630' ) )
        c.rect( cx - 1, y + 2, cx + 1, y + 7, rgb( '#d02020' ) )        # prayer tag
        c.px( cx, y + 4, GOLD )
    c.outline( OUTLINE )
    for y in range( 0, 10 ):                                           # smoke after the outline
        c.px( 18 + round( 1.5 * math.sin( y / 2 ) ), 16 - y, SMOKE )
        c.px( 30 - y // 3, 18 - y, SMOKE )


@sprite( 'f_sgn_lu_huong', 32, 32 )
def lu_huong( c ):
    # a great bronze urn on lion feet, full of ash and the red stubs of joss sticks
    ground_shadow( c, 16, 28, 11, 3 )
    for x in ( 8, 16, 24 ):                                            # three feet
        c.rect( x - 1, 24, x + 1, 28, shade( BRONZE, 0.75 ) )
    c.ellipse( 16, 18, 12, 9, BRONZE, light=shade( BRONZE, 1.45 ), dark=shade( BRONZE, 0.6 ) )
    for x in ( 3, 29 ):                                                # loop handles
        c.ring( x, 14, 2.2, 2.6, shade( BRONZE, 0.9 ), 1.2 )
    c.ellipse( 16, 12, 12, 4.5, shade( BRONZE, 1.2 ) )                # the rim
    c.ellipse( 16, 12, 10.5, 3.4, rgb( '#c8b8a0' ) )                  # ash and sand
    for _ in range( 22 ):                                              # stubs, some still glowing
        x = 16 + c.rand.uniform( -9, 9 )
        y = 12 + c.rand.uniform( -2.6, 2.6 )
        c.line( x, y, x, y - c.rand.randint( 1, 4 ), rgb( '#c02828' ) )
        if c.rand.random() < 0.25:
            c.px( int( x ), int( y ) - 4, EMBER )
    c.line( 9, 21, 23, 21, shade( BRONZE, 0.55 ) )                    # cast band
    finish( c )
    for y in range( 6 ):
        c.px( 13 + round( math.sin( y ) ), 6 - y, SMOKE )
        c.px( 20 - round( math.sin( y ) ), 5 - y, SMOKE )


@sprite( 'f_sgn_ban_tho_lon', 32, 32 )
def ban_tho_lon( c ):
    # the long red-and-gold temple altar with candlesticks, a fruit plate and an incense bowl
    ground_shadow( c, 16, 28, 14, 2.5 )
    c.rect( 1, 10, 30, 27, LACQUER )
    c.rect( 1, 10, 30, 12, shade( LACQUER, 1.3 ) )                    # top surface
    c.frame( 3, 15, 28, 25, GOLD )                                     # gilded carved panel
    for x in range( 5, 27, 4 ):                                        # carved dragon scales
        c.px( x, 20, GOLD )
        c.px( x + 2, 19, GOLD )
    for x in ( 4, 27 ):                                                # brass candlesticks
        c.rect( x, 3, x + 1, 10, rgb( '#d8b048' ) )
        c.px( x, 2, rgb( '#ff8a3a' ) )
    c.ellipse( 10, 9, 3.2, 1.6, rgb( '#e8e0d0' ) )                    # fruit plate
    for x, col in ( ( 9, '#f08a1a' ), ( 11, '#e8d040' ), ( 10, '#d82828' ) ):
        c.ellipse( x, 8, 1.3, 1.3, rgb( col ) )
    c.ellipse( 21, 9, 3, 1.6, rgb( '#c89a40' ) )                       # incense bowl
    for x in ( 20, 21, 22 ):
        c.line( x, 8, x - 1 + ( x - 20 ), 3, rgb( '#c02828' ) )
    finish( c )


@sprite( 'f_sgn_su_tu_da', 32, 64 )
def su_tu_da( c ):
    # a granite guardian lion on its plinth, one paw on the ball, curled mane, open mouth
    ground_shadow( c, 16, 60, 12, 3 )
    c.rect( 4, 46, 27, 60, shade( GRANITE, 0.85 ) )                    # plinth
    c.rect( 4, 46, 27, 48, shade( GRANITE, 1.15 ) )
    c.line( 4, 54, 27, 54, shade( GRANITE, 0.65 ) )
    c.ellipse( 17, 38, 9, 9, GRANITE, light=shade( GRANITE, 1.3 ), dark=shade( GRANITE, 0.7 ) )   # haunches
    c.rect( 9, 30, 15, 46, GRANITE )                                    # forelegs
    c.ellipse( 8, 42, 4, 4, shade( GRANITE, 0.95 ), light=shade( GRANITE, 1.25 ) )   # the ball
    mane = shade( GRANITE, 0.78 )
    c.ellipse( 14, 22, 9.5, 9, mane, light=shade( mane, 1.25 ), dark=shade( mane, 0.7 ) )   # the mane
    for a in range( 0, 360, 30 ):                                       # its tight curls
        x = 14 + 8 * math.cos( math.radians( a ) )
        y = 22 + 7.5 * math.sin( math.radians( a ) )
        c.ellipse( x, y, 1.3, 1.3, shade( mane, 1.2 ) )
        c.px( int( x ), int( y ), shade( mane, 0.6 ) )
    c.ellipse( 14, 24, 5.5, 5, GRANITE, light=shade( GRANITE, 1.3 ) )  # the face
    c.rect( 11, 19, 13, 20, shade( GRANITE, 0.55 ) )                    # heavy brows
    c.rect( 15, 19, 17, 20, shade( GRANITE, 0.55 ) )
    c.px( 12, 21, rgb( '#2a2826' ) )                                    # eyes
    c.px( 16, 21, rgb( '#2a2826' ) )
    c.rect( 13, 23, 15, 24, shade( GRANITE, 0.7 ) )                    # broad nose
    c.rect( 12, 26, 16, 27, shade( GRANITE, 0.45 ) )                    # mouth
    c.px( 14, 26, rgb( '#e8e4dc' ) )                                    # the loose pebble
    c.line( 5, 41, 11, 43, shade( GRANITE, 0.7 ) )                      # ribbon on the ball
    c.noise( 4, 13, 27, 60, [ shade( GRANITE, 0.8 ), shade( GRANITE, 1.15 ) ], 0.08 )
    finish( c )


@sprite( 'f_sgn_tuong_than', 32, 64 )
def tuong_than( c ):
    # a smoke-darkened judge of the Jade Emperor's court: red face, black beard,
    # green and gold robes, a tablet held before the chest
    ground_shadow( c, 16, 60, 11, 3 )
    c.rect( 6, 52, 25, 60, rgb( '#4a3424' ) )                           # dark wood plinth
    c.rect( 6, 52, 25, 53, rgb( '#6a4a34' ) )
    robe = rgb( '#2a6a44' )
    c.polygon( [ ( 8, 52 ), ( 24, 52 ), ( 22, 24 ), ( 10, 24 ) ], robe )
    c.line( 16, 26, 16, 51, GOLD )                                      # gold robe trim
    c.line( 10, 40, 22, 40, GOLD )
    c.rect( 7, 25, 10, 38, shade( robe, 0.8 ) )                         # sleeves
    c.rect( 22, 25, 25, 38, shade( robe, 0.8 ) )
    c.rect( 14, 28, 18, 38, rgb( '#e8dcc0' ) )                          # the ivory tablet
    c.ellipse( 16, 17, 5, 6, rgb( '#b8382a' ), light=rgb( '#d85a40' ) )   # red face
    c.rect( 13, 20, 19, 27, rgb( '#16120e' ) )                          # long black beard
    c.px( 14, 16, rgb( '#f4f0e0' ) )
    c.px( 18, 16, rgb( '#f4f0e0' ) )
    c.rect( 10, 7, 22, 11, rgb( '#1e1a16' ) )                           # official's hat
    c.rect( 7, 9, 25, 10, rgb( '#1e1a16' ) )                            # its wings
    c.px( 16, 8, GOLD )
    c.noise( 6, 7, 25, 52, [ rgb( '#1a1612', 120 ) ], 0.12 )           # a century of smoke
    finish( c )


# --- Chợ Bình Tây -----------------------------------------------------------------------------
@sprite( 'f_sgn_bao_gao', 32, 64 )
def bao_gao( c ):
    # woven plastic rice sacks stacked on a pallet, printed bands and stitched tops
    ground_shadow( c, 16, 60, 14, 3 )
    c.rect( 2, 56, 29, 60, rgb( '#8a6a40' ) )                           # pallet
    for x in range( 4, 29, 6 ):
        c.rect( x, 58, x + 2, 60, rgb( '#5a4428' ) )
    sack = rgb( '#e6e2d6' )
    for row, y in enumerate( ( 45, 35, 25 ) ):
        for x0 in ( ( 2, 16 ) if row % 2 == 0 else ( 6, ) ):
            w = 13 if row % 2 == 0 else 19
            c.rect( x0, y, x0 + w, y + 10, sack )
            c.line( x0, y, x0 + w, y, shade( sack, 1.08 ) )
            c.line( x0, y + 10, x0 + w, y + 10, shade( sack, 0.7 ) )
            c.rect( x0 + 1, y + 4, x0 + w - 1, y + 6, rgb( '#2a5ab0' ) if row != 1 else rgb( '#c03030' ) )
            for x in range( x0 + 1, x0 + w, 2 ):                         # stitched top
                c.px( x, y + 1, shade( sack, 0.6 ) )
    c.noise( 2, 25, 29, 55, [ shade( sack, 0.88 ) ], 0.12 )             # the weave
    finish( c )


@sprite( 'f_sgn_ho_rong', 32, 32 )
def ho_rong( c ):
    # a tiled pond in the market courtyard, a coiled ceramic dragon, koi under the leaves
    rim = rgb( '#3a8a8a' )
    c.rect( 1, 3, 30, 29, rim )
    c.rect( 1, 3, 30, 4, shade( rim, 1.35 ) )
    c.rect( 3, 6, 28, 27, rgb( '#3a5a3a' ) )                            # murky water
    c.noise( 3, 6, 28, 27, [ rgb( '#4a7048' ), rgb( '#2e4a30' ) ], 0.2, only_opaque=True )
    for x, y in ( ( 7, 22 ), ( 23, 9 ) ):                               # koi
        c.ellipse( x, y, 2, 1, rgb( '#f07a2a' ) )
    for _ in range( 7 ):                                                 # floating leaves
        c.px( c.rand.randint( 4, 27 ), c.rand.randint( 7, 26 ), rgb( '#8a7a2a' ) )
    green, gold = rgb( '#3aa05a' ), rgb( '#e0c040' )
    prev = None
    for i in range( 26 ):                                                # the coiled body
        t = i / 25
        a = t * 2.4 * math.pi
        p = ( 16 + 6 * math.cos( a ) * ( 1 - t * 0.4 ), 17 + 4 * math.sin( a ) * ( 1 - t * 0.4 ) - t * 6 )
        if prev:
            c.capsule( prev[0], prev[1], p[0], p[1], 1.6, mix( green, gold, ( i % 3 ) / 6 ) )
        prev = p
    c.ellipse( prev[0], prev[1] - 1, 2.4, 2, rgb( '#d83a2a' ) )         # the head
    c.px( int( prev[0] ), int( prev[1] ) - 2, rgb( '#f4f0e0' ) )
    finish( c, alpha=50 )
