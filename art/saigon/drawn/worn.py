"""Saigon clothing worn on the character: 32x36 overlays (human_body.png, offset 0,-8).

The player sprite is 32x48 (offset 0,-16), so its head top (row 10 male, 11 female)
lands on overlay row 2 / 3; the face is centred on x 15.5.  Derived overlays reuse
dda shapes; these are drawn because the shape itself is Vietnamese.
"""
from draw import sprite, rgb, shade

STRAW = rgb( '#e6d49a' )
STRAW_LIGHT = rgb( '#f6ead0' )
STRAW_DARK = rgb( '#b8a060' )


def non_la( c, dy ):
    # a wide, shallow palm-leaf cone seen from the side.  The overlay cannot reach above
    # row 0 (two rows over the head), so the cone is flattened and its brim sits at the
    # hairline, leaving the face visible.
    brim_y = 3.5 + dy
    c.polygon( [ ( 15.5, 0 ), ( 25.5, brim_y + 0.5 ), ( 5.5, brim_y + 0.5 ) ], STRAW )
    c.polygon( [ ( 15.5, 0 ), ( 25.5, brim_y + 0.5 ), ( 17, brim_y + 0.5 ) ], STRAW_DARK )
    c.line( 6, brim_y, 25, brim_y, shade( STRAW, 0.82 ) )
    c.line( 12, 2 + dy, 19, 2 + dy, STRAW_LIGHT )                  # bamboo ring
    c.px( 15, 0, STRAW_LIGHT )
    c.outline( 0.4 )


@sprite( 'overlay_male_worn_sgn_non_la', 32, 36 )
def male( c ):
    non_la( c, 0 )


@sprite( 'overlay_female_worn_sgn_non_la', 32, 36 )
def female( c ):
    non_la( c, 1 )
