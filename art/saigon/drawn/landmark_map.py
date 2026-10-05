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


# --- L3 (A6) ----------------------------------------------------------------------------------
GLASS = rgb( '#3ab0b0' )
RAIL = rgb( '#8a7a6a' )
CANOPY = rgb( '#a0a4aa' )


@composite( 'sgn_lm_ga_sai_gon', 3, 3 )
def ga_sai_gon( c ):
    # the long station hall on the forecourt, then platform canopies between the tracks
    c.rect( 4, 2, 43, 4, PAVE )
    walls( c, 4, 5, 43, 16, rgb( '#e4e0d4' ), shade( CREAM, 0.6 ) )
    for x in range( 6, 42, 3 ):                                   # the hall's arched windows
        c.px( x, 6, rgb( '#6aa0c8' ) )
    c.rect( 22, 5, 25, 5, INK )
    for y0 in ( 17, 25, 32, 40 ):                                 # platform canopies
        c.rect( 1, y0, 46, y0 + 1, CANOPY )
    for y in ( 20, 22, 28, 30, 35, 37, 43, 45 ):                  # tracks
        c.line( 0, y, 47, y, RAIL )
    for y in range( 19, 47, 1 ):
        if y % 2:
            for x in range( 0, 48, 3 ):
                if c.get( x, y )[3] == 0:
                    c.px( x, y, rgb( '#5a4a3a' ) )                # sleepers
    for x0, y0 in ( ( 3, 20 ), ( 18, 20 ), ( 33, 20 ), ( 18, 35 ), ( 33, 35 ) ):   # the stranded trains
        c.rect( x0, y0, x0 + 11, y0 + 2, rgb( '#2a6a9a' ) )
        c.line( x0, y0 + 1, x0 + 11, y0 + 1, rgb( '#e8e0c8' ) )


@composite( 'sgn_lm_ben_xe_md', 3, 3 )
def ben_xe_md( c ):
    # the ticket hall, the kiosk canopy, the loading bays, and the yard full of coaches
    walls( c, 3, 3, 27, 12, rgb( '#e4e0d4' ), shade( CREAM, 0.6 ) )
    c.rect( 13, 3, 15, 3, INK )
    c.rect( 30, 3, 45, 6, rgb( '#c86a3a' ) )                      # kiosk canopy
    c.rect( 1, 14, 46, 16, CANOPY )                               # loading bays
    c.rect( 1, 17, 46, 46, rgb( '#5a5a5e' ) )                     # the yard
    for row, y in enumerate( ( 19, 26, 35, 42 ) ):
        for col, x in enumerate( ( 3, 19, 35 ) ):
            colour = ( '#e8c040', '#3a7ac8', '#e8e8e8', '#c84a3a' )[( row + col ) % 4]
            c.rect( x, y, x + 9, y + 3, rgb( colour ) )           # coaches
            c.line( x + 1, y + 1, x + 8, y + 1, rgb( '#2a3a4a' ) )   # windows


@composite( 'sgn_lm_tao_dan', 3, 3 )
def tao_dan( c ):
    # old trees over lawns inside the railing, the cross walks and the round centre, the bird
    # café's pavilion in the corner
    c.rect( 1, 1, 46, 46, PARK )
    c.frame( 1, 1, 46, 46, PAVE )
    c.rect( 22, 1, 25, 46, CLAY )
    c.rect( 1, 22, 46, 25, CLAY )
    c.ring( 23.5, 23.5, 8, 8, CLAY, 2 )
    for y in range( 4, 45, 5 ):
        for x in range( 4 + ( y // 5 ) % 2 * 2, 45, 5 ):
            if c.get( x, y )[:3] == PARK[:3]:
                c.ellipse( x, y, 1.8, 1.8, TREE )
                c.px( x - 1, y - 1, shade( TREE, 1.4 ) )
    walls( c, 32, 4, 43, 12, TERRACOTTA, shade( TERRACOTTA, 0.6 ) )   # the bird café
    for x in range( 34, 42, 3 ):
        c.px( x, 8, rgb( '#e8d080' ) )


@composite( 'sgn_lm_ho_con_rua', 1, 1 )
def ho_con_rua( c ):
    # the round pool and the white lotus-and-spire monument
    c.ellipse( 7.5, 8.5, 6.5, 6.5, CLAY )
    c.ellipse( 7.5, 8.5, 5, 5, WATER )
    c.ellipse( 7.5, 8.5, 2.2, 2.2, WHITE )
    c.px( 7, 8, rgb( '#b0b0b8' ) )
    c.px( 13, 13, rgb( '#e0e0e8' ) )                              # the drinks kiosk


@composite( 'sgn_lm_stc', 1, 1 )
def stc( c ):
    # the glass tower seen from above: a teal block, its light side, the crown on the roof
    c.rect( 2, 3, 13, 14, shade( GLASS, 0.7 ) )
    c.rect( 2, 3, 12, 13, GLASS )
    c.line( 2, 3, 12, 3, shade( GLASS, 1.4 ) )
    c.line( 2, 3, 2, 13, shade( GLASS, 1.3 ) )
    c.rect( 5, 6, 9, 10, rgb( '#d8dce0' ) )                       # the crown
    c.ellipse( 7, 8, 1.4, 1.4, rgb( '#d04040' ) )                 # aircraft warning light


@composite( 'sgn_lm_diamond', 2, 2 )
def diamond( c ):
    # the mall's glass block with its diamond crown, the plaza on the street
    c.rect( 2, 1, 29, 3, PAVE )
    walls( c, 2, 4, 29, 29, GLASS, shade( GLASS, 0.6 ) )
    for y in range( 6, 28, 3 ):
        c.line( 3, y, 28, y, shade( GLASS, 0.85 ) )
    c.polygon( [ ( 15.5, 9 ), ( 23, 16.5 ), ( 15.5, 24 ), ( 8, 16.5 ) ], WHITE )   # the diamond
    c.polygon( [ ( 15.5, 11 ), ( 21, 16.5 ), ( 15.5, 22 ), ( 10, 16.5 ) ], rgb( '#a8e0f0' ) )
    c.rect( 13, 4, 18, 4, INK )


@composite( 'sgn_lm_bui_vien', 3, 1 )
def bui_vien( c ):
    # twelve narrow roofs of the backpacker street, neon signs and beer tables on the sidewalk
    c.rect( 0, 1, 47, 3, PAVE )
    for k in range( 12 ):
        x0 = k * 4
        colour = ( '#c86a3a', '#d8b860', '#a0a4aa', '#c84a5a' )[k % 4]
        walls( c, x0, 4, x0 + 3, 14, rgb( colour ), shade( rgb( colour ), 0.6 ) )
        neon = ( '#ff40c0', '#40e0ff', '#ffe040', '#60ff60' )[( k * 3 ) % 4]
        c.px( x0 + 1, 3, rgb( neon ) )
        c.px( x0 + 2, 3, rgb( neon ) )
    for x in range( 1, 47, 3 ):
        c.px( x, 1, rgb( '#e04040' ) )                            # the red plastic stools


# --- L4: the zoo and the amusement parks ------------------------------------------------------
LAKE = rgb( '#3a8ac8' )
LOTUS = rgb( '#4a9a3a' )
SAND = rgb( '#e8d49a' )


def fence( c, w, h ):
    c.rect( 0, 1, w - 1, h - 1, PARK )
    c.frame( 0, 1, w - 1, h - 1, PAVE )


@composite( 'sgn_lm_thao_cam_vien', 4, 4 )
def thao_cam_vien( c ):
    # trees over the grounds, the museum and the temple either side of the avenue, the lotus
    # lake, and the enclosures: tigers, bears, elephants, the crocodile garden
    fence( c, 64, 64 )
    for y in range( 4, 40, 5 ):
        for x in range( 3 + ( y // 5 ) % 2 * 3, 62, 6 ):
            c.ellipse( x, y, 1.6, 1.6, TREE )
    c.rect( 29, 1, 34, 42, CLAY )                                  # the avenue
    c.rect( 2, 27, 61, 29, CLAY )                                  # the cross walk
    tile_roof( c, 5, 4, 23, 15, TERRACOTTA )                       # the history museum
    tile_roof( c, 40, 5, 53, 14, GLAZE )                           # the Hùng Kings temple
    c.ellipse( 46.5, 20, 10, 4.5, LOTUS )                          # the lotus lake
    c.ellipse( 46.5, 20, 6, 2.2, LAKE )
    for x0, x1, col in ( ( 4, 17, '#e0a040' ), ( 20, 29, '#5a4a3a' ), ( 33, 48, '#a07a50' ) ):   # tiger, bear, elephant yards
        c.frame( x0, 43, x1, 60, PAVE )
        c.rect( x0 + 1, 44, x1 - 1, 59, shade( PARK, 1.15 ) if col != '#a07a50' else rgb( '#9a7a50' ) )
        c.ellipse( ( x0 + x1 ) / 2, 52, 2, 1.4, rgb( col ) )        # the animal
    c.frame( 51, 32, 62, 47, PAVE )                                # the crocodile garden
    c.ellipse( 56.5, 39.5, 4, 5, rgb( '#4a6a4a' ) )
    c.px( 55, 39, rgb( '#7a9a3a' ) )
    walls( c, 35, 31, 46, 38, rgb( '#d4d4d8' ), shade( CREAM, 0.6 ) )   # the reptile house


@composite( 'sgn_lm_dam_sen', 4, 4 )
def dam_sen( c ):
    # the lotus-edged lake with the island pagoda and its causeway, the swan boats, the
    # Ferris wheel, the rock garden, the royal bonsai garden, and the park train's loop
    fence( c, 64, 64 )
    c.frame( 2, 3, 61, 61, RAIL )                                  # the park train
    c.ellipse( 32, 36, 21, 16, LOTUS )
    c.ellipse( 32, 36, 19, 14, LAKE )
    c.ellipse( 32, 36, 5, 4, PARK )
    tile_roof( c, 30, 34, 34, 38, GLAZE, ridge=False )             # island pagoda
    c.rect( 31, 40, 33, 53, CLAY )                                 # causeway
    c.rect( 29, 1, 34, 18, CLAY )
    for x in range( 26, 39, 3 ):                                   # swan boats
        c.px( x, 20, WHITE )
    c.ring( 53.5, 10.5, 5, 5, WHITE, 1 )                           # the Ferris wheel
    c.px( 53, 10, rgb( '#e04040' ) )
    c.px( 57, 8, rgb( '#f0c020' ) )
    c.px( 50, 13, rgb( '#3a8ae0' ) )
    for x, y in ( ( 5, 28 ), ( 7, 31 ), ( 5, 34 ), ( 8, 36 ) ):    # rock garden
        c.ellipse( x, y, 1.6, 1.4, rgb( '#9a948a' ) )
    c.rect( 5, 7, 20, 17, CLAY )                                   # the royal bonsai garden
    for y in range( 8, 17, 2 ):
        for x in range( 6, 20, 2 ):
            c.px( x, y, TREE )
    walls( c, 43, 55, 56, 60, TERRACOTTA, shade( TERRACOTTA, 0.6 ) )   # the restaurant


@composite( 'sgn_lm_suoi_tien', 4, 4 )
def suoi_tien( c ):
    # the beach and lagoon under the cliff with the giant, the crocodile lake, the painted
    # dragons in the gardens, the Ferris wheel, the temple, the kỳ lân gate
    fence( c, 64, 64 )
    c.frame( 2, 3, 61, 60, RAIL )
    c.rect( 28, 1, 35, 26, CLAY )
    c.px( 27, 2, rgb( '#e0b030' ) )                                # kỳ lân guardians
    c.px( 36, 2, rgb( '#e0b030' ) )
    c.rect( 4, 29, 29, 58, SAND )                                  # Biển Tiên Đồng
    c.ellipse( 16.5, 47, 11, 8, LAKE )
    c.rect( 4, 56, 29, 58, rgb( '#8a8478' ) )                      # the cliff
    c.ellipse( 16.5, 55, 3, 3.5, rgb( '#2e8a5a' ) )                # Lạc Long Quân
    c.px( 16, 53, rgb( '#e0c040' ) )
    c.frame( 36, 32, 61, 46, rgb( '#c8c4b4' ) )                    # Crocodile Kingdom
    c.ellipse( 48.5, 39, 10, 5.5, rgb( '#4a6a4a' ) )
    for x in ( 44, 48, 52 ):
        c.px( x, 39, rgb( '#7a9a3a' ) )
    for x, y in ( ( 8, 11 ), ( 20, 20 ), ( 43, 11 ), ( 53, 21 ) ):  # the painted dragons
        for i in range( 5 ):
            c.px( x + i, y - ( i % 2 ), rgb( '#3a7ae0' ) )
        c.px( x + 5, y - 1, rgb( '#f08a20' ) )
    c.ring( 50.5, 51, 4.5, 4.5, WHITE, 1 )                         # the Ferris wheel
    c.px( 50, 51, rgb( '#e04040' ) )
    tile_roof( c, 39, 7, 51, 14, GLAZE )                           # the temple


# --- P2 everyday places (not landmarks, but they get pictures too) -------------------------
@composite( 'sgn_pl_cay_xang', 1, 1 )
def cay_xang( c ):
    # the red-and-white canopy over the pumps, the kiosk behind
    c.rect( 2, 2, 13, 7, rgb( '#e8e8e8' ) )
    c.rect( 2, 2, 13, 3, rgb( '#d83030' ) )
    for x in ( 4, 7, 10, 12 ):
        c.px( x, 5, rgb( '#f0c020' ) )
    walls( c, 3, 9, 12, 14, rgb( '#d4d4d8' ), shade( CREAM, 0.6 ) )


@composite( 'sgn_pl_coopmart', 2, 2 )
def coopmart( c ):
    # a big flat-roofed box with the red sign over the glass front
    walls( c, 1, 3, 30, 30, rgb( '#c8ccd0' ), shade( CREAM, 0.6 ) )
    c.rect( 8, 3, 23, 5, rgb( '#d83030' ) )
    c.line( 10, 4, 21, 4, rgb( '#f4f4f4' ) )
    for y in range( 9, 28, 4 ):
        c.line( 3, y, 28, y, rgb( '#b0b4b8' ) )


@composite( 'sgn_pl_benh_vien', 2, 2 )
def benh_vien( c ):
    # a white two-storey block with the red cross on the roof
    walls( c, 1, 4, 30, 30, rgb( '#f0f0ec' ), shade( CREAM, 0.6 ) )
    c.rect( 13, 13, 18, 22, rgb( '#d83030' ) )
    c.rect( 11, 15, 20, 20, rgb( '#d83030' ) )
    c.rect( 13, 1, 18, 3, PAVE )


@composite( 'sgn_pl_cong_an', 1, 1 )
def cong_an( c ):
    # the yellow ward police station with its flag
    walls( c, 2, 4, 13, 14, rgb( '#e8c050' ), shade( OCHRE, 0.6 ) )
    c.line( 3, 1, 3, 4, rgb( '#c8c8cc' ) )
    c.rect( 4, 1, 6, 2, rgb( '#d83030' ) )
    c.px( 5, 1, rgb( '#f0d040' ) )


@composite( 'sgn_pl_nghia_trang', 2, 2 )
def nghia_trang( c ):
    # rows of pale tombs in the grass inside a wall, the path from the gate
    c.rect( 1, 1, 30, 30, PARK )
    c.frame( 1, 1, 30, 30, rgb( '#a8a49a' ) )
    c.rect( 14, 1, 17, 30, CLAY )
    for y in range( 4, 29, 3 ):
        for x in list( range( 3, 13, 2 ) ) + list( range( 19, 29, 2 ) ):
            c.px( x, y, rgb( '#d8e0dc' ) )
    tile_roof( c, 20, 3, 24, 6, TERRACOTTA, ridge=False )


@composite( 'sgn_pl_nha_sach', 1, 1 )
def nha_sach( c ):
    # a shopfront with coloured book spines in the window
    walls( c, 2, 3, 13, 14, rgb( '#d4d4d8' ), shade( CREAM, 0.6 ) )
    for i, x in enumerate( range( 3, 13 ) ):
        c.line( x, 4, x, 7, rgb( ( '#d83030', '#3a7ac8', '#f0c020', '#40a060' )[i % 4] ) )


@composite( 'sgn_pl_xe_may', 1, 1 )
def xe_may( c ):
    # a showroom with a row of new motorbikes behind the glass
    walls( c, 1, 3, 14, 14, rgb( '#d4d4d8' ), shade( CREAM, 0.6 ) )
    c.rect( 2, 4, 13, 8, rgb( '#a8d8e8' ) )
    for x in ( 3, 6, 9, 12 ):
        c.line( x, 5, x, 7, rgb( '#d83030' ) )
