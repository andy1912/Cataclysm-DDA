"""Everyday places (unit P2): the Vietnamese tiled tomb.  Definition in
data/mods/saigon_2000s/furniture/places.json.  3/4 view like UltimateCataclysm.
"""
from draw import sprite, rgb, shade


@sprite( 'f_sgn_mo', 32, 32 )
def mo( c ):
    # a raised cement grave faced with glazed tiles, the stele at the head with a photo,
    # an incense bowl in front
    c.ellipse( 19, 28, 12, 2.5, ( 0, 0, 0, 70 ) )
    tile = rgb( '#d8e0dc' )
    c.rect( 4, 14, 27, 27, shade( tile, 0.8 ) )                         # the base
    c.rect( 4, 14, 27, 16, tile )
    for x in range( 5, 27, 4 ):                                         # glazed tile joints
        c.line( x, 17, x, 26, shade( tile, 0.65 ) )
    c.rect( 7, 12, 24, 14, rgb( '#a8b8b0' ) )                           # the raised slab
    c.rect( 10, 2, 21, 12, rgb( '#8a9690' ) )                           # stele
    c.rect( 10, 2, 21, 3, rgb( '#b0bcb6' ) )
    c.polygon( [ ( 9, 3 ), ( 22, 3 ), ( 20, 0 ), ( 11, 0 ) ], rgb( '#7a3a2a' ) )   # little roof
    c.rect( 14, 4, 17, 7, rgb( '#e8e0d0' ) )                            # the photograph
    c.rect( 15, 5, 16, 6, rgb( '#5a5048' ) )
    for y in ( 9, 10 ):                                                 # carved names
        c.line( 12, y, 19, y, rgb( '#e0c060' ) )
    c.ellipse( 15.5, 19, 2.5, 1.4, rgb( '#c8a040' ) )                   # incense bowl
    for x in ( 14, 16, 17 ):
        c.line( x, 18, x, 15, rgb( '#c03030' ) )
    c.outline( 0.42 )
