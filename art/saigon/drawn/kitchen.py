"""Kitchen and drink items (G23): 20x20 icons, auto-fitted to the UltimateCataclysm budget."""
from draw import sprite, rgb, shade

OUTLINE = 0.38
ALU = rgb( '#c4ccd2' )


def finish( c ):
    c.outline( OUTLINE )
    c.drop_shadow( 1, 1, 90 )


@sprite( 'sgn_noi_com_dien', 20, 20 )
def noi_com_dien( c ):
    # white rice cooker: domed flowery lid, black handle, red "cook" light
    c.rect( 4, 9, 15, 16, rgb( '#eef0ec' ) )
    c.rect( 12, 9, 15, 16, rgb( '#d4d8d4' ) )
    c.ellipse( 9.5, 9, 6, 3, rgb( '#f8f8f4' ) )
    c.ellipse( 9.5, 8, 2, 1, rgb( '#e86a9a' ) )                 # printed flower
    c.rect( 8, 5, 11, 6, rgb( '#2a2a2e' ) )                     # handle
    c.px( 6, 14, rgb( '#e83a2a' ) )                             # light
    c.line( 5, 12, 14, 12, rgb( '#b8bcb8' ) )
    finish( c )


@sprite( 'sgn_bep_than_to_ong', 20, 20 )
def bep_than( c ):
    # squat metal bucket stove, clay-lined top with a briquette showing
    c.rect( 4, 9, 15, 16, rgb( '#8a8e92' ) )
    c.line( 4, 12, 15, 12, rgb( '#6a6e72' ) )
    c.ellipse( 9.5, 9, 6, 2.6, rgb( '#c8a07a' ) )               # clay rim
    c.ellipse( 9.5, 9, 4, 1.7, rgb( '#2a2624' ) )               # briquette
    for x in ( 8, 10, 12 ):
        c.px( x, 9, rgb( '#e8602a' ) )                          # glowing holes
    c.rect( 7, 14, 12, 15, rgb( '#2a2624' ) )                   # air door
    finish( c )


@sprite( 'sgn_than_to_ong', 20, 20 )
def than_to_ong( c ):
    # a honeycomb coal briquette: short black cylinder punched with holes
    c.rect( 4, 9, 15, 14, rgb( '#2e2c2a' ) )
    c.ellipse( 9.5, 9, 6, 2.6, rgb( '#3e3a36' ) )
    for x, y in ( ( 6, 9 ), ( 8, 8 ), ( 10, 9 ), ( 12, 8 ), ( 13, 10 ), ( 8, 10 ), ( 11, 10 ) ):
        c.px( x, y, rgb( '#121110' ) )
    c.line( 4, 14, 15, 14, rgb( '#1a1918' ) )
    finish( c )


@sprite( 'sgn_phin', 20, 20 )
def phin( c ):
    # aluminium drip filter on its saucer, lid on top
    c.ellipse( 9.5, 15, 7, 2, rgb( '#a8b0b6' ) )                # saucer
    c.polygon( [ ( 5, 8 ), ( 14, 8 ), ( 13, 14 ), ( 6, 14 ) ], ALU )
    c.line( 6, 8, 6, 13, rgb( '#e8eef2' ) )
    c.ellipse( 9.5, 8, 5, 1.6, rgb( '#d8dee2' ) )               # lid
    c.rect( 9, 5, 10, 7, rgb( '#9aa2a8' ) )                     # knob
    c.px( 10, 16, rgb( '#5a3a22' ) )                            # drip
    finish( c )


@sprite( 'sgn_ca_phe_bot', 20, 20 )
def ca_phe_bot( c ):
    # paper packet of ground robusta, folded top, red label with a coffee bean
    c.rect( 5, 6, 14, 16, rgb( '#8a5a32' ) )
    c.rect( 5, 6, 14, 7, rgb( '#6a4224' ) )
    c.rect( 6, 10, 13, 14, rgb( '#c8262a' ) )
    c.ellipse( 9.5, 12, 1.8, 1.2, rgb( '#4a2a14' ) )
    c.line( 9, 11, 10, 13, rgb( '#c8262a' ) )
    finish( c )


@sprite( 'sgn_bich_nylon', 20, 20 )
def bich_nylon( c ):
    # tied plastic bag of iced milk coffee with a straw
    c.ellipse( 9.5, 12, 5, 4.5, rgb( '#c8a07a', 230 ) )
    c.ellipse( 8, 10, 1.5, 1.2, rgb( '#f4f0e8' ) )              # ice glint
    c.polygon( [ ( 8, 7 ), ( 11, 7 ), ( 10, 9 ), ( 9, 9 ) ], rgb( '#e8e8e8' ) )   # twisted neck
    c.rect( 8, 6, 11, 6, rgb( '#e8484a' ) )                     # rubber band
    c.line( 12, 3, 10, 9, rgb( '#2f8ad8' ) )                    # straw
    finish( c )


@sprite( 'sgn_ly_nhua', 20, 20 )
def ly_nhua( c ):
    # clear ribbed cup of pink drink, sealed film lid, striped straw
    c.polygon( [ ( 5, 7 ), ( 14, 7 ), ( 13, 16 ), ( 6, 16 ) ], rgb( '#f0a0c0' ) )
    for y in ( 9, 12, 15 ):
        c.line( 6, y, 13, y, rgb( '#f8d0e0' ) )
    c.rect( 5, 6, 14, 7, rgb( '#f0f4f8' ) )
    c.line( 11, 2, 10, 7, rgb( '#e83a3a' ) )
    c.px( 11, 3, rgb( '#ffffff' ) )
    finish( c )


@sprite( 'sgn_chai_nuoc_mam', 20, 20 )
def chai_nuoc_mam( c ):
    # tall glass bottle of amber fish sauce, red cap, label with a fish
    c.rect( 8, 7, 11, 16, rgb( '#a8642a', 235 ) )
    c.rect( 9, 4, 10, 6, rgb( '#a8642a', 235 ) )
    c.rect( 9, 3, 10, 3, rgb( '#d02a2a' ) )
    c.rect( 8, 10, 11, 13, rgb( '#f2e6c8' ) )
    c.px( 9, 11, rgb( '#2f6ab0' ) )
    c.px( 10, 11, rgb( '#2f6ab0' ) )
    c.line( 8, 8, 8, 15, rgb( '#d8a060' ) )
    finish( c )


@sprite( 'sgn_binh_gas', 20, 20 )
def binh_gas( c ):
    # squat red LPG cylinder, steel collar and valve
    c.ellipse( 9.5, 12, 5.5, 5, rgb( '#c8262a' ), light=rgb( '#e85050' ), dark=rgb( '#8a1a1a' ) )
    c.rect( 7, 5, 12, 7, ALU )                                  # collar
    c.rect( 9, 4, 10, 5, rgb( '#6e767e' ) )                     # valve
    c.line( 5, 12, 14, 12, rgb( '#f2f2f2' ) )                   # stencilled band
    finish( c )


@sprite( 'sgn_can_nhua', 20, 20 )
def can_nhua( c ):
    # blue 20 L plastic can with handle and screw cap
    c.rect( 5, 7, 14, 16, rgb( '#2f6ac8' ) )
    c.rect( 5, 7, 6, 16, rgb( '#5a90e0' ) )
    c.rect( 7, 4, 11, 6, rgb( '#2f6ac8' ) )                     # handle
    c.erase( 8, 5, 10, 5 )                                       # hand hole
    c.rect( 12, 5, 13, 6, rgb( '#f2f2f2' ) )                    # cap
    c.line( 6, 11, 13, 11, rgb( '#1f4a98' ) )
    finish( c )
