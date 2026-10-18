"""Saigon street trees, fruit trees and garden plants (terrain/furniture in region/flora.json).

Sizes and anchoring follow UltimateCataclysm's trees: 96x96 (giant.png, offset -32,-64)
with the trunk rooted in the bottom-centre 32x32 cell, 64x64 for small trees
(large.png, offset -16,-32), 32x32 for shrubs and flowers.  Trees carry a ground tile
as "bg"; that tile (sgn__ground96 / sgn__ground64, sgn__ground32 under shrubs) is a copy of UltimateCataclysm's
summer grass under t_tree (CC-BY-SA 3.0, the UltimateCataclysm contributors).

Species, by how common they are in a 2000s Saigon street or yard:
  cây bàng (tropical almond), cây me (tamarind), cây sao đen (sao, the tall avenue tree),
  cây dừa (coconut palm), cây xoài (mango), cây chuối (banana), cây đu đủ (papaya),
  hoa giấy (bougainvillea), vạn thọ (marigold), dừa cạn (periwinkle).
"""
import math

from draw import sprite, rgb, shade, base_sprite, foliage, cast_shadow

OUTLINE = 0.42
BARK = rgb( '#6e5440' )
BARK_DARK = rgb( '#4a3828' )
BARK_LIGHT = rgb( '#957a5e' )


def ground( c ):
    src = base_sprite( 't_tree_season_summer', 'bg' )
    ox, oy = ( src.width - c.width ) // 2, src.height - c.height
    for y in range( c.height ):
        for x in range( c.width ):
            c.set( x, y, src.get( x + ox, y + oy ) )


@sprite( 'sgn__ground96', 96, 96 )
def ground96( c ):
    ground( c )


@sprite( 'sgn__ground64', 64, 64 )
def ground64( c ):
    ground( c )


@sprite( 'sgn__ground32', 32, 32 )
def ground32( c ):
    src = base_sprite( 't_shrub', 'bg' )   # the grass under UltimateCataclysm's shrubs
    c.paste( src, 0, 0 )


TREE = { 'bg': '@sgn__ground96' }
SMALL_TREE = { 'bg': '@sgn__ground64' }


def trunk( c, x0, y0, x1, y1, w0, w1, bark=BARK ):
    """Tapered trunk from the root (x0, y0) up to (x1, y1), lit from the left."""
    c.capsule( x0, y0, x1, y1, w0, shade( bark, 0.75 ), w1 )
    c.capsule( x0 - 0.6, y0, x1 - 0.6, y1, w0 * 0.7, bark, w1 * 0.7 )
    c.capsule( x0 - w0 * 0.5, y0, x1 - w1 * 0.5, y1, 0.5, shade( bark, 1.25 ), 0.5 )
    c.ellipse( x0, y0 + 1, w0 + 2, 1.5, shade( bark, 0.6 ) )   # root flare


def finish( c, shadow=( 10, -5 ) ):
    c.outline( OUTLINE )
    cast_shadow( c, *shadow, alpha=55 )


def canopy_points( c, cx, cy, rx, ry, n, flat=1.0 ):
    pts = []
    while len( pts ) < n:
        x, y = c.rand.uniform( -1, 1 ), c.rand.uniform( -1, 1 )
        if x * x + y * y <= 1:
            pts.append( ( cx + x * rx, cy + y * ry * flat ) )
    return pts


# --- street shade trees -------------------------------------------------------------------

@sprite( 't_sgn_tree_bang', 96, 96, **TREE )
def bang( c ):
    # tropical almond: straight trunk, branches in flat horizontal tiers, big leaves, a few red
    trunk( c, 48, 88, 47, 30, 3.2, 1.6 )
    for y, half in ( ( 60, 22 ), ( 46, 27 ), ( 32, 24 ), ( 19, 15 ) ):
        c.line( 47 - half * 0.6, y + 2, 47 + half * 0.6, y + 2, BARK_DARK )
        pts = [ ( 47 + c.rand.uniform( -half, half ), y + c.rand.uniform( -3, 3 ) ) for _ in range( half // 2 + 4 ) ]
        foliage( c, pts, rgb( '#2f5a24' ), rgb( '#4f8a32' ), rgb( '#86b84a' ), radius=( 3, 4.5 ) )
    for _ in range( 9 ):  # leaves turning red before they drop
        x, y = 47 + c.rand.uniform( -24, 24 ), c.rand.choice( ( 46, 32, 60 ) ) + c.rand.uniform( -2, 2 )
        if c.opaque( int( x ), int( y ) ):
            c.ellipse( x, y, 1.6, 1.2, rgb( '#c8462a' ) )
    finish( c )


@sprite( 't_sgn_tree_me', 96, 96, **TREE )
def me( c ):
    # tamarind: gnarled trunk, wide feathery canopy of tiny leaflets, hanging brown pods
    trunk( c, 48, 88, 45, 50, 3.6, 2.4 )
    c.capsule( 45, 52, 33, 38, 1.6, BARK, 1.0 )
    c.capsule( 46, 50, 60, 36, 1.6, BARK, 1.0 )
    pts = canopy_points( c, 47, 32, 34, 22, 70 )
    foliage( c, pts, rgb( '#3a6a24' ), rgb( '#6a9a3a' ), rgb( '#a8cc66' ), radius=( 2.5, 4 ) )
    c.noise( 13, 10, 81, 54, [ rgb( '#b8d878' ), rgb( '#4a7a2a' ) ], 0.12 )   # feathery texture
    for _ in range( 10 ):
        x, y = 47 + c.rand.uniform( -26, 26 ), 32 + c.rand.uniform( 4, 20 )
        if c.opaque( int( x ), int( y ) ):
            c.line( x, y, x + 1, y + 3, rgb( '#8a5a2e' ) )
    finish( c )


@sprite( 't_sgn_tree_sao', 96, 96, **TREE )
def sao( c ):
    # sao đen: the tall avenue tree, a long straight grey trunk and a narrow high crown
    trunk( c, 48, 88, 48, 18, 3.2, 1.8, bark=rgb( '#77706a' ) )
    for y in range( 40, 86, 7 ):  # bark fissures
        c.line( 47, y, 47, y + 3, rgb( '#55504a' ) )
    pts = canopy_points( c, 48, 18, 17, 14, 34 )
    foliage( c, pts, rgb( '#1e4220' ), rgb( '#336a32' ), rgb( '#5f9a48' ), radius=( 3, 4.5 ) )
    finish( c, shadow=( 12, -3 ) )


@sprite( 't_sgn_tree_bo_de', 96, 96, **TREE )
def bo_de( c ):
    # sacred fig of the pagoda courtyard: thick buttressed trunk wrapped in a red sash,
    # a huge glossy crown of heart-shaped leaves with long drip tips
    trunk( c, 48, 88, 47, 48, 5.0, 3.0, bark=rgb( '#8a8274' ) )
    for dx in ( -7, -4, 4, 7 ):  # buttress roots
        c.capsule( 48 + dx * 0.4, 84, 48 + dx, 89, 1.2, rgb( '#7a7264' ), 0.8 )
    c.rect( 43, 66, 52, 68, rgb( '#c8262a' ) )
    c.line( 43, 66, 52, 66, rgb( '#e85050' ) )
    c.capsule( 50, 68, 52, 74, 0.8, rgb( '#c8262a' ) )
    c.ellipse( 47, 33, 33, 22, rgb( '#2a5a24' ) )
    pts = canopy_points( c, 47, 32, 36, 25, 130 )
    foliage( c, pts, rgb( '#2a5a24' ), rgb( '#4a8a34' ), rgb( '#8ac458' ), radius=( 3, 5 ) )
    for _ in range( 40 ):  # drip tips
        x, y = 47 + c.rand.uniform( -36, 36 ), 32 + c.rand.uniform( -22, 26 )
        if c.opaque( int( x ), int( y ) ) and not c.opaque( int( x ), int( y ) + 2 ):
            c.px( x, y + 1, rgb( '#3a7a2c' ) )
    finish( c )


# --- fruit trees (harvestable versions show fruit) -------------------------------------------

def coconut_palm( c, fruit ):
    # curved ringed trunk leaning out, a crown of drooping pinnate fronds
    pts = [ ( 48 - 7 * ( 1 - math.cos( t * math.pi / 2 ) ) - 2 * t, 88 - 66 * t ) for t in [ i / 30 for i in range( 31 ) ] ]
    for i, ( x, y ) in enumerate( pts ):
        w = 2.6 - 0.9 * i / 30
        c.ellipse( x, y, w, 1.2, BARK_LIGHT if i % 3 else BARK )
    crown_x, crown_y = pts[-1]
    if fruit:
        for dx, dy in ( ( -2, 3 ), ( 1, 4 ), ( 3, 2 ), ( -1, 5 ), ( 2, 6 ) ):
            c.ellipse( crown_x + dx, crown_y + dy, 2, 2, rgb( '#6a8a2a' ), light=rgb( '#9ab84a' ) )
    for k in range( 11 ):
        angle = k * 2 * math.pi / 11 + 0.3
        length = c.rand.uniform( 22, 30 )
        prev = ( crown_x, crown_y )
        for s in range( 1, 13 ):
            t = s / 12
            x = crown_x + math.cos( angle ) * length * t
            y = crown_y + math.sin( angle ) * length * t * 0.55 + 14 * t * t   # droop
            c.line( prev[0], prev[1], x, y, rgb( '#c8c070' ) )
            for side in ( -1, 1 ):  # leaflets hang down from the rib
                lx = x + math.cos( angle + side * 1.2 ) * 4 * ( 1 - t * 0.5 )
                ly = y + 3 + math.sin( angle + side * 1.2 ) * 2
                c.line( x, y, lx, ly, rgb( '#3f7a2a' ) if side < 0 else rgb( '#5f9a3a' ) )
            prev = ( x, y )
    c.ellipse( crown_x, crown_y, 2.5, 2, rgb( '#8a8a3a' ) )
    finish( c, shadow=( 12, -4 ) )


@sprite( 't_sgn_tree_dua', 96, 96, **TREE )
def dua( c ):
    coconut_palm( c, True )


@sprite( 't_sgn_tree_dua_harvested', 96, 96, **TREE )
def dua_harvested( c ):
    coconut_palm( c, False )


def mango( c, fruit ):
    # dense, dark, dome-shaped evergreen crown of long leaves
    trunk( c, 48, 88, 47, 52, 3.4, 2.2 )
    pts = canopy_points( c, 47, 36, 30, 24, 80 )
    foliage( c, pts, rgb( '#1a3a1c' ), rgb( '#2f5e2c' ), rgb( '#5a8a40' ), radius=( 3, 4.5 ) )
    if fruit:
        for _ in range( 12 ):
            x, y = 47 + c.rand.uniform( -24, 24 ), 36 + c.rand.uniform( -6, 20 )
            if c.opaque( int( x ), int( y ) ):
                c.line( x, y - 2, x, y, rgb( '#3a5a22' ) )
                c.ellipse( x, y + 1.5, 1.4, 2, rgb( '#c8c03a' ), light=rgb( '#e8e070' ) )
    finish( c )


@sprite( 't_sgn_tree_xoai', 96, 96, **TREE )
def xoai( c ):
    mango( c, True )


@sprite( 't_sgn_tree_xoai_harvested', 96, 96, **TREE )
def xoai_harvested( c ):
    mango( c, False )


def banana( c, fruit ):
    # pseudostem with big paddle leaves, some split by the wind, one dry and hanging
    trunk( c, 32, 58, 31, 26, 3.0, 2.2, bark=rgb( '#6a7a3a' ) )
    c.line( 30, 30, 30, 56, rgb( '#8a9a4a' ) )
    leaves = ( ( -2.7, 27 ), ( -2.0, 26 ), ( -1.35, 25 ), ( -0.6, 27 ), ( -3.4, 22 ), ( 0.25, 22 ), ( -1.65, 18 ) )
    for n, ( angle, length ) in enumerate( leaves ):
        tip = ( 31 + math.cos( angle ) * length, 24 + math.sin( angle ) * length * 0.75 )
        body = rgb( '#5aa03a' ) if n % 2 else rgb( '#4a9030' )
        for t in [ i / 24 for i in range( 25 ) ]:
            x, y = 31 + ( tip[0] - 31 ) * t, 24 + ( tip[1] - 24 ) * t + 7 * t * t
            w = 4.6 * math.sin( math.pi * min( 0.96, t * 0.88 + 0.1 ) )
            c.ellipse( x, y, w, w * 0.75, body )
            c.ellipse( x - w * 0.3, y - w * 0.3, w * 0.4, w * 0.3, shade( body, 1.2 ) )
        for t in [ i / 24 for i in range( 25 ) ]:
            x, y = 31 + ( tip[0] - 31 ) * t, 24 + ( tip[1] - 24 ) * t + 7 * t * t
            c.px( x, y, rgb( '#c8e080' ) )   # midrib
        for t in ( 0.45, 0.7 ):  # wind tears
            x, y = 31 + ( tip[0] - 31 ) * t, 24 + ( tip[1] - 24 ) * t + 7 * t * t
            c.line( x, y, x + math.cos( angle + 1.5 ) * 3, y + math.sin( angle + 1.5 ) * 3, rgb( '#3a7a2a' ) )
    c.capsule( 31, 34, 37, 46, 1.6, rgb( '#9a7a4a' ), 1.0 )   # dry hanging leaf
    if fruit:
        for i in range( 4 ):
            for j in range( 3 ):
                c.ellipse( 35 + j * 2.2, 31 + i * 2.6, 1.3, 1.1, rgb( '#9ac040' ) )
        c.ellipse( 37, 43, 1.8, 2.6, rgb( '#7a2a4a' ) )        # the purple bud
    finish( c, shadow=( 8, -3 ) )


@sprite( 't_sgn_tree_chuoi', 64, 64, **SMALL_TREE )
def chuoi( c ):
    banana( c, True )


@sprite( 't_sgn_tree_chuoi_harvested', 64, 64, **SMALL_TREE )
def chuoi_harvested( c ):
    banana( c, False )


def papaya( c, fruit ):
    # slender scarred trunk, an umbrella of deeply lobed leaves on long stalks
    trunk( c, 32, 58, 32, 22, 2.0, 1.5, bark=rgb( '#8a8a7a' ) )
    for y in range( 26, 56, 4 ):
        c.line( 31, y, 33, y, rgb( '#6a6a5a' ) )
    if fruit:
        for dx, dy in ( ( -3, 25 ), ( 3, 25 ), ( -2, 29 ), ( 2, 29 ), ( 0, 27 ) ):
            c.ellipse( 32 + dx, dy, 1.6, 2.4, rgb( '#7a9a2a' ) if dy > 26 else rgb( '#e8902a' ), light=rgb( '#c8d860' ) )
    for k in range( 8 ):
        angle = -math.pi + k * math.pi / 7
        lx, ly = 32 + math.cos( angle ) * 15, 20 + math.sin( angle ) * 9
        c.line( 32, 21, lx, ly, rgb( '#a8b860' ) )
        foliage( c, [ ( lx + c.rand.uniform( -2, 2 ), ly + c.rand.uniform( -1, 1 ) ) for _ in range( 3 ) ],
                 rgb( '#2f6a24' ), rgb( '#4f9a32' ), rgb( '#8ac850' ), radius=( 2, 3 ) )
    finish( c, shadow=( 7, -3 ) )


@sprite( 't_sgn_tree_du_du', 64, 64, **SMALL_TREE )
def du_du( c ):
    papaya( c, True )


@sprite( 't_sgn_tree_du_du_harvested', 64, 64, **SMALL_TREE )
def du_du_harvested( c ):
    papaya( c, False )


# --- shrubs and flowers (32x32) ---------------------------------------------------------------

@sprite( 't_sgn_shrub_hoa_giay', 32, 32, bg='@sgn__ground32' )
def hoa_giay( c ):
    # bougainvillea: a sprawling thorny mass smothered in magenta bracts
    pts = canopy_points( c, 16, 18, 11, 9, 16 )
    foliage( c, pts, rgb( '#244a1c' ), rgb( '#3f7a2a' ), rgb( '#6aa040' ), radius=( 2.5, 3.5 ) )
    for _ in range( 22 ):
        x, y = 16 + c.rand.uniform( -11, 11 ), 18 + c.rand.uniform( -8, 8 )
        if c.opaque( int( x ), int( y ) ):
            c.ellipse( x, y, 1.3, 1.0, rgb( '#d82a8a' ) )
            c.px( x - 0.5, y - 0.5, rgb( '#f070b8' ) )
    finish( c, shadow=( 3, -1 ) )


def flowers( c, petal, centre ):
    for _ in range( 7 ):
        x, y = 16 + c.rand.uniform( -9, 9 ), 18 + c.rand.uniform( -7, 7 )
        c.line( x, y + 1, x + c.rand.uniform( -1, 1 ), y + 4, rgb( '#3f7a2a' ) )
        c.ellipse( x + 1.5, y + 3, 1.5, 0.8, rgb( '#4f8a32' ) )
        c.ellipse( x, y, 1.6, 1.4, petal )
        c.px( x, y, centre )
    finish( c, shadow=( 2, -1 ) )


@sprite( 'f_sgn_van_tho', 32, 32 )
def van_tho( c ):
    # marigolds, grown in every yard for Tết
    flowers( c, rgb( '#f29a1a' ), rgb( '#c8601a' ) )


@sprite( 'f_sgn_dua_can', 32, 32 )
def dua_can( c ):
    # Madagascar periwinkle, the hardy pink-and-white flower of cracked pavements
    flowers( c, rgb( '#f07aa8' ), rgb( '#a81a4a' ) )


# --- wild plants of vacant lots, canal banks and field edges (G19) ----------------------------

@sprite( 't_sgn_shrub_ngu_sac', 32, 32, bg='@sgn__ground32' )
def ngu_sac( c ):
    # lantana: a rough green mound dotted with little flower domes, yellow to orange to pink
    pts = canopy_points( c, 16, 18, 11, 8, 14 )
    foliage( c, pts, rgb( '#2a4a1e' ), rgb( '#4a7a2e' ), rgb( '#7aa44a' ), radius=( 2.5, 3.5 ) )
    for colour in ( rgb( '#f2c232' ), rgb( '#f08a2c' ), rgb( '#e8508e' ) ) * 4:
        x, y = 16 + c.rand.uniform( -10, 10 ), 18 + c.rand.uniform( -7, 6 )
        if c.opaque( int( x ), int( y ) ):
            c.ellipse( x, y, 1.2, 1.0, colour )
    finish( c, shadow=( 3, -1 ) )


@sprite( 't_sgn_shrub_khoai_mi', 32, 32, bg='@sgn__ground32' )
def khoai_mi( c ):
    # cassava: knobbly red-brown stems topped with hand-shaped leaves
    for x0, lean in ( ( 12, -2 ), ( 16, 0 ), ( 20, 3 ) ):
        c.line( x0, 28, x0 + lean, 10, rgb( '#8a4a3a' ) )
        for y in range( 14, 27, 4 ):
            c.px( x0 + lean * ( 28 - y ) / 18, y, rgb( '#5a2a20' ) )   # leaf scars
    for cx, cy in ( ( 10, 10 ), ( 16, 7 ), ( 23, 10 ), ( 13, 14 ), ( 20, 15 ) ):
        for k in range( 5 ):                                          # palmate leaflets
            a = -2.6 + k * 0.55
            c.capsule( cx, cy, cx + 5 * math.cos( a ), cy + 4 * math.sin( a ), 0.9, rgb( '#3f7a2a' ), 0.4 )
        c.px( cx, cy, rgb( '#a85a4a' ) )
    finish( c, shadow=( 3, -1 ) )


@sprite( 'f_sgn_xau_ho', 32, 32 )
def xau_ho( c ):
    # sensitive plant: a low creeper of feathery leaves with pink pompom flowers
    for _ in range( 9 ):
        x, y = 16 + c.rand.uniform( -10, 10 ), 19 + c.rand.uniform( -6, 6 )
        a = c.rand.uniform( 0, math.pi )
        dx, dy = 4 * math.cos( a ), 2 * math.sin( a )
        c.line( x - dx, y - dy, x + dx, y + dy, rgb( '#3f6a2a' ) )
        for t in ( -0.6, -0.2, 0.2, 0.6 ):                            # leaflet pairs
            c.px( x + dx * t, y + dy * t - 1, rgb( '#6a9a3a' ) )
            c.px( x + dx * t, y + dy * t + 1, rgb( '#6a9a3a' ) )
    for _ in range( 4 ):
        x, y = 16 + c.rand.uniform( -8, 8 ), 18 + c.rand.uniform( -5, 5 )
        c.ellipse( x, y, 1.6, 1.6, rgb( '#f07ab8' ) )
        c.px( x, y, rgb( '#ffb8d8' ) )
    finish( c, shadow=( 2, -1 ) )
