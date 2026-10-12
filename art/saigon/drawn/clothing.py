"""Clothing icons (G26): garments laid flat, 20x20, auto-fitted to the UltimateCataclysm
budget.  Worn sprites are derived recolours of the dda garments (derive_recipes.json)."""
from draw import sprite, rgb, shade

OUTLINE = 0.38


def finish( c ):
    c.outline( OUTLINE )
    c.drop_shadow( 1, 1, 90 )


def ao_dai( c, silk, trim, trousers ):
    # long fitted tunic with high collar and side slits over loose trousers
    c.polygon( [ ( 7, 2 ), ( 13, 2 ), ( 16, 6 ), ( 14, 7 ), ( 14, 18 ), ( 6, 18 ), ( 6, 7 ), ( 4, 6 ) ], silk )
    c.rect( 9, 1, 11, 2, trim )                                    # mandarin collar
    c.line( 10, 3, 13, 5, trim )                                   # diagonal closure
    c.line( 6, 12, 6, 18, trousers )                               # trousers showing at the slits
    c.line( 14, 12, 14, 18, trousers )
    c.line( 7, 7, 7, 17, shade( silk, 1.15 ) )
    finish( c )


@sprite( 'sgn_ao_dai_trang', 20, 20 )
def ao_dai_trang( c ):
    ao_dai( c, rgb( '#f6f6f2' ), rgb( '#d8dcd8' ), rgb( '#e8ece8' ) )


@sprite( 'sgn_ao_dai_mau', 20, 20 )
def ao_dai_mau( c ):
    ao_dai( c, rgb( '#c8262a' ), rgb( '#f2c232' ), rgb( '#f4f0e8' ) )
    c.px( 10, 9, rgb( '#f2c232' ) )                               # embroidered phoenix glints
    c.px( 9, 12, rgb( '#f2c232' ) )
    c.px( 11, 14, rgb( '#f2c232' ) )


@sprite( 'sgn_ao_khoac_chong_nang', 20, 20 )
def ao_khoac( c ):
    # pastel hooded jacket with long sleeves, hood and a peak
    body = rgb( '#f4a8c4' )
    c.polygon( [ ( 6, 5 ), ( 14, 5 ), ( 18, 13 ), ( 16, 14 ), ( 14, 9 ), ( 14, 16 ), ( 6, 16 ), ( 6, 9 ), ( 4, 14 ), ( 2, 13 ) ], body )
    c.ellipse( 10, 4, 3.5, 2.6, shade( body, 0.9 ) )              # hood
    c.line( 8, 2, 12, 2, rgb( '#f8d0e0' ) )                       # peak
    c.line( 10, 6, 10, 16, rgb( '#d8d8d8' ) )                     # zip
    finish( c )


@sprite( 'sgn_dep_lao', 20, 20 )
def dep_lao( c ):
    # a pair of thick brown rubber sandals: toe strap and heel strap
    for ox, oy in ( ( 3, 5 ), ( 11, 6 ) ):
        c.ellipse( ox + 3, oy + 2.5, 2.8, 2.8, rgb( '#6a4a2a' ) )
        c.ellipse( ox + 3, oy + 7.5, 2.6, 3.6, rgb( '#6a4a2a' ) )
        c.rect( ox + 1, oy + 2, ox + 5, oy + 7, rgb( '#6a4a2a' ) )
        c.line( ox, oy + 3, ox + 6, oy + 3, rgb( '#3a2a1a' ) )     # toe strap
        c.line( ox + 1, oy + 9, ox + 5, oy + 9, rgb( '#3a2a1a' ) ) # heel strap
    finish( c )


def shirt( c, cloth, pocket, tabs=None ):
    c.polygon( [ ( 6, 3 ), ( 14, 3 ), ( 18, 8 ), ( 15, 9 ), ( 15, 17 ), ( 5, 17 ), ( 5, 9 ), ( 2, 8 ) ], cloth )
    c.polygon( [ ( 8, 3 ), ( 12, 3 ), ( 10, 6 ) ], shade( cloth, 0.75 ) )   # open collar
    c.line( 10, 6, 10, 17, shade( cloth, 0.8 ) )
    c.rect( 6, 8, 8, 10, pocket )
    if tabs:
        c.rect( 7, 3, 8, 4, tabs )
        c.rect( 12, 3, 13, 4, tabs )
    finish( c )


@sprite( 'sgn_ao_cong_an', 20, 20 )
def ao_cong_an( c ):
    shirt( c, rgb( '#d8c068' ), rgb( '#c8aa50' ), tabs=rgb( '#c8262a' ) )


@sprite( 'sgn_ao_trang_hoc_sinh', 20, 20 )
def ao_trang( c ):
    shirt( c, rgb( '#f6f6f4' ), rgb( '#e0e4e8' ) )
    c.line( 6, 9, 8, 9, rgb( '#2f5aa8' ) )                        # embroidered school name


@sprite( 'sgn_quan_cong_an', 20, 20 )
def quan_cong_an( c ):
    # olive trousers laid flat
    c.polygon( [ ( 5, 3 ), ( 15, 3 ), ( 16, 17 ), ( 11, 17 ), ( 10, 8 ), ( 9, 17 ), ( 4, 17 ) ], rgb( '#5a7a3a' ) )
    c.rect( 5, 3, 15, 4, rgb( '#3f5a2a' ) )                       # waistband
    c.line( 7, 5, 6, 16, rgb( '#7a9a52' ) )
    finish( c )
