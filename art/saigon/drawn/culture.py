"""Media and festival items (unit V3): 20x20 item icons.
Definitions in data/mods/saigon_2000s/items/gear/culture.json.
"""
import math

from draw import sprite, rgb, shade

OUTLINE = 0.38
RED = rgb( '#d02828' )
GOLD = rgb( '#f0c030' )


def finish( c ):
    c.outline( OUTLINE )
    c.drop_shadow( 1, 1, 90 )


@sprite( 'sgn_truyen_meo_may', 20, 20 )
def truyen_meo_may( c ):
    # a thin comic with a blue round robot-cat face on the cover
    c.rect( 4, 3, 15, 17, rgb( '#f4f0e0' ) )
    c.rect( 4, 3, 15, 5, rgb( '#e83030' ) )                            # title band
    c.ellipse( 9.5, 11, 4, 3.8, rgb( '#3a9ae0' ) )                      # the cat's head
    c.ellipse( 9.5, 12, 2.8, 2.4, rgb( '#ffffff' ) )                    # face
    c.px( 9, 12, rgb( '#e83030' ) )                                     # nose
    c.line( 8, 14, 11, 14, rgb( '#1a1a1a' ) )
    c.rect( 7, 15, 12, 15, rgb( '#e83030' ) )                           # collar
    c.px( 9, 16, GOLD )                                                  # bell
    finish( c )


@sprite( 'sgn_vcd_phim_bo', 20, 20 )
def vcd_phim_bo( c ):
    # a stack of discs in paper sleeves, the top one bare and iridescent
    for i, y in enumerate( ( 15, 13, 11 ) ):
        c.ellipse( 10, y, 7, 2.6, shade( rgb( '#e8e0cc' ), 1 - i * 0.05 ) )   # sleeves
    c.ellipse( 10, 9, 7, 2.6, rgb( '#c8d0dc' ) )
    for k, col in enumerate( ( '#e080c0', '#80c0f0', '#a0f0a0', '#f0e080' ) ):
        c.px( 5 + k * 3, 9 - ( k % 2 ), rgb( col ) )
    c.ellipse( 10, 9, 1.2, 0.6, rgb( '#5a5a60' ) )                      # centre hole
    finish( c )


@sprite( 'sgn_bang_cassette', 20, 20 )
def bang_cassette( c ):
    # a cassette with a handwritten yellow label and two reels
    c.rect( 3, 6, 16, 14, rgb( '#3a3a40' ) )
    c.rect( 4, 7, 15, 10, rgb( '#f0d860' ) )                            # label
    c.line( 5, 8, 13, 8, rgb( '#3a2a8a' ) )                             # handwriting
    for x in ( 7, 12 ):                                                 # reels
        c.ellipse( x, 12, 1.5, 1.2, rgb( '#e8e8e8' ) )
        c.px( x, 12, rgb( '#3a3a40' ) )
    c.rect( 6, 13, 13, 14, rgb( '#5a5a60' ) )
    finish( c )


@sprite( 'sgn_lich_bloc', 20, 20 )
def lich_bloc( c ):
    # a fat tear-off block on a card printed with a pagoda roof
    c.rect( 4, 2, 15, 7, RED )                                          # the card
    c.polygon( [ ( 6, 6 ), ( 13, 6 ), ( 11, 4 ), ( 8, 4 ) ], GOLD )      # pagoda roof
    c.rect( 5, 7, 14, 17, rgb( '#f8f6f0' ) )                            # the block
    c.rect( 5, 15, 14, 17, shade( rgb( '#f8f6f0' ), 0.8 ) )
    c.rect( 7, 9, 12, 12, RED )                                         # the big day number
    c.rect( 8, 10, 11, 11, rgb( '#f8f6f0' ) )
    c.line( 6, 14, 13, 14, rgb( '#7a7a80' ) )
    finish( c )


@sprite( 'sgn_bao_li_xi', 20, 20 )
def bao_li_xi( c ):
    # a red envelope with a gold character and a note peeking out
    c.rect( 5, 6, 14, 16, RED )
    c.rect( 5, 6, 14, 7, shade( RED, 1.2 ) )
    c.rect( 7, 3, 12, 6, rgb( '#7ac08a' ) )                             # a green đồng note
    c.ellipse( 9.5, 11, 2.6, 2.6, GOLD )
    c.rect( 8, 10, 11, 12, shade( GOLD, 0.6 ) )                         # the character
    c.px( 9, 11, GOLD )
    finish( c )


@sprite( 'sgn_vang_ma', 20, 20 )
def vang_ma( c ):
    # a bundle of gold-foiled votive squares and a Bank of Hell note, tied with red string
    for i, ( x, y ) in enumerate( ( ( 4, 9 ), ( 6, 7 ), ( 8, 9 ) ) ):
        c.rect( x, y, x + 8, y + 7, rgb( '#e8d8a8' ) )
        c.rect( x + 2, y + 2, x + 6, y + 5, GOLD if i != 1 else rgb( '#d8b030' ) )
    c.rect( 9, 4, 17, 8, rgb( '#c85a5a' ) )                             # hell bank note
    c.rect( 11, 5, 15, 7, rgb( '#e8c8a0' ) )
    c.line( 3, 13, 17, 12, RED )                                        # string
    finish( c )


@sprite( 'sgn_long_den_ong_sao', 20, 20 )
def long_den_ong_sao( c ):
    # a five-pointed red cellophane star lantern on a stick
    pts = []
    for k in range( 10 ):
        a = math.radians( -90 + k * 36 )
        r = 7 if k % 2 == 0 else 3
        pts.append( ( 10 + r * math.cos( a ), 9 + r * math.sin( a ) ) )
    c.polygon( pts, RED )
    c.ellipse( 10, 9, 2, 2, rgb( '#f8d060' ) )                          # the candle glow
    c.line( 10, 14, 15, 19, rgb( '#c8a660' ) )                          # stick
    for p in pts[::2]:                                                  # tassels
        c.px( p[0], p[1], GOLD )
    finish( c )


@sprite( 'sgn_banh_trung_thu', 20, 20 )
def banh_trung_thu( c ):
    # a golden mooncake with a stamped pattern, a wedge cut to show the yolk
    c.ellipse( 10, 12, 7, 4, rgb( '#b8742a' ) )                         # side
    c.ellipse( 10, 10, 7, 3.6, rgb( '#e0a050' ), light=rgb( '#f0c070' ) )
    c.ring( 10, 10, 4.5, 2.2, rgb( '#b8742a' ), 1 )                     # stamped ring
    c.px( 10, 10, rgb( '#b8742a' ) )
    c.polygon( [ ( 10, 10 ), ( 17, 10 ), ( 16, 13 ) ], rgb( '#c8a070' ) )   # the cut wedge
    c.ellipse( 14, 11, 1.2, 1, rgb( '#f0a020' ) )                       # salted yolk
    finish( c )
