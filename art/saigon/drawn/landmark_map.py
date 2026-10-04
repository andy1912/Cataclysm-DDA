"""Overmap pictures for the District 1 landmarks (asset unit A1, doc/saigon/MAP.md).

Each landmark is drawn once as a plan view, 16 px per overmap tile, in the Larwick Overmap
style (bright flat colours on the transparent black map), then cut into one 16x16 icon per
piece (sgn_lm_<name>_<x><y>).  The pieces rotate with the building, so the picture stays
whole when a city places the landmark facing east, south or west.  Local north (the top)
is the street side, as in the mapgen.
"""
from draw import sprite, rgb, shade, Canvas

OCHRE = rgb( '#e8c050' )
CREAM = rgb( '#eadcb8' )
BRICK = rgb( '#c84a30' )
SLATE = rgb( '#6e7890' )
GRASS = rgb( '#3a9a3a' )
PARK = rgb( '#1e5a1e' )
TREE = rgb( '#2a8a2a' )
WHITE = rgb( '#f4f2ea' )
PAVE = rgb( '#8a8a90' )
WATER = rgb( '#4aa0e0' )
INK = rgb( '#202024' )


def composite( lid, w, h ):
    """Register w x h overmap pieces cut from one ( 16w x 16h ) drawing."""
    def deco( fn ):
        cache = {}

        def whole():
            if 'c' not in cache:
                c = Canvas( 16 * w, 16 * h, seed=sum( map( ord, lid ) ) )
                fn( c )
                cache['c'] = c
            return cache['c']

        for x in range( w ):
            for y in range( h ):
                def piece( c, x=x, y=y ):
                    big = whole()
                    for py in range( 16 ):
                        for px in range( 16 ):
                            p = big.get( x * 16 + px, y * 16 + py )
                            if p[3]:
                                c.set( px, py, p )
                sprite( '%s_%d%d' % ( lid, x, y ), 16, 16, overmap=True, rotates=True )( piece )
        return fn
    return deco


def walls( c, x0, y0, x1, y1, roof, wall ):
    c.rect( x0, y0, x1, y1, wall )
    c.rect( x0 + 1, y0 + 1, x1 - 1, y1 - 1, roof )


def clock( c, cx, cy ):
    c.ellipse( cx, cy, 1.6, 1.6, WHITE )
    c.px( int( cx ), int( cy ), INK )


@composite( 'sgn_lm_ben_thanh', 3, 3 )
def ben_thanh( c ):
    # the market hall under long ochre roofs, glazed skylights along the cross aisles,
    # and the three-faced clock tower over the main gate on the street
    walls( c, 3, 10, 44, 45, OCHRE, shade( OCHRE, 0.6 ) )
    for y in ( 15, 21, 33, 39 ):                                  # roof ridges
        c.line( 4, y, 43, y, shade( OCHRE, 0.78 ) )
    c.rect( 22, 11, 25, 44, rgb( '#f6eccc' ) )                    # north-south aisle skylight
    c.rect( 4, 26, 43, 28, rgb( '#f6eccc' ) )                     # east-west aisle skylight
    for x in ( 4, 43 ):                                           # side gates
        c.rect( x, 26, x, 28, INK )
    c.rect( 23, 45, 24, 45, INK )
    walls( c, 18, 1, 29, 11, rgb( '#f0d478' ), shade( OCHRE, 0.55 ) )   # the clock tower
    c.rect( 21, 10, 26, 11, INK )                                 # the gate under it
    clock( c, 23.5, 5.5 )


@composite( 'sgn_lm_duc_ba', 2, 3 )
def duc_ba( c ):
    # Công xã Paris square with the Virgin Mary statue, then the red-brick cathedral:
    # twin bell towers on the façade, a slate nave roof, the rounded apse at the back
    c.ellipse( 15.5, 5.5, 8, 3.2, GRASS )
    c.px( 15, 5, WHITE )
    c.px( 16, 5, WHITE )
    c.px( 15, 4, WHITE )
    walls( c, 6, 16, 25, 41, SLATE, BRICK )                      # nave
    c.line( 15, 17, 15, 40, shade( SLATE, 1.3 ) )                 # roof ridge
    c.line( 16, 17, 16, 40, shade( SLATE, 1.3 ) )
    c.rect( 4, 26, 27, 29, BRICK )                                # transept
    c.rect( 5, 27, 26, 28, SLATE )
    c.ellipse( 15.5, 42, 8, 5, BRICK )                            # apse
    c.ellipse( 15.5, 42, 6.5, 3.6, SLATE )
    for x0 in ( 3, 21 ):                                          # the two towers, spires
        walls( c, x0, 11, x0 + 7, 18, rgb( '#d85a3c' ), shade( BRICK, 0.6 ) )
        c.rect( x0 + 2, 13, x0 + 5, 16, SLATE )
        c.px( x0 + 3, 14, WHITE )
        c.px( x0 + 4, 15, WHITE )
    c.rect( 13, 15, 18, 16, INK )                                 # the main doors


@composite( 'sgn_lm_buu_dien', 3, 2 )
def buu_dien( c ):
    # the long ochre post office: a barrel-vaulted hall roof with iron ribs, the white-trimmed
    # façade on the square and the clock in the central pediment
    walls( c, 3, 9, 44, 28, rgb( '#8a9a90' ), OCHRE )
    for x in range( 6, 43, 4 ):                                   # vault ribs
        c.line( x, 11, x, 26, rgb( '#6e7e76' ) )
    c.line( 4, 18, 43, 18, rgb( '#b0c0b6' ) )                     # vault crown
    c.rect( 3, 9, 44, 11, OCHRE )                                 # façade band
    c.line( 3, 11, 44, 11, WHITE )
    walls( c, 18, 4, 29, 11, OCHRE, shade( OCHRE, 0.6 ) )        # central pediment
    clock( c, 23.5, 7 )
    c.rect( 21, 11, 26, 11, INK )                                 # doors


@composite( 'sgn_lm_nha_hat', 2, 2 )
def nha_hat( c ):
    # the cream opera house: the great arched entrance on Lam Sơn square, a slate roof
    # over the auditorium and the higher fly tower over the stage at the back
    walls( c, 4, 6, 27, 29, rgb( '#9a9aa4' ), CREAM )
    c.rect( 5, 7, 26, 12, CREAM )                                 # foyer, under the façade
    walls( c, 7, 21, 24, 28, rgb( '#7a7a86' ), shade( CREAM, 0.8 ) )   # fly tower
    c.ellipse( 15.5, 7, 4.5, 3.5, INK )                           # the arch
    c.ellipse( 15.5, 7, 3, 2.2, rgb( '#f0c060' ) )                # lit foyer seen through it
    c.rect( 4, 4, 27, 5, PAVE )                                   # the steps
    for x in ( 9, 22 ):                                           # statues on the façade
        c.px( x, 6, WHITE )


@composite( 'sgn_lm_ubnd_tp', 3, 2 )
def ubnd_tp( c ):
    # City Hall: the statue garden at the head of Nguyễn Huệ, the yellow Beaux-Arts
    # building around a courtyard, the clock tower over the entrance
    c.ellipse( 23.5, 3.5, 11, 2.6, GRASS )
    c.px( 23, 3, WHITE )
    c.px( 24, 3, WHITE )
    walls( c, 3, 8, 44, 30, SLATE, OCHRE )
    c.rect( 15, 15, 32, 24, GRASS )                               # inner courtyard
    c.frame( 14, 14, 33, 25, OCHRE )
    for x0 in ( 3, 39 ):                                          # corner pavilions
        walls( c, x0, 8, x0 + 5, 13, rgb( '#f0d478' ), shade( OCHRE, 0.6 ) )
    walls( c, 19, 6, 28, 13, rgb( '#f0d478' ), shade( OCHRE, 0.6 ) )   # clock tower
    clock( c, 23.5, 9.5 )
    c.rect( 22, 13, 25, 13, INK )


@composite( 'sgn_lm_dinh_doc_lap', 3, 3 )
def dinh_doc_lap( c ):
    # Independence Palace: railings and gate on the street, the oval lawn with its drive
    # and fountain, rows of tamarind trees, the long white palace with its concrete fins
    # and the helipad on the roof terrace
    c.rect( 0, 4, 47, 47, PARK )
    c.line( 0, 3, 47, 3, PAVE )
    c.erase( 17, 3, 30, 3 )                                       # the gate
    c.rect( 19, 4, 28, 9, PAVE )
    c.ring( 23.5, 18, 20, 8.5, PAVE, 2 )                          # the oval drive
    c.ellipse( 23.5, 18, 17.5, 6.5, GRASS )
    c.ellipse( 23.5, 18, 3, 1.6, WATER )
    c.rect( 19, 26, 28, 31, PAVE )
    for y in range( 7, 33, 6 ):
        for x in ( 2, 45 ):
            c.ellipse( x, y, 1.6, 1.6, TREE )
    walls( c, 6, 31, 41, 45, rgb( '#d4d4d8' ), WHITE )           # the palace, flat roof
    for x in range( 7, 41, 2 ):                                   # the brise-soleil fins
        c.px( x, 32, rgb( '#9a9aa6' ) )
        c.px( x, 33, rgb( '#9a9aa6' ) )
    c.ring( 33.5, 39, 3, 3, rgb( '#d04040' ), 1 )                 # helipad
    c.line( 32, 38, 32, 40, rgb( '#d04040' ) )
    c.line( 35, 38, 35, 40, rgb( '#d04040' ) )
    c.px( 33, 39, rgb( '#d04040' ) )
    c.px( 34, 39, rgb( '#d04040' ) )
    c.rect( 22, 31, 25, 31, INK )                                 # glass doors


# --- L2: Chợ Lớn (A3) -------------------------------------------------------------------------
GLAZE = rgb( '#2e8a4a' )
TERRACOTTA = rgb( '#c0603a' )
CLAY = rgb( '#b45c3a' )


def tile_roof( c, x0, y0, x1, y1, colour, ridge=True ):
    # a Chinese tiled roof: courses of tiles, a ridge with red-and-gold ornaments at the ends
    walls( c, x0, y0, x1, y1, colour, shade( colour, 0.6 ) )
    for y in range( y0 + 2, y1, 2 ):
        c.line( x0 + 1, y, x1 - 1, y, shade( colour, 0.82 ) )
    if ridge:
        my = ( y0 + y1 ) // 2
        c.line( x0 + 1, my, x1 - 1, my, shade( colour, 1.4 ) )
        c.px( x0 + 1, my, rgb( '#e04030' ) )
        c.px( x1 - 1, my, rgb( '#e04030' ) )
        c.px( ( x0 + x1 ) // 2, my, rgb( '#f0c040' ) )


@composite( 'sgn_lm_thien_hau', 2, 2 )
def thien_hau( c ):
    # gate hall and main hall under green glazed roofs, side galleries, the open courtyard
    # with its great burner, the guardian lions in the terracotta forecourt
    c.rect( 2, 1, 29, 4, CLAY )
    c.px( 12, 3, WHITE )
    c.px( 19, 3, WHITE )
    tile_roof( c, 2, 5, 29, 12, GLAZE )                           # gate hall
    tile_roof( c, 2, 19, 29, 29, GLAZE )                          # main hall
    tile_roof( c, 2, 12, 9, 19, shade( GLAZE, 0.85 ), ridge=False )    # side galleries
    tile_roof( c, 22, 12, 29, 19, shade( GLAZE, 0.85 ), ridge=False )
    c.rect( 10, 13, 21, 18, CLAY )                                # the courtyard
    c.ellipse( 15.5, 15.5, 1.8, 1.6, rgb( '#a07a3a' ) )           # the burner
    c.px( 15, 14, rgb( '#ff8a3a' ) )
    c.rect( 14, 5, 17, 5, INK )                                   # the gate


@composite( 'sgn_lm_ngoc_hoang', 2, 2 )
def ngoc_hoang( c ):
    # the walled garden with its turtle pond and trees, the path to the dark temple
    c.rect( 1, 1, 30, 11, PARK )
    c.line( 1, 1, 30, 1, rgb( '#c8a070' ) )
    c.erase( 13, 1, 18, 1 )
    c.rect( 13, 2, 18, 11, CLAY )
    c.ellipse( 24.5, 6.5, 5, 3.2, rgb( '#c8a070' ) )             # the turtle pond, stone rim
    c.ellipse( 24.5, 6.5, 4, 2.4, rgb( '#4aa0b8' ) )
    for x, y in ( ( 23, 6 ), ( 26, 7 ), ( 25, 5 ) ):               # turtles basking
        c.px( x, y, rgb( '#6a5a2a' ) )
    for x, y in ( ( 4, 4 ), ( 8, 7 ), ( 4, 9 ), ( 21, 10 ) ):
        c.ellipse( x, y, 1.6, 1.6, TREE )
    tile_roof( c, 3, 12, 28, 19, GLAZE )                          # front hall
    tile_roof( c, 3, 19, 21, 29, shade( GLAZE, 0.9 ) )            # Jade Emperor hall
    tile_roof( c, 21, 19, 28, 29, shade( GLAZE, 0.75 ), ridge=False )  # Hall of the Ten Hells
    c.rect( 14, 12, 17, 12, INK )


@composite( 'sgn_lm_binh_tay', 3, 3 )
def binh_tay( c ):
    # four wings under terracotta roofs around the garden courtyard with the dragon fountain,
    # pavilion roofs at the corners, the clock tower over the north gate
    tile_roof( c, 3, 6, 44, 17, TERRACOTTA )                      # north wing
    tile_roof( c, 3, 32, 44, 44, TERRACOTTA )                     # south wing
    tile_roof( c, 3, 17, 15, 32, TERRACOTTA, ridge=False )        # west wing
    tile_roof( c, 32, 17, 44, 32, TERRACOTTA, ridge=False )       # east wing
    for x0, y0 in ( ( 2, 5 ), ( 39, 5 ), ( 2, 39 ), ( 39, 39 ) ):  # corner pavilions
        walls( c, x0, y0, x0 + 6, y0 + 6, GLAZE, shade( GLAZE, 0.55 ) )
        c.px( x0 + 3, y0 + 3, rgb( '#f0c040' ) )
    c.rect( 16, 18, 31, 31, CLAY )                                # the courtyard
    for x0, y0 in ( ( 17, 19 ), ( 26, 19 ), ( 17, 27 ), ( 26, 27 ) ):
        c.rect( x0, y0, x0 + 3, y0 + 3, GRASS )
        c.ellipse( x0 + 1.5, y0 + 1.5, 1.3, 1.3, TREE )
    c.ellipse( 23.5, 24.5, 2.6, 2, WATER )                        # the dragon fountain
    c.px( 23, 24, rgb( '#3aa05a' ) )
    c.px( 24, 25, rgb( '#e0c040' ) )
    c.px( 23, 21, WHITE )                                         # Quách Đàm's statue
    walls( c, 19, 0, 28, 7, rgb( '#f0d478' ), shade( OCHRE, 0.55 ) )   # clock tower
    c.rect( 21, 1, 26, 3, GLAZE )
    clock( c, 23.5, 5 )
