"""Saigon street food, fruit and money: 20x20 item icons (UltimateCataclysm small.png style).

Objects sit low in the 20x20 cell with a soft dark outline and a one-pixel shadow line
underneath, lit from the top left, like the original item icons.
"""
from draw import sprite, rgb, shade

OUTLINE = 0.38
WHITE_CERAMIC = rgb( '#eef0ea' )
PORCELAIN_BLUE = rgb( '#3d6fb0' )
CRUST = rgb( '#d79a45' )
CRUST_LIGHT = rgb( '#f2c677' )
CRUST_DARK = rgb( '#a3642a' )


def finish( c, shadow=True ):
    c.outline( OUTLINE )
    if shadow:
        c.drop_shadow( 1, 1, 90 )


def plate( c, cx=10, cy=12, rx=8, ry=4 ):
    c.ellipse( cx, cy + 1, rx, ry, shade( WHITE_CERAMIC, 0.78 ) )
    c.ellipse( cx, cy, rx, ry, WHITE_CERAMIC )
    c.ring( cx, cy, rx, ry, rgb( '#ffffff' ), 1 )


def baguette( c, filled ):
    c.capsule( 3.5, 14.5, 15.5, 5.5, 3.0, CRUST_DARK, 2.6 )
    c.capsule( 3, 14, 15, 5, 2.7, CRUST, 2.3 )
    c.capsule( 3, 13, 14, 5, 1.0, CRUST_LIGHT, 0.8 )
    if filled:
        # the split: pâté, cold pork, pickled carrot and daikon, cucumber, cilantro
        filling = [ rgb( '#8a4b32' ), rgb( '#e8a3a0' ), rgb( '#f08a2c' ), rgb( '#f4f0d8' ), rgb( '#4f9a3a' ),
                    rgb( '#e8a3a0' ), rgb( '#3f8a2e' ), rgb( '#f08a2c' ) ]
        for i, colour in enumerate( filling ):
            t = ( i + 1 ) / ( len( filling ) + 1 )
            x, y = 3 + 12 * t, 14 - 9 * t
            c.px( x + 1, y - 1, colour )
            c.px( x + 1, y, shade( colour, 0.8 ) )
        c.px( 9, 7, rgb( '#5fb048' ) )  # cilantro sprig poking out
        c.px( 12, 5, rgb( '#5fb048' ) )
    else:
        for x, y in ( ( 5, 12 ), ( 8, 10 ), ( 11, 8 ) ):  # baker's scoring
            c.line( x, y, x + 1, y - 1, CRUST_LIGHT )
            c.px( x + 1, y, CRUST_DARK )


@sprite( 'sgn_pho_bo', 20, 20 )
def pho( c ):
    # white porcelain bowl with a blue band, seen from the front and above
    c.polygon( [ ( 2, 9 ), ( 18, 9 ), ( 15, 16 ), ( 5, 16 ) ], WHITE_CERAMIC )
    c.polygon( [ ( 12, 9 ), ( 18, 9 ), ( 15, 16 ), ( 12, 16 ) ], shade( WHITE_CERAMIC, 0.85 ) )
    c.line( 3, 12, 17, 12, PORCELAIN_BLUE )
    c.line( 4, 13, 16, 13, shade( PORCELAIN_BLUE, 0.8 ) )
    c.rect( 7, 16, 13, 17, shade( WHITE_CERAMIC, 0.75 ) )
    # broth surface with noodles, beef and herbs
    c.ellipse( 10, 9, 8, 3.2, rgb( '#f7f5ee' ) )
    c.ellipse( 10, 9, 7, 2.4, rgb( '#c88a3e' ) )
    for x, y in ( ( 5, 9 ), ( 6, 8 ), ( 8, 10 ), ( 13, 8 ), ( 14, 10 ), ( 11, 10 ) ):
        c.line( x, y, x + 2, y, rgb( '#f3ead2' ) )
    for x, y in ( ( 8, 8 ), ( 12, 9 ) ):
        c.rect( x, y, x + 1, y, rgb( '#a8564a' ) )
        c.px( x, y + 1, rgb( '#8a3f36' ) )
    for x, y in ( ( 6, 10 ), ( 10, 8 ), ( 14, 9 ), ( 11, 7 ) ):
        c.px( x, y, rgb( '#4fae3c' ) )
    c.px( 15, 8, rgb( '#d23b2a' ) )  # chili slice
    finish( c )


@sprite( 'sgn_banh_mi_thit', 20, 20 )
def banh_mi_thit( c ):
    baguette( c, True )
    finish( c )


@sprite( 'sgn_banh_mi_bread', 20, 20 )
def banh_mi_bread( c ):
    baguette( c, False )
    finish( c )


@sprite( 'sgn_com_tam', 20, 20 )
def com_tam( c ):
    plate( c )
    # broken rice mound
    c.ellipse( 7, 11, 4, 2.6, rgb( '#f6f2e4' ) )
    c.noise( 4, 9, 10, 13, [ rgb( '#e2dcc6' ), rgb( '#fffdf4' ) ], 0.35 )
    c.px( 6, 10, rgb( '#5fb048' ) )  # scallion oil
    c.px( 8, 11, rgb( '#5fb048' ) )
    # grilled pork chop with char marks
    c.ellipse( 13, 11, 3.6, 2.2, rgb( '#b8653a' ) )
    c.line( 11, 12, 14, 9, rgb( '#6e3a22' ) )
    c.line( 13, 13, 16, 10, rgb( '#6e3a22' ) )
    c.px( 12, 10, rgb( '#e09a5c' ) )
    # cucumber and tomato slices
    c.px( 4, 13, rgb( '#7cc35a' ) )
    c.px( 5, 14, rgb( '#7cc35a' ) )
    c.px( 15, 14, rgb( '#d8402e' ) )
    finish( c )


@sprite( 'sgn_banh_chung', 20, 20 )
def banh_chung( c ):
    # a square slice: leaf-green rind, sticky rice, mung bean, fatty pork
    c.polygon( [ ( 4, 8 ), ( 14, 8 ), ( 16, 6 ), ( 6, 6 ) ], rgb( '#6a9a42' ) )      # top edge (leaf)
    c.polygon( [ ( 14, 8 ), ( 16, 6 ), ( 16, 14 ), ( 14, 16 ) ], rgb( '#3f6f2a' ) )   # side (leaf)
    c.rect( 4, 8, 13, 15, rgb( '#cfe0a4' ) )                                         # green-tinted rice
    c.rect( 4, 8, 13, 8, rgb( '#5c8e36' ) )
    c.rect( 6, 10, 11, 13, rgb( '#e8c45a' ) )                                        # mung bean
    c.rect( 8, 11, 9, 12, rgb( '#c47a62' ) )                                         # pork
    c.px( 8, 11, rgb( '#f2e6d6' ) )                                                  # fat
    c.noise( 4, 9, 13, 15, [ rgb( '#e4eec4' ), rgb( '#bcd28e' ) ], 0.2 )
    finish( c )


@sprite( 'sgn_mi_goi', 20, 20 )
def mi_goi( c ):
    # cellophane packet: red-orange with a yellow band and a bowl of noodles printed on it
    c.rect( 3, 6, 16, 15, rgb( '#d8402a' ) )
    c.rect( 3, 6, 16, 6, rgb( '#f06a48' ) )
    c.rect( 3, 11, 16, 12, rgb( '#f2c230' ) )
    for x in ( 3, 16 ):  # crimped seams
        for y in range( 6, 16, 2 ):
            c.px( x, y, rgb( '#f7a088' ) )
    c.ellipse( 9, 9, 3, 1.6, rgb( '#f4e2a4' ) )
    c.line( 7, 9, 11, 9, rgb( '#d8a84c' ) )
    c.px( 13, 8, rgb( '#ffffff' ) )
    c.px( 14, 8, rgb( '#ffffff' ) )
    c.line( 5, 14, 14, 14, rgb( '#a82a1c' ) )
    finish( c )


@sprite( 'sgn_banh_pho', 20, 20 )
def banh_pho( c ):
    # a sealed bag of dry flat rice sticks
    c.rect( 4, 6, 15, 15, rgb( '#dfe6ec' ) )
    for x in range( 5, 15, 2 ):
        c.line( x, 7, x, 14, rgb( '#fbf8ee' ) )
        c.line( x + 1, 7, x + 1, 14, rgb( '#e6e0cc' ) )
    c.rect( 4, 6, 15, 7, rgb( '#c8d2da' ) )
    c.rect( 7, 10, 12, 11, rgb( '#2f74c0' ) )  # printed label
    c.px( 4, 6, rgb( '#ffffff' ) )
    finish( c )


@sprite( 'sgn_rau_muong', 20, 20 )
def rau_muong( c ):
    # a bunch of water spinach: hollow stems tied with red raffia, arrow leaves on top
    for dx in range( 0, 5 ):
        c.line( 3 + dx, 17, 11 + dx, 6, rgb( '#7fb04a' ) if dx % 2 else rgb( '#9cc862' ) )
    for x, y in ( ( 11, 5 ), ( 14, 6 ), ( 12, 3 ), ( 16, 4 ), ( 9, 6 ) ):
        c.polygon( [ ( x, y ), ( x + 4, y - 1 ), ( x + 2, y + 2 ) ], rgb( '#3f8a2e' ) )
        c.px( x + 1, y, rgb( '#5fb048' ) )
    c.line( 5, 12, 9, 15, rgb( '#d0302a' ) )
    finish( c )


@sprite( 'sgn_durian', 20, 20 )
def durian( c ):
    # a wedge of spiky green husk holding custard-yellow pods
    c.polygon( [ ( 2, 15 ), ( 17, 15 ), ( 14, 8 ), ( 5, 8 ) ], rgb( '#7a8a3a' ) )
    for x in range( 3, 17, 2 ):
        c.px( x, 16, rgb( '#5a6a2a' ) )
        c.px( x + 1, 15, rgb( '#9aa84a' ) )
    c.rect( 4, 9, 15, 11, rgb( '#f4f0d0' ) )  # white pith
    for cx in ( 6.5, 10, 13.5 ):
        c.ellipse( cx, 9, 2.2, 2.4, rgb( '#f2cf52' ), light=rgb( '#fbe89a' ), dark=rgb( '#d2a83a' ) )
    finish( c )


@sprite( 'sgn_mit', 20, 20 )
def mit( c ):
    # waxy golden jackfruit pods
    for cx, cy in ( ( 6, 12 ), ( 10, 10 ), ( 14, 12 ), ( 9, 14 ) ):
        c.ellipse( cx, cy, 2.6, 2.0, rgb( '#f0a92c' ), light=rgb( '#ffd36a' ), dark=rgb( '#c47a18' ) )
        c.px( cx - 1, cy - 1, rgb( '#fff0b0' ) )
    finish( c )


@sprite( 'sgn_thanh_long', 20, 20 )
def thanh_long( c ):
    # whole magenta dragon fruit with green-tipped scales, and a cut half
    c.ellipse( 8, 10, 5, 4, rgb( '#d8317a' ), light=rgb( '#f25c9e' ), dark=rgb( '#a01e58' ) )
    for x, y in ( ( 4, 8 ), ( 8, 6 ), ( 11, 8 ), ( 6, 12 ), ( 10, 12 ), ( 3, 11 ), ( 12, 10 ) ):
        c.px( x, y, rgb( '#e8508e' ) )
        c.px( x + 1, y - 1, rgb( '#7cb84a' ) )
    c.ellipse( 14, 13, 3.6, 3.0, rgb( '#c02868' ) )
    c.ellipse( 14, 13, 2.8, 2.2, rgb( '#f7f4ee' ) )
    for x, y in ( ( 13, 12 ), ( 15, 13 ), ( 13, 14 ) ):
        c.px( x, y, rgb( '#3a3a3a' ) )
    finish( c )


def note( c, base, dark, light, ox, oy ):
    c.rect( ox, oy, ox + 12, oy + 5, base )
    c.frame( ox, oy, ox + 12, oy + 5, dark )
    c.ellipse( ox + 9.5, oy + 3, 1.6, 1.8, light )      # watermark portrait window
    c.px( ox + 9, oy + 3, dark )
    c.line( ox + 2, oy + 2, ox + 6, oy + 2, light )    # value numerals
    c.line( ox + 2, oy + 3, ox + 4, oy + 3, light )


def notes( c, base, dark, light ):
    note( c, shade( base, 0.82 ), dark, light, 5, 7 )
    note( c, base, dark, light, 3, 10 )
    finish( c )


@sprite( 'sgn_dong_10k', 20, 20 )
def dong_10k( c ):
    notes( c, rgb( '#b58a52' ), rgb( '#6e4e28' ), rgb( '#e2c48e' ) )


@sprite( 'sgn_dong_50k', 20, 20 )
def dong_50k( c ):
    notes( c, rgb( '#d0668e' ), rgb( '#7e2a4e' ), rgb( '#f4b4cc' ) )


@sprite( 'sgn_dong_100k', 20, 20 )
def dong_100k( c ):
    notes( c, rgb( '#5f9a5c' ), rgb( '#2e5a30' ), rgb( '#a8d4a0' ) )


@sprite( 'sgn_vang_chi', 20, 20 )
def vang_chi( c ):
    # one chỉ of gold leaf in a red gold-shop packet
    c.rect( 5, 8, 14, 15, rgb( '#c8282a' ) )
    c.rect( 5, 8, 14, 8, rgb( '#e8484a' ) )
    c.rect( 7, 10, 12, 13, rgb( '#f2c232' ) )
    c.rect( 7, 10, 9, 11, rgb( '#ffe68a' ) )
    c.px( 11, 13, rgb( '#b88a18' ) )
    c.ring( 10, 11.5, 1.6, 1.6, rgb( '#b88a18' ) )  # shop stamp
    finish( c )


@sprite( 'dry_rice', 20, 20 )
def dry_rice( c ):
    # a woven polypropylene rice sack, folded open at the top to show the grain
    c.polygon( [ ( 4, 7 ), ( 16, 7 ), ( 17, 17 ), ( 3, 17 ) ], rgb( '#eceae0' ) )
    for y in range( 8, 17, 2 ):
        c.line( 4, y, 16, y, rgb( '#d8d4c4' ) )                     # weave
    c.rect( 6, 11, 14, 14, rgb( '#2f8a4a' ) )                       # printed label
    c.rect( 8, 12, 12, 12, rgb( '#f2c232' ) )
    c.ellipse( 10, 6.5, 6, 2, rgb( '#f8f6ee' ) )                    # open top: rice
    c.noise( 5, 5, 15, 8, [ rgb( '#e4e0d0' ), rgb( '#ffffff' ) ], 0.4 )
    finish( c )


# --- dda items the Saigon content uses that UltimateCataclysm has no sprite for (review R8) ---

@sprite( 'noodles_fast', 20, 20 )
def noodles_fast( c ):
    # a dry brick of instant noodles, wavy strands on top
    c.rect( 4, 8, 15, 15, rgb( '#e8b85a' ) )
    c.rect( 4, 8, 15, 9, rgb( '#f4d48a' ) )
    for y in range( 10, 15, 2 ):
        for x in range( 4, 16, 3 ):
            c.line( x, y, x + 1, y + 1, rgb( '#c8903a' ) )
    finish( c )


@sprite( 'pickle', 20, 20 )
def pickle( c ):
    # a small pickled gherkin, bumpy skin
    c.capsule( 5, 13, 14, 8, 2.6, rgb( '#6a8a2a' ) )
    c.capsule( 5, 12, 13, 8, 1.2, rgb( '#9ab84a' ) )
    for x, y in ( ( 7, 13 ), ( 10, 11 ), ( 12, 10 ), ( 8, 10 ) ):
        c.px( x, y, rgb( '#4a6a1a' ) )
    finish( c )
