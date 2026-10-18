"""Saigon clothing, tools and motorbike parts: 20x20 item icons.

These replace looks_like stand-ins that read as American: the nón lá was a fedora,
dép tổ ong drew as sneakers, the dao rựa as a machete, the bếp ga mini as an esbit
stove.  Worn overlays (32x36) for the clothing stay derived for now (derive_recipes.json).
"""
from draw import sprite, rgb, shade

OUTLINE = 0.38
STRAW = rgb( '#e6d49a' )
STRAW_LIGHT = rgb( '#f6ead0' )
STRAW_DARK = rgb( '#b8a060' )
STEEL = rgb( '#b8c0c8' )
STEEL_DARK = rgb( '#6e767e' )


def finish( c ):
    c.outline( OUTLINE )
    c.drop_shadow( 1, 1, 90 )


@sprite( 'sgn_non_la', 20, 20 )
def non_la( c ):
    # palm-leaf cone seen from the side and a little above, with a pink chin ribbon
    c.polygon( [ ( 10, 3 ), ( 18, 14 ), ( 2, 14 ) ], STRAW )
    c.ellipse( 10, 14, 8, 2, STRAW )
    c.polygon( [ ( 10, 3 ), ( 18, 14 ), ( 12, 15 ) ], STRAW_DARK )   # shaded side
    for y in ( 6, 9, 12 ):                                            # bamboo rings
        half = ( y - 3 ) * 8 / 11
        c.line( 10 - half + 1, y, 10 + half - 1, y, STRAW_LIGHT if y < 12 else shade( STRAW, 0.9 ) )
    c.line( 10, 3, 6, 12, STRAW_LIGHT )                               # highlight along the leaf seam
    c.line( 4, 15, 6, 17, rgb( '#e86a9a' ) )                          # chin ribbon
    c.line( 16, 15, 14, 17, rgb( '#e86a9a' ) )
    c.line( 6, 17, 14, 17, rgb( '#f28ab4' ) )
    finish( c )


@sprite( 'sgn_dep_to_ong', 20, 20, fit=( 15, 12 ) )
def dep_to_ong( c ):
    # a pair of foam honeycomb sandals, seen from above: one blue, one white
    for ox, oy, sole in ( ( 2, 4, rgb( '#5a8ed8' ) ), ( 12, 6, rgb( '#eef2f6' ) ) ):
        c.ellipse( ox + 3, oy + 3, 3, 3.2, sole )          # toe end
        c.ellipse( ox + 3, oy + 8, 2.6, 3.6, sole )        # heel end
        c.rect( ox + 1, oy + 3, ox + 5, oy + 8, sole )
        holes = shade( sole, 0.7 )
        for y in range( oy + 1, oy + 12, 2 ):              # honeycomb holes, staggered
            for x in range( ox + 1 + ( ( y - oy ) // 2 ) % 2, ox + 6, 2 ):
                if c.opaque( x - 1, y ) and c.opaque( x + 1, y ) and c.opaque( x, y + 1 ):
                    c.px( x, y, holes )
        strap = rgb( '#2f5aa8' )
        c.rect( ox, oy + 4, ox + 6, oy + 5, strap )        # closed-toe band
        c.line( ox, oy + 4, ox + 6, oy + 4, shade( strap, 1.3 ) )
    finish( c )


@sprite( 'sgn_ao_ba_ba', 20, 20 )
def ao_ba_ba( c ):
    # collarless southern shirt laid flat: dark brown cotton, two low pockets, front buttons
    body = rgb( '#5a3a2a' )
    c.polygon( [ ( 6, 3 ), ( 14, 3 ), ( 18, 9 ), ( 15, 10 ), ( 15, 17 ), ( 5, 17 ), ( 5, 10 ), ( 2, 9 ) ], body )
    c.polygon( [ ( 8, 3 ), ( 12, 3 ), ( 10, 6 ) ], shade( body, 0.55 ) )   # inside of the round neck
    c.line( 10, 6, 10, 17, shade( body, 0.7 ) )
    for y in ( 8, 11, 14 ):
        c.px( 11, y, rgb( '#d8c8a8' ) )
    c.rect( 6, 13, 8, 15, shade( body, 1.15 ) )
    c.rect( 12, 13, 14, 15, shade( body, 1.15 ) )
    c.line( 6, 4, 3, 8, shade( body, 1.25 ) )
    finish( c )


@sprite( 'sgn_ong_tay_chong_nang', 20, 20 )
def ong_tay( c ):
    # a pair of long sun sleeves with thumb loops
    for x0, y0, colour in ( ( 3, 14, rgb( '#7ab8e0' ) ), ( 7, 16, rgb( '#5a9ad0' ) ) ):
        c.capsule( x0, y0, x0 + 10, y0 - 10, 1.6, colour, 1.2 )
        c.line( x0 + 9, y0 - 11, x0 + 11, y0 - 9, rgb( '#f2f2f2' ) )   # elastic cuff
        c.px( x0 + 11, y0 - 12, shade( colour, 0.7 ) )                   # thumb loop
    finish( c )


@sprite( 'sgn_dao_rua', 20, 20 )
def dao_rua( c ):
    # heavy square-tipped chopping blade on a round wooden handle
    c.capsule( 3, 17, 7, 13, 1.3, rgb( '#8a5a32' ) )
    c.line( 3, 17, 7, 13, rgb( '#b07a48' ) )
    c.rect( 7, 12, 8, 13, STEEL_DARK )                      # ferrule
    c.polygon( [ ( 8, 13 ), ( 7, 10 ), ( 14, 3 ), ( 18, 6 ), ( 11, 13 ) ], STEEL )
    c.line( 8, 13, 18, 6, rgb( '#e8eef2' ) )                # sharpened edge
    c.line( 7, 10, 14, 3, STEEL_DARK )                      # thick spine
    c.line( 14, 3, 18, 6, STEEL_DARK )                      # square tip
    finish( c )


@sprite( 'sgn_bep_ga_mini', 20, 20 )
def bep_ga_mini( c ):
    # suitcase-sized portable butane stove: black case, steel top, round burner, orange knob
    c.polygon( [ ( 2, 9 ), ( 14, 9 ), ( 18, 6 ), ( 6, 6 ) ], rgb( '#c8ced4' ) )      # top plate
    c.rect( 2, 9, 14, 15, rgb( '#2a2c30' ) )                                         # front
    c.polygon( [ ( 14, 9 ), ( 18, 6 ), ( 18, 12 ), ( 14, 15 ) ], rgb( '#1c1e22' ) )  # side
    c.ellipse( 8.5, 7.5, 3.2, 1.3, rgb( '#5a6068' ) )                                # burner ring
    c.ellipse( 8.5, 7.5, 1.6, 0.7, rgb( '#2a2c30' ) )
    for x in ( 6, 11 ):                                                              # pot supports
        c.px( x, 7, rgb( '#e8ecf0' ) )
    c.rect( 3, 11, 9, 13, rgb( '#3a3e44' ) )                                         # canister lid
    c.ellipse( 12, 12, 1.4, 1.4, rgb( '#f08a2c' ) )                                  # knob
    finish( c )


@sprite( 'sgn_thung_xop', 20, 20 )
def thung_xop( c ):
    # white polystyrene market box with its lid, beaded texture
    c.polygon( [ ( 2, 8 ), ( 13, 8 ), ( 18, 4 ), ( 7, 4 ) ], rgb( '#fafafa' ) )      # lid top
    c.rect( 2, 8, 13, 16, rgb( '#e8eaec' ) )                                         # front
    c.polygon( [ ( 13, 8 ), ( 18, 4 ), ( 18, 12 ), ( 13, 16 ) ], rgb( '#c8ccd0' ) )  # side
    c.line( 2, 10, 13, 10, rgb( '#c0c4c8' ) )                                        # lid seam
    c.line( 13, 10, 18, 6, rgb( '#a8acb0' ) )
    c.noise( 2, 4, 18, 16, [ rgb( '#d8dadc' ), rgb( '#ffffff' ) ], 0.18 )
    c.line( 5, 13, 9, 13, rgb( '#3a6ab0' ) )                                         # marker scrawl
    finish( c )


@sprite( 'sgn_engine_110cc_item', 20, 20 )
def engine_110cc( c ):
    # air-cooled single: finned cylinder leaning forward over a rounded crankcase
    c.ellipse( 8, 13, 6, 4, rgb( '#9aa2aa' ), light=rgb( '#c8d0d6' ), dark=rgb( '#6a727a' ) )  # crankcase
    c.polygon( [ ( 9, 10 ), ( 13, 4 ), ( 17, 6 ), ( 13, 12 ) ], rgb( '#8a9298' ) )            # cylinder
    for i in range( 4 ):                                                                       # cooling fins
        c.line( 10 + i, 9 - i * 1.5, 14 + i, 11 - i * 1.5, rgb( '#d0d6dc' ) )
    c.rect( 15, 4, 17, 5, rgb( '#3a3e44' ) )                                                   # spark plug cap
    c.ellipse( 6, 13, 2, 2, rgb( '#50565c' ) )                                                 # clutch cover
    c.line( 2, 16, 5, 16, rgb( '#2a2c30' ) )                                                   # kick-start
    finish( c )


@sprite( 'sgn_moto_tank_4l', 20, 20 )
def moto_tank( c ):
    # small pressed-steel tank from under an underbone seat, red paint and a chrome cap
    c.polygon( [ ( 3, 10 ), ( 7, 6 ), ( 15, 6 ), ( 17, 9 ), ( 16, 14 ), ( 4, 14 ) ], rgb( '#b82a2a' ) )
    c.line( 7, 7, 14, 7, rgb( '#e86060' ) )
    c.line( 4, 13, 16, 13, rgb( '#7e1a1a' ) )
    c.ellipse( 11, 6, 1.6, 1, STEEL )
    c.line( 4, 15, 6, 16, STEEL_DARK )                       # fuel tap
    finish( c )


# --- dda items UltimateCataclysm has no sprite for, seen on every Saigon altar and stall --------

@sprite( 'incense', 20, 20 )
def incense( c ):
    # a bundle of nhang: thin sticks with red-dyed handles and brown incense tips, tied in paper
    tips = [ ( 8, 1 ), ( 12, 1 ), ( 15, 3 ), ( 18, 6 ), ( 19, 10 ) ]
    for tx, ty in tips:                                                            # fanned sticks
        c.line( 5, 17, tx, ty, rgb( '#7a5232' ) )                                  # incense coat
        c.line( 5, 17, 5 + ( tx - 5 ) * 0.3, 17 + ( ty - 17 ) * 0.3, rgb( '#d02a2a' ) )   # red handles
    c.rect( 6, 14, 8, 15, rgb( '#f2c232' ) )                                       # gold paper band
    c.px( 15, 3, rgb( '#f2a050' ) )                                                # one lit tip
    c.px( 15, 1, rgb( '#c8c8c8' ) )                                                # smoke
    c.px( 16, 0, rgb( '#e0e0e0' ) )
    c.drop_shadow( 1, 1, 90 )   # no outline: it would fill the gaps between the thin sticks


@sprite( 'knife_cleaver', 20, 20 )
def cleaver( c ):
    # dao phay: a broad rectangular kitchen cleaver with a wooden handle
    c.capsule( 3, 17, 7, 13, 1.1, rgb( '#6e4a2a' ) )
    c.polygon( [ ( 7, 13 ), ( 6, 8 ), ( 12, 2 ), ( 17, 7 ), ( 10, 14 ) ], STEEL )
    c.line( 10, 14, 17, 7, rgb( '#eef2f4' ) )                                      # edge
    c.line( 6, 8, 12, 2, STEEL_DARK )                                              # spine
    c.px( 9, 6, STEEL_DARK )                                                       # hanging hole
    finish( c )


@sprite( 'tape_measure', 20, 20 )
def tape_measure( c ):
    # yellow case, a tongue of steel tape pulled out
    c.ellipse( 9, 11, 5, 5, rgb( '#f2c232' ), light=rgb( '#fbe27a' ), dark=rgb( '#c8961a' ) )
    c.ellipse( 9, 11, 2, 2, rgb( '#3a3a3a' ) )
    c.rect( 13, 14, 18, 15, rgb( '#d8d0a0' ) )
    for x in range( 14, 19, 2 ):
        c.px( x, 14, rgb( '#3a3a3a' ) )
    c.rect( 18, 13, 18, 15, rgb( '#6e767e' ) )                                     # hook
    finish( c )


@sprite( 'ring_wedding', 20, 20 )
def ring_wedding( c ):
    # gold band seen at an angle, a small diamond on top
    c.ring( 10, 12, 4.5, 3, rgb( '#e8b830' ), 1.6 )
    c.ring( 10, 12, 4.5, 3, rgb( '#fbe27a' ), 0.6 )
    c.polygon( [ ( 8.5, 9 ), ( 11.5, 9 ), ( 10, 6.5 ) ], rgb( '#e8f4fa' ) )
    c.px( 9, 8, rgb( '#ffffff' ) )
    finish( c )


@sprite( 'wood_block', 20, 20 )
def wood_block( c ):
    # a short sawn block of wood, end grain showing (debris of smashed furniture)
    c.rect( 5, 9, 14, 14, rgb( '#a8784a' ) )
    c.rect( 5, 9, 14, 9, rgb( '#c8986a' ) )
    c.ellipse( 14, 11.5, 1.6, 2.6, rgb( '#d8b07a' ) )
    c.ring( 14, 11.5, 1.2, 2, rgb( '#a8784a' ), 0.6 )
    finish( c )


@sprite( 'wooden_post_short', 20, 20 )
def wooden_post_short( c ):
    # a broken chair or table leg
    c.line( 4, 15, 14, 5, rgb( '#8a5a32' ) )
    c.line( 5, 15, 15, 5, rgb( '#b07a48' ) )
    c.line( 14, 4, 16, 5, rgb( '#d8b07a' ) )                     # splintered end
    finish( c )


@sprite( 'processor', 20, 20 )
def processor( c ):
    # a CPU: green package, silver heat spreader, gold pins (internet-café loot)
    c.rect( 5, 6, 14, 15, rgb( '#2e7a4a' ) )
    c.rect( 7, 8, 12, 13, rgb( '#c8ccd0' ) )
    c.line( 7, 8, 12, 8, rgb( '#eef2f4' ) )
    for k in range( 6, 14, 2 ):
        c.px( k, 5, rgb( '#e8c040' ) )
        c.px( k, 16, rgb( '#e8c040' ) )
        c.px( 4, k + 1, rgb( '#e8c040' ) )
        c.px( 15, k + 1, rgb( '#e8c040' ) )
    finish( c )
