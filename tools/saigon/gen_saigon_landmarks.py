#!/usr/bin/env python3
"""Generate the real Saigon landmarks of the 2000s (doc/saigon/LANDMARKS.md, phases L1-L4).

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
        self.vehicles = []      # ( x, y, vehicle_group, rotation, chance ); keep each inside one map tile
        self.monsters = []      # place_monster entries for specific animals; ranges inside one map tile
        self.npcs = []          # ( x, y, npc id ); the people who hold the place (N6)

    def vehicle( self, x, y, group, rotation, chance ):
        self.vehicles.append( ( x, y, group, rotation, chance ) )

    def npc( self, x, y, who ):
        """Place an npc (template id) on this level (N6).

        place_npcs wants a `type: "npc"` template, not an npc_class, and it has no
        chance key: whoever is listed is there.  Unlike place_monster there is no
        one-map-tile-per-range rule here, since NPCs live in submap storage and the
        engine nudges a spawn off a wall.  Keep each one inside a single map tile
        all the same, so unloading and reloading one tile of a multi-tile landmark
        never duplicates a person.
        """
        self.npcs.append( ( x, y, who ) )

    def monster( self, x0, y0, x1, y1, mon, chance=100, repeat=None ):
        assert x0 // 24 == x1 // 24 and y0 // 24 == y1 // 24, ( 'monster range crosses a map tile', x0, y0, x1, y1 )
        m = { 'monster': mon, 'x': [ x0, x1 ], 'y': [ y0, y1 ], 'chance': chance }
        if repeat:
            m['repeat'] = repeat
        self.monsters.append( m )

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


INDOOR = set( '#RCH.:=^wW+DPbktrvqmyuasdcxpKZQAe<>jnhEFUOBY{}234!%&5i/' )

# Per-landmark symbols for the L4 parks (mapgen object keys override the shared palette)
LOCAL = {
    'sgn_lm_thao_cam_vien': {
        'terrain': { '$': 't_sgn_hoa_sen', '(': 't_sgn_gach_tau', '*': 't_grass', 'f': 't_dirt', ';': 't_dirt',
                     '/': 't_reinforced_glass', '\\': 't_monkey_bars' },
        'furniture': { '(': 'f_sgn_chau_kieng', '*': 'f_boulder_large', ';': 'f_hay' } },
    'sgn_lm_dam_sen': {
        'terrain': { '1': 't_water_dp', '$': 't_sgn_hoa_sen', '(': 't_sgn_gach_tau', ')': 't_water_sh',
                     '@': 't_concrete', '*': 't_grass', '`': 't_railroad_track_small' },
        'furniture': { '(': 'f_sgn_chau_kieng', ')': 'f_sgn_thuyen_thien_nga', '@': 'f_sgn_vong_quay',
                       '*': 'f_boulder_large' } },
    'sgn_lm_lang_ong': {
        'terrain': { '*': 't_sgn_gach_tau' }, 'furniture': { '*': 'f_sgn_mo' } },
    'sgn_lm_thong_nhat': {
        'terrain': { '@': 't_dirt', '`': 't_pavement_y', '(': 't_concrete', '3': 't_concrete' },
        'furniture': { '(': 'f_bench' } },
    'sgn_lm_vinh_nghiem': {
        'furniture': { '5': 'f_bed' }, 'items': { '5': { 'item': 'sgn_temple', 'chance': 30 } } },
    'sgn_lm_nha_rong': {
        'terrain': { '$': 't_floor_waxed', '~': 't_water_dp' },
        'furniture': { '$': 'f_displaycase' } },
    'sgn_lm_san_bay': {
        'terrain': { '@': 't_pavement', '`': 't_pavement_y' },
        'furniture': { 'B': 'f_counter' },          # the bag belts behind check-in, not rice sacks
        'items': { '4': { 'item': 'sgn_tourist', 'chance': 15 },
                   'j': { 'item': 'sgn_tourist', 'chance': 25 },
                   'B': { 'item': 'sgn_tourist', 'chance': 40, 'repeat': [ 1, 2 ] } } },
    'sgn_lm_suoi_tien': {
        'terrain': { '1': 't_water_dp', ';': 't_sand', '@': 't_concrete', "'": 't_concrete', ')': 't_concrete',
                     '(': 't_grass', '*': 't_grass', '`': 't_railroad_track_small', 'f': 't_dirt' },
        'furniture': { '@': 'f_sgn_vong_quay', "'": 'f_sgn_tuong_khong_lo', ')': 'f_sgn_ky_lan',
                       '(': 'f_sgn_rong_lon', '*': 'f_boulder_large' } },
}


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
                        z0.at( x, y + 1, 'j' if stall != 'v' else 'v' )
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


# --- 7. Chùa Bà Thiên Hậu (Chợ Lớn) ---------------------------------------------------------
def thien_hau():
    # the Cantonese temple of the sea goddess: a gate hall, an open courtyard with the great
    # burner under the sky, side galleries, and the main hall, its ceiling hung with coils
    z0 = Level( 2, 2, ',' )
    z0.rect( 0, 0, 47, 1, 'S' )
    z0.rect( 2, 2, 45, 6, 'o' )                        # forecourt
    z0.at( 18, 5, 'L' )                                # the guardian lions
    z0.at( 29, 5, 'L' )
    z0.box( 2, 7, 45, 45, '#', 'n' )
    for x in range( 22, 26 ):                          # the gate
        z0.at( x, 7, '+' )
    for x in ( 6, 12, 18, 29, 35, 41 ):                # gate hall: two rows of red pillars
        z0.at( x, 10, 'O' )
        z0.at( x, 15, 'O' )
    for x in range( 5, 43, 4 ):
        z0.at( x, 12, 'h' )
    z0.rect( 3, 18, 44, 18, '#' )                      # into the courtyard
    z0.rect( 16, 18, 31, 18, 'n' )
    z0.rect( 14, 19, 33, 28, 'o' )                     # the courtyard, open to the sky
    z0.at( 23, 23, 'V' )
    for y in ( 19, 28 ):
        for x in ( 14, 33 ):
            z0.at( x, y, 'O' )
    for y in range( 20, 28, 3 ):                       # side galleries
        z0.at( 7, y, 'h' )
        z0.at( 40, y, 'h' )
    z0.rect( 3, 29, 44, 29, '#' )                      # into the main hall
    z0.rect( 16, 29, 31, 29, 'n' )
    for y in range( 31, 39, 3 ):                       # the ceiling of hanging coils
        for x in range( 5, 43, 5 ):
            z0.at( x, y, 'h' )
    for x in ( 10, 16, 31, 37 ):
        for y in ( 32, 38 ):
            z0.at( x, y, 'O' )
    z0.at( 23, 36, 'U' )                               # the burner before the goddess
    z0.rect( 16, 41, 31, 41, 'E' )                     # the main altar
    z0.at( 23, 43, 'F' )                               # Thiên Hậu and her attendants
    z0.at( 24, 43, 'F' )
    z0.rect( 5, 41, 10, 41, 'E' )                      # side altars
    z0.rect( 37, 41, 42, 41, 'E' )
    z0.at( 7, 43, 'F' )
    z0.at( 40, 43, 'F' )
    z1 = roof_over( z0, INDOOR, 'N' )                  # green glazed tile roofs
    return { 0: z0, 1: z1 }


# --- 8. Chùa Ngọc Hoàng (Đa Kao) -----------------------------------------------------------
def ngoc_hoang():
    # the Jade Emperor pagoda: a garden with the turtle pond, a front hall of fierce guardian
    # statues, the Jade Emperor's hall, and the dark Hall of the Ten Hells to one side
    z0 = Level( 2, 2, 'g' )
    z0.rect( 0, 0, 47, 1, 'S' )
    z0.rect( 2, 2, 45, 2, '#' )                        # garden wall and gate
    z0.rect( 20, 2, 27, 2, 'o' )
    z0.rect( 20, 3, 27, 17, 'o' )                      # path to the hall
    z0.at( 19, 4, 'L' )
    z0.at( 28, 4, 'L' )
    z0.ellipse( 37, 10, 7, 4.5, 'M' )                  # the turtle pond
    for x, y in ( ( 6, 5 ), ( 12, 9 ), ( 6, 14 ), ( 43, 16 ), ( 31, 15 ) ):
        z0.at( x, y, 'T' )
    z0.at( 23, 12, 'V' )
    z0.box( 5, 18, 42, 45, '#', 'n' )
    for x in range( 22, 26 ):
        z0.at( x, 18, '+' )
    for y in range( 20, 28, 2 ):                       # guardian statues along the walls
        z0.at( 6, y, 'F' )
        z0.at( 41, y, 'F' )
    for x, y in ( ( 16, 20 ), ( 31, 20 ), ( 16, 27 ), ( 31, 27 ) ):
        z0.at( x, y, 'O' )
    for x, y in ( ( 12, 24 ), ( 18, 22 ), ( 29, 22 ), ( 35, 24 ) ):
        z0.at( x, y, 'h' )
    z0.at( 23, 23, 'U' )
    z0.rect( 6, 29, 41, 29, '#' )
    z0.at( 23, 29, '+' )
    z0.at( 24, 29, '+' )
    z0.rect( 33, 30, 33, 44, '#' )                     # the Hall of the Ten Hells
    z0.at( 33, 37, '+' )
    for y in range( 31, 44, 2 ):
        z0.at( 7, y, 'F' )                             # the Emperor's court
        z0.at( 40, y, 'F' )                            # the judges of hell
        z0.at( 36, y, 'F' )
    z0.rect( 12, 39, 27, 39, 'E' )                     # the Jade Emperor's altar
    z0.at( 19, 41, 'F' )
    z0.at( 20, 41, 'F' )
    for x, y in ( ( 14, 33 ), ( 25, 33 ), ( 19, 35 ) ):
        z0.at( x, y, 'h' )
    z1 = roof_over( z0, INDOOR, 'N' )
    return { 0: z0, 1: z1 }


# --- 9. Chợ Bình Tây (Chợ Lớn) -------------------------------------------------------------
def binh_tay():
    # the wholesale market: four wings of stalls around a garden courtyard with the dragon
    # fountain and the founder's statue, and a clock tower over the north gate
    z0 = Level( 3, 3, ',' )
    z0.rect( 0, 0, 71, 1, 'S' )
    z0.box( 4, 8, 67, 67, '#', ':' )
    z0.rect( 30, 3, 41, 8, '#' )                       # clock-tower gate
    z0.rect( 32, 4, 39, 8, ':' )
    for x in range( 33, 39 ):
        z0.at( x, 3, '+' )
    for y in ( 36, 37 ):                               # the other three gates
        z0.at( 4, y, '+' )
        z0.at( 67, y, '+' )
    for x in ( 35, 36 ):
        z0.at( x, 67, '+' )
    z0.box( 24, 26, 47, 49, '#', 'o' )                 # the courtyard
    for x in ( 35, 36 ):
        z0.at( x, 26, ':' )
        z0.at( x, 49, ':' )
    for y in ( 37, 38 ):
        z0.at( 24, y, ':' )
        z0.at( 47, y, ':' )
    for x0, y0 in ( ( 26, 28 ), ( 40, 28 ), ( 26, 42 ), ( 40, 42 ) ):   # garden beds
        z0.rect( x0, y0, x0 + 5, y0 + 5, 'g' )
        z0.at( x0 + 2, y0 + 2, 'T' )
    z0.at( 35, 37, 'J' )                               # the dragon fountain
    z0.at( 35, 31, 'z' )                               # the founder, Quách Đàm
    for y in ( 12, 17, 22 ):                           # north wing: rice and grain by the sack
        for x in range( 7, 65 ):
            if ( x - 7 ) % 8 < 6 and not 31 <= x <= 40:
                z0.at( x, y, 'B' )
    for y in ( 53, 58, 63 ):                           # south wing: household goods
        for x in range( 7, 65 ):
            if ( x - 7 ) % 8 < 6 and not 33 <= x <= 38:
                z0.at( x, y, 'y' )
    for x in ( 9, 14, 19 ):                            # west wing: produce
        for y in range( 27, 49 ):
            if not 35 <= y <= 40:
                z0.at( x, y, 'q' )
    for x in ( 52, 58 ):                               # east wing: the food stalls
        for y in range( 28, 48, 3 ):
            if not 35 <= y <= 40:
                z0.at( x, y, 'u' )
                z0.at( x + 1, y, 's' )
    z1 = roof_over( z0, INDOOR, 'l' )                  # terracotta tile roofs
    z1.rect( 30, 3, 41, 8, '#' )
    z2 = Level( 3, 3, ' ' )
    z2.rect( 31, 3, 40, 7, '#' )
    for x in ( 35, 36 ):
        z2.at( x, 3, 'K' )
    z3 = Level( 3, 3, ' ' )
    z3.rect( 32, 4, 39, 6, '_' )
    return { 0: z0, 1: z1, 2: z2, 3: z3 }


# --- 11. Ga Sài Gòn ------------------------------------------------------------------------
def ga_sai_gon():
    # the station forecourt, the ticket hall (windows, departure boards, waiting benches,
    # food stalls), then covered platforms between four tracks where the last trains stand.
    # Each track bed is 7 rows (a passenger car is 17 x 7) and lies inside one map-tile row.
    z0 = Level( 3, 3, ',' )
    z0.rect( 0, 0, 71, 1, 'S' )
    for x in range( 6, 66, 8 ):                        # xe ôm and parked motorbikes on the forecourt
        z0.vehicle( x, 4, 'sgn_vg_sidewalk_parked', 90, 45 )
    z0.box( 6, 8, 65, 24, 'C', '.' )                   # the ticket hall
    for x in range( 8, 64, 3 ):
        z0.at( x, 8, 'W' )
    for x in range( 33, 39 ):
        z0.at( x, 8, 'D' )
    z0.rect( 9, 11, 31, 11, '3' )                      # ticket windows, staff behind them
    z0.rect( 7, 9, 31, 10, '.' )
    for x in range( 40, 47 ):
        z0.at( x, 10, '2' )                            # the departure boards
    for y in ( 14, 17, 20 ):                           # waiting benches
        for x in range( 38, 63 ):
            if ( x - 38 ) % 6 < 4:
                z0.at( x, y, '4' )
    for x in range( 9, 30, 4 ):                        # food stalls
        z0.at( x, 19, 'u' )
        z0.at( x, 20, 's' )
    for x in ( 14, 15, 34, 35, 54, 55 ):               # out to the platforms
        z0.at( x, 24, '+' )
    for y0, y1 in ( ( 25, 30 ), ( 38, 40 ), ( 48, 51 ), ( 59, 61 ) ):   # covered platforms
        z0.rect( 2, y0, 69, y1, ':' )
        for x in range( 4, 69, 8 ):
            z0.at( x, y0, 'P' )
        for x in range( 8, 66, 12 ):
            z0.at( x, y0 + 1, '4' )
    for y0, track in ( ( 31, True ), ( 41, True ), ( 52, True ), ( 62, True ) ):   # track beds
        z0.rect( 0, y0, 71, y0 + 6, '"' )               # ballast, then one standard-gauge track
        z0.rect( 0, y0 + 1, 71, y0 + 5, '-' )
        z0.rect( 0, y0 + 1, 71, y0 + 1, '0' )
        z0.rect( 0, y0 + 5, 71, y0 + 5, '0' )
    for cx in ( 12, 36, 60 ):                          # stranded trains: SE1 on track 1 ...
        z0.vehicle( cx, 34, 'sgn_vg_train', 0, 75 )
    for cx in ( 36, 60 ):                              # ... a half train on track 3
        z0.vehicle( cx, 55, 'sgn_vg_train', 0, 60 )
    z0.vehicle( 12, 65, 'sgn_vg_train', 0, 40 )        # a locomotive or car in the yard
    z0.rect( 0, 70, 71, 70, 'I' )
    z1 = roof_over( z0, INDOOR )
    return { 0: z0, 1: z1 }


# --- 12. Bến xe Miền Đông ------------------------------------------------------------------
def ben_xe_mien_dong():
    # the ticket hall, a row of kiosks under a canopy, the loading bays, and a yard of coaches
    # that never left.  Each coach (14 x 7) is parked inside one map tile.
    z0 = Level( 3, 3, ',' )
    z0.rect( 0, 0, 71, 1, 'S' )
    z0.box( 4, 4, 40, 19, 'C', '.' )                   # ticket hall
    for x in range( 6, 39, 3 ):
        z0.at( x, 4, 'W' )
    for x in range( 20, 24 ):
        z0.at( x, 4, 'D' )
    for x in range( 7, 38 ):                           # ticket windows of forty bus companies
        if x % 4 != 0:
            z0.at( x, 8, '3' )
    for y in ( 12, 15 ):
        for x in range( 8, 37 ):
            if x % 5 != 0:
                z0.at( x, y, '4' )
    for x in ( 10, 11, 30, 31 ):
        z0.at( x, 19, '+' )
    z0.rect( 44, 4, 69, 10, ':' )                      # kiosks under a canopy
    for x in range( 45, 69, 4 ):
        z0.at( x, 6, 'u' )
        z0.at( x, 7, 's' )
    for x in range( 44, 70, 6 ):
        z0.at( x, 4, 'P' )
    z0.rect( 2, 21, 69, 24, ':' )                      # loading bays
    for x in range( 2, 70, 6 ):
        z0.at( x, 24, 'P' )
    for x in range( 6, 66, 12 ):
        z0.at( x, 22, '4' )
    for cy in ( 30, 40, 54, 64 ):
        for cx in ( 14, 38, 62 ):
            z0.vehicle( cx, cy, 'sgn_vg_coach', 0, 55 )
    z1 = roof_over( z0, INDOOR )
    return { 0: z0, 1: z1 }


# --- 13. Công viên Tao Đàn -----------------------------------------------------------------
def tao_dan():
    # old sao trees over lawns and paths inside a railing, the bird café's pavilion where old
    # men hang their cages beside their coffee, stone chess tables under the trees
    z0 = Level( 3, 3, 'g' )
    z0.rect( 0, 0, 71, 1, 'S' )
    z0.rect( 1, 2, 70, 2, 'I' )
    z0.rect( 1, 2, 1, 70, 'I' )
    z0.rect( 70, 2, 70, 70, 'I' )
    z0.rect( 1, 70, 70, 70, 'I' )
    z0.rect( 32, 2, 39, 2, 'o' )                       # the gate
    z0.rect( 33, 3, 38, 68, 'o' )                      # the main walks
    z0.rect( 3, 33, 68, 38, 'o' )
    z0.ellipse( 35.5, 35.5, 12, 12, 'o' )
    z0.ellipse( 35.5, 35.5, 8, 8, 'g' )
    trees = [ ( x, y ) for y in range( 6, 68, 7 ) for x in range( 5 + ( y // 7 ) % 2 * 3, 68, 8 ) ]
    for x, y in trees:
        if z0.get( x, y ) == 'g':
            z0.at( x, y, '9' )
    for x, y in ( ( 28, 10 ), ( 43, 10 ), ( 28, 60 ), ( 43, 60 ), ( 10, 30 ), ( 10, 41 ), ( 61, 30 ), ( 61, 41 ) ):
        z0.at( x, y, '7' )                             # stone chess tables beside the walks
    for x in range( 31, 41, 3 ):
        z0.at( x, 31, 'b' )
        z0.at( x, 40, 'b' )
    # the bird café: a pavilion in the north-east corner
    z0.rect( 48, 6, 66, 20, 'o' )
    z0.rect( 50, 8, 64, 18, ':' )
    for x, y in ( ( 50, 8 ), ( 64, 8 ), ( 50, 18 ), ( 64, 18 ), ( 57, 8 ), ( 57, 18 ) ):
        z0.at( x, y, 'P' )
    for x in range( 52, 64, 3 ):
        z0.at( x, 10, '6' )                            # bird cages hung along the eaves
        z0.at( x, 16, '6' )
    for x in range( 53, 63, 4 ):
        z0.at( x, 13, 't' )
        z0.at( x + 1, 13, 's' )
    z0.box( 40, 8, 46, 14, 'C', '.' )                  # the café's kitchen kiosk
    z0.at( 43, 14, '+' )
    z0.at( 42, 10, 'u' )
    z0.at( 44, 10, 'u' )
    z1 = roof_over( z0, INDOOR, 'l' )
    return { 0: z0, 1: z1 }


# --- 14. Hồ Con Rùa ------------------------------------------------------------------------
def ho_con_rua():
    # the round pool with the lotus-and-spire monument, benches on the rim, and a drinks
    # kiosk where students bought bánh tráng trộn after class
    z0 = Level( 1, 1, ',' )
    z0.rect( 0, 0, 23, 1, 'S' )
    z0.ellipse( 12, 13, 9, 9, 'o' )
    z0.ellipse( 12, 13, 7, 7, '~' )
    z0.at( 11, 12, '8' )
    for x, y in ( ( 4, 6 ), ( 19, 6 ), ( 3, 13 ), ( 20, 13 ) ):
        z0.at( x, y, 'b' )
    for x, y in ( ( 1, 3 ), ( 22, 3 ), ( 1, 22 ), ( 22, 22 ) ):
        z0.at( x, y, 'T' )
    z0.box( 17, 18, 21, 22, 'C', '.' )
    z0.at( 18, 18, '+' )
    z0.at( 19, 20, 'u' )
    z1 = roof_over( z0, INDOOR )
    return { 0: z0, 1: z1 }


# --- 15. Saigon Trade Center ---------------------------------------------------------------
def saigon_trade_center():
    # the tallest tower in Vietnam until 2010, cut to ten storeys: a glass lobby, office
    # floors around a stair core, a sky lounge at the top.  The vantage point of the city.
    def shell():
        lv = Level( 1, 1, ' ' )
        lv.box( 3, 4, 20, 21, 'Y', '.' )
        lv.box( 13, 14, 19, 20, 'C', '.' )             # the stair core
        lv.at( 13, 17, '+' )
        return lv
    levels = {}
    z0 = Level( 1, 1, ',' )
    z0.rect( 0, 0, 23, 1, 'S' )
    z0.box( 3, 4, 20, 21, 'Y', '.' )
    z0.box( 13, 14, 19, 20, 'C', '.' )
    z0.at( 13, 17, '+' )
    for x in range( 10, 14 ):
        z0.at( x, 4, 'D' )
    z0.rect( 5, 8, 9, 8, 'j' )                         # the reception desk
    for x in ( 6, 9 ):
        z0.at( x, 12, 'b' )
    levels[0] = z0
    stairs = ( ( 15, 16 ), ( 17, 18 ) )                # alternate so each flight meets the next
    for z in range( 1, 10 ):
        lv = shell()
        if z < 9:
            for y in ( 7, 10 ):
                for x in range( 5, 19, 3 ):
                    lv.at( x, y, 'Q' )
                    lv.at( x, y + 1, 'c' )
            for y in range( 14, 21, 3 ):
                lv.at( 5, y, 'x' )
        else:                                          # the sky lounge
            for x, y in ( ( 6, 7 ), ( 10, 7 ), ( 6, 11 ), ( 10, 11 ), ( 6, 15 ), ( 6, 19 ) ):
                lv.at( x, y, 't' )
                lv.at( x + 1, y, 'c' )
        levels[z] = lv
    for z in range( 0, 9 ):
        x, y = stairs[z % 2]
        levels[z].at( x, y, '<' )
        levels[z + 1].at( x, y, '>' )
    levels[10] = roof_over( levels[9], INDOOR )
    return levels


# --- 16. Diamond Plaza ---------------------------------------------------------------------
def diamond_plaza():
    # the 1999 mall beside the cathedral: glass front, boutiques around an atrium with
    # escalators, a department-store floor, and the food court and cinema on top
    def shell( z ):
        lv = Level( 2, 2, ',' if z == 0 else ' ' )
        lv.box( 2, 4, 45, 45, 'Y', '.' )
        for x0 in ( 12, 35 ):                          # boutique fronts along both sides
            lv.rect( x0, 8, x0, 42, 'Y' )
            for y in range( 11, 42, 6 ):
                lv.at( x0, y, 'D' )
        return lv
    z0 = shell( 0 )
    z0.rect( 0, 0, 47, 1, 'S' )
    for x in range( 21, 27 ):
        z0.at( x, 4, 'D' )
    for y in range( 9, 42, 3 ):                        # boutiques: fashion and cosmetics
        for x in ( 4, 7, 10 ):
            z0.at( x, y, '!' )
        for x in ( 37, 40, 43 ):
            z0.at( x, y, '!' if y % 2 else '%' )
    z0.rect( 17, 12, 30, 12, 'j' )                     # perfume counters in the atrium
    z1 = shell( 1 )
    for y in range( 9, 42, 3 ):                        # department store: shoes and electronics
        for x in ( 4, 7, 10 ):
            z1.at( x, y, '%' )
        for x in ( 37, 40, 43 ):
            z1.at( x, y, '&' )
    z2 = Level( 2, 2, ' ' )
    z2.box( 2, 4, 45, 45, 'Y', '.' )
    for x in range( 6, 42, 6 ):                        # food court
        z2.at( x, 8, 'u' )
        for y in range( 12, 20, 3 ):
            z2.at( x, y, 't' )
            z2.at( x + 1, y, 'c' )
    z2.box( 4, 26, 32, 43, 'C', '.' )                  # the cinema
    z2.at( 18, 26, '+' )
    for y in range( 29, 41, 2 ):
        z2.rect( 7, y, 29, y, 'b' )
    z2.rect( 6, 42, 30, 42, '=' )                      # the screen wall
    # escalators: up from each floor, landing beside the next flight up
    z0.at( 23, 30, '{' )
    z1.at( 23, 30, '}' )
    z1.at( 25, 30, '{' )
    z2.at( 25, 30, '}' )
    z3 = roof_over( z2, INDOOR )
    return { 0: z0, 1: z1, 2: z2, 3: z3 }


# --- 17. Phạm Ngũ Lão – Bùi Viện -----------------------------------------------------------
def bui_vien():
    # a block of the backpacker street: twelve narrow lots of bars, travel agents and
    # guesthouse lobbies, beer tables and low stools spilling over the sidewalk under the
    # signs, two floors of guesthouse rooms above
    z0 = Level( 3, 1, ',' )
    z0.rect( 0, 0, 71, 1, 'S' )
    for x in range( 2, 70, 5 ):                        # bia hơi tables on the sidewalk
        z0.at( x, 3, '[' )
        z0.at( x + 1, 3, ']' )
        z0.at( x, 4, ']' )
    for k in range( 12 ):
        z0.at( 6 * k + 3, 5, '?' )                     # the shop signs
    z1, z2 = Level( 3, 1, ' ' ), Level( 3, 1, ' ' )
    for lv in ( z0, z1, z2 ):
        lv.rect( 0, 6, 71, 21, '.' )
        lv.rect( 0, 6, 71, 6, '#' )
        lv.rect( 0, 21, 71, 21, '#' )
        for k in range( 12 ):
            lv.rect( 6 * k, 6, 6 * k, 21, '#' )
        lv.rect( 71, 6, 71, 21, '#' )
    for k in range( 12 ):
        x0 = 6 * k
        z0.at( x0 + 2, 6, '+' )                        # open bar fronts
        z0.at( x0 + 3, 6, '+' )
        kind = k % 3
        if kind == 0:                                  # bar
            z0.rect( x0 + 1, 16, x0 + 3, 16, 'j' )
            for y in ( 9, 12 ):
                z0.at( x0 + 2, y, 't' )
                z0.at( x0 + 3, y, 's' )
            z0.at( x0 + 1, 14, 'i' )
        elif kind == 1:                                # travel agent: open tours, bus tickets to Phnom Penh
            for y in ( 9, 12 ):
                z0.at( x0 + 2, y, 'Q' )
                z0.at( x0 + 3, y, 'c' )
            z0.at( x0 + 1, 15, 'i' )
            z0.at( x0 + 1, 16, 'i' )
        else:                                          # guesthouse lobby
            z0.rect( x0 + 1, 10, x0 + 2, 10, 'j' )
            z0.at( x0 + 4, 8, 'b' )
            z0.at( x0 + 1, 14, 'i' )
        for lv in ( z1, z2 ):                          # guesthouse rooms
            for x in range( x0 + 2, x0 + 4 ):
                lv.at( x, 6, 'w' )
            lv.rect( x0 + 1, 13, x0 + 2, 13, '#' )
            lv.at( x0 + 2, 13, '+' )
            for y in ( 8, 10, 15, 18 ):
                lv.at( x0 + 1, y, '5' )
        z0.at( x0 + 4, 19, '<' )
        z1.at( x0 + 4, 19, '>' )
        z1.at( x0 + 4, 17, '<' )
        z2.at( x0 + 4, 17, '>' )
    z3 = roof_over( z2, INDOOR )
    z3.rect( 0, 6, 71, 6, '|' )                        # roof railing over the street
    return { 0: z0, 1: z1, 2: z2, 3: z3 }


def scatter_trees( lv, step=6 ):
    """Trees on open lawn only: a tile whose whole 3x3 neighbourhood is still grass."""
    for y in range( 5, lv.h - 5, step ):
        for x in range( 5 + ( y // step ) % 2 * ( step // 2 ), lv.w - 5, step + 1 ):
            if all( lv.get( x + dx, y + dy ) == 'g' for dx in ( -1, 0, 1 ) for dy in ( -1, 0, 1 ) ):
                lv.at( x, y, '9' if ( x * 7 + y ) % 3 else 'T' )


# --- 18. Thảo Cầm Viên (Saigon Zoo and Botanical Gardens) ---------------------------------
def thao_cam_vien():
    # the 1864 zoo and botanical garden: the gate on Nguyễn Bỉnh Khiêm, the history museum and
    # the Hùng Kings temple facing each other across the entrance avenue, old trees, a lotus
    # lake and an orchid-and-bonsai garden, then the enclosures: tigers, bears, elephants,
    # deer, the crocodile garden, the primate cages and the reptile house.
    lv = Level( 4, 4, 'g' )
    lv.rect( 0, 0, 95, 1, 'S' )
    lv.rect( 0, 2, 95, 2, 'I' )
    lv.rect( 0, 2, 0, 95, 'I' )
    lv.rect( 95, 2, 95, 95, 'I' )
    lv.rect( 0, 95, 95, 95, 'I' )
    lv.rect( 44, 2, 51, 2, 'o' )                       # the gate
    lv.box( 38, 3, 42, 7, 'C', '.' )                   # ticket booth
    lv.at( 42, 5, '+' )
    lv.at( 39, 4, '3' )
    for y in range( 6, 60, 7 ):                        # old trees over the grounds
        for x in range( 4 + ( y // 7 ) % 2 * 4, 92, 9 ):
            lv.at( x, y, '9' if ( x + y ) % 3 else 'T' )
    lv.rect( 44, 3, 51, 62, 'o' )                      # the entrance avenue
    lv.rect( 3, 40, 92, 43, 'o' )                      # the cross walk
    lv.box( 8, 6, 34, 22, '#', '.' )                   # Bảo tàng Lịch sử, the history museum
    for y in range( 8, 21, 3 ):
        lv.at( 8, y, 'w' )
    lv.at( 34, 13, '+' )
    lv.at( 34, 14, '+' )
    for y in range( 9, 20, 4 ):                        # display cases
        lv.rect( 12, y, 30, y, 'j' )
    lv.rect( 35, 12, 43, 15, 'o' )
    lv.box( 60, 8, 80, 20, '#', 'n' )                  # Đền Hùng, the Hùng Kings temple
    lv.at( 60, 13, '+' )
    lv.at( 60, 14, '+' )
    for x in ( 64, 70, 76 ):
        lv.at( x, 10, 'O' )
        lv.at( x, 18, 'O' )
    lv.rect( 73, 12, 73, 15, 'E' )
    lv.at( 68, 13, 'U' )
    lv.rect( 52, 12, 59, 15, 'o' )
    lv.at( 57, 11, 'L' )
    lv.at( 57, 16, 'L' )
    for y in range( 25, 37, 3 ):                       # orchid and bonsai garden
        for x in range( 8, 32, 3 ):
            lv.at( x, y, '(' )
    lv.ellipse( 70, 30, 16, 7, '~' )                   # the lotus lake
    lv.ellipse( 70, 30, 14, 5.5, '$' )
    lv.ellipse( 70, 30, 6, 2.5, '~' )
    for x in range( 52, 90, 6 ):                       # kiosks on the cross walk
        lv.at( x, 44, 'u' )
        lv.at( x + 1, 44, 's' )
    for x in range( 6, 40, 8 ):
        lv.at( x, 39, 'b' )
    # enclosures, south of the cross walk
    lv.box( 30, 46, 44, 58, 'I', 'g' )                 # deer paddock
    lv.monster( 32, 49, 42, 57, 'mon_deer', 80, [ 2, 4 ] )
    lv.box( 52, 46, 70, 58, '#', '.' )                 # the reptile house
    lv.at( 61, 46, '+' )
    for x0 in ( 54, 59, 64 ):                          # glass tanks
        lv.box( x0, 50, x0 + 4, 54, '/', '.' )
    lv.monster( 55, 51, 57, 53, 'sgn_mon_tran', 70 )
    lv.monster( 65, 51, 67, 53, 'sgn_mon_tran', 70 )
    lv.box( 6, 46, 26, 58, 'I', 'g' )                  # primate cages
    for y in range( 48, 57, 3 ):
        lv.rect( 9, y, 23, y, '\\' )
    lv.monster( 8, 49, 22, 57, 'sgn_mon_khi', 90, [ 3, 6 ] )
    lv.box( 76, 48, 93, 70, 'I', 'g' )                 # the crocodile garden
    lv.ellipse( 85, 59, 6, 8, 'M' )
    lv.monster( 78, 50, 92, 70, 'sgn_mon_ca_sau', 90, [ 2, 4 ] )
    lv.box( 6, 64, 26, 88, 'I', 'g' )                  # tigers
    for x, y in ( ( 10, 70 ), ( 20, 80 ), ( 12, 84 ) ):
        lv.at( x, y, '*' )
    lv.ellipse( 18, 70, 3, 2, '~' )
    lv.monster( 8, 74, 22, 87, 'mon_tiger', 80, [ 1, 2 ] )
    lv.box( 30, 64, 44, 88, 'I', 'g' )                 # bears
    lv.at( 36, 82, '*' )
    # every other enclosure here is 80-90 with a count; the bear pen was chance 70 and a
    # single animal, so it stood empty often enough for saigon_zoo_animals to miss it
    lv.monster( 32, 74, 42, 87, 'mon_bear', 90, [ 1, 2 ] )
    lv.box( 50, 64, 72, 92, 'I', 'f' )                 # the elephant yard
    for x in ( 54, 58, 62 ):
        lv.at( x, 66, ';' )
    lv.ellipse( 66, 84, 3, 2, '~' )
    lv.monster( 52, 74, 70, 90, 'sgn_mon_voi', 90, [ 1, 2 ] )
    lv.rect( 44, 62, 51, 62, 'o' )
    lv.rect( 27, 59, 29, 92, 'o' )                     # walks between the enclosures
    lv.rect( 45, 59, 49, 92, 'o' )
    lv.rect( 73, 71, 75, 92, 'o' )
    z1 = roof_over( lv, INDOOR, 'l' )
    for y in range( 8, 21 ):                           # the temple's green glazed roof
        for x in range( 60, 81 ):
            if z1.get( x, y ) == 'l':
                z1.at( x, y, 'N' )
    return { 0: lv, 1: z1 }


# --- 19. Công viên Văn hóa Đầm Sen --------------------------------------------------------
def dam_sen():
    # the lotus-pond park: a big lake with lotus at its edges, an island pagoda reached by a
    # causeway, swan boats at the jetty, the Ferris wheel, the rock garden with its waterfall,
    # the Nam Tú royal garden of bonsai, and the park train that runs round the fence
    lv = Level( 4, 4, 'g' )
    lv.rect( 0, 0, 95, 1, 'S' )
    lv.rect( 0, 2, 95, 2, 'I' )
    lv.rect( 0, 2, 0, 95, 'I' )
    lv.rect( 95, 2, 95, 95, 'I' )
    lv.rect( 0, 95, 95, 95, 'I' )
    lv.rect( 44, 2, 51, 2, 'o' )
    lv.box( 36, 3, 42, 8, 'C', '.' )                   # ticket booths
    lv.at( 42, 6, '+' )
    lv.at( 37, 4, '3' )
    lv.at( 39, 4, '3' )
    lv.rect( 44, 3, 51, 26, 'o' )                      # the walk to the lake
    for y in ( 4, 91 ):                                # the park train's loop
        lv.rect( 3, y, 92, y, '`' )
    for x in ( 3, 92 ):
        lv.rect( x, 4, x, 91, '`' )
    lv.rect( 44, 4, 51, 4, 'o' )                       # level crossing at the gate
    lv.vehicle( 12, 91, 'sgn_vg_mini_train', 0, 70 )
    lv.ellipse( 48, 54, 32, 24, '$' )                  # the lake, lotus round its edge
    lv.ellipse( 48, 54, 29, 21, '1' )
    lv.ellipse( 48, 54, 8, 6, 'g' )                    # the island
    lv.box( 45, 51, 51, 57, '#', 'n' )                 # its pagoda
    lv.at( 48, 51, '+' )
    lv.at( 48, 55, 'E' )
    lv.rect( 47, 60, 49, 79, 'o' )                     # the causeway from the south shore
    lv.rect( 47, 48, 49, 50, 'o' )
    lv.rect( 40, 27, 56, 28, 'o' )                     # the jetty
    for x in range( 41, 56, 3 ):
        lv.at( x, 29, ')' )
    lv.at( 80, 16, '@' )                               # the Ferris wheel
    lv.rect( 74, 18, 86, 20, 'o' )
    for y in range( 40, 60, 3 ):                       # the rock garden and its waterfall
        for x in range( 6, 14, 2 ):
            lv.at( x, y, '*' if ( x + y ) % 4 else 'X' )
    lv.ellipse( 14, 50, 3, 4, '~' )
    lv.rect( 8, 10, 30, 26, '(' )                      # Nam Tú royal garden of bonsai
    for y in range( 11, 26 ):
        for x in range( 9, 30 ):
            if ( x % 3 and y % 3 ):
                lv.at( x, y, 'o' )
    lv.box( 64, 82, 84, 90, 'C', '.' )                 # the restaurant
    lv.at( 74, 82, '+' )
    for x in range( 67, 82, 4 ):
        lv.at( x, 85, 't' )
        lv.at( x + 1, 85, 'c' )
    lv.at( 66, 88, 'u' )
    for x in range( 12, 40, 7 ):                       # kiosks and benches along the walks
        lv.at( x, 84, 'u' )
        lv.at( x + 1, 84, 's' )
    for y in range( 34, 76, 8 ):
        lv.at( 86, y, 'b' )
        lv.at( 10, y + 2, 'b' )
    for x, y in ( ( 20, 34 ), ( 30, 30 ), ( 64, 30 ), ( 76, 34 ), ( 82, 70 ), ( 20, 74 ), ( 30, 80 ), ( 66, 76 ) ):
        lv.at( x, y, '9' )
    scatter_trees( lv )                                # 60 % of Đầm Sen is trees and gardens
    z1 = roof_over( lv, INDOOR, 'l' )
    for y in range( 51, 58 ):                          # the island pagoda's green roof
        for x in range( 45, 52 ):
            if z1.get( x, y ) == 'l':
                z1.at( x, y, 'N' )
    return { 0: lv, 1: z1 }


# --- 20. Khu du lịch Suối Tiên ------------------------------------------------------------
def suoi_tien():
    # the 1995 legends park: the kỳ lân gate, Biển Tiên Đồng's artificial beach and wave
    # lagoon under the cliff where Lạc Long Quân stands over the waterfall, the Crocodile
    # Kingdom's lake, giant painted dragons in the gardens, the Ferris wheel and the park
    # train, and the temple of the Buddha
    lv = Level( 4, 4, 'g' )
    lv.rect( 0, 0, 95, 1, 'S' )
    lv.rect( 0, 2, 95, 2, 'I' )
    lv.rect( 0, 2, 0, 95, 'I' )
    lv.rect( 95, 2, 95, 95, 'I' )
    lv.rect( 0, 95, 95, 95, 'I' )
    lv.rect( 42, 2, 53, 2, 'o' )
    lv.at( 41, 3, ')' )                                # the kỳ lân gate guardians
    lv.at( 54, 3, ')' )
    lv.box( 30, 3, 37, 8, 'C', '.' )                   # ticket booths
    lv.at( 37, 6, '+' )
    lv.at( 31, 4, '3' )
    lv.rect( 42, 3, 53, 40, 'o' )                      # the processional walk
    for y in ( 5, 90 ):                                # the park train
        lv.rect( 3, y, 92, y, '`' )
    for x in ( 3, 92 ):
        lv.rect( x, 5, x, 90, '`' )
    lv.rect( 42, 5, 53, 5, 'o' )
    lv.vehicle( 60, 90, 'sgn_vg_mini_train', 0, 70 )
    # Biển Tiên Đồng: sand, a lagoon, the cliff and the giant over the waterfall
    lv.rect( 6, 44, 44, 88, ';' )
    lv.ellipse( 25, 70, 17, 12, '~' )
    lv.ellipse( 25, 72, 12, 8, '1' )
    lv.rect( 6, 84, 44, 88, 'X' )                      # the cliff
    lv.rect( 22, 82, 28, 84, '~' )                     # the waterfall's pool
    lv.at( 25, 86, "'" )                               # Lạc Long Quân
    lv.rect( 22, 85, 28, 85, '~' )
    for x in range( 8, 44, 6 ):                        # beach umbrellas and loungers
        lv.at( x, 48, 'b' )
    # the Crocodile Kingdom
    lv.box( 54, 48, 92, 70, '|', 'g' )
    lv.ellipse( 73, 59, 16, 9, 'M' )
    lv.rect( 54, 46, 92, 47, 'o' )                     # the viewing walk
    for x0 in ( 55, 72 ):
        lv.monster( x0, 50, x0 + 15, 69, 'sgn_mon_ca_sau', 100, [ 3, 6 ] )
    # gardens with the giant dragons
    for x, y in ( ( 12, 16 ), ( 30, 30 ), ( 64, 16 ), ( 80, 32 ) ):
        lv.at( x, y, '(' )
    for x, y in ( ( 8, 30 ), ( 20, 24 ), ( 70, 26 ), ( 86, 14 ) ):
        lv.at( x, y, '9' )
    lv.at( 76, 76, '@' )                               # the Ferris wheel
    lv.rect( 70, 78, 82, 80, 'o' )
    lv.box( 58, 10, 76, 22, '#', 'n' )                 # the temple of the Buddha
    lv.at( 58, 15, '+' )
    lv.at( 58, 16, '+' )
    for x in ( 62, 68 ):
        lv.at( x, 12, 'O' )
        lv.at( x, 20, 'O' )
    lv.rect( 72, 13, 72, 18, 'E' )
    lv.at( 74, 15, 'F' )
    lv.at( 67, 15, 'U' )
    lv.rect( 54, 14, 57, 17, 'o' )
    for x in range( 10, 40, 8 ):                       # kiosks along the walk
        lv.at( x, 40, 'u' )
        lv.at( x + 1, 40, 's' )
    scatter_trees( lv )
    z1 = roof_over( lv, INDOOR, 'N' )
    return { 0: lv, 1: z1 }


# --- 20. Sân bay Tân Sơn Nhất (the international terminal of 2007) -------------------------
def san_bay():
    # landside curb with abandoned taxis and a coach, the glass departures hall (check-in rows,
    # benches), security, duty-free and food on the airside, the gate lounges, and the apron
    # with its stand lines.  Real-map only: the airfield around it is sgn_sb_* (gen_san_bay.py).
    z0 = Level( 3, 2, ',' )
    z0.rect( 0, 0, 71, 1, 'S' )
    # each vehicle sits 12+ tiles into its map tile: a coach reaches 11 tiles back from its x
    for x, group in ( ( 12, 'sgn_vg_street_traffic' ), ( 20, 'sgn_vg_street_traffic' ),
                      ( 38, 'sgn_vg_street_traffic' ), ( 62, 'sgn_vg_coach' ) ):
        z0.vehicle( x, 4, group, 0, 50 )
    z0.rect( 0, 8, 71, 9, 'S' )
    z0.box( 2, 10, 69, 37, 'Y', '.' )
    for x0 in ( 10, 34, 58 ):                          # the doors from the curb
        z0.rect( x0, 10, x0 + 3, 10, 'D' )
    for x in range( 30, 42, 3 ):                       # benches in front of the departure boards
        z0.at( x, 13, '4' )
        z0.at( x + 1, 13, '4' )
    z0.rect( 32, 11, 39, 11, '2' )
    for x0, x1 in ( ( 6, 26 ), ( 44, 64 ) ):           # check-in counters, bag belts behind
        z0.rect( x0, 17, x1, 17, 'j' )
        z0.rect( x0, 19, x1, 19, 'B' )
    z0.rect( 3, 22, 68, 22, 'C' )                      # security: two lanes through the wall
    for x0 in ( 18, 50 ):
        z0.rect( x0, 22, x0 + 3, 22, ':' )
        z0.at( x0 - 1, 21, 'j' )
        z0.at( x0 + 4, 21, 'j' )
    for x in range( 5, 17, 2 ):                        # duty-free: clothes, then electronics
        z0.at( x, 25, '!' )
        z0.at( x, 27, '%' )
    for x in range( 20, 30, 2 ):
        z0.at( x, 25, '&' )
    for x in range( 44, 62, 4 ):                       # the food court
        z0.at( x, 25, 'u' )
        z0.at( x, 26, 's' )
        z0.at( x + 1, 26, 's' )
    for x in range( 6, 66, 8 ):                        # pillars, then the gate lounges
        z0.at( x, 29, 'P' )
    for y in ( 31, 33, 35 ):
        for x in range( 5, 67 ):
            if ( x - 5 ) % 7 < 5:
                z0.at( x, y, '4' )
    for x0 in ( 11, 34, 57 ):                          # gates out to the stands
        z0.rect( x0, 37, x0 + 1, 37, 'D' )
    z0.rect( 0, 38, 71, 47, '@' )                      # the apron, a stand line per gate
    z0.rect( 0, 39, 71, 39, '`' )
    for x in ( 12, 35, 58 ):
        z0.rect( x, 40, x, 47, '`' )
    z0.vehicle( 40, 43, 'sgn_vg_coach', 0, 30 )        # an apron bus that never left
    z1 = roof_over( z0, INDOOR )
    return { 0: z0, 1: z1 }


# --- 21. Nhà thờ Tân Định (L-loc3) -------------------------------------------------------------
def tan_dinh():
    # the pink church of 1876 on Hai Bà Trưng: a forecourt and gate, the square bell tower over
    # the door, a nave of pink columns and pews, the altar, and the Virgin Mary's grotto
    z0 = Level( 2, 2, ',' )
    z0.rect( 0, 0, 47, 1, 'S' )
    z0.rect( 2, 2, 45, 2, '|' )
    z0.rect( 21, 2, 26, 2, ',' )                       # the gate
    z0.box( 10, 8, 37, 45, 'H', '.' )                  # the pink nave
    z0.box( 19, 8, 28, 15, 'H', '.' )                  # the tower over the porch
    for x in ( 23, 24 ):
        z0.at( x, 8, '+' )
        z0.at( x, 15, '+' )
    for y in range( 18, 44, 4 ):
        z0.at( 10, y, 'w' )
        z0.at( 37, y, 'w' )
    for y in range( 18, 41, 4 ):                       # columns either side of the aisle
        z0.at( 15, y, 'P' )
        z0.at( 32, y, 'P' )
    for y in range( 17, 39, 2 ):                       # pews
        z0.rect( 17, y, 22, y, 'b' )
        z0.rect( 25, y, 30, y, 'b' )
    z0.rect( 19, 41, 28, 41, 'a' )                     # the altar
    z0.at( 23, 43, 'Z' )
    z0.rect( 39, 20, 46, 30, 'g' )                     # the grotto in the side garden
    z0.at( 42, 24, 'Z' )
    for x, y in ( ( 40, 27 ), ( 43, 27 ), ( 45, 22 ) ):
        z0.at( x, y, 'G' )
    for x, y in ( ( 4, 10 ), ( 5, 30 ), ( 42, 10 ), ( 43, 38 ) ):
        z0.at( x, y, 'T' )
    levels = { 0: z0 }
    for z in ( 1, 2, 3 ):
        lv = Level( 2, 2, ' ' )
        if z == 1:
            lv.rect( 10, 8, 37, 45, '_' )              # the nave roof
        if z < 3:
            lv.box( 19, 8, 28, 15, 'H', '.' )          # the tower climbs on
            for x in ( 19, 28 ):
                lv.at( x, 11, 'w' )
        else:
            lv.rect( 19, 8, 28, 15, '|' )              # the belfry, open, a railing round it
            lv.rect( 20, 9, 27, 14, '_' )
        levels[z] = lv
    levels[0].at( 20, 10, '<' )
    levels[1].at( 20, 10, '>' )
    levels[1].at( 26, 13, '<' )
    levels[2].at( 26, 13, '>' )
    levels[2].at( 20, 10, '<' )
    levels[3].at( 20, 10, '>' )
    levels[4] = Level( 2, 2, ' ' )
    levels[4].rect( 20, 9, 27, 14, '_' )               # the belfry's roof and the spire stub
    return levels


# --- 22. Chợ Tân Định (L-loc3) -----------------------------------------------------------------
def cho_tan_dinh():
    # the 1926 market hall, famous for fabric: bolts of cloth down the middle aisles, produce and
    # fish along one side, a row of food stalls with stools at the back
    z0 = Level( 2, 2, ',' )
    z0.rect( 0, 0, 47, 1, 'S' )
    z0.box( 2, 4, 45, 45, 'C', ':' )
    for x in range( 4, 44, 4 ):
        z0.at( x, 4, 'W' )
    for x in range( 21, 27 ):
        z0.at( x, 4, 'D' )
    for x in ( 2, 45 ):
        for y in ( 23, 24 ):
            z0.at( x, y, 'D' )
    for y in range( 8, 34, 3 ):                        # cloth stalls, two double rows
        z0.rect( 8, y, 18, y, 'y' )
        z0.rect( 29, y, 39, y, 'y' )
    for y in range( 8, 34, 2 ):                        # produce and fish along the walls
        z0.at( 4, y, 'q' )
        z0.at( 43, y, 'm' )
    for x in range( 6, 42, 4 ):                        # the food row at the back
        z0.at( x, 38, 'u' )
        z0.at( x, 40, 's' )
        z0.at( x + 1, 40, 's' )
    z1 = roof_over( z0, INDOOR )
    return { 0: z0, 1: z1 }


# --- 23. Bến Nhà Rồng (L-loc3) -----------------------------------------------------------------
def nha_rong():
    # the customs house of 1863 on the river, the Dragon House for the two glazed dragons on its
    # roof: a garden, a columned porch, exhibition rooms of glass cases on two floors, the quay
    z0 = Level( 2, 2, 'g' )
    z0.rect( 0, 0, 47, 1, 'S' )
    z0.rect( 22, 2, 25, 9, ',' )                       # the drive
    for x, y in ( ( 5, 4 ), ( 12, 6 ), ( 35, 5 ), ( 42, 4 ) ):
        z0.at( x, y, 'T' )
    z0.box( 8, 10, 39, 33, 'C', '^' )
    for x in range( 12, 37, 4 ):
        z0.at( x, 11, 'O' )                            # the red porch columns
    for x in ( 23, 24 ):
        z0.at( x, 10, 'D' )
    for x in range( 10, 39, 4 ):
        z0.at( x, 33, 'W' )
    z0.rect( 9, 20, 38, 20, 'C' )                      # two halls
    for x in ( 16, 31 ):
        z0.at( x, 20, '+' )
    for x in range( 11, 37, 4 ):                       # glass cases
        z0.at( x, 15, '$' )
        z0.at( x, 25, '$' )
        z0.at( x, 29, '$' )
    z0.at( 37, 13, '<' )
    z0.rect( 0, 34, 47, 40, ',' )                      # the quay
    for x in range( 4, 47, 8 ):
        z0.at( x, 40, 'X' )                            # bollards
    z0.rect( 0, 41, 47, 47, '~' )
    z1 = Level( 2, 2, ' ' )
    z1.box( 8, 10, 39, 33, 'C', '^' )
    for x in range( 10, 39, 4 ):
        z1.at( x, 10, 'W' )
        z1.at( x, 33, 'W' )
    for x in range( 11, 37, 4 ):
        z1.at( x, 18, '$' )
        z1.at( x, 26, '$' )
    z1.at( 37, 13, '>' )
    z2 = Level( 2, 2, ' ' )
    z2.rect( 8, 10, 39, 33, 'N' )                      # the green glazed roof
    for x in ( 9, 38 ):
        z2.at( x, 21, 'J' )                            # the two dragons at the ridge ends
    return { 0: z0, 1: z1, 2: z2 }


# --- 24. Khách sạn Rex (L-loc3) ----------------------------------------------------------------
def rex():
    # the hotel on the corner of Nguyễn Huệ and Lê Lợi: a lobby and restaurant, four floors of
    # rooms, and the rooftop garden bar under the crown, the place to watch the city from
    def floor():
        lv = Level( 2, 2, ' ' )
        lv.box( 3, 4, 44, 43, 'C', '=' )
        lv.rect( 4, 22, 43, 25, '.' )                  # the corridor
        for x in range( 4, 44, 8 ):                    # rooms either side
            lv.rect( x + 7, 5, x + 7, 21, 'C' )
            lv.rect( x + 7, 26, x + 7, 42, 'C' )
            lv.at( x + 3, 21, '+' )
            lv.at( x + 3, 26, '+' )
            lv.at( x + 2, 8, '5' )
            lv.at( x + 2, 38, '5' )
            lv.at( x + 5, 10, 't' )
            lv.at( x + 5, 36, 't' )
            lv.at( x + 3, 4, 'w' )
            lv.at( x + 3, 43, 'w' )
        return lv
    z0 = Level( 2, 2, ',' )
    z0.rect( 0, 0, 47, 1, 'S' )
    z0.box( 3, 4, 44, 43, 'C', '^' )
    for x in range( 5, 43, 2 ):
        z0.at( x, 4, 'Y' )
    for x in range( 22, 26 ):
        z0.at( x, 4, 'D' )
    z0.rect( 8, 9, 16, 9, 'j' )                        # reception
    for x, y in ( ( 28, 9 ), ( 34, 9 ), ( 28, 14 ), ( 34, 14 ) ):
        z0.at( x, y, 't' )
        z0.at( x + 1, y, 'c' )
    z0.rect( 4, 24, 43, 24, 'C' )                      # the restaurant at the back
    z0.at( 23, 24, '+' )
    for x in range( 7, 42, 6 ):
        for y in ( 29, 35 ):
            z0.at( x, y, 't' )
            z0.at( x, y + 1, 'c' )
    z0.at( 41, 20, 'A' )                               # the lobby piano
    levels = { 0: z0 }
    for z in range( 1, 5 ):
        levels[z] = floor()
    roof = Level( 2, 2, ' ' )
    roof.rect( 3, 4, 44, 43, '_' )
    roof.box( 3, 4, 44, 43, '|', '_' )                 # the parapet railing
    for x, y in ( ( 10, 12 ), ( 18, 12 ), ( 10, 30 ), ( 18, 30 ), ( 30, 30 ) ):
        roof.at( x, y, 't' )
        roof.at( x + 1, y, 'c' )
    roof.rect( 28, 10, 38, 10, 'j' )                   # the bar
    roof.at( 23, 6, 'Z' )                              # the crown
    for x, y in ( ( 6, 8 ), ( 40, 40 ), ( 6, 40 ) ):
        roof.at( x, y, 'T' )
    levels[5] = roof
    stairs = ( ( 41, 6 ), ( 41, 8 ) )
    for z in range( 0, 5 ):
        x, y = stairs[z % 2]
        levels[z].at( x, y, '<' )
        levels[z + 1].at( x, y, '>' )
    return levels


# --- 25. Chùa Vĩnh Nghiêm (L-loc6) -------------------------------------------------------------
def vinh_nghiem():
    # the Japanese-built pagoda of 1964 on Nam Kỳ Khởi Nghĩa: the three-door gate, a paved yard,
    # the main hall with the Buddha, the bell house, the monks' rooms, and the seven-storey
    # Quan Âm tower in the side garden
    z0 = Level( 3, 3, 'o' )
    z0.rect( 0, 0, 71, 1, 'S' )
    z0.rect( 2, 2, 69, 2, '#' )
    z0.box( 30, 2, 41, 7, '#', 'o' )                   # the tam quan gate
    for x in ( 33, 35, 37 ):
        z0.at( x, 2, '+' )
    z0.at( 35, 7, '+' )
    for x, y in ( ( 8, 10 ), ( 62, 10 ), ( 8, 64 ), ( 62, 64 ), ( 20, 30 ), ( 50, 30 ) ):
        z0.at( x, y, '9' )
    z0.box( 18, 18, 53, 45, 'O', 'n' )                 # the main hall, red columns
    for x in range( 31, 41 ):
        z0.at( x, 18, '+' if x % 2 else 'O' )
    z0.rect( 26, 38, 45, 38, 'E' )                     # the altar
    z0.at( 35, 41, 'F' )                               # the Buddha
    for x in ( 24, 30, 40, 46 ):
        z0.at( x, 34, 'U' )                            # incense urns
    for y in range( 24, 33, 3 ):
        z0.rect( 26, y, 45, y, 'h' )                   # incense coils hung in rows
    z0.box( 4, 20, 13, 29, '#', 'n' )                  # the bell house
    z0.at( 13, 24, '+' )
    z0.at( 8, 24, 'K' )
    z0.box( 18, 52, 53, 66, '#', '.' )                 # the monks' rooms
    for x in range( 22, 52, 6 ):
        z0.rect( x + 4, 53, x + 4, 65, '#' )
        z0.at( x + 1, 52, '+' )
        z0.at( x + 1, 60, '5' )
    z0.box( 58, 40, 66, 48, '#', 'n' )                 # the tower's ground floor
    z0.at( 62, 40, '+' )
    z0.at( 63, 46, 'F' )
    levels = { 0: z0 }
    for z in range( 1, 7 ):                            # the tower climbs alone
        lv = Level( 3, 3, ' ' )
        if z == 1:
            lv.rect( 18, 18, 53, 45, 'l' )             # tiled roofs over the halls
            lv.rect( 4, 20, 13, 29, 'l' )
            lv.rect( 18, 52, 53, 66, 'l' )
        lv.box( 58, 40, 66, 48, '#', 'n' )
        for y in ( 43, 45 ):
            lv.at( 58, y, 'w' )
            lv.at( 66, y, 'w' )
        lv.at( 63, 46, 'F' )
        levels[z] = lv
    stairs = ( ( 60, 42 ), ( 64, 42 ) )
    for z in range( 0, 6 ):
        x, y = stairs[z % 2]
        levels[z].at( x, y, '<' )
        levels[z + 1].at( x, y, '>' )
    levels[7] = Level( 3, 3, ' ' )
    levels[7].rect( 58, 40, 66, 48, 'l' )
    return levels


# --- 26. Lăng Ông Bà Chiểu (L-loc6) ------------------------------------------------------------
def lang_ong():
    # the shrine and tomb of Marshal Lê Văn Duyệt in Bình Thạnh: the gate, a garden court, the
    # worship hall with its lions and altar, and behind it the walled tomb under the trees
    z0 = Level( 2, 3, 'g' )
    z0.rect( 0, 0, 47, 1, 'S' )
    z0.rect( 1, 2, 46, 2, '#' )
    z0.rect( 1, 2, 1, 70, '#' )
    z0.rect( 46, 2, 46, 70, '#' )
    z0.rect( 1, 70, 46, 70, '#' )
    z0.rect( 20, 2, 27, 2, 'o' )                       # the gate
    z0.rect( 22, 3, 25, 20, 'o' )
    z0.at( 21, 4, 'L' )
    z0.at( 26, 4, 'L' )
    for x, y in ( ( 6, 8 ), ( 40, 8 ), ( 6, 30 ), ( 41, 30 ), ( 10, 58 ), ( 37, 58 ) ):
        z0.at( x, y, 'T' )
    z0.box( 10, 21, 37, 42, 'O', 'n' )                 # the worship hall
    for x in range( 21, 27 ):
        z0.at( x, 21, '+' if x % 2 else 'O' )
    z0.rect( 15, 36, 32, 36, 'E' )
    z0.at( 23, 39, 'F' )
    for x in ( 16, 31 ):
        z0.at( x, 32, 'U' )
    for y in range( 25, 32, 3 ):
        z0.rect( 15, y, 32, y, 'h' )
    z0.rect( 16, 48, 31, 64, '#' )                     # the tomb's enclosure
    z0.rect( 17, 49, 30, 63, 'o' )
    z0.rect( 23, 48, 24, 48, 'o' )
    z0.rect( 20, 54, 27, 59, '*' )                     # the twin tombs
    z0.at( 23, 51, 'J' )                               # the stone screen
    z1 = roof_over( z0, INDOOR, 'l' )
    return { 0: z0, 1: z1 }


# --- 27. Sân vận động Thống Nhất (L-loc6) ------------------------------------------------------
def thong_nhat():
    # the city stadium: ticket windows at the gates, a red track round the pitch, the covered
    # main stand on one side and open terraces on the others
    z0 = Level( 4, 4, ',' )
    z0.rect( 0, 0, 95, 1, 'S' )
    z0.box( 4, 6, 91, 91, 'C', ',' )
    for x in ( 44, 45, 46, 47, 48, 49, 50, 51 ):
        z0.at( x, 6, ',' )                             # the main gate
    for x in range( 38, 44 ):
        z0.at( x, 4, '3' )                             # ticket windows
    z0.rect( 16, 20, 79, 77, '@' )                     # the track
    z0.rect( 22, 26, 73, 71, 'g' )                     # the pitch
    z0.rect( 47, 26, 48, 71, '`' )                     # halfway line
    z0.rect( 22, 26, 73, 26, '`' )
    z0.rect( 22, 71, 73, 71, '`' )
    z0.rect( 22, 26, 22, 71, '`' )
    z0.rect( 73, 26, 73, 71, '`' )
    for x in ( 42, 53 ):
        z0.rect( x, 26, x, 28, '|' )                   # goalposts, roughly
        z0.rect( x, 69, x, 71, '|' )
    for y in range( 9, 18, 2 ):                        # the covered main stand, north
        z0.rect( 10, y, 85, y, '4' )
    z0.box( 8, 8, 87, 18, 'C', ':' )
    for x in range( 20, 80, 12 ):
        z0.at( x, 18, '+' )
    for y in range( 81, 89, 2 ):                       # open terraces
        z0.rect( 10, y, 85, y, '(' )
    for x in range( 7, 14, 2 ):
        z0.rect( x, 22, x, 76, '(' )
        z0.rect( 95 - x - 7, 22, 95 - x - 7, 76, '(' )
    z1 = Level( 4, 4, ' ' )
    z1.rect( 8, 8, 87, 18, '_' )
    return { 0: z0, 1: z1 }


# --- 28. Chợ An Đông (L-loc6) ------------------------------------------------------------------
def an_dong():
    # the four-storey market of Chợ Lớn's edge: gold and jewellery at the doors, fabric and
    # clothing wholesale on every floor above, stairwells at the corners
    def hall( z ):
        lv = Level( 2, 2, ',' if z == 0 else ' ' )
        if z == 0:
            lv.rect( 0, 0, 47, 1, 'S' )
        lv.box( 2, 3, 45, 45, 'C', '.' )
        for x in range( 4, 44, 3 ):
            lv.at( x, 3, 'W' if z else ( 'D' if 20 <= x <= 27 else 'W' ) )
        for y in range( 8, 42, 3 ):
            if z == 0:
                lv.rect( 6, y, 18, y, 'v' if y < 14 else 'y' )
                lv.rect( 29, y, 41, y, 'v' if y < 14 else 'y' )
            else:
                lv.rect( 6, y, 18, y, 'y' if z % 2 else '!' )
                lv.rect( 29, y, 41, y, '!' if z % 2 else 'y' )
        return lv
    levels = { z: hall( z ) for z in range( 4 ) }
    stairs = ( ( 4, 6 ), ( 43, 43 ) )
    for z in range( 3 ):
        x, y = stairs[z % 2]
        levels[z].at( x, y, '<' )
        levels[z + 1].at( x, y, '>' )
    levels[4] = roof_over( levels[3], INDOOR )
    return levels


# --- N6: the people who hold each landmark -------------------------------------------------------
# ( z, x, y, npc_class, chance ).  The classes are in data/mods/saigon_2000s/npcs/classes.json.
# check_staff() refuses to generate unless every entry lands on a walkable tile, so moving a wall
# in a builder cannot quietly leave somebody standing inside it.
STAFF = {
    'sgn_lm_ben_thanh': [
        ( 0, 11, 34, 'sgn_class_vendor' ), ( 0, 17, 34, 'sgn_class_vendor' ),
        ( 0, 23, 34, 'sgn_class_vendor' ), ( 0, 47, 34, 'sgn_class_vendor' ),
        ( 0, 53, 34, 'sgn_class_vendor' ), ( 0, 35, 32, 'sgn_class_vendor' ),
        ( 0, 36, 40, 'sgn_class_vendor' ) ],
    'sgn_lm_duc_ba': [
        ( 0, 23, 58, 'sgn_class_priest' ), ( 0, 23, 35, 'sgn_class_park_elder' ),
        ( 0, 24, 45, 'sgn_class_caretaker' ) ],
    'sgn_lm_buu_dien': [
        ( 0, 12, 13, 'sgn_class_postal_clerk' ), ( 0, 19, 13, 'sgn_class_postal_clerk' ),
        ( 0, 26, 13, 'sgn_class_postal_clerk' ), ( 0, 47, 13, 'sgn_class_postal_clerk' ),
        ( 0, 54, 13, 'sgn_class_postal_clerk' ) ],
    'sgn_lm_nha_hat': [
        ( 0, 23, 11, 'sgn_class_craftsman' ), ( 0, 23, 35, 'sgn_class_park_elder' ) ],
    'sgn_lm_ubnd_tp': [
        ( 0, 30, 16, 'sgn_class_civil_servant' ), ( 0, 36, 16, 'sgn_class_civil_servant' ),
        ( 0, 42, 16, 'sgn_class_civil_servant' ), ( 0, 30, 25, 'sgn_class_guard' ) ],
    'sgn_lm_dinh_doc_lap': [
        ( 0, 36, 39, 'sgn_class_guard' ), ( 0, 24, 46, 'sgn_class_civil_servant' ),
        ( 0, 48, 46, 'sgn_class_civil_servant' ) ],
    'sgn_lm_thien_hau': [
        ( 0, 23, 4, 'sgn_class_monk' ), ( 0, 20, 24, 'sgn_class_monk' ),
        ( 0, 20, 38, 'sgn_class_monk' ) ],
    'sgn_lm_ngoc_hoang': [
        ( 0, 23, 10, 'sgn_class_monk' ), ( 0, 20, 36, 'sgn_class_monk' ),
        ( 0, 38, 36, 'sgn_class_caretaker' ) ],
    'sgn_lm_binh_tay': [
        ( 0, 12, 13, 'sgn_class_vendor' ), ( 0, 22, 13, 'sgn_class_vendor' ),
        ( 0, 55, 29, 'sgn_class_vendor' ), ( 0, 30, 35, 'sgn_class_vendor' ) ],
    'sgn_lm_ga_sai_gon': [
        ( 0, 12, 10, 'sgn_class_transport_clerk' ), ( 0, 20, 10, 'sgn_class_transport_clerk' ),
        ( 0, 28, 10, 'sgn_class_transport_clerk' ), ( 0, 20, 27, 'sgn_class_vendor' ) ],
    'sgn_lm_ben_xe_md': [
        ( 0, 11, 7, 'sgn_class_transport_clerk' ), ( 0, 19, 7, 'sgn_class_transport_clerk' ),
        ( 0, 27, 7, 'sgn_class_transport_clerk' ), ( 0, 20, 23, 'sgn_class_transport_clerk' ) ],
    'sgn_lm_tao_dan': [
        ( 0, 35, 20, 'sgn_class_park_elder' ), ( 0, 20, 35, 'sgn_class_park_elder' ),
        ( 0, 43, 12, 'sgn_class_vendor' ) ],
    'sgn_lm_ho_con_rua': [
        ( 0, 12, 4, 'sgn_class_park_elder' ), ( 0, 19, 21, 'sgn_class_vendor' ) ],
    'sgn_lm_stc': [
        ( 0, 10, 10, 'sgn_class_office_worker' ), ( 1, 10, 12, 'sgn_class_office_worker' ),
        ( 4, 10, 12, 'sgn_class_office_worker' ) ],
    'sgn_lm_diamond': [
        ( 0, 23, 20, 'sgn_class_shopkeeper' ), ( 2, 26, 13, 'sgn_class_vendor' ) ],
    'sgn_lm_thao_cam_vien': [
        ( 0, 40, 5, 'sgn_class_caretaker' ), ( 0, 47, 20, 'sgn_class_park_elder' ),
        ( 0, 20, 41, 'sgn_class_park_elder' ), ( 0, 68, 15, 'sgn_class_monk' ) ],
    'sgn_lm_dam_sen': [
        ( 0, 47, 20, 'sgn_class_caretaker' ), ( 0, 47, 24, 'sgn_class_park_elder' ) ],
    'sgn_lm_suoi_tien': [
        ( 0, 47, 20, 'sgn_class_caretaker' ), ( 0, 47, 24, 'sgn_class_park_elder' ) ],
    'sgn_lm_san_bay': [
        ( 0, 10, 18, 'sgn_class_transport_clerk' ), ( 0, 34, 18, 'sgn_class_transport_clerk' ),
        ( 0, 58, 18, 'sgn_class_transport_clerk' ), ( 0, 40, 15, 'sgn_class_vendor' ) ],
    'sgn_lm_tan_dinh': [
        ( 0, 23, 38, 'sgn_class_priest' ), ( 0, 23, 26, 'sgn_class_caretaker' ) ],
    'sgn_lm_cho_tan_dinh': [
        ( 0, 12, 36, 'sgn_class_vendor' ), ( 0, 34, 36, 'sgn_class_vendor' ) ],
    'sgn_lm_nha_rong': [
        ( 0, 23, 13, 'sgn_class_dock_worker' ), ( 0, 23, 37, 'sgn_class_dock_worker' ) ],
    'sgn_lm_rex': [
        ( 0, 12, 11, 'sgn_class_shopkeeper' ), ( 0, 23, 28, 'sgn_class_vendor' ),
        ( 5, 33, 12, 'sgn_class_backpacker' ) ],
    'sgn_lm_vinh_nghiem': [
        ( 0, 35, 14, 'sgn_class_monk' ), ( 0, 28, 22, 'sgn_class_monk' ),
        ( 0, 8, 26, 'sgn_class_monk' ) ],
    'sgn_lm_lang_ong': [
        ( 0, 23, 10, 'sgn_class_caretaker' ), ( 0, 23, 34, 'sgn_class_monk' ) ],
    'sgn_lm_thong_nhat': [
        ( 0, 47, 5, 'sgn_class_transport_clerk' ), ( 0, 47, 20, 'sgn_class_park_elder' ) ],
    'sgn_lm_an_dong': [
        ( 0, 8, 6, 'sgn_class_vendor' ), ( 0, 39, 6, 'sgn_class_vendor' ) ],
}

# Bùi Viện is twelve lots of bar, travel agent and guesthouse, one person each.
STAFF['sgn_lm_bui_vien'] = [
    ( 0, 6 * k + 4, 10, 'sgn_class_vendor' if k % 3 == 0 else 'sgn_class_shopkeeper' )
    for k in range( 12 )
] + [ ( 0, 14, 4, 'sgn_class_backpacker' ), ( 0, 44, 4, 'sgn_class_backpacker' ),
      ( 0, 65, 4, 'sgn_class_vendor' ) ]

# Tiles a person may stand on: interior floor, tiled path, paving, grass, the stadium track and
# a roof terrace (Rex's garden bar is on the roof).
STAND = set( '.:=^on2S,g@_' )


def npc_id( cls ):
    """The npc template that stands for an npc_class.

    place_npcs names a `type: "npc"` template, not an npc_class, so STAFF names the
    class (which carries the gear) and the template it maps to is the same word with
    the prefix swapped.  Both live in data/mods/saigon_2000s/npcs/.
    """
    assert cls.startswith( 'sgn_class_' ), cls
    return 'sgn_npc_' + cls[len( 'sgn_class_' ):]


def staff( lid ):
    """STAFF entries as ( z, x, y, npc template )."""
    for z, x, y, cls in STAFF.get( lid, [] ):
        yield z, x, y, npc_id( cls )


def check_staff( lid, levels ):
    """Every person in STAFF must land on a walkable tile, on a level that exists."""
    bad = []
    for z, x, y, who in staff( lid ):
        if z not in levels:
            bad.append( '%s: z%d has no level' % ( who, z ) )
            continue
        ch = levels[z].get( x, y )
        if ch not in STAND:
            bad.append( '%s at z%d (%d,%d) stands on %r' % ( who, z, x, y, ch ) )
    return bad


LANDMARKS = {
    # id: ( builder, w, h, name, symbol colour, monsters per OMT-ish, items per symbol )
    'sgn_lm_ben_thanh': ( ben_thanh, 3, 3, 'Chợ Bến Thành', 'yellow' ),
    'sgn_lm_duc_ba': ( duc_ba, 2, 3, 'Nhà thờ Đức Bà', 'light_red' ),
    'sgn_lm_buu_dien': ( buu_dien, 3, 2, 'Bưu điện Thành phố', 'yellow' ),
    'sgn_lm_nha_hat': ( nha_hat, 2, 2, 'Nhà hát Thành phố', 'white' ),
    'sgn_lm_ubnd_tp': ( ubnd_tp, 3, 2, 'UBND Thành phố', 'yellow' ),
    'sgn_lm_dinh_doc_lap': ( dinh_doc_lap, 3, 3, 'Dinh Độc Lập', 'white' ),
    'sgn_lm_thien_hau': ( thien_hau, 2, 2, 'Chùa Bà Thiên Hậu', 'light_red' ),
    'sgn_lm_ngoc_hoang': ( ngoc_hoang, 2, 2, 'Chùa Ngọc Hoàng', 'light_red' ),
    'sgn_lm_binh_tay': ( binh_tay, 3, 3, 'Chợ Bình Tây', 'yellow' ),
    'sgn_lm_ga_sai_gon': ( ga_sai_gon, 3, 3, 'Ga Sài Gòn', 'light_gray' ),
    'sgn_lm_ben_xe_md': ( ben_xe_mien_dong, 3, 3, 'Bến xe Miền Đông', 'light_gray' ),
    'sgn_lm_tao_dan': ( tao_dan, 3, 3, 'Công viên Tao Đàn', 'green' ),
    'sgn_lm_ho_con_rua': ( ho_con_rua, 1, 1, 'Hồ Con Rùa', 'light_blue' ),
    'sgn_lm_stc': ( saigon_trade_center, 1, 1, 'Saigon Trade Center', 'cyan' ),
    'sgn_lm_diamond': ( diamond_plaza, 2, 2, 'Diamond Plaza', 'cyan' ),
    'sgn_lm_bui_vien': ( bui_vien, 3, 1, 'Phố Tây Bùi Viện', 'magenta' ),
    'sgn_lm_thao_cam_vien': ( thao_cam_vien, 4, 4, 'Thảo Cầm Viên', 'green' ),
    'sgn_lm_dam_sen': ( dam_sen, 4, 4, 'Công viên Đầm Sen', 'light_cyan' ),
    'sgn_lm_suoi_tien': ( suoi_tien, 4, 4, 'Khu du lịch Suối Tiên', 'light_red' ),
    'sgn_lm_san_bay': ( san_bay, 3, 2, 'Sân bay Tân Sơn Nhất', 'light_cyan' ),
    # L-loc3
    'sgn_lm_tan_dinh': ( tan_dinh, 2, 2, 'Nhà thờ Tân Định', 'pink' ),
    'sgn_lm_cho_tan_dinh': ( cho_tan_dinh, 2, 2, 'Chợ Tân Định', 'yellow' ),
    'sgn_lm_nha_rong': ( nha_rong, 2, 2, 'Bến Nhà Rồng', 'light_green' ),
    'sgn_lm_rex': ( rex, 2, 2, 'Khách sạn Rex', 'yellow' ),
    # L-loc6
    'sgn_lm_vinh_nghiem': ( vinh_nghiem, 3, 3, 'Chùa Vĩnh Nghiêm', 'light_red' ),
    'sgn_lm_lang_ong': ( lang_ong, 2, 3, 'Lăng Ông Bà Chiểu', 'light_red' ),
    'sgn_lm_thong_nhat': ( thong_nhat, 4, 4, 'Sân vận động Thống Nhất', 'light_green' ),
    'sgn_lm_an_dong': ( an_dong, 2, 2, 'Chợ An Đông', 'yellow' ),
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
            'Z': 't_concrete', 'A': 't_floor_waxed', 'e': 't_sgn_gach_men', 'j': 't_thconc_floor',
            'o': 't_sgn_gach_tau', 'n': 't_sgn_gach_tau_trong', 'O': 't_sgn_cot_son', 'h': 't_sgn_gach_tau_trong',
            'E': 't_sgn_gach_tau_trong', 'F': 't_sgn_gach_tau_trong', 'U': 't_sgn_gach_tau_trong',
            'L': 't_sgn_gach_tau', 'V': 't_sgn_gach_tau', 'J': 't_sgn_gach_tau', 'z': 't_sgn_gach_tau',
            'B': 't_thconc_floor', 'M': 't_water_murky', 'N': 't_sgn_ngoi_men_xanh', 'l': 't_sgn_mai_ngoi',
            'Y': 't_sgn_kinh_xanh', 'Q': 't_sgn_gach_men', '{': 't_sgn_thang_cuon_len', '}': 't_sgn_thang_cuon_xuong',
            '0': 't_railroad_track_h_on_tie', '-': 't_railroad_tie_h', '"': 't_railroad_rubble', '2': 't_thconc_floor', '3': 't_sgn_gach_men',
            '4': 't_thconc_floor', '6': 't_sgn_gach_tau', '7': 't_sgn_gach_tau', '8': 't_water_sh',
            '9': 't_sgn_tree_sao', '!': 't_sgn_gach_men', '%': 't_sgn_gach_men', '&': 't_sgn_gach_men',
            '5': 't_sgn_gach_men', 'i': 't_sgn_gach_men', '?': 't_concrete', '[': 't_concrete', ']': 't_concrete' },
        'furniture': {
            'G': 'f_sgn_van_tho', 'b': 'f_bench', 'k': 'f_counter', 't': 'f_table', 'r': 'f_rack',
            'v': 'f_sgn_quay_vang', 'q': 'f_counter', 'm': 'f_counter', 'y': 'f_rack', 'u': 'f_sgn_ban_inox',
            's': 'f_stool', 'a': 'f_table', 'd': 'f_desk', 'c': 'f_chair', 'x': 'f_filing_cabinet',
            'p': 'f_sgn_buong_dien_thoai', 'K': 'f_sgn_dong_ho', 'Z': 'f_statue', 'A': 'f_piano', 'e': 'f_desk',
            'j': 'f_counter', 'h': 'f_sgn_nhang_vong', 'E': 'f_sgn_ban_tho_lon', 'F': 'f_sgn_tuong_than',
            'U': 'f_sgn_lu_huong', 'V': 'f_sgn_lu_huong', 'L': 'f_sgn_su_tu_da', 'J': 'f_sgn_ho_rong',
            'z': 'f_statue', 'B': 'f_sgn_bao_gao', 'Q': 'f_desk', '2': 'f_sgn_bang_gio_tau', '3': 'f_sgn_quay_ve',
            '4': 'f_bench', '6': 'f_sgn_long_chim', '7': 'f_sgn_ban_da', '8': 'f_sgn_thap_rua', '!': 'f_rack',
            '%': 'f_rack', '&': 'f_rack', '5': 'f_bed', 'i': 'f_rack', '?': 'f_sgn_bang_hieu',
            '[': 'f_table', ']': 'f_stool' },
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
            'e': { 'item': 'sgn_palace_bunker', 'chance': 80, 'repeat': [ 1, 3 ] },
            'E': { 'item': 'sgn_temple', 'chance': 70, 'repeat': [ 1, 2 ] },
            'B': { 'item': 'sgn_cho_wholesale', 'chance': 60, 'repeat': [ 1, 2 ] },
            'Q': { 'item': 'sgn_office_desk', 'chance': 50 },
            '4': { 'item': 'sgn_train_station', 'chance': 25 },
            '!': { 'item': 'sgn_mall_fashion', 'chance': 50, 'repeat': [ 1, 2 ] },
            '%': { 'item': 'sgn_shoes', 'chance': 50 },
            '&': { 'item': 'sgn_electronics', 'chance': 40 },
            '5': { 'item': 'sgn_tourist', 'chance': 30 },
            'i': { 'item': 'sgn_tourist', 'chance': 45, 'repeat': [ 1, 2 ] } } }


def oter( lid, x, y, z ):
    return '%s_%d%d%s' % ( lid, x, y, '' if z == 0 else ( '_b' if z < 0 else '_z%d' % z ) )


MONSTERS = [ { 'group': 'sgn_GROUP_SAIGON_AWAKE', 'x': [ 0, 23 ], 'y': [ 0, 23 ], 'chance': 35 },
             { 'group': 'sgn_GROUP_ZOMBIE_DORMANT', 'x': [ 0, 23 ], 'y': [ 0, 23 ], 'chance': 40, 'repeat': [ 1, 3 ] } ]


def generate():
    mapgens, terrains, buildings = [], [], []
    for lid, ( build, w, h, name, colour ) in LANDMARKS.items():
        levels = build()
        bad = check_staff( lid, levels )
        if bad:
            raise SystemExit( '%s: %s' % ( lid, '; '.join( bad ) ) )
        for z, x, y, who in staff( lid ):
            levels[z].npc( x, y, who )
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
            if lv.monsters:
                obj['place_monster'] = obj.get( 'place_monster', [] ) + lv.monsters
            for key, table in LOCAL.get( lid, {} ).items():
                obj[key] = table
            if lv.vehicles:
                obj['place_vehicles'] = [ { 'vehicle': g, 'x': x, 'y': y, 'rotation': r, 'chance': ch }
                                          for x, y, g, r, ch in lv.vehicles ]
            if lv.npcs:
                obj['place_npcs'] = [ { 'class': w, 'x': x, 'y': y } for x, y, w in lv.npcs ]
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
