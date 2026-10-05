"""Household items, tools and clothes (unit V2): 20x20 item icons.
Definitions in data/mods/saigon_2000s/items/gear/household_2.json.  The worn overlays of the
four clothes are derived from dda's (derive_recipes.json).
"""
import math

from draw import sprite, rgb, shade

OUTLINE = 0.38


def finish( c ):
    c.outline( OUTLINE )
    c.drop_shadow( 1, 1, 90 )


@sprite( 'sgn_binh_thuy', 20, 20 )
def binh_thuy( c ):
    # a tin vacuum flask printed with peach blossoms, a plastic cup-lid on top
    body = rgb( '#e86a8a' )
    c.rect( 6, 6, 13, 17, body )
    c.rect( 6, 6, 8, 17, shade( body, 1.2 ) )
    c.rect( 7, 3, 12, 5, rgb( '#d8d8dc' ) )                            # cup lid
    c.rect( 6, 17, 13, 17, shade( body, 0.6 ) )
    for x, y in ( ( 9, 9 ), ( 11, 12 ), ( 8, 14 ) ):                   # peach blossoms
        c.px( x, y, rgb( '#fff0f4' ) )
        c.px( x + 1, y, rgb( '#f8c0d0' ) )
    c.line( 13, 8, 15, 10, rgb( '#c8c8cc' ) )                          # handle
    c.line( 15, 10, 13, 13, rgb( '#c8c8cc' ) )
    finish( c )


@sprite( 'sgn_noi_dat', 20, 20 )
def noi_dat( c ):
    # a squat clay pot, sooty at the bottom, lid with a knob
    clay = rgb( '#b46a3a' )
    c.ellipse( 10, 12, 7, 5, clay, light=shade( clay, 1.25 ), dark=shade( clay, 0.7 ) )
    c.ellipse( 10, 16, 5, 1.6, rgb( '#2a2420' ) )                       # soot
    c.ellipse( 10, 8, 6, 1.8, shade( clay, 1.1 ) )                      # lid
    c.rect( 9, 5, 11, 7, shade( clay, 0.9 ) )
    finish( c )


@sprite( 'sgn_thot_go_me', 20, 20 )
def thot_go_me( c ):
    # a round slice of tamarind trunk: bark rim, growth rings, a worn dip
    c.ellipse( 10, 13, 8, 3.6, rgb( '#6a4a2a' ) )                       # side and bark
    c.ellipse( 10, 11, 8, 3.4, rgb( '#c89a62' ) )
    c.ring( 10, 11, 5, 2, rgb( '#a87a48' ), 1 )
    c.ring( 10, 11, 2.5, 1, rgb( '#a87a48' ), 1 )
    c.ring( 10, 11, 8, 3.4, rgb( '#5a3a20' ), 1 )
    finish( c )


@sprite( 'sgn_choi_cha', 20, 20 )
def choi_cha( c ):
    # a stiff fan of coconut leaf ribs bound to a short bamboo handle
    c.line( 4, 3, 9, 10, rgb( '#c8a660' ) )                             # handle
    c.rect( 8, 9, 10, 11, rgb( '#c03030' ) )                            # the binding
    for k in range( -4, 5 ):                                            # ribs
        a = math.radians( 45 + k * 7 )
        c.line( 10, 11, 10 + 8 * math.cos( a ), 11 + 8 * math.sin( a ), rgb( '#d8c080' ) if k % 2 else rgb( '#b89a58' ) )
    finish( c )


@sprite( 'sgn_am_nhom', 20, 20 )
def am_nhom( c ):
    # a dented aluminium kettle with a sooty bottom
    alu = rgb( '#c8ccd0' )
    c.ellipse( 9, 12, 6, 4.5, alu, light=shade( alu, 1.2 ), dark=shade( alu, 0.75 ) )
    c.ellipse( 9, 16, 4.5, 1.2, rgb( '#3a3632' ) )
    c.polygon( [ ( 14, 11 ), ( 18, 7 ), ( 18, 8 ), ( 15, 13 ) ], alu )   # spout
    c.ring( 9, 7, 3.5, 2.5, rgb( '#2a2a2e' ), 1 )                        # handle
    c.rect( 8, 7, 10, 8, rgb( '#2a2a2e' ) )
    c.px( 6, 11, rgb( '#9a9ea2' ) )                                     # a dent
    finish( c )


@sprite( 'sgn_long_ban', 20, 20 )
def long_ban( c ):
    # a dome of woven pink plastic mesh
    pink = rgb( '#e8608a' )
    c.ellipse( 10, 12, 8, 6, pink )
    c.erase( 1, 13, 19, 19 )
    c.ellipse( 10, 13, 8, 1.6, shade( pink, 0.75 ) )                    # rim
    for x in range( 4, 17, 2 ):                                         # the weave
        for y in range( 7, 13, 2 ):
            if c.opaque( x, y ):
                c.px( x, y, shade( pink, 1.3 ) )
    c.rect( 9, 5, 11, 6, shade( pink, 0.8 ) )                           # handle loop
    finish( c )


@sprite( 'sgn_bo_va_xe', 20, 20 )
def bo_va_xe( c ):
    # tyre levers, a red rubber patch, a tube of glue and a scrap of inner tube
    c.ellipse( 9, 13, 6, 2.6, rgb( '#2a2a2e' ) )                        # inner tube scrap
    c.ellipse( 9, 13, 3.5, 1.2, rgb( '#5a5a60' ) )                    # its inside
    c.line( 4, 6, 9, 10, rgb( '#3a6ac8' ) )                             # tyre levers
    c.line( 6, 5, 11, 9, rgb( '#3a6ac8' ) )
    c.rect( 12, 6, 15, 9, rgb( '#c83030' ) )                            # patch
    c.capsule( 13, 14, 17, 11, 1.2, rgb( '#e8c040' ) )                  # glue tube
    finish( c )


@sprite( 'sgn_can_cau_tre', 20, 20 )
def can_cau_tre( c ):
    # a long bamboo pole with nodes, line and a flip-flop float
    c.line( 2, 18, 17, 2, rgb( '#c8a660' ) )
    c.line( 3, 18, 18, 2, rgb( '#a8864a' ) )
    for t in ( 0.25, 0.5, 0.75 ):                                       # bamboo nodes
        x, y = 2 + 15 * t, 18 - 16 * t
        c.px( x, y, rgb( '#7a5a2a' ) )
    c.line( 18, 2, 18, 12, rgb( '#e8e8e8' ) )                           # line
    c.rect( 17, 12, 19, 13, rgb( '#3a8ac8' ) )                          # the float
    finish( c )


@sprite( 'sgn_khoa_chu_u', 20, 20 )
def khoa_chu_u( c ):
    # a hardened steel U-lock, red rubber coating, the cross bar with its keyhole
    red = rgb( '#c83030' )
    c.ring( 10, 8, 5, 5.5, red, 2 )
    c.erase( 4, 8, 16, 14 )
    c.rect( 4, 8, 5, 14, red )
    c.rect( 15, 8, 16, 14, red )
    c.rect( 3, 14, 17, 16, rgb( '#7a7e86' ) )                           # cross bar
    c.px( 10, 15, rgb( '#e8c040' ) )                                    # keyhole
    finish( c )


@sprite( 'sgn_non_coi', 20, 20 )
def non_coi( c ):
    # an olive pith helmet with a brim all round and a red-star badge
    olive = rgb( '#6a7a3a' )
    c.ellipse( 10, 13, 9, 2.6, shade( olive, 0.8 ) )                     # brim
    c.ellipse( 10, 10, 6, 5, olive, light=shade( olive, 1.3 ), dark=shade( olive, 0.75 ) )
    c.erase( 2, 14, 18, 19 )
    c.ellipse( 10, 13, 9, 2.2, shade( olive, 0.9 ) )
    c.ellipse( 10, 10, 1.4, 1.4, rgb( '#d02020' ) )                     # badge
    c.px( 10, 10, rgb( '#f0d040' ) )
    finish( c )


@sprite( 'sgn_do_bo', 20, 20 )
def do_bo( c ):
    # a folded flowered rayon set: shirt on top of the matching trousers
    pink = rgb( '#e88aa8' )
    c.rect( 3, 11, 16, 16, shade( pink, 0.85 ) )                         # trousers
    c.polygon( [ ( 4, 5 ), ( 16, 5 ), ( 17, 11 ), ( 3, 11 ) ], pink )    # shirt
    c.polygon( [ ( 8, 5 ), ( 12, 5 ), ( 10, 8 ) ], shade( pink, 0.7 ) )  # collar
    for x, y in ( ( 5, 7 ), ( 13, 8 ), ( 7, 10 ), ( 11, 13 ), ( 5, 14 ), ( 14, 15 ) ):   # flowers
        c.px( x, y, rgb( '#fff4c0' ) )
        c.px( x + 1, y, rgb( '#5fb048' ) )
    finish( c )


@sprite( 'sgn_khan_ran', 20, 20 )
def khan_ran( c ):
    # a black-and-white checked scarf, folded, the fringe hanging
    for y in range( 5, 14 ):
        for x in range( 3, 17 ):
            c.px( x, y, rgb( '#1e1e22' ) if ( x // 2 + y // 2 ) % 2 else rgb( '#ece8e0' ) )
    for x in range( 4, 16, 2 ):                                         # fringe
        c.line( x, 14, x, 16, rgb( '#ece8e0' ) )
    finish( c )


@sprite( 'sgn_dep_quai_hau', 20, 20 )
def dep_quai_hau( c ):
    # a pair of brown sandals with heel straps
    brown = rgb( '#7a4a28' )
    for dx in ( 0, 7 ):
        c.capsule( 5 + dx, 15, 6 + dx, 6, 2.4, shade( brown, 0.8 ) )    # sole
        c.line( 3 + dx, 9, 8 + dx, 9, brown )                           # toe strap
        c.line( 3 + dx, 13, 8 + dx, 13, brown )                         # ankle strap
        c.line( 4 + dx, 15, 7 + dx, 15, rgb( '#c8a070' ) )              # heel strap
    finish( c )
