#!/usr/bin/env python3
"""Generate the city's corners (unit V2): eleven everyday places of 2009 Saigon that the
shophouse lots, the landmarks and gen_places.py did not have yet.

  quán cà phê võng      the hammock café: tin-roofed sheds of hammocks in a garden (parks pool)
  bia hơi vỉa hè        the sidewalk beer place: low tables, a beer tank, a grill (shops pool)
  hớt tóc vỉa hè        the street corner: a barber under a tamarind, a tyre fixer, a newsstand
  dãy nhà trọ           a boarding house of migrant workers: two floors of tiny rooms (houses pool)
  đình                  the old village's communal house: lỗ bộ weapon racks, the altar (parks pool)
  nhà thờ họ            a clan hall: ancestral altar, the two oldest graves in the yard (parks pool)
  tiệm điện thoại       a mobile phone shop: phones under glass, top-up cards, a repair bench
  chợ tạm               a makeshift night market on a closed street, tarps and carts
  lò nước đá            an ice depot: block ice in rice-husk lined rooms (sgn_vn_ice)
  bãi giữ xe            a guarded motorbike lot with an attendant's booth and a tin canopy
  trạm xe buýt          a bus terminus: a shelter, the bay, the dispatcher's office

The building kit (Level grids, roof_over, the shared sgn_lm palette, the npc template mapping,
the per-tile zombie spawns) is the landmark generator's, as in gen_places.py.  Each place adds
its own symbols as mapgen object keys (applied after the palette, so they win).  Local frame:
the street is to the north.  Map pictures are borrowed (looks_like) from drawn buildings that
look alike; no new art.

Before writing, every place is checked like tests/saigon_landmarks_test.cpp does it: each door
reachable from the street, each INDOORS tile roofed, each staircase paired, each person on a
walkable tile.

Run from the repo root:  python3 tools/saigon/gen_vn_places.py
"""
import glob
import json
import os
import sys

sys.path.insert( 0, os.path.dirname( __file__ ) )
import gen_saigon_landmarks as lm  # noqa: E402
from gen_saigon_landmarks import Level, roof_over  # noqa: E402

INDOOR = lm.INDOOR | set( '$()*@;f1' )
TIN = '/'   # a corrugated tin roof (t_sgn_mai_ton), the sheds and canopies of these places


def street( z0, deep=1 ):
    z0.rect( 0, 0, 23, deep, 'S' )


def roof( z0, cover, ch='_' ):
    return roof_over( z0, cover, ch )


def roof_rects( z0, rects, ch ):
    out = Level( z0.w // 24, z0.h // 24, ' ' )
    for x0, y0, x1, y1 in rects:
        out.rect( x0, y0, x1, y1, ch )
    return out


def roof_rect( lv, x0, y0, x1, y1, ch=TIN ):
    lv.rect( x0, y0, x1, y1, ch )


# --- Quán cà phê võng ------------------------------------------------------------------------
def cafe_vong():
    # the hammock café on the edge of town where xe ôm drivers and travellers sleep off the
    # noon heat: two open sheds of hammocks under tin, a garden of trees, a kitchen hut
    z0 = Level( 1, 1, 'g' )
    street( z0 )
    for x in range( 0, 24 ):
        z0.at( x, 2, '|' )
    z0.rect( 9, 2, 14, 6, ',' )                        # the gate and the bike parking
    for x in ( 10, 13 ):
        z0.vehicle( x, 4, 'sgn_vg_sidewalk_parked', 90, 50 )
    for x, y in ( ( 3, 4 ), ( 20, 4 ), ( 6, 6 ), ( 17, 6 ), ( 22, 14 ), ( 1, 15 ) ):
        z0.at( x, y, 'T' if x % 2 else '9' )
    for y0 in ( 8, 15 ):                               # two sheds, open on every side
        x1 = 21 if y0 == 8 else 13
        z0.rect( 2, y0, x1, y0 + 4, ':' )
        for x in range( 2, x1 + 1, 5 ):
            z0.at( x, y0, 'P' )
            z0.at( x, y0 + 4, 'P' )
        for x in range( 4, x1, 2 ):                    # hammocks in two rows, a low table between
            z0.at( x, y0 + 1, '(' )
            z0.at( x, y0 + 3, '(' )
        for x in range( 5, x1, 4 ):
            z0.at( x, y0 + 2, '[' )
    z0.box( 15, 15, 21, 21, '#', ':' )                 # the kitchen hut
    z0.at( 18, 15, '+' )
    z0.at( 15, 18, 'w' )
    z0.rect( 16, 17, 19, 17, '$' )                     # the counter: phin filters, robusta
    z0.at( 20, 19, '*' )                               # the ice chest
    z0.at( 16, 20, '1' )                               # the water jar
    z0.at( 20, 16, '@' )                               # shelves of the kitchen
    z0.npc( 18, 18, lm.npc_id( 'sgn_class_vendor' ) )           # behind the counter
    # the drivers who never woke from their nap, and one who did
    z0.monster( 3, 9, 20, 11, 'pseudo_dormant_sgn_mon_zombie_xe_om', 60, [ 1, 2 ] )
    z0.monster( 3, 16, 12, 18, 'sgn_mon_zombie_xe_om', 30 )
    z1 = Level( 1, 1, ' ' )
    z1.g = roof( z0, set( ':P([' ), TIN ).g
    for y in range( 15, 22 ):
        for x in range( 15, 22 ):
            z1.at( x, y, '_' )
    return { 0: z0, 1: z1 }


# --- Bia hơi vỉa hè ---------------------------------------------------------------------------
def bia_hoi():
    # the draught-beer place that takes over a corner every evening: rows of low tables and
    # plastic stools across the forecourt, umbrellas, and the shop behind with the beer tank,
    # the ice chests and the clay grill
    z0 = Level( 1, 1, ',' )
    street( z0 )
    for y in ( 4, 8, 12 ):
        for x in range( 3, 22, 4 ):
            z0.at( x, y, '[' )
            z0.at( x - 1, y, ']' )
            z0.at( x + 1, y, ']' )
            z0.at( x, y + 1, ']' )
    for x, y in ( ( 5, 6 ), ( 13, 6 ), ( 9, 10 ), ( 17, 10 ), ( 21, 6 ) ):
        z0.at( x, y, '\\' )                            # umbrellas
    z0.box( 1, 15, 22, 22, '#', '.' )                  # the shop
    for x in range( 8, 16 ):
        z0.at( x, 15, ';' )                            # a roller shutter, rolled up in the evening
    z0.at( 4, 15, 'w' )
    z0.at( 19, 15, 'w' )
    z0.rect( 3, 17, 6, 17, 'j' )                       # the counter
    z0.at( 3, 20, '@' )                                # the beer tank
    z0.at( 5, 20, '@' )
    for x in ( 9, 11 ):
        z0.at( x, 21, '*' )                            # ice chests
    z0.at( 14, 21, '$' )                               # the clay grill
    z0.rect( 17, 18, 21, 18, '#' )
    z0.at( 19, 18, '+' )
    for x in ( 17, 19, 21 ):
        z0.at( x, 21, ')' )                            # crates of bottles and the stock
    z0.npc( 4, 18, lm.npc_id( 'sgn_class_vendor' ) )            # behind the counter
    # the evening's drinkers: workers off a site, still at their tables
    z0.monster( 2, 3, 21, 13, 'pseudo_dormant_sgn_mon_zombie_tho_ho', 50, [ 1, 3 ] )
    z0.monster( 2, 3, 21, 13, 'sgn_mon_zombie_xe_om', 35 )
    z1 = roof( z0, INDOOR | set( ';' ) )
    return { 0: z0, 1: z1 }


# --- Hớt tóc vỉa hè: the street corner --------------------------------------------------------
def hot_toc():
    # a wide sidewalk under two old tamarinds: a barber's chair and a mirror nailed to the
    # trunk, a tyre fixer's toolbox and pump, a lottery seller's stool, a newsstand kiosk;
    # behind it the barber's family house
    z0 = Level( 1, 1, ',' )
    street( z0, 5 )
    z0.at( 4, 3, 'T' )
    z0.at( 19, 3, 'T' )
    z0.at( 4, 4, '*' )                                 # the mirror on the tree
    z0.at( 4, 5, '(' )                                 # the barber's chair
    z0.at( 6, 5, ']' )
    z0.at( 7, 5, ']' )                                 # stools for the next in line
    z0.at( 2, 5, '\\' )                                # the barber's box
    z0.at( 18, 4, '$' )                                # the tyre fixer's toolbox
    z0.at( 17, 5, '$' )
    z0.vehicle( 21, 4, 'sgn_vg_sidewalk_parked', 90, 60 )   # a bike waiting for its tyre
    z0.at( 12, 2, ']' )                                # the lottery seller's stool
    z0.box( 9, 6, 15, 9, 'C', ':' )                    # the newsstand
    z0.at( 15, 8, '+' )
    z0.rect( 10, 7, 14, 7, ')' )
    z0.box( 2, 12, 21, 22, '#', '.' )                  # the barber's family house
    z0.at( 11, 12, '+' )
    for x in ( 5, 8, 15, 18 ):
        z0.at( x, 12, 'w' )
    z0.rect( 3, 17, 20, 17, '#' )
    z0.at( 6, 17, '+' )
    z0.at( 17, 17, '+' )
    z0.at( 11, 15, '1' )                               # the family altar
    z0.at( 4, 14, '`' )                                # the TV
    z0.at( 19, 14, '\'' )                              # a hammock
    z0.at( 4, 20, 'f' )
    z0.at( 4, 21, 'f' )                                # beds
    z0.at( 19, 21, 'f' )
    z0.at( 10, 21, '@' )                               # the kitchen corner
    z0.at( 12, 21, '@' )
    z0.npc( 5, 5, lm.npc_id( 'sgn_class_craftsman' ) )          # the barber, by his chair
    z0.npc( 12, 3, lm.npc_id( 'sgn_class_vendor' ) )            # the lottery seller
    z1 = roof( z0, lm.INDOOR | set( ')`\'f1@' ) )
    return { 0: z0, 1: z1 }


# --- Dãy nhà trọ ------------------------------------------------------------------------------
def nha_tro():
    # a boarding house of the workers who came from the provinces: a folding gate, the
    # landlady's room, a long corridor of 3 x 4 metre rooms, shared washrooms at the end;
    # the same rooms upstairs along an inside corridor
    z0 = Level( 1, 1, ',' )
    street( z0 )
    z0.rect( 0, 2, 23, 2, ',' )
    z0.box( 1, 3, 22, 23, '#', ':' )
    for x in ( 11, 12 ):
        z0.at( x, 3, ';' )                             # the folding iron gate
    z0.rect( 10, 4, 13, 22, ',' )                      # the corridor, open to the sky
    rooms( z0, 0 )
    z0.box( 1, 3, 9, 7, '#', '.' )                     # the landlady's room by the gate
    z0.at( 9, 5, '+' )
    z0.at( 5, 3, 'w' )
    z0.at( 3, 5, 'f' )
    z0.at( 7, 6, 'Q' )
    z0.at( 6, 6, 'c' )
    z0.at( 3, 4, '1' )
    for y in ( 6, 9, 12, 15, 18 ):
        z0.vehicle( 11, y, 'sgn_vg_parked_twowheelers', 90, 45 )
    z0.at( 12, 21, '<' )
    z0.npc( 5, 5, lm.npc_id( 'sgn_class_caretaker' ) )          # the landlady
    # the night-shift sleepers in their rooms
    z0.monster( 2, 8, 8, 22, 'pseudo_dormant_sgn_mon_zombie_tho_ho', 50, [ 1, 2 ] )
    z0.monster( 15, 4, 21, 22, 'pseudo_dormant_sgn_mon_zombie_khuan_vac', 50, [ 1, 2 ] )
    z1 = Level( 1, 1, ' ' )
    z1.box( 1, 3, 22, 23, '#', ':' )
    rooms( z1, 1 )
    z1.box( 1, 3, 9, 7, '#', ':' )
    z1.at( 9, 5, '+' )
    z1.at( 3, 4, 'f' )
    z1.at( 3, 6, 'f' )
    z1.at( 7, 4, '@' )
    for x in ( 5, 11, 12, 18 ):
        z1.at( x, 3, 'w' )
    z1.at( 12, 21, '>' )
    z1.monster( 2, 8, 8, 22, 'pseudo_dormant_sgn_mon_zombie_tho_ho', 40 )
    z1.monster( 15, 4, 21, 22, 'sgn_mon_zombie_khuan_vac', 25 )
    z2 = roof( z1, INDOOR )
    return { 0: z0, 1: z1, 2: z2 }


def rooms( lv, z ):
    # tiny rooms down both sides of the corridor (x 10-13): a sleeping mat, a cupboard with the
    # gas ring, a clothes line; the last two on the east side are the shared washrooms
    for y0 in range( 7, 23, 4 ):
        if y0 + 4 > 23:
            break
        lv.box( 1, y0, 9, y0 + 4, '#', ':' )
        lv.at( 9, y0 + 2, '+' )
        lv.at( 2, y0 + 1, 'f' )
        lv.at( 3, y0 + 1, 'f' )
        lv.at( 8, y0 + 1, '@' )
        lv.at( 5, y0 + 3, '$' )
    for y0 in range( 3, 23, 4 ):
        if y0 + 4 > 23:
            break
        lv.box( 14, y0, 22, y0 + 4, '#', ':' )
        lv.at( 14, y0 + 2, '+' )
        if y0 >= 15:                                   # washrooms
            lv.at( 20, y0 + 1, '!' )
            lv.at( 20, y0 + 3, '%' )
            continue
        lv.at( 21, y0 + 1, 'f' )
        lv.at( 20, y0 + 1, 'f' )
        lv.at( 15, y0 + 1, '@' )
        lv.at( 18, y0 + 3, '$' )
    if z == 1:
        lv.rect( 10, 4, 13, 22, ':' )                  # the upstairs corridor


# --- Đình -------------------------------------------------------------------------------------
def dinh():
    # the communal house of the village that was here before the city: a walled yard of
    # old trees behind the three-door gate, stone lions, the open front hall where the lỗ bộ
    # weapon racks stand guard, and the sanctuary with the altar of the village's guardian
    z0 = Level( 1, 1, 'o' )
    street( z0 )
    z0.rect( 0, 2, 23, 23, '#' )
    z0.rect( 1, 3, 22, 22, 'o' )
    z0.rect( 8, 2, 15, 2, 'o' )                        # the gate: three openings between columns
    for x in ( 8, 10, 13, 15 ):
        z0.at( x, 2, 'O' )
    z0.at( 9, 4, 'L' )
    z0.at( 14, 4, 'L' )
    for x, y in ( ( 3, 5 ), ( 20, 5 ), ( 2, 17 ), ( 21, 17 ) ):
        z0.at( x, y, '9' )                             # the old trees
    z0.at( 11, 7, '\\' )                               # the yard's incense burner
    z0.rect( 4, 9, 19, 12, 'n' )                       # the front hall, open on all sides
    for x in range( 4, 20, 3 ):
        z0.at( x, 9, 'O' )
        z0.at( x, 12, 'O' )
    for y in ( 10, 11 ):
        for x in ( 5, 6, 17, 18 ):
            z0.at( x, y, '(' )                         # lỗ bộ weapon racks
    z0.at( 9, 10, 'h' )
    z0.at( 14, 10, 'h' )
    z0.box( 3, 13, 20, 21, '#', 'n' )                  # the sanctuary
    for x in ( 10, 11, 12, 13 ):
        z0.at( x, 13, '+' if x in ( 11, 12 ) else 'O' )
    z0.rect( 9, 19, 14, 19, 'E' )                      # the guardian's altar
    z0.at( 11, 20, 'F' )
    z0.at( 12, 20, 'F' )
    z0.at( 11, 17, 'U' )
    z0.at( 12, 17, 'U' )
    z0.at( 5, 18, 'E' )                                # side altars
    z0.at( 18, 18, 'E' )
    z0.at( 5, 15, 'h' )
    z0.at( 18, 15, 'h' )
    z0.at( 7, 15, '$' )                                # potted kumquats
    z0.at( 16, 15, '$' )
    z0.npc( 11, 10, lm.npc_id( 'sgn_class_caretaker' ) )        # the keeper, in the front hall
    z0.npc( 7, 6, lm.npc_id( 'sgn_class_park_elder' ) )         # an elder of the festival committee
    z0.monster( 4, 14, 19, 20, 'pseudo_dormant_sgn_mon_zombie_dam_tang', 30 )
    z1 = roof_rects( z0, ( ( 8, 2, 15, 2 ), ( 4, 9, 19, 12 ), ( 3, 13, 20, 21 ) ), 'l' )
    return { 0: z0, 1: z1 }


# --- Nhà thờ họ -------------------------------------------------------------------------------
def nha_tho_ho():
    # a clan hall: a small walled yard with the founders' two graves, the hall of the
    # ancestral altar with the tablets and the clan register, the long table of the death-day
    # feasts, the keeper's room at the back
    z0 = Level( 1, 1, 'g' )
    street( z0 )
    z0.rect( 1, 2, 22, 22, '#' )
    z0.rect( 2, 3, 21, 21, 'g' )
    z0.rect( 10, 2, 13, 2, ';' )                       # the iron gate
    z0.rect( 11, 3, 12, 9, 'o' )
    z0.at( 5, 6, '*' )
    z0.at( 18, 6, '*' )                                # the founders' graves
    z0.at( 3, 4, 'T' )
    z0.at( 20, 4, 'T' )
    z0.box( 4, 10, 19, 21, '#', 'n' )
    z0.at( 11, 10, '+' )
    z0.at( 12, 10, '+' )
    for x in ( 7, 16 ):
        z0.at( x, 10, 'w' )
    z0.rect( 9, 18, 14, 18, 'E' )                      # the ancestral altar and its tablets
    z0.at( 11, 16, 'U' )
    z0.at( 7, 12, 'h' )
    z0.at( 16, 12, 'h' )
    z0.rect( 7, 14, 9, 14, 't' )                       # the feast table
    z0.rect( 7, 13, 9, 13, 'c' )
    z0.rect( 7, 15, 9, 15, 'c' )
    z0.at( 18, 13, '$' )                               # the register cabinet
    z0.rect( 5, 19, 18, 19, '#' )
    z0.at( 17, 19, '+' )
    z0.at( 15, 20, 'f' )                               # the keeper's room
    z0.at( 18, 20, '@' )
    z0.npc( 12, 14, lm.npc_id( 'sgn_class_caretaker' ) )        # the keeper
    z1 = roof_rects( z0, ( ( 4, 10, 19, 21 ), ), 'l' )
    return { 0: z0, 1: z1 }


# --- Tiệm điện thoại di động ------------------------------------------------------------------
def dien_thoai():
    # a mobile phone shop: glass cases of Nokias and Motorolas, the counter of top-up cards and
    # SIM kits, the repair bench at the back, boxes in the stock room
    z0 = Level( 1, 1, ',' )
    street( z0 )
    for x in ( 4, 7, 16, 19 ):
        z0.vehicle( x, 3, 'sgn_vg_sidewalk_parked', 90, 40 )
    z0.at( 2, 4, '?' )
    z0.at( 21, 4, '?' )                                # the brand signs
    z0.box( 2, 5, 21, 21, 'C', '.' )
    for x in range( 3, 21 ):
        z0.at( x, 5, 'W' )
    for x in ( 11, 12 ):
        z0.at( x, 5, 'D' )
    z0.rect( 4, 8, 9, 8, '$' )                         # glass cases
    z0.rect( 14, 8, 19, 8, '$' )
    z0.rect( 4, 11, 4, 14, '$' )
    z0.rect( 9, 12, 14, 12, '@' )                      # the top-up counter
    z0.rect( 15, 11, 19, 11, '(' )                     # the repair bench
    z0.at( 17, 10, 'c' )
    z0.rect( 3, 16, 20, 16, 'C' )                      # the stock room
    z0.at( 11, 16, '+' )
    for x in range( 4, 20, 3 ):
        z0.at( x, 18, ')' )
        z0.at( x, 20, ')' )
    z0.npc( 11, 13, lm.npc_id( 'sgn_class_shopkeeper' ) )       # behind the top-up counter
    z0.npc( 17, 12, lm.npc_id( 'sgn_class_craftsman' ) )        # at the repair bench
    z1 = roof( z0, INDOOR )
    return { 0: z0, 1: z1 }


# --- Chợ tạm: the night market ----------------------------------------------------------------
def cho_tam():
    # a street closed off at dusk: rows of tables under tarps and umbrellas, clothes on rails,
    # fruit, cheap household goods, food carts and the drinks seller's ice chest
    z0 = Level( 1, 1, '`' )
    street( z0 )
    z0.rect( 0, 22, 23, 23, 'S' )
    kinds = '($*1'
    for i, y in enumerate( ( 3, 8, 9, 14, 15, 20 ) ):
        for x in range( 2, 22 ):
            if x in ( 11, 12 ):
                continue
            k = kinds[( i + x // 5 ) % len( kinds )]
            z0.at( x, y, k if x % 5 else '\\' )
    for x in ( 4, 9, 15, 19 ):
        z0.at( x, 5, 'u' )                             # food carts in the aisles
        z0.at( x, 18, 'u' )
    for x in ( 5, 10, 14, 20 ):
        z0.at( x, 4, ']' )
        z0.at( x, 19, ']' )
    for x in ( 3, 7, 16, 20 ):
        z0.at( x, 11, ')' )                            # food stalls with stools, on the cross aisle
        z0.at( x, 12, ']' )
    z0.npc( 6, 6, lm.npc_id( 'sgn_class_vendor' ) )
    z0.npc( 17, 17, lm.npc_id( 'sgn_class_vendor' ) )
    z0.monster( 2, 4, 21, 19, 'sgn_mon_zombie_vendor', 50, [ 1, 2 ] )
    z0.monster( 2, 4, 21, 19, 'pseudo_dormant_sgn_mon_zombie_vendor', 50, [ 1, 3 ] )
    z1 = Level( 1, 1, ' ' )
    return { 0: z0, 1: z1 }


# --- Lò nước đá -------------------------------------------------------------------------------
def lo_da():
    # an ice depot: the loading yard where ba gác collect the morning's blocks, the shed with
    # the freezing machinery, two cold rooms lined with rice husk where the blocks are stacked
    z0 = Level( 1, 1, ',' )
    street( z0 )
    z0.vehicle( 6, 4, 'sgn_vg_street_traffic', 0, 40 )
    z0.vehicle( 17, 4, 'sgn_vg_street_traffic', 0, 30 )
    z0.box( 1, 7, 22, 22, '/', ':' )
    for x in range( 9, 15 ):
        z0.at( x, 7, ';' )                             # the rolling door
    z0.rect( 3, 9, 7, 9, '@' )                         # the freezing machinery
    z0.rect( 16, 9, 20, 9, '@' )
    z0.rect( 3, 11, 6, 11, 'j' )                       # the scale and the order book
    z0.at( 5, 10, 'Q' )
    for x0, x1 in ( ( 2, 10 ), ( 13, 21 ) ):           # two cold rooms
        z0.box( x0, 13, x1, 21, 'C', ':' )
        z0.at( ( x0 + x1 ) // 2, 13, '1' )
        for y in ( 15, 17, 19 ):
            for x in range( x0 + 2, x1 - 1, 2 ):
                z0.at( x, y, '$' )                     # stacked ice blocks
        z0.rect( x0 + 1, 20, x1 - 1, 20, '*' )         # rice husk
    z0.npc( 5, 12, lm.npc_id( 'sgn_class_dock_worker' ) )       # at the scale
    z0.npc( 12, 10, lm.npc_id( 'sgn_class_dock_worker' ) )      # on the shed floor
    z0.monster( 3, 14, 9, 19, 'pseudo_dormant_sgn_mon_zombie_khuan_vac', 40 )
    z0.monster( 2, 8, 21, 12, 'sgn_mon_zombie_khuan_vac', 30 )
    z1 = roof( z0, INDOOR | set( '/;$*@1' ) )
    return { 0: z0, 1: z1 }


# --- Bãi giữ xe -------------------------------------------------------------------------------
def giu_xe():
    # a guarded motorbike lot: a fence, the attendant's booth by the entrance with the ticket
    # stubs and a rack of left helmets, three rows of bikes under a tin canopy
    z0 = Level( 1, 1, ',' )
    street( z0 )
    for x in range( 0, 24 ):
        z0.at( x, 2, 'I' )
        z0.at( x, 23, 'I' )
    for y in range( 2, 24 ):
        z0.at( 0, y, 'I' )
        z0.at( 23, y, 'I' )
    z0.rect( 9, 2, 13, 2, ',' )                        # the entrance
    z0.box( 15, 3, 20, 6, 'C', ':' )                   # the booth
    z0.at( 15, 5, '+' )
    z0.at( 17, 3, 'W' )
    z0.at( 16, 4, '$' )
    z0.at( 17, 4, 'c' )
    z0.at( 19, 5, '(' )
    for y in ( 9, 14, 19 ):                            # the canopy rows
        for x in range( 2, 22, 6 ):
            z0.at( x, y - 1, 'P' )
        for x in range( 3, 21, 2 ):
            z0.vehicle( x, y, 'sgn_vg_parked_twowheelers', 90, 60 )
    z0.npc( 17, 5, lm.npc_id( 'sgn_class_caretaker' ) )         # the attendant
    z0.monster( 2, 7, 21, 21, 'sgn_mon_zombie_xe_om', 40 )
    z0.monster( 2, 7, 21, 21, 'pseudo_dormant_sgn_mon_zombie_xe_om', 40, [ 1, 2 ] )
    z1 = roof( z0, INDOOR )
    for y in ( 9, 14, 19 ):
        roof_rect( z1, 2, y - 1, 21, y + 1 )
    return { 0: z0, 1: z1 }


# --- Trạm xe buýt -----------------------------------------------------------------------------
def tram_xe_buyt():
    # a bus terminus of the 2000s city buses: the shelter on a wide sidewalk with its sign, the
    # bay where two buses wait, the dispatcher's office and the washrooms
    z0 = Level( 1, 1, ',' )
    street( z0, 3 )
    z0.rect( 3, 2, 9, 2, '(' )                         # the shelter's bench
    z0.at( 2, 3, 'P' )
    z0.at( 10, 3, 'P' )
    z0.at( 12, 3, '?' )                                # the route sign
    z0.at( 15, 3, 'u' )                                # a drinks cart
    z0.rect( 1, 5, 17, 5, '\\' )                       # the bay's yellow line
    z0.rect( 1, 22, 17, 22, '\\' )
    z0.vehicle( 13, 8, 'sgn_vg_coach', 0, 60 )         # a bus is 14 x 7: x - 11 .. x + 2, y - 2 .. y + 4;
    #                                                    x 2 .. 15 leaves a walkway to the doors
    z0.vehicle( 13, 15, 'sgn_vg_coach', 0, 35 )
    z0.box( 18, 5, 22, 12, 'C', ':' )                  # the dispatcher's office
    z0.at( 18, 8, '+' )
    z0.at( 22, 8, 'w' )
    z0.at( 20, 6, 'Q' )
    z0.at( 20, 7, 'c' )
    z0.at( 21, 11, ')' )
    z0.box( 18, 14, 22, 21, 'C', '.' )                 # washrooms
    z0.at( 18, 17, '+' )
    z0.at( 21, 15, '!' )
    z0.at( 21, 17, '!' )
    z0.at( 21, 19, '%' )
    z0.npc( 20, 9, lm.npc_id( 'sgn_class_transport_clerk' ) )   # the dispatcher
    z0.npc( 14, 2, lm.npc_id( 'sgn_class_vendor' ) )            # the drinks cart
    z0.monster( 1, 0, 11, 4, 'sgn_mon_zombie_sot', 40 )         # still waiting for the bus
    z1 = roof( z0, INDOOR - set( 'u(' ) )
    roof_rect( z1, 2, 2, 10, 3 )
    return { 0: z0, 1: z1 }


# --- symbols, loot and the table of places ------------------------------------------------------
def group( *entries ):
    """An inline item group: ( "item" or "group", id, prob[, count] ) tuples."""
    out = []
    for e in entries:
        d = { e[0]: e[1], 'prob': e[2] }
        if len( e ) > 3:
            d['count'] = e[3]
        out.append( d )
    return { 'subtype': 'distribution', 'entries': out }


PHONES = group( ( 'item', 'sgn_dien_thoai', 40 ), ( 'item', 'sgn_the_cao', 40, [ 1, 10 ] ),
                ( 'group', 'sgn_electronics', 30 ) )
LO_BO = group( ( 'item', 'sgn_dao_lo_bo', 70 ), ( 'group', 'sgn_weapons_melee_common', 20 ),
               ( 'group', 'sgn_temple', 10 ) )
ICE_CHEST = group( ( 'group', 'sgn_vn_ice', 50 ), ( 'group', 'sgn_vn_drinks', 50 ) )
HELMETS = group( ( 'item', 'sgn_non_bao_hiem', 70 ), ( 'group', 'sgn_vn_daily_pocket', 30 ) )
TICKETS = group( ( 'item', 'sgn_ve_so', 50, [ 1, 5 ] ), ( 'item', 'sgn_newspaper', 50 ) )

STALL = { '(': 'f_table', '$': 'f_table', '*': 'f_table', '1': 'f_fridge', ')': 'f_table' }

PLACES = {
    # id: ( builder, w, h, name, colour, pool, weight, looks_like, local symbols )
    'sgn_vp_cafe_vong': (
        cafe_vong, 1, 1, 'quán cà phê võng', 'brown', 'parks', 12, 'sgn_pl_cong_vien_00',
        { 'terrain': { '(': 't_thconc_floor', '$': 't_thconc_floor', '*': 't_thconc_floor',
                       '1': 't_thconc_floor', '@': 't_thconc_floor', TIN: 't_sgn_mai_ton' },
          'furniture': { '(': 'f_sgn_vong', '$': 'f_counter', '*': 'f_fridge', '1': 'f_sgn_lu_nuoc',
                         '@': 'f_rack' },
          'liquids': { '1': { 'liquid': 'water', 'amount': [ 40, 240 ] } },
          'items': { '$': { 'item': 'sgn_cafe', 'chance': 60, 'repeat': [ 1, 2 ] },
                     '*': { 'item': ICE_CHEST, 'chance': 70, 'repeat': [ 1, 3 ] },
                     '@': { 'item': 'sgn_vn_daily_kitchen', 'chance': 50, 'repeat': [ 1, 2 ] },
                     '(': { 'item': 'sgn_vn_daily_pocket', 'chance': 10 } } } ),
    'sgn_vp_bia_hoi': (
        bia_hoi, 1, 1, 'bia hơi vỉa hè', 'yellow', 'shops', 5, 'sgn_nhaong_row_1',
        { 'terrain': { '\\': 't_concrete', ';': 't_rdoor_o', '@': 't_sgn_gach_men', '*': 't_sgn_gach_men',
                       '$': 't_sgn_gach_men', ')': 't_sgn_gach_men' },
          'furniture': { '\\': 'f_sgn_du', '@': 'f_standing_tank', '*': 'f_fridge', '$': 'f_sgn_bep_nuong',
                         ')': 'f_crate_c' },
          'liquids': { '@': { 'liquid': 'sgn_bia_hoi', 'amount': [ 20, 120 ] } },
          'items': { '*': { 'item': ICE_CHEST, 'chance': 70, 'repeat': [ 1, 3 ] },
                     ')': { 'item': 'sgn_nhau', 'chance': 60, 'repeat': [ 1, 3 ] },
                     '$': { 'item': 'sgn_vn_food_street', 'chance': 50, 'repeat': [ 1, 2 ] },
                     'j': { 'item': 'sgn_vn_daily_kitchen', 'chance': 40 },
                     '[': { 'item': 'sgn_vn_food_street', 'chance': 15 } } } ),
    'sgn_vp_hot_toc': (
        hot_toc, 1, 1, 'hớt tóc vỉa hè', 'light_cyan', 'shops', 3, 'sgn_nhaong_row_1',
        { 'terrain': { '(': 't_sidewalk', '*': 't_sidewalk', '@': 't_sgn_gach_men', '$': 't_sidewalk',
                       ')': 't_thconc_floor', '1': 't_sgn_gach_men', '`': 't_sgn_gach_men',
                       '\'': 't_sgn_gach_men', 'f': 't_sgn_gach_men', '\\': 't_sidewalk' },
          'furniture': { '\\': 'f_cardboard_box', '(': 'f_barber_chair', '*': 'f_bigmirror', '@': 'f_cupboard', '$': 'f_workbench',
                         ')': 'f_counter', '1': 'f_sgn_ban_tho', '`': 'f_sgn_tivi_crt', '\'': 'f_sgn_vong',
                         'f': 'f_bed' },
          'items': { '(': { 'item': 'sgn_barber', 'chance': 30 },
                     '\\': { 'item': 'sgn_barber', 'chance': 60, 'repeat': [ 1, 2 ] },
                     '$': { 'item': 'sgn_moto_shop', 'chance': 50, 'repeat': [ 1, 2 ] },
                     ')': { 'item': TICKETS, 'chance': 60, 'repeat': [ 1, 3 ] },
                     '@': { 'item': 'sgn_vn_daily_kitchen', 'chance': 40 },
                     '1': { 'item': 'sgn_pagoda', 'chance': 40 },
                     'f': { 'item': 'sgn_vn_daily_home', 'chance': 30 } } } ),
    'sgn_vp_nha_tro': (
        nha_tro, 1, 1, 'dãy nhà trọ', 'light_gray', 'houses', 6, 'sgn_hem_block',
        { 'terrain': { ';': 't_sgn_cua_sat_keo_c', 'f': 't_thconc_floor', '@': 't_thconc_floor',
                       '$': 't_thconc_floor', '1': 't_sgn_gach_men', '!': 't_sgn_gach_men', '%': 't_sgn_gach_men' },
          'furniture': { 'f': 'f_makeshift_bed', '@': 'f_cupboard', '$': 'f_sgn_day_phoi', '1': 'f_sgn_ban_tho',
                         '!': 'f_toilet', '%': 'f_sink' },
          'items': { 'f': { 'item': 'sgn_vn_daily_home', 'chance': 25 },
                     '@': { 'item': 'sgn_vn_daily_kitchen', 'chance': 40 },
                     '$': { 'item': 'sgn_shophouse_living', 'chance': 30 },
                     'Q': { 'item': 'sgn_vn_daily_shop', 'chance': 50 } } } ),
    'sgn_vp_dinh': (
        dinh, 1, 1, 'đình', 'light_red', 'parks', 10, 'sgn_chua',
        { 'terrain': { '\\': 't_sgn_gach_tau', '(': 't_sgn_gach_tau_trong', '$': 't_sgn_gach_tau_trong' },
          'furniture': { '\\': 'f_sgn_lu_huong', '(': 'f_rack_wood', '$': 'f_sgn_chau_kieng' },
          'items': { '(': { 'item': LO_BO, 'chance': 80, 'repeat': [ 1, 2 ] },
                     'E': { 'item': 'sgn_pagoda', 'chance': 50 } } } ),
    'sgn_vp_nha_tho_ho': (
        nha_tho_ho, 1, 1, 'nhà thờ họ', 'light_red', 'parks', 5, 'sgn_chua',
        { 'terrain': { ';': 't_sgn_cua_sat_keo_c', '*': 't_grass', '$': 't_sgn_gach_tau_trong',
                       'f': 't_sgn_gach_tau_trong', '@': 't_sgn_gach_tau_trong' },
          'furniture': { '*': 'f_sgn_mo', '$': 'f_bookcase', 'f': 'f_bed', '@': 'f_cupboard' },
          'items': { '$': { 'item': 'sgn_temple', 'chance': 60, 'repeat': [ 1, 2 ] },
                     'f': { 'item': 'sgn_vn_daily_home', 'chance': 40 },
                     '@': { 'item': 'sgn_vn_daily_kitchen', 'chance': 40 } } } ),
    'sgn_vp_dien_thoai': (
        dien_thoai, 1, 1, 'tiệm điện thoại di động', 'light_green', 'shops', 4, 'sgn_pl_nha_sach_00',
        { 'terrain': { '$': 't_sgn_gach_men', '@': 't_sgn_gach_men', '(': 't_sgn_gach_men',
                       ')': 't_thconc_floor' },
          'furniture': { '$': 'f_displaycase', '@': 'f_counter', '(': 'f_workbench', ')': 'f_rack' },
          'items': { '$': { 'item': PHONES, 'chance': 60, 'repeat': [ 1, 2 ] },
                     '@': { 'item': PHONES, 'chance': 70, 'repeat': [ 1, 3 ] },
                     '(': { 'item': 'sgn_electronics_repair', 'chance': 60 },
                     ')': { 'item': 'sgn_electronics', 'chance': 50, 'repeat': [ 1, 2 ] } } } ),
    'sgn_vp_cho_tam': (
        cho_tam, 1, 1, 'chợ tạm', 'yellow', 'shops', 2, 'sgn_cho_nw',
        { 'terrain': { '`': 't_pavement', '(': 't_pavement', '$': 't_pavement', '*': 't_pavement',
                       '1': 't_pavement', ')': 't_pavement', '\\': 't_pavement', 'u': 't_pavement' },
          'furniture': dict( STALL, **{ '\\': 'f_sgn_du' } ),
          'items': { '(': { 'item': 'sgn_cho_cloth', 'chance': 50 },
                     '$': { 'item': 'sgn_vn_daily_shop', 'chance': 50 },
                     '*': { 'item': 'sgn_vn_food_fruit', 'chance': 60, 'repeat': [ 1, 2 ] },
                     '1': { 'item': ICE_CHEST, 'chance': 60, 'repeat': [ 1, 2 ] },
                     ')': { 'item': 'sgn_vn_food_street', 'chance': 60, 'repeat': [ 1, 2 ] } } } ),
    'sgn_vp_lo_da': (
        lo_da, 1, 1, 'lò nước đá', 'light_blue', 'shops', 2, 'sgn_pl_kho_00',
        { 'terrain': { '/': 't_wall_metal', ';': 't_door_metal_c', '1': 't_door_metal_c',
                       '$': 't_thconc_floor', '*': 't_thconc_floor', '@': 't_thconc_floor' },
          'furniture': { '*': 'f_hay', '@': 'f_machinery_old' },
          'items': { '$': { 'item': 'sgn_vn_ice', 'chance': 80, 'repeat': [ 1, 3 ] },
                     '@': { 'item': 'sgn_loot_hardware', 'chance': 20 },
                     'j': { 'item': 'sgn_vn_ice', 'chance': 40 } } } ),
    'sgn_vp_giu_xe': (
        giu_xe, 1, 1, 'bãi giữ xe', 'light_gray', 'shops', 3, 'sgn_pl_cay_xang_00',
        { 'terrain': { '$': 't_thconc_floor', '(': 't_thconc_floor', TIN: 't_sgn_mai_ton' },
          'furniture': { '$': 'f_desk', '(': 'f_rack' },
          'items': { '$': { 'item': TICKETS, 'chance': 60 },
                     '(': { 'item': HELMETS, 'chance': 70, 'repeat': [ 1, 4 ] } } } ),
    'sgn_vp_tram_xe_buyt': (
        tram_xe_buyt, 1, 1, 'trạm xe buýt', 'light_cyan', 'shops', 2, 'sgn_lm_ben_xe_md_00',
        { 'terrain': { '(': 't_sidewalk', '\\': 't_pavement_y', 'u': 't_sidewalk', ')': 't_thconc_floor',
                       '!': 't_sgn_gach_men', '%': 't_sgn_gach_men', TIN: 't_sgn_mai_ton' },
          'furniture': { '(': 'f_bench', ')': 'f_rack', '!': 'f_toilet', '%': 'f_sink' },
          'items': { ')': { 'item': TICKETS, 'chance': 50, 'repeat': [ 1, 2 ] },
                     'u': { 'item': 'sgn_vn_drinks', 'chance': 50 } } } ),
}


# --- the structure check (tests/saigon_landmarks_test.cpp, done on the grids) -----------------
REPO = os.path.join( os.path.dirname( os.path.abspath( __file__ ) ), '..', '..' )


def load_defs():
    defs = {}
    files = glob.glob( os.path.join( REPO, 'data', 'json', '**', '*.json' ), recursive=True ) + \
        glob.glob( os.path.join( lm.ROOT, '**', '*.json' ), recursive=True )
    for f in files:
        try:
            with open( f, encoding='utf-8' ) as fh:
                d = json.load( fh )
        except ( ValueError, OSError ):
            continue
        for o in d if isinstance( d, list ) else [ d ]:
            if isinstance( o, dict ) and o.get( 'type' ) in ( 'terrain', 'furniture' ):
                key = o.get( 'id' ) or o.get( 'abstract' )
                if isinstance( key, str ):
                    defs[key] = o
    return defs


def resolved( defs, i, key ):
    o = defs.get( i )
    while o:
        if key in o:
            return o[key]
        o = defs.get( o.get( 'copy-from' ) )
    return None


def flags( defs, i ):
    chain = []
    o = defs.get( i )
    while o:
        chain.append( o )
        o = defs.get( o.get( 'copy-from' ) )
    out = set()
    for o in reversed( chain ):
        if 'flags' in o:
            out = set( o['flags'] )
        out |= set( o.get( 'extend', {} ).get( 'flags', [] ) )
        out -= set( o.get( 'delete', {} ).get( 'flags', [] ) )
    return out


def check( pid, levels, local, defs, pal ):
    def ter( ch ):
        t = local.get( 'terrain', {} ).get( ch ) or pal['terrain'].get( ch )
        return t if isinstance( t, str ) else None

    def furn( ch ):
        return local.get( 'furniture', {} ).get( ch ) or pal['furniture'].get( ch )

    def blocked( ch ):
        t = ter( ch )
        if t is None:
            return False
        if 'DOOR' in flags( defs, t ):
            return False
        if resolved( defs, t, 'move_cost' ) in ( 0, None ):
            return True
        f = furn( ch )
        return f is not None and resolved( defs, f, 'move_cost_mod' ) == -1

    bad = []
    for z, lv in levels.items():
        for y in range( lv.h ):
            for x in range( lv.w ):
                ch = lv.get( x, y )
                if ch == ' ':
                    continue
                t = ter( ch )
                if t is None and z == 0:
                    bad.append( 'z%d %d,%d %r has no terrain' % ( z, x, y, ch ) )
                elif t is not None and t not in defs:
                    bad.append( 'unknown terrain %s' % t )
                f = furn( ch )
                if f is not None and f not in defs:
                    bad.append( 'unknown furniture %s' % f )
                if t and 'INDOORS' in flags( defs, t ):
                    if z + 1 not in levels or levels[z + 1].get( x, y ) == ' ':
                        bad.append( 'z%d %d,%d %s (%r) has no roof' % ( z, x, y, t, ch ) )
                if t == 't_stairs_up' and ( z + 1 not in levels or ter( levels[z + 1].get( x, y ) ) != 't_stairs_down' ):
                    bad.append( 'z%d %d,%d stairs up meet no stairs down' % ( z, x, y ) )
        for x, y, who in lv.npcs:
            if blocked( lv.get( x, y ) ):
                bad.append( '%s at z%d %d,%d stands on %r' % ( who, z, x, y, lv.get( x, y ) ) )
    z0 = levels[0]
    seen = { ( x, 0 ) for x in range( z0.w ) if not blocked( z0.get( x, 0 ) ) }
    todo = list( seen )
    while todo:
        x, y = todo.pop()
        for dx, dy in ( ( 1, 0 ), ( -1, 0 ), ( 0, 1 ), ( 0, -1 ) ):
            q = ( x + dx, y + dy )
            if 0 <= q[0] < z0.w and 0 <= q[1] < z0.h and q not in seen and not blocked( z0.get( *q ) ):
                seen.add( q )
                todo.append( q )
    doors = [ ( x, y ) for y in range( z0.h ) for x in range( z0.w )
              if ter( z0.get( x, y ) ) and 'DOOR' in flags( defs, ter( z0.get( x, y ) ) ) ]
    for d in doors:
        if d not in seen:
            bad.append( 'door at %d,%d cannot be reached from the street' % d )
    return [ '%s: %s' % ( pid, b ) for b in bad ], len( doors )


def generate():
    mapgens, terrains, buildings = [], [], []
    defs = load_defs()
    pal = lm.palette()
    problems = []
    for pid, ( build, w, h, name, colour, _pool, _weight, looks, local ) in PLACES.items():
        levels = build()
        bad, _doors = check( pid, levels, local, defs, pal )
        problems += bad
        overmaps = []
        for z, lv in sorted( levels.items() ):
            rows = lv.rows()
            assert len( rows ) == h * 24 and all( len( r ) == w * 24 for r in rows ), ( pid, z )
            grid = [ [ lm.oter( pid, x, y, z ) for x in range( w ) ] for y in range( h ) ]
            obj = { 'fill_ter': 't_concrete' if z == 0 else 't_open_air', 'rows': rows, 'palettes': [ 'sgn_lm' ] }
            if z == 0:
                obj['flags'] = lm.CLEARING
                obj['place_monster'] = [ dict( m, x=[ ox * 24, ox * 24 + 23 ], y=[ oy * 24 + ( 6 if oy == 0 else 0 ), oy * 24 + 23 ] )
                                         for oy in range( h ) for ox in range( w ) for m in lm.MONSTERS ]
            if lv.monsters:
                obj['place_monster'] = obj.get( 'place_monster', [] ) + lv.monsters
            for key, table in local.items():
                obj[key] = table
            if lv.vehicles:
                obj['place_vehicles'] = [ { 'vehicle': g, 'x': x, 'y': y, 'rotation': r, 'chance': ch }
                                          for x, y, g, r, ch in lv.vehicles ]
            if lv.npcs:
                obj['place_npcs'] = [ { 'class': who, 'x': x, 'y': y } for x, y, who in lv.npcs ]
            mapgens.append( { 'type': 'mapgen', 'om_terrain': grid, 'object': obj } )
            for y in range( h ):
                for x in range( w ):
                    tid = lm.oter( pid, x, y, z )
                    terrains.append( { 'type': 'overmap_terrain', 'id': tid,
                                       'copy-from': 'generic_city_building' if z == 0 else 'generic_city_building_roof',
                                       'name': name if z == 0 else name + ' (roof)', 'sym': '&' if z == 0 else '#',
                                       'color': colour, 'looks_like': looks if ( x, y, z ) == ( 0, 0, 0 )
                                       else lm.oter( pid, 0, 0, 0 ) } )
                    overmaps.append( { 'point': [ x, y, z ], 'overmap': tid + '_north' } )
        buildings.append( { 'type': 'city_building', 'id': pid, 'locations': [ 'land' ],
                            'flags': [ 'SAIGON' ], 'city_sizes': [ 4, -1 ], 'overmaps': overmaps } )
    return mapgens, terrains + buildings, problems


def main():
    mg, om, problems = generate()
    if problems:
        sys.exit( 'structure problems:\n  ' + '\n  '.join( problems ) )
    root = lm.ROOT
    os.makedirs( os.path.join( root, 'mapgen', 'vn_places' ), exist_ok=True )
    with open( os.path.join( root, 'mapgen', 'vn_places', 'vn_places.json' ), 'w', encoding='utf-8' ) as f:
        json.dump( mg, f, ensure_ascii=False, indent=2 )
    with open( os.path.join( root, 'overmap', 'vn_places.json' ), 'w', encoding='utf-8' ) as f:
        json.dump( om, f, ensure_ascii=False, indent=2 )
    print( 'wrote %d places: %s' % ( len( PLACES ), ', '.join( PLACES ) ) )
    print( 'region weights: ' + ', '.join( '%s %s %d' % ( p[5], k, p[6] ) for k, p in PLACES.items() ) )


if __name__ == '__main__':
    main()
