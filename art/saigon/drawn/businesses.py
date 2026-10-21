"""Shophouse businesses (unit P1): furniture for the tailor, the herbalist, the photocopy
shop and the quán nhậu.  Definitions in data/mods/saigon_2000s/furniture/businesses.json.
3/4 view, light from the top left, soft outline and shadow, like UltimateCataclysm.
"""
from draw import sprite, rgb, shade

OUTLINE = 0.42


def finish( c ):
    c.outline( OUTLINE )
    c.drop_shadow( 2, 2, 70 )


def ground_shadow( c, cx, cy, rx, ry ):
    c.ellipse( cx + 3, cy, rx, ry, ( 0, 0, 0, 70 ) )


@sprite( 'f_sgn_may_may', 32, 32 )
def may_may( c ):
    # a black cast-iron sewing machine with gold lettering on a wooden top and iron treadle
    ground_shadow( c, 16, 29, 12, 2.5 )
    iron = rgb( '#2a2a2e' )
    c.rect( 5, 18, 7, 29, iron )                                        # treadle legs
    c.rect( 24, 18, 26, 29, iron )
    c.rect( 7, 26, 24, 27, iron )                                       # the treadle
    c.rect( 3, 15, 28, 18, rgb( '#8a5a32' ) )                           # wooden top
    c.rect( 3, 15, 28, 15, rgb( '#a87448' ) )
    c.rect( 8, 7, 22, 9, iron )                                         # the arm
    c.rect( 20, 7, 23, 15, iron )                                       # the pillar
    c.rect( 7, 9, 9, 13, iron )                                         # needle head
    c.line( 8, 13, 8, 15, rgb( '#c8c8cc' ) )                            # needle
    c.line( 11, 8, 18, 8, rgb( '#e0b030' ) )                            # gold lettering
    c.ellipse( 24.5, 10, 2.5, 2.5, rgb( '#5a5a60' ) )                   # hand wheel
    c.px( 14, 6, rgb( '#e8e8e0' ) )                                     # thread spool
    finish( c )


@sprite( 'f_sgn_tu_thuoc_bac', 32, 64 )
def tu_thuoc_bac( c ):
    # a tall wall of small labelled wooden drawers with brass pulls, jars on top
    ground_shadow( c, 16, 61, 14, 2.5 )
    wood = rgb( '#7a4a28' )
    c.rect( 2, 14, 29, 60, wood )
    c.rect( 2, 14, 29, 15, shade( wood, 1.25 ) )
    for row in range( 8 ):
        for col in range( 4 ):
            x0, y0 = 4 + col * 6, 17 + row * 5
            c.rect( x0, y0, x0 + 4, y0 + 3, shade( wood, 1.12 ) )
            c.px( x0 + 2, y0 + 1, rgb( '#d8b048' ) )                    # brass pull
            c.px( x0 + 1, y0, rgb( '#f0e8d0' ) )                        # paper label
    for x, col in ( ( 6, '#c8a070' ), ( 14, '#5a7a4a' ), ( 22, '#a85a3a' ) ):   # jars on top
        c.ellipse( x, 10, 3, 4, rgb( col ), light=shade( rgb( col ), 1.25 ) )
        c.rect( x - 2, 5, x + 2, 6, rgb( '#d02020' ) )
    finish( c )


@sprite( 'f_sgn_may_photo', 32, 32 )
def may_photo( c ):
    # a big beige photocopier with a lid, paper trays and a green start button
    ground_shadow( c, 16, 29, 13, 2.5 )
    beige = rgb( '#d8d0bc' )
    c.rect( 4, 9, 27, 28, beige )
    c.rect( 4, 9, 27, 12, shade( beige, 1.1 ) )                         # lid
    c.rect( 4, 13, 27, 13, rgb( '#5a5a60' ) )                           # glass edge
    for y in ( 18, 23 ):                                                # paper trays
        c.rect( 6, y, 25, y + 3, shade( beige, 0.88 ) )
        c.rect( 13, y + 1, 18, y + 1, rgb( '#5a5a60' ) )
    c.rect( 20, 14, 25, 16, rgb( '#3a3a40' ) )                          # control panel
    c.px( 24, 15, rgb( '#40c060' ) )                                    # start button
    c.rect( 0, 15, 4, 17, rgb( '#f4f4f0' ) )                            # copies sticking out
    finish( c )


@sprite( 'f_sgn_bep_nuong', 32, 32 )
def bep_nuong( c ):
    # a squat clay charcoal grill with a wire grate and something grilling
    ground_shadow( c, 16, 28, 11, 2.5 )
    clay = rgb( '#b46a3a' )
    c.polygon( [ ( 6, 14 ), ( 26, 14 ), ( 23, 28 ), ( 9, 28 ) ], clay )
    c.polygon( [ ( 18, 14 ), ( 26, 14 ), ( 23, 28 ), ( 18, 28 ) ], shade( clay, 0.8 ) )
    c.rect( 13, 21, 18, 25, rgb( '#2a1a10' ) )                          # draught hole
    c.px( 15, 23, rgb( '#ff6a20' ) )
    c.ellipse( 16, 14, 10, 3, rgb( '#3a2a20' ) )                        # coals
    for x in range( 8, 25, 3 ):
        c.px( x, 14, rgb( '#ff8a30' ) )
    for x in range( 7, 26, 2 ):                                         # wire grate
        c.line( x, 12, x, 15, rgb( '#9a9aa0' ) )
    c.rect( 10, 11, 14, 12, rgb( '#e8c8a0' ) )                          # squid
    c.rect( 17, 11, 21, 12, rgb( '#a85a2a' ) )                          # ribs
    finish( c )
