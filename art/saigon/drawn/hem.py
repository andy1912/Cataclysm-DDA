"""Hẻm and shopfront terrain and furniture (G22): accordion gates, alley paving,
breeze-block walls and laundry lines.

The gates are see-through, so they are drawn as bars over a "bg" of alley paving (the
engine draws bg under fg).  The paving has three weighted variants so long alleys don't
tile visibly.
"""
from draw import sprite, rgb, shade

OUTLINE = 0.42
GATE = rgb( '#5f7f6e' )          # the usual faded green paint on iron
GATE_LIGHT = rgb( '#8fb09e' )
GATE_DARK = rgb( '#34463c' )
CONCRETE = rgb( '#9c988e' )


def paving( c, variant ):
    c.rect( 0, 0, 31, 31, CONCRETE )
    c.noise( 0, 0, 31, 31, [ shade( CONCRETE, 0.9 ), shade( CONCRETE, 1.08 ) ], 0.35 )
    if variant >= 1:                                   # a patch of newer concrete
        c.rect( 4, 18, 17, 27, shade( CONCRETE, 1.1 ) )
        c.frame( 4, 18, 17, 27, shade( CONCRETE, 0.8 ) )
    if variant == 2:                                   # oil stain from parked bikes
        c.ellipse( 22, 9, 5, 3, rgb( '#5a5850', 150 ) )
    # cracks
    x, y = c.rand.randint( 2, 28 ), 0
    while y < 31:
        nx, ny = x + c.rand.choice( ( -1, 0, 1 ) ), y + c.rand.randint( 2, 4 )
        c.line( x, y, nx, ny, shade( CONCRETE, 0.62 ) )
        x, y = nx, ny


@sprite( 't_sgn_hem_xi_mang', 32, 32,
         fg=[ { 'weight': 3, 'sprite': '@t_sgn_hem_xi_mang' }, { 'weight': 1, 'sprite': '@t_sgn_hem_xi_mang__patch' },
              { 'weight': 1, 'sprite': '@t_sgn_hem_xi_mang__oil' } ] )
def hem_xi_mang( c ):
    paving( c, 0 )


@sprite( 't_sgn_hem_xi_mang__patch', 32, 32 )
def hem_patch( c ):
    paving( c, 1 )


@sprite( 't_sgn_hem_xi_mang__oil', 32, 32 )
def hem_oil( c ):
    paving( c, 2 )


def gate_frame( c ):
    c.rect( 0, 2, 2, 29, GATE_DARK )                    # wall-side posts
    c.rect( 29, 2, 31, 29, GATE_DARK )
    c.rect( 0, 2, 31, 3, GATE )                         # top track
    c.line( 0, 2, 31, 2, GATE_LIGHT )
    c.rect( 0, 28, 31, 29, GATE_DARK )                  # bottom rail


@sprite( 't_sgn_cua_sat_keo_c', 32, 32, bg='@t_sgn_hem_xi_mang' )
def gate_closed( c ):
    # flat bars every 4 px, linked by a criss-cross scissor lattice
    gate_frame( c )
    for x in range( 4, 29, 4 ):
        c.rect( x, 4, x, 27, GATE )
        c.px( x, 4, GATE_LIGHT )
    for x in range( 4, 25, 4 ):
        for y0 in ( 5, 13, 21 ):
            c.line( x, y0, x + 4, y0 + 6, GATE_LIGHT )
            c.line( x + 4, y0, x, y0 + 6, GATE_DARK )
    c.rect( 26, 14, 28, 17, rgb( '#c8a028' ) )          # padlock
    c.px( 27, 13, rgb( '#7a6a3a' ) )


@sprite( 't_sgn_cua_sat_keo_o', 32, 32, bg='@t_sgn_hem_xi_mang' )
def gate_open( c ):
    # folded: the bars bunch up against the left post
    gate_frame( c )
    for x in range( 3, 9 ):
        c.rect( x, 4, x, 27, GATE if x % 2 else GATE_DARK )
    for y in range( 6, 26, 5 ):
        c.line( 3, y, 8, y + 2, GATE_LIGHT )


@sprite( 't_sgn_tuong_bong_gio', 32, 32 )
def tuong_bong_gio( c ):
    # 2x2 cast blocks, each pierced with a four-petal flower pattern
    face = rgb( '#e8e0cc' )
    hole = rgb( '#4a463e' )
    c.rect( 0, 0, 31, 31, face )
    for bx in ( 0, 16 ):
        for by in ( 0, 16 ):
            c.frame( bx, by, bx + 15, by + 15, shade( face, 0.78 ) )          # mortar joints
            cx, cy = bx + 8, by + 8
            for dx, dy in ( ( 0, -4 ), ( 4, 0 ), ( 0, 4 ), ( -4, 0 ) ):         # petals
                c.ellipse( cx + dx, cy + dy, 1.8, 1.8, hole )
            c.ellipse( cx, cy, 1.2, 1.2, hole )
            for dx, dy in ( ( -5, -5 ), ( 5, -5 ), ( 5, 5 ), ( -5, 5 ) ):       # corner diamonds
                c.polygon( [ ( cx + dx, cy + dy - 1.5 ), ( cx + dx + 1.5, cy + dy ), ( cx + dx, cy + dy + 1.5 ),
                             ( cx + dx - 1.5, cy + dy ) ], hole )
            c.line( bx + 1, by + 1, bx + 14, by + 1, shade( face, 1.1 ) )      # lit top edge
    c.noise( 0, 0, 31, 31, [ shade( face, 0.92 ) ], 0.15 )


@sprite( 'f_sgn_day_phoi', 32, 32 )
def day_phoi( c ):
    # a wire across the alley, shirts and a sarong pegged on it
    c.line( 0, 6, 31, 7, rgb( '#d8dcd8' ) )
    shirts = ( ( 2, rgb( '#e05050' ) ), ( 11, rgb( '#f2f2ee' ) ), ( 21, rgb( '#5a8ed8' ) ) )
    for x, colour in shirts:
        c.polygon( [ ( x, 7 ), ( x + 7, 7 ), ( x + 8, 10 ), ( x + 6, 10 ), ( x + 6, 17 ), ( x + 1, 17 ),
                     ( x + 1, 10 ), ( x - 1, 10 ) ], colour )
        c.line( x + 1, 8, x + 1, 16, shade( colour, 1.2 ) )
        c.px( x + 2, 7, rgb( '#f2c232' ) )                                   # pegs
        c.px( x + 5, 7, rgb( '#f2c232' ) )
    c.rect( 19, 7, 20, 22, rgb( '#7a3a8a' ) )                                # a hanging sarong
    c.rect( 29, 7, 31, 14, rgb( '#f2c232' ) )                                # a child's shorts
    c.outline( OUTLINE )
    c.drop_shadow( 2, 3, 60 )
