#!/usr/bin/env python3
"""Generate the real Saigon landmarks of the 2000s (doc/saigon/LANDMARKS.md, phase L1).

Each landmark is a multi-tile city building (OVERMAP_UNIQUE, SAIGON) drawn on one big grid
per z-level (W*24 x H*24 tiles), then cut into a multi-OMT mapgen (2-D om_terrain).
Local frame: the street is to the north, so the façade or gate faces north.  Real
proportions are scaled down to fit a city block (<= 3x3 OMT) but the recognisable parts
are kept: Bến Thành's clock-tower gate and cross aisles, the cathedral's twin towers and
nave, the post office's long hall of counters and phone booths, the theatre's arched
entrance and auditorium, City Hall's clock tower and courtyard, the palace's oval lawn,
fins and bunker.

Run from the repo root:  python3 tools/saigon/gen_saigon_landmarks.py
"""
import json
import os

ROOT = os.path.join( os.path.dirname( __file__ ), '..', '..', 'data', 'mods', 'saigon_2000s' )
CLEARING = [ 'ERASE_FURNITURE_BEFORE_PLACING_TERRAIN', 'ERASE_TRAP_BEFORE_PLACING_TERRAIN',
             'ALLOW_TERRAIN_UNDER_ITEMS' ]


class Level:
    """One z-level of a landmark: a grid of palette symbols, W*24 x H*24."""

    def __init__( self, w, h, fill ):
        self.w, self.h = w * 24, h * 24
        self.g = [ [ fill ] * self.w for _ in range( self.h ) ]

    def rect( self, x0, y0, x1, y1, ch ):
        for y in range( max( 0, y0 ), min( self.h - 1, y1 ) + 1 ):
            for x in range( max( 0, x0 ), min( self.w - 1, x1 ) + 1 ):
                self.g[y][x] = ch

    def box( self, x0, y0, x1, y1, wall, floor ):
        self.rect( x0, y0, x1, y1, wall )
        self.rect( x0 + 1, y0 + 1, x1 - 1, y1 - 1, floor )

    def at( self, x, y, ch ):
        self.g[y][x] = ch

    def ellipse( self, cx, cy, rx, ry, ch ):
        for y in range( self.h ):
            for x in range( self.w ):
                if ( ( x + 0.5 - cx ) / rx ) ** 2 + ( ( y + 0.5 - cy ) / ry ) ** 2 <= 1:
                    self.g[y][x] = ch

    def get( self, x, y ):
        return self.g[y][x]

    def rows( self ):
        return [ ''.join( r ) for r in self.g ]


def roof_over( level, indoor, roof_ch='_' ):
    """A roof level covering every tile of `level` whose symbol is in `indoor`."""
    out = Level( level.w // 24, level.h // 24, ' ' )
    for y in range( level.h ):
        for x in range( level.w ):
            if level.get( x, y ) in indoor:
                out.at( x, y, roof_ch )
    return out


INDOOR = set( '#RCH.:=^wW+DPbktrvqmyuasdcxpKZQAef<>' )


# --- 1. Chợ Bến Thành ---------------------------------------------------------------------
def ben_thanh():
    z0 = Level( 3, 3, ',' )
    z0.rect( 0, 0, 71, 3, 'S' )                         # Quách Thị Trang square
    z0.box( 4, 6, 67, 67, '#', ':' )                   # the hall
    for x in ( 34, 35, 36, 37 ):                       # south gate under the clock tower (faces the street)
        z0.at( x, 6, '+' )
    for y in ( 35, 36 ):                               # east and west main gates
        z0.at( 4, y, '+' )
        z0.at( 67, y, '+' )
    for x in ( 35, 36 ):
        z0.at( x, 67, '+' )
    for x in ( 14, 24, 47, 57 ):                       # side gates
        z0.at( x, 6, '+' )
        z0.at( x, 67, '+' )
    z0.rect( 32, 2, 39, 6, '#' )                       # clock-tower base straddling the gate
    z0.rect( 34, 3, 37, 6, ':' )
    for x in ( 34, 35, 36, 37 ):
        z0.at( x, 2, '+' )
    # four quadrants of stalls split by a cross of wide aisles (x 33-38, y 33-38)
    quads = { ( 0, 0 ): 'y', ( 1, 0 ): 'v', ( 0, 1 ): 'q', ( 1, 1 ): 'm' }   # cloth, gold, produce, meat-fish
    for ( qx, qy ), stall in quads.items():
        x0, x1 = ( 7, 30 ) if qx == 0 else ( 41, 64 )
        y0, y1 = ( 9, 30 ) if qy == 0 else ( 41, 64 )
        for y in range( y0, y1 + 1, 4 ):
            for x in range( x0, x1 + 1 ):
                if ( x - x0 ) % 8 < 6:
                    z0.at( x, y, stall )
                    if y + 1 <= y1:
                        z0.at( x, y + 1, 'k' if stall != 'v' else 'v' )
    for x in range( 8, 64, 6 ):                        # food stalls in the aisle (the famous food court)
        if not 32 <= x <= 39:
            z0.at( x, 35, 'u' )
            z0.at( x, 36, 's' )
    z1 = roof_over( z0, INDOOR )
    z1.rect( 32, 2, 39, 6, '#' )
    z2 = Level( 3, 3, ' ' )
    z2.rect( 33, 2, 38, 5, '#' )
    for x in ( 35, 36 ):
        z2.at( x, 2, 'K' )                             # the clock faces the square
    z3 = Level( 3, 3, ' ' )
    z3.rect( 34, 3, 37, 5, '_' )
    return { 0: z0, 1: z1, 2: z2, 3: z3 }


# --- 2. Nhà thờ Đức Bà ----------------------------------------------------------------------
def duc_ba():
    z0 = Level( 2, 3, ',' )
    z0.rect( 0, 0, 47, 1, 'S' )
    z0.rect( 4, 3, 43, 10, ',' )                       # Công xã Paris square
    z0.ellipse( 24, 7, 4, 2.5, 'g' )
    z0.at( 23, 7, 'Z' )                                # the Virgin Mary statue
    z0.box( 6, 14, 41, 69, 'R', '.' )                  # red Toulouse brick
    z0.box( 6, 14, 13, 21, 'R', '.' )                  # twin towers
    z0.box( 34, 14, 41, 21, 'R', '.' )
    for x in ( 22, 23, 24, 25 ):
        z0.at( x, 14, '+' )
    z0.at( 13, 18, '+' )
    z0.at( 34, 18, '+' )
    for y in range( 26, 60, 5 ):
        z0.at( 6, y, 'w' )
        z0.at( 41, y, 'w' )
    for y in range( 24, 58, 4 ):                       # nave columns
        z0.at( 15, y, 'P' )
        z0.at( 32, y, 'P' )
    for y in range( 25, 57, 2 ):                       # pews either side of the aisle
        z0.rect( 17, y, 22, y, 'b' )
        z0.rect( 25, y, 30, y, 'b' )
    z0.rect( 19, 62, 28, 62, 'a' )                     # altar and the apse statue
    z0.at( 23, 66, 'Z' )
    z0.at( 9, 16, '<' )                                # west tower stair
    levels = { 0: z0 }
    for z in ( 1, 2, 3 ):
        lv = Level( 2, 3, ' ' )
        if z == 1:
            lv.rect( 6, 14, 41, 69, '_' )              # the nave roof, between the towers too
        for tx in ( 6, 34 ):
            if z < 3:
                lv.box( tx, 14, tx + 7, 21, 'R', '.' )
                for y in ( 16, 19 ):
                    lv.at( tx, y, 'w' )
                    lv.at( tx + 7, y, 'w' )
            else:
                lv.rect( tx, 14, tx + 7, 21, '|' )         # open belfry top, railings
                lv.rect( tx + 1, 15, tx + 6, 20, '_' )
        levels[z] = lv
    # one stair shaft up the west tower, alternating corners so no tile is both < and >
    levels[0].at( 9, 16, '<' )
    levels[1].at( 9, 16, '>' )
    levels[1].at( 11, 19, '<' )
    levels[2].at( 11, 19, '>' )
    levels[2].at( 9, 16, '<' )
    levels[3].at( 9, 16, '>' )
    levels[3].at( 11, 19, '_' )
    levels[4] = Level( 2, 3, ' ' )
    for tx in ( 7, 35 ):
        levels[4].rect( tx + 2, 16, tx + 3, 19, '_' )   # spire stubs
    return levels


# --- 3. Bưu điện Thành phố ----------------------------------------------------------------
def buu_dien():
    z0 = Level( 3, 2, ',' )
    z0.rect( 0, 0, 71, 1, 'S' )
    z0.box( 4, 8, 67, 43, '#', '.' )                   # patterned tile hall floor
    for x in ( 34, 35, 36, 37 ):
        z0.at( x, 8, '+' )
    for x in range( 8, 66, 4 ):
        if not 32 <= x <= 39:
            z0.at( x, 8, 'w' )
    for x in range( 9, 64 ):                           # counters along both long sides
        if x % 7 != 0:
            z0.at( x, 12, 'k' )
            z0.at( x, 39, 'k' )
    for y in range( 15, 37, 3 ):                       # wooden phone booths along the end walls
        z0.at( 6, y, 'p' )
        z0.at( 65, y, 'p' )
    for y in range( 18, 34, 4 ):                       # writing tables down the middle
        z0.rect( 28, y, 31, y, 't' )
        z0.rect( 40, y, 43, y, 't' )
    z0.at( 36, 41, 'Z' )                               # the portrait wall
    z1 = roof_over( z0, INDOOR )
    for x in ( 35, 36 ):
        z1.at( x, 8, 'K' )                             # the façade clock
    return { 0: z0, 1: z1 }


# --- 4. Nhà hát Thành phố ------------------------------------------------------------------
def nha_hat():
    z0 = Level( 2, 2, ',' )
    z0.rect( 0, 0, 47, 1, 'S' )
    z0.box( 4, 7, 43, 45, 'C', '.' )
    for x in range( 18, 30 ):                          # the great arched entrance
        z0.at( x, 7, '+' if x % 3 else 'P' )
    z0.rect( 22, 8, 25, 13, '=' )                      # foyer carpet runner
    z0.rect( 5, 14, 42, 14, 'C' )
    for x in ( 12, 23, 24, 35 ):
        z0.at( x, 14, '+' )
    for y in range( 16, 37, 2 ):                       # rows of seats, centre aisle
        z0.rect( 8, y, 21, y, 'b' )
        z0.rect( 26, y, 39, y, 'b' )
    z0.rect( 22, 15, 25, 37, '=' )
    z0.rect( 6, 39, 41, 44, '^' )                      # the stage
    z0.at( 10, 41, 'A' )                               # a piano
    z1 = roof_over( z0, INDOOR )
    return { 0: z0, 1: z1 }


# --- 5. UBND Thành phố (City Hall) ---------------------------------------------------------
def ubnd_tp():
    z0 = Level( 3, 2, ',' )
    z0.rect( 0, 0, 71, 1, 'S' )
    z0.ellipse( 36, 7, 10, 3.5, 'g' )                  # the park in front
    z0.at( 35, 7, 'Z' )                                # the statue
    for x in ( 24, 26, 46, 48 ):
        z0.at( x, 7, 'G' )
    z0.box( 6, 14, 65, 45, '#', '.' )
    z0.box( 22, 22, 49, 37, '#', 'g' )                 # inner courtyard
    for x in ( 34, 35, 36, 37 ):
        z0.at( x, 14, '+' )
        z0.at( x, 22, '+' )
    for x in range( 10, 64, 4 ):
        if not 32 <= x <= 39:
            z0.at( x, 14, 'w' )
    for x0 in ( 9, 52 ):                               # office wings
        for y in range( 17, 43, 4 ):
            z0.at( x0, y, 'd' )
            z0.at( x0 + 1, y, 'c' )
            z0.at( x0 + 6, y, 'd' )
            z0.at( x0 + 7, y, 'c' )
    for y in range( 24, 36, 2 ):
        z0.at( 7, y, 'x' )
        z0.at( 64, y, 'x' )
    z0.at( 12, 16, '<' )
    z1 = Level( 3, 2, ' ' )
    z1.box( 6, 14, 65, 45, '#', '.' )
    z1.rect( 22, 22, 49, 37, ' ' )                     # courtyard open to the sky
    z1.box( 21, 21, 50, 38, '#', '#' )
    z1.rect( 22, 22, 49, 37, ' ' )
    for y in range( 17, 43, 4 ):
        z1.at( 10, y, 'd' )
        z1.at( 60, y, 'd' )
    z1.at( 12, 16, '>' )
    z1.rect( 32, 14, 39, 18, '#' )                     # clock tower rises over the entrance
    z2 = roof_over( z1, INDOOR )
    z2.rect( 32, 14, 39, 18, '#' )
    for x in ( 35, 36 ):
        z2.at( x, 14, 'K' )
    z3 = Level( 3, 2, ' ' )
    z3.rect( 33, 15, 38, 17, '_' )
    return { 0: z0, 1: z1, 2: z2, 3: z3 }


# --- 6. Dinh Độc Lập ----------------------------------------------------------------------
def dinh_doc_lap():
    z0 = Level( 3, 3, 'g' )
    z0.rect( 0, 0, 71, 1, 'S' )
    z0.rect( 0, 3, 71, 3, 'I' )                        # the railings along the street
    z0.rect( 30, 3, 41, 3, ',' )                       # the gate
    z0.ellipse( 36, 20, 30, 12, ',' )                  # driveway round the oval lawn
    z0.ellipse( 36, 20, 26, 9, 'g' )
    z0.ellipse( 36, 20, 4, 2.2, '~' )                  # fountain
    z0.rect( 30, 4, 41, 10, ',' )
    z0.box( 8, 36, 63, 63, 'C', '.' )                  # the palace
    for x in range( 9, 63, 2 ):                        # concrete "bamboo" brise-soleil fins
        z0.at( x, 36, 'P' )
    for x in ( 34, 35, 36, 37 ):
        z0.at( x, 36, 'D' )
    z0.rect( 9, 37, 62, 41, '=' )                      # the reception hall
    for x in ( 20, 51 ):
        z0.rect( x, 42, x, 62, 'C' )
        z0.at( x, 50, '+' )
    for y in range( 44, 62, 4 ):                       # cabinet room and offices
        z0.rect( 26, y, 45, y, 't' )
        z0.at( 25, y, 'c' )
        z0.at( 46, y, 'c' )
        z0.at( 12, y, 'd' )
        z0.at( 56, y, 'd' )
    z0.at( 14, 40, '<' )
    z0.at( 36, 62, '>' )                               # down to the bunker
    for x in ( 4, 66 ):
        for y in range( 8, 34, 6 ):
            z0.at( x, y, 'T' )                         # the old trees of the grounds
    levels = { 0: z0 }
    for z in ( 1, 2 ):
        lv = Level( 3, 3, ' ' )
        lv.box( 8, 36, 63, 63, 'C', '.' )
        for x in range( 9, 63, 2 ):
            lv.at( x, 36, 'P' )
        lv.rect( 9, 37, 62, 39, '=' )                   # balcony gallery behind the fins
        for y in range( 42, 62, 5 ):
            lv.rect( 24, y, 47, y, 't' )
            lv.at( 12, y, 'd' )
        levels[z] = lv
    levels[1].at( 14, 40, '>' )
    levels[1].at( 16, 40, '<' )
    levels[2].at( 16, 40, '>' )
    levels[2].at( 14, 40, '.' )
    levels[3] = roof_over( levels[2], INDOOR )
    levels[3].rect( 8, 36, 63, 36, '|' )               # roof terrace railing
    bunker = Level( 3, 3, 'X' )                       # z-1: rock with the command bunker
    bunker.box( 26, 52, 47, 63, 'C', '.' )
    bunker.rect( 29, 56, 44, 56, 'e' )                 # radio and map tables of the war room
    bunker.rect( 29, 59, 44, 59, 'd' )
    bunker.at( 36, 62, '<' )
    levels[-1] = bunker
    return levels


LANDMARKS = {
    # id: ( builder, w, h, name, symbol colour, monsters per OMT-ish, items per symbol )
    'sgn_lm_ben_thanh': ( ben_thanh, 3, 3, 'Chợ Bến Thành', 'yellow' ),
    'sgn_lm_duc_ba': ( duc_ba, 2, 3, 'Nhà thờ Đức Bà', 'light_red' ),
    'sgn_lm_buu_dien': ( buu_dien, 3, 2, 'Bưu điện Thành phố', 'yellow' ),
    'sgn_lm_nha_hat': ( nha_hat, 2, 2, 'Nhà hát Thành phố', 'white' ),
    'sgn_lm_ubnd_tp': ( ubnd_tp, 3, 2, 'UBND Thành phố', 'yellow' ),
    'sgn_lm_dinh_doc_lap': ( dinh_doc_lap, 3, 3, 'Dinh Độc Lập', 'white' ),
}


def palette():
    return {
        'type': 'palette', 'id': 'sgn_lm',
        'terrain': {
            'S': 't_sidewalk', ',': 't_concrete', 'g': 't_grass', 'G': 't_grass', '~': 't_water_sh',
            'I': 't_chainfence', 'T': 't_sgn_tree_me', 'X': 't_rock',
            '#': 't_brick_wall', 'R': 't_sgn_gach_do', 'C': 't_concrete_wall', 'H': 't_sgn_tuong_hong',
            '.': 't_sgn_gach_men', ':': 't_thconc_floor', '=': 't_carpet_red', '^': 't_floor_waxed',
            'w': 't_window_domestic', 'W': 't_window', '+': 't_door_c', 'D': 't_door_glass_c', 'P': 't_pillar',
            '<': 't_stairs_up', '>': 't_stairs_down', '_': 't_concrete_roof', '|': 't_railing',
            'b': 't_sgn_gach_men', 'k': 't_thconc_floor', 't': 't_sgn_gach_men', 'r': 't_thconc_floor',
            'v': 't_thconc_floor', 'q': 't_thconc_floor', 'm': 't_thconc_floor', 'y': 't_thconc_floor',
            'u': 't_thconc_floor', 's': 't_thconc_floor', 'a': 't_sgn_gach_men', 'd': 't_sgn_gach_men',
            'c': 't_sgn_gach_men', 'x': 't_sgn_gach_men', 'p': 't_thconc_floor', 'K': 't_concrete_roof',
            'Z': 't_concrete', 'A': 't_floor_waxed', 'e': 't_sgn_gach_men' },
        'furniture': {
            'G': 'f_sgn_van_tho', 'b': 'f_bench', 'k': 'f_counter', 't': 'f_table', 'r': 'f_rack',
            'v': 'f_sgn_quay_vang', 'q': 'f_counter', 'm': 'f_counter', 'y': 'f_rack', 'u': 'f_sgn_ban_inox',
            's': 'f_stool', 'a': 'f_table', 'd': 'f_desk', 'c': 'f_chair', 'x': 'f_filing_cabinet',
            'p': 'f_sgn_buong_dien_thoai', 'K': 'f_sgn_dong_ho', 'Z': 'f_statue', 'A': 'f_piano', 'e': 'f_desk' },
        'items': {
            'y': { 'item': 'sgn_cho_cloth', 'chance': 60, 'repeat': [ 1, 3 ] },
            'v': { 'item': 'sgn_gold_shop', 'chance': 50 },
            'q': { 'item': 'sgn_cho_stall_produce', 'chance': 50 },
            'm': { 'item': 'sgn_cho_stall_meat_fish', 'chance': 50 },
            'u': { 'item': 'sgn_street_cart', 'chance': 50 },
            'a': { 'item': 'sgn_church', 'chance': 70, 'repeat': [ 1, 3 ] },
            'p': { 'item': 'sgn_post_office', 'chance': 40 },
            'k': { 'item': 'sgn_post_office', 'chance': 15 },
            'd': { 'item': 'sgn_ward_office', 'chance': 40 },
            'x': { 'item': 'sgn_ward_office', 'chance': 60, 'repeat': [ 1, 2 ] },
            'e': { 'item': 'sgn_palace_bunker', 'chance': 80, 'repeat': [ 1, 3 ] } } }


def oter( lid, x, y, z ):
    return '%s_%d%d%s' % ( lid, x, y, '' if z == 0 else ( '_b' if z < 0 else '_z%d' % z ) )


MONSTERS = [ { 'group': 'sgn_GROUP_SAIGON_AWAKE', 'x': [ 0, 23 ], 'y': [ 0, 23 ], 'chance': 35 },
             { 'group': 'sgn_GROUP_ZOMBIE_DORMANT', 'x': [ 0, 23 ], 'y': [ 0, 23 ], 'chance': 40, 'repeat': [ 1, 3 ] } ]


def generate():
    mapgens, terrains, buildings = [], [], []
    for lid, ( build, w, h, name, colour ) in LANDMARKS.items():
        levels = build()
        overmaps = []
        for z, lv in sorted( levels.items() ):
            rows = lv.rows()
            assert len( rows ) == h * 24 and all( len( r ) == w * 24 for r in rows ), ( lid, z )
            grid = [ [ oter( lid, x, y, z ) for x in range( w ) ] for y in range( h ) ]
            fill = 't_rock' if z < 0 else ( 't_concrete' if z == 0 else 't_open_air' )
            obj = { 'fill_ter': fill, 'rows': rows, 'palettes': [ 'sgn_lm' ] }
            if z == 0:
                obj['flags'] = CLEARING
                # one range per map tile: ranges may not cross tile boundaries in multi-tile mapgen
                obj['place_monster'] = [ dict( m, x=[ ox * 24, ox * 24 + 23 ], y=[ oy * 24 + ( 6 if oy == 0 else 0 ), oy * 24 + 23 ] )
                                         for oy in range( h ) for ox in range( w ) for m in MONSTERS ]
            mapgens.append( { 'type': 'mapgen', 'om_terrain': grid, 'object': obj } )
            for y in range( h ):
                for x in range( w ):
                    tid = oter( lid, x, y, z )
                    base = 'generic_city_building' if z == 0 else (
                        'generic_city_building_roof' if z > 0 else 'generic_city_building' )
                    t = { 'type': 'overmap_terrain', 'id': tid, 'copy-from': base,
                          'name': name if z == 0 else ( name + ( ' (upper floor)' if z > 0 else ' (basement)' ) ),
                          'sym': '&' if z == 0 else '#', 'color': colour, 'looks_like': oter( lid, 0, 0, 0 ) }
                    if tid == oter( lid, 0, 0, 0 ):
                        t['looks_like'] = 'house'
                    if z < 0:
                        t['delete'] = { 'flags': [ 'SIDEWALK' ] }
                    terrains.append( t )
                    overmaps.append( { 'point': [ x, y, z ], 'overmap': tid + '_north' } )
        buildings.append( { 'type': 'city_building', 'id': lid, 'locations': [ 'land' ],
                            'flags': [ 'SAIGON', 'OVERMAP_UNIQUE' ], 'city_sizes': [ 6, -1 ],
                            'overmaps': overmaps } )
    return [ palette() ] + mapgens, terrains + buildings


def main():
    mg, om = generate()
    os.makedirs( os.path.join( ROOT, 'mapgen', 'landmarks' ), exist_ok=True )
    with open( os.path.join( ROOT, 'mapgen', 'landmarks', 'saigon_landmarks.json' ), 'w' ) as f:
        json.dump( mg, f, ensure_ascii=False, indent=2 )
    with open( os.path.join( ROOT, 'overmap', 'saigon_landmarks.json' ), 'w' ) as f:
        json.dump( om, f, ensure_ascii=False, indent=2 )
    print( 'wrote %d landmarks: %s' % ( len( LANDMARKS ), ', '.join( LANDMARKS ) ) )


if __name__ == '__main__':
    main()
