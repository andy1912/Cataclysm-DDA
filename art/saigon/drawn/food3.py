"""More Saigon street food (unit V1): 20x20 item icons in the style of food.py.
Definitions in data/mods/saigon_2000s/items/food/street_food_3.json.
"""
from draw import sprite, rgb, shade

OUTLINE = 0.38
CERAMIC = rgb( '#eef0ea' )
BLUE = rgb( '#3d6fb0' )
MELAMINE = rgb( '#e8dcb0' )


def finish( c ):
    c.outline( OUTLINE )
    c.drop_shadow( 1, 1, 90 )


def bowl( c, broth, band=BLUE ):
    """A porcelain soup bowl from the front, the broth surface showing."""
    c.polygon( [ ( 2, 9 ), ( 18, 9 ), ( 15, 16 ), ( 5, 16 ) ], CERAMIC )
    c.polygon( [ ( 12, 9 ), ( 18, 9 ), ( 15, 16 ), ( 12, 16 ) ], shade( CERAMIC, 0.85 ) )
    c.line( 3, 12, 17, 12, band )
    c.rect( 7, 16, 13, 17, shade( CERAMIC, 0.75 ) )
    c.ellipse( 10, 9, 8, 3.2, rgb( '#f7f5ee' ) )
    c.ellipse( 10, 9, 7, 2.4, broth )


def plate( c, colour=MELAMINE ):
    c.ellipse( 10, 14, 8.5, 3.6, shade( colour, 0.78 ) )
    c.ellipse( 10, 13, 8.5, 3.4, colour )


@sprite( 'sgn_hot_vit_lon', 20, 20 )
def hot_vit_lon( c ):
    # a warm duck egg in a little cup, top cracked open, salt and a rau răm sprig beside it
    c.polygon( [ ( 5, 12 ), ( 13, 12 ), ( 12, 17 ), ( 6, 17 ) ], rgb( '#d8d4cc' ) )   # egg cup
    c.ellipse( 9, 9, 3.8, 4.6, rgb( '#e8dcc4' ), light=rgb( '#f6eedc' ) )
    c.ellipse( 9, 6, 3, 1.4, rgb( '#c8a060' ) )                       # opened top: the yolk
    c.px( 8, 6, rgb( '#e8c060' ) )
    for x in range( 6, 13, 2 ):                                         # the cracked shell rim
        c.px( x, 5 + ( x % 4 ) // 2, rgb( '#fff8ec' ) )
    c.line( 14, 15, 17, 11, rgb( '#4f9a3a' ) )                         # rau răm
    c.px( 16, 11, rgb( '#7a3a5a' ) )
    c.ellipse( 15.5, 16, 1.6, 0.8, rgb( '#f4f4f0' ) )                   # salt and pepper
    finish( c )


@sprite( 'sgn_bun_bo_hue', 20, 20 )
def bun_bo_hue( c ):
    bowl( c, rgb( '#c8502a' ), band=rgb( '#b03a2a' ) )
    for x, y in ( ( 6, 9 ), ( 9, 8 ), ( 13, 9 ) ):                     # beef, pork knuckle, blood cube
        c.px( x, y, rgb( '#6a3a2a' ) )
    c.rect( 11, 9, 12, 10, rgb( '#5a1a1a' ) )
    c.px( 7, 10, rgb( '#f0e8d0' ) )                                     # round noodles
    c.px( 15, 8, rgb( '#5fb048' ) )
    c.px( 4, 9, rgb( '#e8a020' ) )                                      # chili oil
    finish( c )


@sprite( 'sgn_bun_thit_nuong', 20, 20 )
def bun_thit_nuong( c ):
    plate( c, rgb( '#f4f2ea' ) )
    c.ellipse( 8, 12, 4.5, 2.2, rgb( '#f6f2e6' ) )                      # vermicelli nest
    for x, y in ( ( 10, 11 ), ( 12, 12 ), ( 14, 11 ), ( 11, 13 ) ):      # charred grilled pork
        c.rect( x, y, x + 1, y, rgb( '#8a4a22' ) )
        c.px( x, y - 1, rgb( '#3a2010' ) )
    c.px( 5, 11, rgb( '#5fb048' ) )
    c.px( 6, 13, rgb( '#f08a2c' ) )                                     # pickled carrot
    c.px( 9, 11, rgb( '#d8b070' ) )                                     # peanuts
    c.ellipse( 16, 8, 2, 1.4, rgb( '#e0a050' ) )                        # little bowl of nước chấm
    finish( c )


@sprite( 'sgn_banh_cuon', 20, 20 )
def banh_cuon( c ):
    plate( c )
    for i, x in enumerate( ( 5, 9, 13 ) ):                              # three translucent rolls
        c.capsule( x - 1.5, 13 - i % 2, x + 1.5, 11 - i % 2, 1.8, rgb( '#f2eee4' ) )
        c.px( x, 12 - i % 2, rgb( '#c8b8a4' ) )                         # filling showing through
    for x in range( 4, 16, 3 ):                                         # fried shallots
        c.px( x, 10, rgb( '#c88a3a' ) )
    c.rect( 14, 13, 16, 14, rgb( '#e8c8b4' ) )                          # chả lụa slices
    finish( c )


@sprite( 'sgn_chao_long', 20, 20 )
def chao_long( c ):
    bowl( c, rgb( '#e8e0cc' ), band=rgb( '#7a8a96' ) )
    for x, y in ( ( 6, 9 ), ( 10, 8 ), ( 13, 9 ) ):                     # offal slices and blood pudding
        c.px( x, y, rgb( '#7a2a2a' ) )
    c.px( 8, 10, rgb( '#a87050' ) )
    c.line( 11, 10, 15, 6, rgb( '#e0b060' ) )                           # a fried dough stick
    c.px( 5, 8, rgb( '#5fb048' ) )
    finish( c )


@sprite( 'sgn_bo_bia', 20, 20 )
def bo_bia( c ):
    # a soft rice-paper roll, ends showing jicama and sausage, a dab of dark sauce
    c.capsule( 4, 13, 15, 8, 3.0, rgb( '#f0ece0' ) )
    c.capsule( 4, 13, 15, 8, 1.6, rgb( '#e8e0cc' ) )
    c.ellipse( 15, 8, 2.2, 2.2, rgb( '#f4f0e0' ) )                      # cut end
    c.px( 15, 8, rgb( '#c03030' ) )                                     # lạp xưởng
    c.px( 14, 7, rgb( '#f08a2c' ) )
    c.px( 16, 9, rgb( '#5fb048' ) )
    c.ellipse( 6, 16, 2.4, 1, rgb( '#5a2a1a' ) )                        # hoisin and peanut
    c.px( 6, 15, rgb( '#d8b070' ) )
    finish( c )


@sprite( 'sgn_banh_flan', 20, 20 )
def banh_flan( c ):
    plate( c, rgb( '#f4f2ea' ) )
    c.polygon( [ ( 6, 13 ), ( 14, 13 ), ( 13, 7 ), ( 7, 7 ) ], rgb( '#f0c860' ) )   # custard
    c.polygon( [ ( 11, 13 ), ( 14, 13 ), ( 13, 7 ), ( 11, 7 ) ], rgb( '#d8a840' ) )
    c.ellipse( 10, 7, 3, 1.2, rgb( '#7a3a10' ) )                        # caramel top
    c.px( 9, 7, rgb( '#a85a20' ) )
    for x in ( 5, 15 ):                                                 # crushed ice and coffee
        c.px( x, 12, rgb( '#dceef4' ) )
    c.line( 4, 14, 16, 14, rgb( '#5a3a22' ) )
    finish( c )


@sprite( 'sgn_sua_dau_nanh', 20, 20 )
def sua_dau_nanh( c ):
    # warm soy milk in a knotted plastic bag with a straw poking out
    c.ellipse( 10, 12, 5, 5, rgb( '#f2ecd8', 230 ), light=rgb( '#fffaf0' ) )
    c.polygon( [ ( 8, 7 ), ( 12, 7 ), ( 11, 5 ), ( 9, 5 ) ], rgb( '#f2ecd8', 230 ) )
    c.line( 8, 5, 12, 5, rgb( '#d02020' ) )                             # rubber band
    c.line( 11, 9, 14, 2, rgb( '#e04080' ) )                            # straw
    c.line( 7, 10, 7, 14, rgb( '#ffffff' ) )                            # shine on the bag
    finish( c )


@sprite( 'sgn_nuoc_dua', 20, 20 )
def nuoc_dua( c ):
    # a green coconut with its top hacked off and a straw stuck in
    c.ellipse( 10, 12, 6, 5.5, rgb( '#5a9a3a' ), light=rgb( '#7ab84a' ), dark=rgb( '#3a6a2a' ) )
    c.polygon( [ ( 7, 8 ), ( 13, 8 ), ( 12, 5 ), ( 8, 5 ) ], rgb( '#c8d890' ) )   # the cut white husk
    c.ellipse( 10, 5, 2, 0.8, rgb( '#f4f4e8' ) )
    c.line( 10, 5, 13, 1, rgb( '#f0f0f0' ) )                            # straw
    c.px( 13, 1, rgb( '#d02020' ) )
    finish( c )


@sprite( 'sgn_kho_bo', 20, 20 )
def kho_bo( c ):
    # a plastic bag of chewy red dried-beef strips with chili
    c.rect( 4, 5, 15, 16, rgb( '#f0f4f4', 120 ) )
    c.line( 4, 5, 15, 5, rgb( '#c8d0d0' ) )
    for i in range( 6 ):
        x = 5 + i * 2
        c.line( x, 15, x + 2, 7, rgb( '#a83a22' ) if i % 2 else rgb( '#c85030' ) )
    c.px( 8, 9, rgb( '#f02020' ) )
    c.px( 12, 12, rgb( '#f02020' ) )
    finish( c )


@sprite( 'sgn_lap_xuong', 20, 20 )
def lap_xuong( c ):
    # a pair of glossy red Chinese sausages tied with string
    for dx in ( 0, 4 ):
        c.capsule( 5 + dx, 16, 8 + dx, 5, 1.8, rgb( '#a82a2a' ) )
        c.line( 5 + dx, 14, 7 + dx, 6, rgb( '#d85a4a' ) )               # glossy fat
        c.px( 6 + dx, 10, rgb( '#f0e0d0' ) )
    c.line( 8, 4, 12, 4, rgb( '#e8e0c8' ) )                             # the string
    c.line( 10, 4, 10, 1, rgb( '#e8e0c8' ) )
    finish( c )


@sprite( 'sgn_mam_tom', 20, 20 )
def mam_tom( c ):
    # a squat glass jar of purple-grey shrimp paste with a red lid
    c.rect( 6, 7, 14, 16, rgb( '#8a7a86' ) )
    c.rect( 6, 7, 8, 16, rgb( '#a8989e' ) )
    c.rect( 5, 4, 15, 6, rgb( '#c83030' ) )
    c.rect( 7, 10, 13, 12, rgb( '#f0e8c0' ) )                           # label
    c.px( 9, 11, rgb( '#c83030' ) )
    c.px( 11, 11, rgb( '#c83030' ) )
    finish( c )
