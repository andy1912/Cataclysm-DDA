"""L4: Thảo Cầm Viên, Đầm Sen and Suối Tiên (asset unit A7).  Definitions in
data/mods/saigon_2000s/monsters/zoo.json and furniture/parks.json.

Animals follow UltimateCataclysm's monster sprites: side view facing right, feet on the
bottom rows, soft outline, no drop shadow.  Big animals are 64x64 (large.png, offset
-16,-32) like mon_tiger / mon_moose; small ones 32x32.  Park pieces are furniture: the
Ferris wheel is 96x96 and the giant statue 64x96, both rooted in the bottom-centre cell.
"""
import math

from draw import sprite, rgb, shade, mix

OUTLINE = 0.42


def finish( c, shadow=( 2, 2 ), alpha=70 ):
    c.outline( OUTLINE )
    c.drop_shadow( shadow[0], shadow[1], alpha )


def ground_shadow( c, cx, cy, rx, ry ):
    c.ellipse( cx + 3, cy, rx, ry, ( 0, 0, 0, 70 ) )


# --- animals ----------------------------------------------------------------------------------
@sprite( 'sgn_mon_voi', 64, 64 )
def voi( c ):
    # an Asian elephant: high rounded back, small ears, trunk curling, short tusks, red dust
    skin = rgb( '#7a7470' )
    for x in ( 18, 26, 40, 47 ):                                        # legs, far pair darker
        k = 0.72 if x in ( 26, 47 ) else 1.0
        c.rect( x, 40, x + 6, 61, shade( skin, k ) )
        c.rect( x, 60, x + 6, 61, shade( skin, 0.5 * k + 0.4 ) )          # toenails
    c.ellipse( 33, 34, 20, 15, skin, light=shade( skin, 1.25 ), dark=shade( skin, 0.7 ) )   # body
    c.ellipse( 30, 23, 12, 6, shade( skin, 1.08 ) )                     # the high back
    c.ellipse( 51, 30, 9, 10, skin, light=shade( skin, 1.2 ), dark=shade( skin, 0.75 ) )    # head
    c.ellipse( 46, 31, 6, 8, shade( skin, 0.62 ), light=shade( skin, 0.8 ) )   # the ear, in shadow
    c.ellipse( 55, 21, 4, 3, shade( skin, 1.15 ) )                      # twin domes of the skull
    prev = ( 57, 34 )                                                   # the trunk
    for i in range( 1, 12 ):
        t = i / 11
        p = ( 58 + 2 * math.sin( t * 2.4 ), 34 + 22 * t - ( 6 * t * t if t > 0.8 else 0 ) )
        c.capsule( prev[0], prev[1], p[0], p[1], 3.6 - 1.8 * t, shade( skin, 1.05 ) )
        prev = p
    c.line( 55, 38, 59, 41, rgb( '#ece4d0' ) )                          # short tusk
    c.px( 54, 28, rgb( '#1a1612' ) )                                    # eye
    c.line( 13, 30, 10, 42, shade( skin, 0.7 ) )                        # tail
    for y in range( 26, 46, 4 ):                                        # skin wrinkles
        c.line( 22, y, 40, y + 1, shade( skin, 0.85 ) )
    c.noise( 12, 18, 62, 61, [ rgb( '#a0644a', 90 ) ], 0.06 )          # red dust
    c.outline( OUTLINE )


@sprite( 'sgn_mon_ca_sau', 64, 64 )
def ca_sau( c ):
    # a Siamese crocodile low on the ground: tapering tail, scute ridges, long snout
    hide = rgb( '#5a6a3a' )
    prev = ( 4, 52 )
    for i in range( 1, 30 ):                                            # body and tail, one taper
        t = i / 29
        p = ( 4 + 50 * t, 52 - 2 * math.sin( t * math.pi ) )
        c.capsule( prev[0], prev[1], p[0], p[1], 0.8 + 5.2 * math.sin( min( t, 0.75 ) / 0.75 * math.pi / 2 ),
                   mix( hide, shade( hide, 1.25 ), t * 0.3 ) )
        prev = p
    c.polygon( [ ( 50, 47 ), ( 63, 51 ), ( 63, 54 ), ( 50, 56 ) ], shade( hide, 1.05 ) )   # snout
    c.line( 52, 52, 63, 53, rgb( '#2a2c18' ) )                          # the jaw line
    for x in range( 54, 63, 2 ):                                        # teeth
        c.px( x, 52, rgb( '#e8e0c8' ) )
    c.px( 50, 47, rgb( '#d8c040' ) )                                    # eye
    for x in ( 18, 38 ):                                                # splayed legs
        c.line( x, 54, x - 3, 59, shade( hide, 0.8 ) )
        c.line( x + 4, 54, x + 6, 59, shade( hide, 0.7 ) )
    for x in range( 8, 48, 3 ):                                         # scute ridges
        c.px( x, 47 - int( 2 * math.sin( x / 50 * math.pi ) ), shade( hide, 0.6 ) )
    c.line( 14, 55, 46, 55, rgb( '#a8a070' ) )                          # pale belly
    c.outline( OUTLINE )


@sprite( 'sgn_mon_khi', 32, 32 )
def khi( c ):
    # a long-tailed macaque on all fours, tail arched over, pale face
    fur = rgb( '#8a7454' )
    prev = ( 9, 19 )                                                    # the tail
    for i in range( 1, 10 ):
        t = i / 9
        p = ( 9 - 6 * math.sin( t * 2.2 ), 19 - 13 * t + 6 * t * t )
        c.line( prev[0], prev[1], p[0], p[1], shade( fur, 0.85 ) )
        prev = p
    for x in ( 11, 14, 20, 23 ):
        c.rect( x, 22, x + 1, 28, shade( fur, 0.8 if x in ( 14, 23 ) else 1.0 ) )
    c.ellipse( 17, 20, 8, 4.5, fur, light=shade( fur, 1.25 ), dark=shade( fur, 0.75 ) )
    c.ellipse( 25, 16, 4, 4, fur, light=shade( fur, 1.2 ) )
    c.ellipse( 26.5, 17, 2.2, 2.4, rgb( '#d8b49a' ) )                   # the pale face
    c.px( 27, 16, rgb( '#1a1410' ) )
    c.outline( OUTLINE )


@sprite( 'sgn_mon_tran', 32, 32 )
def tran( c ):
    # a coiled reticulated python, gold with a black net pattern, head raised
    gold = rgb( '#c8a040' )
    for r, y in ( ( 10, 25 ), ( 7.5, 22 ), ( 5, 19 ) ):                # the coils
        c.ellipse( 16, y, r, r * 0.45, gold, light=shade( gold, 1.25 ), dark=shade( gold, 0.7 ) )
        c.ring( 16, y, r - 1.5, r * 0.45 - 0.8, rgb( '#2a2010' ), 1 )
    c.capsule( 18, 18, 23, 11, 2, gold )                                # the neck
    c.ellipse( 24.5, 10, 3, 2, shade( gold, 1.1 ) )                     # head
    c.px( 25, 9, rgb( '#1a1410' ) )
    for _ in range( 12 ):                                               # the net pattern
        c.px( 16 + c.rand.randint( -9, 9 ), 22 + c.rand.randint( -4, 4 ), rgb( '#3a2a10' ) )
    c.outline( OUTLINE )


# --- park furniture ---------------------------------------------------------------------------
@sprite( 't_sgn_hoa_sen', 32, 32 )
def hoa_sen( c ):
    # shallow green water crowded with lotus leaves, a pink flower and a seed head
    c.rect( 0, 0, 31, 31, rgb( '#3a6a5a' ) )
    c.noise( 0, 0, 31, 31, [ rgb( '#4a7a6a' ), rgb( '#2e5a4a' ) ], 0.2 )
    leaf = rgb( '#4a9a3a' )
    for cx, cy, r in ( ( 7, 7, 5 ), ( 22, 5, 4 ), ( 25, 18, 5.5 ), ( 9, 22, 6 ), ( 17, 28, 3.5 ) ):
        c.ellipse( cx, cy, r, r * 0.8, leaf, light=shade( leaf, 1.25 ), dark=shade( leaf, 0.7 ) )
        c.line( cx, cy, cx + r * 0.7, cy - r * 0.5, shade( leaf, 0.6 ) )       # the notch
        c.px( int( cx ), int( cy ), shade( leaf, 1.4 ) )
    c.ellipse( 16, 13, 2.6, 2.2, rgb( '#f0a0c0' ), light=rgb( '#ffd0e0' ) )  # the flower
    c.px( 16, 12, rgb( '#f8e080' ) )
    c.ellipse( 4, 14, 1.5, 1.2, rgb( '#a8b060' ) )                      # a seed head


@sprite( 'f_sgn_thuyen_thien_nga', 32, 32 )
def thien_nga( c ):
    # a white fibreglass swan pedal boat, long neck, orange beak, a canopy seat behind
    ground_shadow( c, 15, 27, 12, 2.5 )
    white = rgb( '#f2f0ea' )
    c.ellipse( 14, 22, 11, 5, white, light=rgb( '#ffffff' ), dark=rgb( '#c8c4bc' ) )   # hull
    c.ellipse( 9, 18, 6, 3.5, shade( white, 0.92 ) )                    # folded wing
    c.capsule( 22, 21, 23, 9, 1.8, white )                              # the neck
    c.ellipse( 24, 8, 2.6, 2, white )
    c.polygon( [ ( 26, 7 ), ( 30, 9 ), ( 26, 10 ) ], rgb( '#f08a20' ) )   # beak
    c.px( 24, 7, rgb( '#1a1612' ) )
    c.rect( 11, 14, 16, 15, rgb( '#3a7ac8' ) )                          # seat canopy
    c.line( 4, 26, 25, 26, rgb( '#a0b8c0' ) )                           # waterline
    finish( c, alpha=45 )


@sprite( 'f_sgn_vong_quay', 96, 96 )
def vong_quay( c ):
    # the big wheel: white rim and spokes, coloured gondolas, an A-frame down to its base
    cx, cy, r = 48, 40, 34
    steel = rgb( '#e8ecf0' )
    for side in ( -1, 1 ):                                              # A-frame legs
        c.line( cx, cy, cx + side * 14, 93, rgb( '#b8c0c8' ) )
        c.line( cx + side, cy, cx + side * 15, 93, rgb( '#98a0a8' ) )
    for k in range( 16 ):                                               # spokes
        a = k / 16 * 2 * math.pi
        c.line( cx, cy, cx + r * math.cos( a ), cy + r * math.sin( a ), rgb( '#c8d0d8' ) )
    c.ring( cx, cy, r, r, steel, 2 )
    c.ring( cx, cy, r - 4, r - 4, rgb( '#c8d0d8' ), 1 )
    c.ellipse( cx, cy, 4, 4, rgb( '#8a9098' ) )                         # hub
    colours = [ '#e04040', '#f0c020', '#3a8ae0', '#40b060', '#e070c0', '#f08a20', '#40c8c8', '#a060e0' ]
    for k in range( 8 ):                                                # gondolas hang below the rim
        a = k / 8 * 2 * math.pi + 0.2
        gx, gy = cx + r * math.cos( a ), cy + r * math.sin( a )
        c.line( gx, gy, gx, gy + 3, rgb( '#606870' ) )
        c.rect( gx - 3, gy + 3, gx + 3, gy + 8, rgb( colours[k] ) )
        c.rect( gx - 2, gy + 4, gx + 2, gy + 5, rgb( '#c8e0f0' ) )
    c.rect( 34, 88, 62, 94, rgb( '#7a7a80' ) )                          # the boarding platform
    finish( c )


@sprite( 'f_sgn_tuong_khong_lo', 64, 96 )
def tuong_khong_lo( c ):
    # Lạc Long Quân towering over the beach: crowned dragon lord in scaled green-gold robes,
    # arms spread over the sea, standing on a rock where the waterfall poured
    ground_shadow( c, 32, 92, 22, 3 )
    rock = rgb( '#8a8478' )
    c.polygon( [ ( 6, 94 ), ( 58, 94 ), ( 52, 72 ), ( 12, 72 ) ], rock )          # the rock
    c.noise( 6, 72, 58, 94, [ shade( rock, 0.7 ), shade( rock, 1.2 ) ], 0.25 )
    c.rect( 26, 76, 37, 93, rgb( '#7ab8e0', 160 ) )                     # the dry waterfall's stain
    robe = rgb( '#2e8a5a' )
    c.polygon( [ ( 20, 74 ), ( 44, 74 ), ( 39, 30 ), ( 25, 30 ) ], robe )
    for y in range( 34, 74, 4 ):                                        # dragon scales
        for x in range( 24, 41, 3 ):
            c.px( x + ( y // 4 ) % 2, y, rgb( '#e0c040' ) )
    c.line( 32, 30, 32, 74, rgb( '#e0c040' ) )
    c.polygon( [ ( 25, 32 ), ( 6, 24 ), ( 8, 28 ), ( 25, 38 ) ], robe )        # arms spread
    c.polygon( [ ( 39, 32 ), ( 58, 24 ), ( 56, 28 ), ( 39, 38 ) ], robe )
    c.ellipse( 6, 25, 2.5, 2.5, rgb( '#d8a878' ) )
    c.ellipse( 58, 25, 2.5, 2.5, rgb( '#d8a878' ) )
    c.ellipse( 32, 22, 6, 7, rgb( '#d8a878' ), light=rgb( '#e8c098' ) )   # face
    c.rect( 28, 26, 36, 31, rgb( '#2a1a10' ) )                          # beard
    c.px( 30, 21, rgb( '#1a1410' ) )
    c.px( 34, 21, rgb( '#1a1410' ) )
    c.polygon( [ ( 24, 15 ), ( 40, 15 ), ( 38, 6 ), ( 32, 10 ), ( 26, 6 ) ], rgb( '#e0c040' ) )   # crown
    c.px( 32, 12, rgb( '#d02020' ) )
    finish( c )


@sprite( 'f_sgn_ky_lan', 32, 64 )
def ky_lan( c ):
    # a gaudy gate guardian: gold scaled body sitting on a plinth, green mane, red open jaws
    ground_shadow( c, 16, 60, 11, 2.5 )
    c.rect( 5, 50, 26, 60, rgb( '#c84030' ) )                           # red plinth
    c.rect( 5, 50, 26, 52, rgb( '#e05a40' ) )
    gold = rgb( '#e0b030' )
    c.ellipse( 16, 40, 9, 10, gold, light=shade( gold, 1.25 ), dark=shade( gold, 0.7 ) )
    c.rect( 10, 40, 14, 50, gold )                                      # forelegs
    for y in range( 34, 48, 3 ):
        for x in range( 10, 23, 3 ):
            c.px( x + ( y // 3 ) % 2, y, shade( gold, 0.7 ) )
    mane = rgb( '#2e9a5a' )
    for a in range( 0, 360, 36 ):                                       # a ring of curled mane tufts
        x = 14 + 8 * math.cos( math.radians( a ) )
        y = 25 + 7 * math.sin( math.radians( a ) )
        c.ellipse( x, y, 2.4, 2.4, mane, light=shade( mane, 1.3 ) )
    c.rect( 7, 20, 19, 31, gold )                                       # the square lion head
    c.rect( 7, 20, 19, 21, shade( gold, 1.25 ) )
    for x in ( 10, 16 ):                                                # bulging eyes
        c.ellipse( x, 23, 2, 1.8, rgb( '#ffffff' ) )
        c.px( x, 23, rgb( '#1a1410' ) )
    c.rect( 8, 26, 18, 30, rgb( '#d02020' ) )                           # wide open red jaws
    for x in range( 9, 18, 2 ):
        c.px( x, 26, rgb( '#ffffff' ) )                                 # teeth
    c.ellipse( 13, 25, 1.6, 1, shade( gold, 0.6 ) )                     # the nose
    c.line( 13, 19, 13, 13, rgb( '#f0e0a0' ) )                          # the single horn
    c.line( 24, 44, 28, 36, rgb( '#2e9a5a' ) )                          # flame tail
    finish( c )


@sprite( 'f_sgn_rong_lon', 64, 64 )
def rong_lon( c ):
    # a concrete dragon's coils rising and dipping through the garden, blue with orange spines
    ground_shadow( c, 32, 60, 28, 3 )
    blue, orange = rgb( '#3a7ae0' ), rgb( '#f08a20' )
    pts = [ ( 2 + 2 * i, 58 - 14 * abs( math.sin( i / 26 * 2.5 * math.pi ) ) ) for i in range( 27 ) ]
    for a, b in zip( pts, pts[1:] ):
        c.capsule( a[0], a[1], b[0], b[1], 3.6, blue )
    for a in pts[::2]:
        c.polygon( [ ( a[0] - 1.5, a[1] - 3 ), ( a[0] + 1.5, a[1] - 3 ), ( a[0], a[1] - 7 ) ], orange )   # spines
        c.px( int( a[0] ), int( a[1] ) + 2, rgb( '#f0d060' ) )          # belly scales
    hx, hy = 56, 34                                                     # the raised head
    c.capsule( pts[-1][0], pts[-1][1], hx, hy + 4, 3.4, blue )
    c.ellipse( hx, hy, 6, 5, blue, light=shade( blue, 1.3 ) )
    c.polygon( [ ( hx + 3, hy ), ( 63, hy + 2 ), ( hx + 3, hy + 4 ) ], rgb( '#d02020' ) )   # open jaws
    c.line( hx - 2, hy - 4, hx - 6, hy - 10, orange )                   # horns
    c.line( hx, hy - 4, hx + 1, hy - 11, orange )
    c.line( hx + 4, hy + 4, hx + 8, hy + 10, rgb( '#f0d060' ) )         # whiskers
    c.px( hx + 1, hy - 1, rgb( '#ffffff' ) )
    finish( c )
