"""Street dishes, dried goods, work gear and trade goods (G25): 20x20 icons, auto-fitted to
the UltimateCataclysm budget, plus the worn shoulder pole (32x36 overlays)."""
from draw import sprite, rgb, shade

OUTLINE = 0.38
BAMBOO = rgb( '#c8a860' )
WICKER = rgb( '#a87a42' )


def finish( c ):
    c.outline( OUTLINE )
    c.drop_shadow( 1, 1, 90 )


@sprite( 'sgn_hu_tieu', 20, 20 )
def hu_tieu( c ):
    c.polygon( [ ( 2, 9 ), ( 18, 9 ), ( 15, 16 ), ( 5, 16 ) ], rgb( '#f2f0e8' ) )
    c.line( 3, 12, 17, 12, rgb( '#c8262a' ) )                      # red rim band
    c.ellipse( 10, 9, 8, 3.2, rgb( '#f7f5ee' ) )
    c.ellipse( 10, 9, 7, 2.4, rgb( '#d8a050' ) )                   # sweet broth
    for x, y in ( ( 6, 9 ), ( 13, 8 ) ):
        c.rect( x, y, x + 1, y, rgb( '#f08a6a' ) )                 # shrimp
    c.px( 9, 8, rgb( '#f2f0e8' ) )                                 # quail egg
    c.px( 11, 10, rgb( '#4fae3c' ) )
    finish( c )


@sprite( 'sgn_banh_xeo', 20, 20 )
def banh_xeo( c ):
    c.ellipse( 10, 11, 7, 4, rgb( '#f2c232' ), light=rgb( '#fbe27a' ), dark=rgb( '#c8961a' ) )
    c.line( 3, 11, 17, 11, rgb( '#d8a028' ) )                      # the fold
    for x in ( 6, 10, 14 ):
        c.px( x, 9, rgb( '#e8907a' ) )                             # shrimp peeking
    c.px( 8, 13, rgb( '#5fb048' ) )
    finish( c )


@sprite( 'sgn_goi_cuon', 20, 20 )
def goi_cuon( c ):
    for y in ( 8, 12 ):
        c.capsule( 4, y, 15, y, 1.8, rgb( '#eef0e8', 235 ) )
        c.px( 7, y, rgb( '#f08a6a' ) )
        c.px( 11, y, rgb( '#5fb048' ) )
        c.px( 13, y, rgb( '#f08a6a' ) )
    c.ellipse( 16, 15, 2, 1.4, rgb( '#8a5a2a' ) )                  # peanut dip
    finish( c )


@sprite( 'sgn_xoi', 20, 20 )
def xoi( c ):
    c.polygon( [ ( 3, 10 ), ( 16, 10 ), ( 14, 15 ), ( 5, 15 ) ], rgb( '#4f8a32' ) )   # banana leaf
    c.ellipse( 9.5, 10, 5.5, 2.6, rgb( '#f4f0e0' ) )
    c.noise( 5, 8, 14, 11, [ rgb( '#f2d24a' ), rgb( '#c8902a' ) ], 0.4 )             # mung bean, shallots
    finish( c )


@sprite( 'sgn_banh_bao', 20, 20 )
def banh_bao( c ):
    c.ellipse( 10, 11, 5.5, 4.5, rgb( '#f8f6f0' ), light=rgb( '#ffffff' ), dark=rgb( '#d8d4c8' ) )
    c.line( 10, 7, 10, 9, rgb( '#d8d4c8' ) )                       # pleated top
    c.line( 8, 8, 10, 9, rgb( '#d8d4c8' ) )
    c.line( 12, 8, 10, 9, rgb( '#d8d4c8' ) )
    c.rect( 7, 15, 13, 15, rgb( '#e8d8a0' ) )                      # paper base
    finish( c )


@sprite( 'sgn_kho_muc', 20, 20 )
def kho_muc( c ):
    c.polygon( [ ( 10, 3 ), ( 14, 7 ), ( 13, 12 ), ( 7, 12 ), ( 6, 7 ) ], rgb( '#e8b08a' ) )
    for x in range( 7, 14, 2 ):
        c.line( x, 12, x - 1 + ( x % 3 ), 17, rgb( '#c8805a' ) )    # tentacles
    c.line( 10, 4, 10, 11, rgb( '#f4d0b0' ) )
    finish( c )


@sprite( 'sgn_tom_kho', 20, 20 )
def tom_kho( c ):
    for cx, cy in ( ( 7, 11 ), ( 11, 10 ), ( 9, 13 ), ( 13, 13 ), ( 6, 14 ) ):
        c.ellipse( cx, cy, 2, 1.4, rgb( '#f08a4a' ), light=rgb( '#f8b07a' ) )
        c.px( cx - 2, cy, rgb( '#c85a2a' ) )
    finish( c )


@sprite( 'sgn_banh_trang', 20, 20 )
def banh_trang( c ):
    c.ellipse( 10, 11, 7, 4, rgb( '#f2eee0', 230 ) )
    for x in range( 4, 17, 2 ):
        c.line( x, 9, x, 13, rgb( '#e2dccc' ) )                    # bamboo-mat imprint
    c.line( 4, 11, 16, 11, rgb( '#e2dccc' ) )
    finish( c )


@sprite( 'sgn_xa_beng', 20, 20 )
def xa_beng( c ):
    c.line( 3, 17, 16, 3, rgb( '#4a4e52' ) )
    c.line( 4, 17, 17, 3, rgb( '#7a8288' ) )
    c.line( 16, 3, 18, 4, rgb( '#7a8288' ) )                       # flattened tip
    finish( c )


@sprite( 'sgn_quang_ganh', 20, 20 )
def quang_ganh( c ):
    c.line( 2, 6, 17, 6, BAMBOO )                                  # the pole
    for cx in ( 4, 15 ):
        c.line( cx - 2, 7, cx, 11, rgb( '#8a6a3a' ) )              # cords
        c.line( cx + 2, 7, cx, 11, rgb( '#8a6a3a' ) )
        c.ellipse( cx, 13, 3, 2.5, WICKER, light=rgb( '#c8a060' ) )
    finish( c )


@sprite( 'sgn_ro_nhua', 20, 20 )
def ro_nhua( c ):
    c.polygon( [ ( 3, 8 ), ( 16, 8 ), ( 14, 15 ), ( 5, 15 ) ], rgb( '#3faa5a' ) )
    for x in range( 5, 15, 2 ):
        for y in ( 10, 13 ):
            c.px( x, y, rgb( '#1f6a32' ) )                         # perforations
    c.rect( 3, 8, 16, 8, rgb( '#6ad08a' ) )
    finish( c )


@sprite( 'sgn_thau_nhua', 20, 20 )
def thau_nhua( c ):
    c.ellipse( 10, 12, 7, 3.5, rgb( '#c8262a' ) )
    c.ellipse( 10, 11, 7, 2.6, rgb( '#e84a4a' ) )
    c.ellipse( 10, 11.3, 5.5, 1.8, rgb( '#a81c1c' ) )             # inside
    finish( c )


@sprite( 'sgn_luoi_chai', 20, 20 )
def luoi_chai( c ):
    c.ellipse( 10, 11, 6, 4.5, rgb( '#d8dcd0', 160 ) )
    for k in range( -5, 6, 2 ):
        c.line( 10 + k, 7, 10 + k * 1.1, 15, rgb( '#a8ac9e' ) )
    for y in range( 8, 15, 2 ):
        c.line( 4, y, 16, y, rgb( '#a8ac9e' ) )
    for x in range( 4, 17, 3 ):
        c.px( x, 15, rgb( '#5a5e62' ) )                            # lead weights
    finish( c )


@sprite( 'sgn_ve_so', 20, 20 )
def ve_so( c ):
    c.rect( 3, 8, 16, 13, rgb( '#f4ecd8' ) )
    c.rect( 3, 8, 6, 13, rgb( '#d83a5a' ) )
    for x in range( 8, 16, 2 ):
        c.px( x, 10, rgb( '#2a2a2a' ) )                            # the numbers
        c.px( x, 12, rgb( '#2a2a2a' ) )
    finish( c )


@sprite( 'sgn_thuoc_la', 20, 20 )
def thuoc_la( c ):
    c.line( 4, 13, 15, 8, rgb( '#f4f2ee' ) )
    c.line( 4, 14, 15, 9, rgb( '#e8e4dc' ) )
    c.line( 4, 13, 6, 12, rgb( '#d89a4a' ) )                       # filter
    c.line( 4, 14, 6, 13, rgb( '#d89a4a' ) )
    finish( c )


@sprite( 'sgn_vang_luong', 20, 20 )
def vang_luong( c ):
    c.rect( 4, 8, 15, 15, rgb( '#c8262a' ) )
    c.rect( 4, 8, 15, 8, rgb( '#e8484a' ) )
    c.rect( 6, 10, 13, 13, rgb( '#f2c232' ) )
    c.rect( 6, 10, 9, 11, rgb( '#ffe68a' ) )
    c.ring( 11, 12, 1.4, 1.2, rgb( '#b88a18' ) )
    finish( c )


def ganh_worn( c, dy ):
    # bamboo pole across the right shoulder, a basket hanging at each end
    c.line( 2, 12 + dy, 30, 9 + dy, BAMBOO )
    c.line( 2, 13 + dy, 30, 10 + dy, shade( BAMBOO, 0.75 ) )
    for x in ( 4, 28 ):
        c.line( x - 2, 12 + dy, x, 22 + dy, rgb( '#8a6a3a' ) )
        c.line( x + 2, 12 + dy, x, 22 + dy, rgb( '#8a6a3a' ) )
        c.ellipse( x, 25 + dy, 3.5, 3, WICKER, light=rgb( '#c8a060' ) )
    c.outline( 0.4 )


@sprite( 'overlay_male_worn_sgn_quang_ganh', 32, 36 )
def ganh_male( c ):
    ganh_worn( c, 0 )


@sprite( 'overlay_female_worn_sgn_quang_ganh', 32, 36 )
def ganh_female( c ):
    ganh_worn( c, 1 )
