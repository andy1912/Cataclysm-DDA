"""Canal terrain (G27, with the B8f canal): stone embankment edge and corrugated tin roofs.
Canal water itself is derived from UltimateCataclysm's shallow water (derive_recipes.json)."""
from draw import sprite, rgb, shade

STONE = rgb( '#8e8a80' )


@sprite( 't_sgn_bo_ke', 32, 32 )
def bo_ke( c ):
    # dressed stone blocks in staggered courses, green slime and tide stains
    c.rect( 0, 0, 31, 31, STONE )
    for row, y in enumerate( range( 0, 32, 8 ) ):
        c.line( 0, y, 31, y, shade( STONE, 0.7 ) )
        for x in range( -8 + ( row % 2 ) * 8, 32, 16 ):
            c.line( x, y, x, y + 7, shade( STONE, 0.7 ) )
        c.line( 0, y + 1, 31, y + 1, shade( STONE, 1.15 ) )
    c.noise( 0, 0, 31, 31, [ shade( STONE, 0.9 ), shade( STONE, 1.08 ) ], 0.3 )
    c.noise( 0, 20, 31, 31, [ rgb( '#4a6a3a' ), rgb( '#5a7a42' ) ], 0.35 )   # slime at the water line


def mai_ton( c, sheet ):
    # corrugated iron: ridges every 4 px, a nailed seam, rust streaks
    c.rect( 0, 0, 31, 31, sheet )
    for x in range( 0, 32, 4 ):
        c.line( x, 0, x, 31, shade( sheet, 1.25 ) )
        c.line( x + 2, 0, x + 2, 31, shade( sheet, 0.75 ) )
    c.line( 0, 15, 31, 15, shade( sheet, 0.6 ) )
    for x in range( 2, 32, 8 ):
        c.px( x, 15, rgb( '#d8d8d8' ) )
    for _ in range( 3 ):
        x = c.rand.randint( 1, 30 )
        c.line( x, 16, x, 16 + c.rand.randint( 4, 12 ), rgb( '#8a4a2a' ) )


@sprite( 't_sgn_mai_ton', 32, 32,
         fg=[ { 'weight': 3, 'sprite': '@t_sgn_mai_ton' }, { 'weight': 2, 'sprite': '@t_sgn_mai_ton__rust' },
              { 'weight': 2, 'sprite': '@t_sgn_mai_ton__grey' } ] )
def mai_ton_blue( c ):
    mai_ton( c, rgb( '#4a7ab0' ) )


@sprite( 't_sgn_mai_ton__rust', 32, 32 )
def mai_ton_rust( c ):
    mai_ton( c, rgb( '#9a5a32' ) )


@sprite( 't_sgn_mai_ton__grey', 32, 32 )
def mai_ton_grey( c ):
    mai_ton( c, rgb( '#9aa0a4' ) )
