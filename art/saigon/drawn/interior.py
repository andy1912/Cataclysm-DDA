"""Shophouse interior (G21): patterned cement floors, glazed tiles, Thần Tài shrine,
water jar, hammock, CRT TV and potted plants.

Floors repeat a 16x16 motif 2x2 so they tile seamlessly across a room; furniture is
32x32 in UltimateCataclysm's 3/4 view with a soft outline and shadow.
"""
import math

from draw import sprite, rgb

OUTLINE = 0.42


def finish( c ):
    c.outline( OUTLINE )
    c.drop_shadow( 2, 2, 70 )


def gach_bong( c, motif ):
    """Repeat a 16x16 cement-tile motif over the 32x32 cell."""
    for ox in ( 0, 16 ):
        for oy in ( 0, 16 ):
            motif( c, ox, oy )
            c.line( ox, oy + 15, ox + 15, oy + 15, rgb( '#8a8478' ) )   # grout
            c.line( ox + 15, oy, ox + 15, oy + 15, rgb( '#8a8478' ) )
    # worn and muted, so items lying on the floor still read
    c.rect( 0, 0, 31, 31, rgb( '#d8d0bc', 70 ) )
    c.noise( 0, 0, 31, 31, [ rgb( '#000000', 24 ) ], 0.2 )


@sprite( 't_sgn_gach_bong_1', 32, 32 )
def gach_bong_flower( c ):
    def motif( c, x, y ):
        c.rect( x, y, x + 14, y + 14, rgb( '#e8dcc0' ) )
        for dx, dy in ( ( 0, -4 ), ( 4, 0 ), ( 0, 4 ), ( -4, 0 ) ):
            c.ellipse( x + 7.5 + dx, y + 7.5 + dy, 2.6, 2.6, rgb( '#b8462e' ) )
        c.ellipse( x + 7.5, y + 7.5, 1.8, 1.8, rgb( '#e0a02a' ) )
        for cx, cy in ( ( 0, 0 ), ( 15, 0 ), ( 0, 15 ), ( 15, 15 ) ):    # quarter-circles meet at corners
            c.ellipse( x + cx, y + cy, 3, 3, rgb( '#3f6a5a' ) )
    gach_bong( c, motif )


@sprite( 't_sgn_gach_bong_2', 32, 32 )
def gach_bong_star( c ):
    def motif( c, x, y ):
        c.rect( x, y, x + 14, y + 14, rgb( '#ece6d6' ) )
        cx, cy = x + 7.5, y + 7.5
        pts = []
        for k in range( 16 ):
            r = 6.5 if k % 2 == 0 else 3
            a = k * math.pi / 8
            pts.append( ( cx + r * math.cos( a ), cy + r * math.sin( a ) ) )
        c.polygon( pts, rgb( '#2f5a9a' ) )
        c.ellipse( cx, cy, 1.6, 1.6, rgb( '#ece6d6' ) )
        c.frame( x, y, x + 14, y + 14, rgb( '#2f5a9a' ) )
    gach_bong( c, motif )


@sprite( 't_sgn_gach_bong_3', 32, 32 )
def gach_bong_trellis( c ):
    def motif( c, x, y ):
        c.rect( x, y, x + 14, y + 14, rgb( '#e6e2d0' ) )
        for cx, cy in ( ( 7.5, 0 ), ( 7.5, 15 ), ( 0, 7.5 ), ( 15, 7.5 ) ):
            c.ring( x + cx, y + cy, 7, 7, rgb( '#4a7a4a' ), 1.2 )
        c.ellipse( x + 7.5, y + 7.5, 1.4, 1.4, rgb( '#c8462e' ) )
    gach_bong( c, motif )


@sprite( 't_sgn_gach_bong_4', 32, 32 )
def gach_bong_wave( c ):
    def motif( c, x, y ):
        c.rect( x, y, x + 14, y + 14, rgb( '#b8b4aa' ) )
        for k in range( 4 ):
            c.ring( x + 7.5, y + 7.5, 7 - k * 1.6, 7 - k * 1.6, rgb( '#8a867c' ) if k % 2 else rgb( '#d8d4ca' ), 0.9 )
        c.ellipse( x + 7.5, y + 7.5, 2.2, 2.2, rgb( '#e0b22a' ) )
    gach_bong( c, motif )


@sprite( 't_sgn_gach_men', 32, 32 )
def gach_men( c ):
    # one big beige glazed tile per cell, faint marble veins and a glossy highlight
    c.rect( 0, 0, 31, 31, rgb( '#e6dcc8' ) )
    for _ in range( 3 ):
        x, y = c.rand.uniform( 0, 31 ), c.rand.uniform( 0, 31 )
        for _ in range( 8 ):
            nx, ny = x + c.rand.uniform( -4, 4 ), y + c.rand.uniform( 1, 4 )
            c.line( x, y, nx, ny, rgb( '#d0c4ac' ) )
            x, y = nx, ny
    c.line( 3, 3, 12, 3, rgb( '#f6f0e4' ) )
    c.line( 0, 31, 31, 31, rgb( '#b8ae98' ) )
    c.line( 31, 0, 31, 31, rgb( '#b8ae98' ) )


@sprite( 'f_sgn_ban_tho_than_tai', 32, 32 )
def than_tai( c ):
    # small red floor shrine: a jolly figure, incense cup, bananas, a beer can
    c.rect( 7, 14, 25, 27, rgb( '#b82024' ) )
    c.rect( 7, 14, 25, 15, rgb( '#e8484a' ) )
    c.rect( 8, 16, 24, 26, rgb( '#7a1a1a' ) )                     # alcove
    c.ellipse( 12, 21, 2.6, 3, rgb( '#f2c88a' ) )                  # Ông Địa, round belly
    c.ellipse( 12, 18, 1.6, 1.6, rgb( '#f2c88a' ) )
    c.ellipse( 19, 21, 2.2, 2.8, rgb( '#e8b830' ) )                # Thần Tài in gold
    c.rect( 14, 24, 17, 26, rgb( '#c89a3a' ) )                     # incense cup
    for x in ( 15, 16 ):
        c.line( x, 19, x, 24, rgb( '#d02a2a' ) )
    c.capsule( 21, 25, 24, 24, 0.8, rgb( '#f2d24a' ) )             # bananas
    c.rect( 9, 24, 10, 26, rgb( '#d8dce0' ) )                      # beer can
    c.rect( 7, 11, 25, 13, rgb( '#f2c232' ) )                      # gilded top board
    finish( c )


@sprite( 'f_sgn_lu_nuoc', 32, 32 )
def lu_nuoc( c ):
    # glazed brown earthenware jar with a dragon band, open top with water and a dipper
    glaze = rgb( '#6e4024' )
    c.ellipse( 16, 19, 11, 10, glaze, light=rgb( '#9a6038' ), dark=rgb( '#4a2814' ) )
    c.ellipse( 16, 9, 8, 3, rgb( '#5a3418' ) )                     # rim
    c.ellipse( 16, 9, 6.5, 2.2, rgb( '#4a7a9a' ) )                 # water
    c.ellipse( 14, 9, 2, 1, rgb( '#2f74c0' ) )                     # floating dipper
    c.line( 15, 9, 20, 7, rgb( '#2f74c0' ) )
    for k in range( 9 ):                                           # dragon band
        x = 7 + k * 2.2
        c.px( x, 18 + ( 1 if k % 2 else -1 ), rgb( '#c8a048' ) )
        c.px( x + 1, 18, rgb( '#c8a048' ) )
    finish( c )


@sprite( 'f_sgn_vong', 32, 32 )
def vong( c ):
    # a knotted nylon hammock slung diagonally between two wall hooks
    c.rect( 2, 4, 4, 6, rgb( '#7a8288' ) )
    c.rect( 27, 25, 29, 27, rgb( '#7a8288' ) )
    for k in range( -3, 4 ):                                       # the sagging net
        c.line( 4, 5, 15 + k * 1.5, 16 - k * 1.5, rgb( '#3f9a5a' ) )
        c.line( 15 + k * 1.5, 16 - k * 1.5, 28, 26, rgb( '#3f9a5a' ) )
    for t in ( 0.35, 0.5, 0.65 ):                                  # cross knots
        x, y = 4 + 24 * t, 5 + 21 * t
        c.line( x - 4, y + 3, x + 3, y - 4, rgb( '#7ac88a' ) )
    c.outline( OUTLINE )
    c.drop_shadow( 3, 3, 50 )


@sprite( 'f_sgn_tivi_crt', 32, 32 )
def tivi_crt( c ):
    # boxy CRT on a lace-covered wooden cabinet, rabbit-ear antenna
    c.rect( 5, 21, 27, 29, rgb( '#7a4a2a' ) )                      # cabinet
    c.rect( 5, 21, 27, 22, rgb( '#f4f0e6' ) )                      # lace runner
    c.rect( 7, 8, 25, 21, rgb( '#3a3c40' ) )                       # TV body
    c.rect( 9, 10, 21, 19, rgb( '#5a8aa0' ) )                      # screen
    c.line( 10, 11, 14, 11, rgb( '#a8d0e0' ) )
    c.rect( 22, 11, 24, 12, rgb( '#9aa0a4' ) )                     # knobs
    c.rect( 22, 15, 24, 16, rgb( '#9aa0a4' ) )
    c.line( 15, 8, 10, 1, rgb( '#c8ccd0' ) )                       # antenna
    c.line( 17, 8, 23, 2, rgb( '#c8ccd0' ) )
    finish( c )


@sprite( 'f_sgn_chau_kieng', 32, 32 )
def chau_kieng( c ):
    # glazed blue-and-white pot with a kumquat bush hung with little orange fruit
    c.polygon( [ ( 9, 20 ), ( 23, 20 ), ( 21, 29 ), ( 11, 29 ) ], rgb( '#2f5a9a' ) )
    c.line( 10, 22, 22, 22, rgb( '#e8eef4' ) )
    c.line( 11, 26, 21, 26, rgb( '#e8eef4' ) )
    c.rect( 8, 19, 24, 20, rgb( '#4a7ac0' ) )
    for cx, cy, r in ( ( 16, 12, 7 ), ( 11, 15, 4 ), ( 21, 15, 4 ) ):
        c.ellipse( cx, cy, r, r * 0.85, rgb( '#2f6a2a' ), light=rgb( '#5a9a3a' ), dark=rgb( '#1f4a1c' ) )
    for _ in range( 9 ):
        x, y = 16 + c.rand.uniform( -8, 8 ), 13 + c.rand.uniform( -5, 4 )
        if c.opaque( int( x ), int( y ) ):
            c.ellipse( x, y, 1.1, 1.1, rgb( '#f08a1a' ) )
    finish( c )
