#!/usr/bin/env python3
"""Fidelity audit of the real-map Saigon 2009 (unit R-fid): how closely the written overmap files
match the OpenStreetMap source and the city of late 2009, in numbers.

  python3 tools/saigon/realmap/audit_fidelity.py [FOLDER] [--json OUT.json]

FOLDER defaults to data/mods/saigon_2000s/realmap_2009.  Reads the z 0 layer of every
overmap_*.omap.gz there and the local OSM extract (osm/*.osm.json), and reports:

  scale      the projection against the WGS84 great-circle distance over long pairs of points
  roads      for each key street: the share of the tiles its OSM ways cross that are road within
             one tile (coverage), the share of those road tiles in one linked piece (continuity),
             and the longest run of its line with no road within one tile (gap)
  water      the same for the river and the canals, counting water, bridges and ferry docks
  bridges    the OSM bridges over the river and the main canals, present or not, and whether
             each existed in late 2009
  landmarks  every placed landmark's centre against its anchor and against the OSM feature of
             that name
  districts  land use mix per district (nearest district centre, districts_2009.json)
  2009       roads and bridges in today's OSM that came after 2009 and must not be on the map

Data © OpenStreetMap contributors, ODbL 1.0.
"""
import glob
import gzip
import json
import math
import os
import sys
import unicodedata

HERE = os.path.dirname( os.path.abspath( __file__ ) )
ROOT = os.path.join( HERE, '..', '..', '..' )
sys.path.insert( 0, HERE )
import classify as C  # noqa: E402

OM = 180
ORIGIN_OM = ( -1, -2 )
W, H = C.AREA_W, C.AREA_H
DIRS = { 'n': ( 0, -1 ), 'e': ( 1, 0 ), 's': ( 0, 1 ), 'w': ( -1, 0 ) }
SUFFIX_CONN = { '_isolated': '', '_end_south': 'n', '_end_west': 'e', '_end_north': 's', '_end_east': 'w',
                '_ns': 'ns', '_ew': 'ew', '_ne': 'ne', '_es': 'es', '_sw': 'sw', '_wn': 'nw',
                '_nes': 'nes', '_new': 'new', '_nsw': 'nsw', '_esw': 'esw', '_nesw': 'nesw' }

# Streets a Saigonese of 2009 would look for (today's OSM names; Võ Văn Kiệt was Bến Chương Dương /
# Hàm Tử / Trần Văn Kiểu along the canal in 2009)
KEY_ROADS = [
    ( 'Lê Lợi', 10.7735, 106.700 ), ( 'Nguyễn Huệ', 10.7745, 106.703 ), 'Đồng Khởi', 'Cách Mạng Tháng Tám', 'Nam Kỳ Khởi Nghĩa',
    'Điện Biên Phủ', 'Võ Văn Tần', 'Trần Hưng Đạo', 'Nguyễn Văn Cừ', 'Võ Văn Kiệt', 'Lê Duẩn',
    ( 'Tôn Đức Thắng', 10.778, 106.706 ), 'Hàm Nghi', 'Pasteur', 'Nguyễn Thị Minh Khai', 'Nguyễn Đình Chiểu', 'Lý Thái Tổ',
    '3 Tháng 2', 'Nguyễn Trãi', 'Hùng Vương', 'An Dương Vương', 'Hồng Bàng', 'Lý Thường Kiệt',
    'Nguyễn Tri Phương', 'Trường Chinh', 'Cộng Hòa', 'Hoàng Văn Thụ', 'Nguyễn Văn Trỗi', 'Lê Văn Sỹ',
    'Phan Đăng Lưu', 'Xô Viết Nghệ Tĩnh', ( 'Đinh Tiên Hoàng', 10.79, 106.70 ), 'Nguyễn Tất Thành',
    'Nguyễn Hữu Cảnh', 'Xa lộ Hà Nội', 'Huỳnh Tấn Phát', 'Lương Định Của', 'Quang Trung', 'Nguyễn Oanh',
    'Lê Quang Định', ( 'Bạch Đằng', 10.803, 106.703 ), 'Kha Vạn Cân', 'Phạm Thế Hiển', 'Tùng Thiện Vương',
    'Võ Nguyên Giáp', ( 'Hoàng Diệu', 10.760, 106.703 ), ( 'Hai Bà Trưng', 10.785, 106.695 ),
]
# Water: name fragments of the OSM waterway lines and polygons
KEY_WATER = [
    ( 'Sông Sài Gòn', [ 'sông sài gòn' ] ),
    ( 'Bến Nghé', [ 'bến nghé' ] ),
    ( 'Tàu Hủ', [ 'tàu hủ' ] ),
    ( 'Nhiêu Lộc – Thị Nghè', [ 'nhiêu lộc', 'thị nghè' ] ),
    ( 'Tân Hóa – Lò Gốm', [ 'lò gốm', 'tân hóa' ] ),
    ( 'Kênh Đôi', [ 'kênh đôi' ] ),
    ( 'Kênh Tẻ', [ 'kênh tẻ' ] ),
    ( 'Rạch Văn Thánh', [ 'văn thánh' ] ),
    ( 'Kênh Thanh Đa', [ 'kênh thanh đa' ] ),
    ( 'Rạch Chiếc', [ 'rạch chiếc' ] ),
]
# Bridges over the river and the city's main canals: name -> ( opened, note ).  Years from memory
# (checked where noted in corrections_2009.json); 'after' = after 2009, must not be on the map.
KEY_BRIDGES = {
    'Cầu Sài Gòn': ( 1961, 'Xa lộ Hà Nội over the Sài Gòn river' ),
    'Cầu Thủ Thiêm': ( 2008, 'Bình Thạnh - Thủ Thiêm, opened January 2008' ),
    'Cầu Phú Mỹ': ( 2009, 'opened 2 September 2009: there in late 2009' ),
    'Cầu Bình Triệu 1': ( 1950, '' ), 'Cầu Bình Triệu 2': ( 2002, '' ),
    'Cầu Kênh Tẻ': ( 2003, '' ), 'Cầu Tân Thuận 1': ( 1970, '' ), 'Cầu Tân Thuận 2': ( 2006, '' ),
    'Cầu Khánh Hội': ( 1920, '' ), 'Cầu Ông Lãnh': ( 1920, '' ), 'Cầu Calmette': ( 1920, '' ),
    'Cầu Chữ Y': ( 1939, '' ), 'Cầu Nguyễn Văn Cừ': ( 2006, '' ), 'Cầu Chà Và': ( 1930, '' ),
    'Cầu Nhị Thiên Đường': ( 1925, '' ), 'Cầu Thị Nghè 1': ( 1960, '' ), 'Cầu Bông': ( 1950, '' ),
    'Cầu Kiệu': ( 1950, '' ), 'Cầu Điện Biên Phủ': ( 1960, '' ), 'Cầu Lê Văn Sỹ': ( 1960, '' ),
    'Cầu Công Lý': ( 1960, '' ), 'Cầu Văn Thánh 1': ( 1960, '' ), 'Cầu Rạch Chiếc': ( 1961, 'old spans' ),
    'Cầu Kinh Thanh Đa': ( 1960, '' ),
    'Cầu Sài Gòn 2': ( 'after', 'opened 2021' ),
    'Cầu Ba Son': ( 'after', 'Thủ Thiêm 2, opened 2022' ),
    'Cầu Thị Nghè 2': ( 'after', 'opened about 2013-14 (from memory)' ),
    'Cầu Phú Hữu': ( 'after', 'ring road 2, after 2015' ),
    'Cầu Bà Dạt': ( 'after', 'Long Thành expressway, 2015' ),
    'Cầu Bà Hiện': ( 'after', 'Long Thành expressway, 2015' ),
    'Cầu Mương Kênh': ( 'after', 'Long Thành expressway, 2015' ),
    'Cầu Đỗ Xuân Hợp': ( 'after', 'Long Thành expressway, 2015' ),
}
# Roads in today's OSM that were not there in late 2009 (corrections_2009.json drops them)
POST_2009_ROADS = [ 'Mai Chí Thọ', 'Phạm Văn Đồng', 'Võ Chí Công', 'Long Thành', 'Vành đai 2', 'Trần Bạch Đằng',
                    'Tố Hữu', 'Nguyễn Cơ Thạch', 'Song Hành', 'Trường Sơn nối dài', 'Nối Trần Quốc Hoàn',
                    'Đường nối Trần Quốc Hoàn' ]
# Landmarks: OSM name fragments for an independent position (land and place extracts)
LANDMARK_OSM = {
    'sgn_lm_ben_thanh': [ 'chợ bến thành' ], 'sgn_lm_duc_ba': [ 'đức bà', 'notre' ],
    'sgn_lm_buu_dien': [ 'bưu điện thành phố', 'bưu điện trung tâm' ],
    'sgn_lm_dinh_doc_lap': [ 'dinh độc lập', 'hội trường thống nhất' ],
    'sgn_lm_binh_tay': [ 'chợ bình tây' ], 'sgn_lm_ga_sai_gon': [ 'ga sài gòn' ],
    'sgn_lm_thao_cam_vien': [ 'thảo cầm viên' ], 'sgn_lm_dam_sen': [ 'đầm sen' ],
    'sgn_lm_thien_hau': [ 'tuệ thành' ], 'sgn_lm_ngoc_hoang': [ 'ngọc hoàng', 'phước hải' ],
    'sgn_lm_tao_dan': [ 'tao đàn' ], 'sgn_lm_an_dong': [ 'chợ an đông' ], 'sgn_lm_tan_dinh': [ 'nhà thờ tân định' ],
    'sgn_lm_cho_tan_dinh': [ 'chợ tân định' ], 'sgn_lm_vinh_nghiem': [ 'vĩnh nghiêm' ],
    'sgn_lm_lang_ong': [ 'lăng ông' ], 'sgn_lm_thong_nhat': [ 'sân vận động thống nhất' ],
    'sgn_lm_nha_rong': [ 'nhà rồng' ], 'sgn_lm_suoi_tien': [ 'suối tiên' ],
}
# Places that are not landmarks but that a player would look for: the nearest building of that kind
KEY_PLACES = [ ( 'Bệnh viện Chợ Rẫy', 'chợ rẫy', 'sgn_pl_benh_vien' ),
               ( 'Bệnh viện Từ Dũ', 'từ dũ', 'sgn_pl_benh_vien' ),
               ( 'Chợ Bà Chiểu', 'chợ bà chiểu', 'sgn_cho' ),
               ( 'Chợ Tân Định (place)', 'chợ tân định', 'sgn_' ),
               ( 'Chùa Giác Lâm', 'giác lâm', 'sgn_chua' ) ]


def nfc( s ):
    return unicodedata.normalize( 'NFC', s or '' )


def low( s ):
    return nfc( s ).lower().strip()


def bare( name ):
    n = low( name )
    for pre in ( 'đường ', 'đại lộ ' ):
        if n.startswith( pre ):
            n = n[len( pre ):]
    return n


def load_osm( name ):
    return json.load( open( os.path.join( HERE, 'osm', 'saigon_%s.osm.json' % name ) ) )['elements']


def load_map( folder ):
    tiles = {}
    for f in glob.glob( os.path.join( folder, 'overmap_*.omap.gz' ) ):
        for o in json.load( gzip.open( f, 'rt' ) ):
            if o['z'] != 0:
                continue
            ox, oy = o['om_pos'][0] - ORIGIN_OM[0], o['om_pos'][1] - ORIGIN_OM[1]
            i = 0
            for t, n in o['layers']:
                for _ in range( n ):
                    tiles[( ox * OM + i % OM, oy * OM + i // OM )] = t
                    i += 1
    return tiles


def walk( geom ):
    out = []
    for a, b in zip( geom, geom[1:] ):
        x0, y0 = C.latlon_to_tile( a['lat'], a['lon'] )
        x1, y1 = C.latlon_to_tile( b['lat'], b['lon'] )
        n = int( max( abs( x1 - x0 ), abs( y1 - y0 ) ) * 4 ) + 1
        for i in range( n + 1 ):
            t = i / n
            p = ( int( math.floor( x0 + ( x1 - x0 ) * t ) ), int( math.floor( y0 + ( y1 - y0 ) * t ) ) )
            if not out or p != out[-1]:
                out.append( p )
    return [ p for p in out if 0 <= p[0] < W and 0 <= p[1] < H ]


def conn( t ):
    """Linked directions of a road or bridge tile, or None."""
    if t.startswith( 'road_' ):
        return SUFFIX_CONN.get( t[4:], '' )
    if t.startswith( 'bridge_' ):
        return 'ns' if t in ( 'bridge_north', 'bridge_south' ) else 'ew'
    return None


def is_road( t ):
    return t.startswith( 'road_' ) or t.startswith( 'bridge_' )


def is_water( t ):
    return t.startswith( 'lake' ) or t.startswith( 'bridge_' ) or t.startswith( 'sgn_ben_pha' )


def near( tiles, p, pred, r=1 ):
    return any( pred( tiles.get( ( p[0] + dx, p[1] + dy ), '' ) ) for dx in range( -r, r + 1 ) for dy in range( -r, r + 1 ) )


def clusters( paths, reach=2 ):
    """Group paths (lists of tiles) whose tiles come within `reach` tiles of each other: the same
    name is used by unrelated streets in several districts."""
    parent = list( range( len( paths ) ) )

    def find( i ):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    cell = {}
    for i, path in enumerate( paths ):
        for p in path:
            for dx in range( -reach, reach + 1 ):
                for dy in range( -reach, reach + 1 ):
                    j = cell.setdefault( ( p[0] + dx, p[1] + dy ), i )
                    if find( j ) != find( i ):
                        parent[find( j )] = find( i )
    out = {}
    for i, path in enumerate( paths ):
        out.setdefault( find( i ), [] ).append( path )
    return sorted( out.values(), key=lambda c: -sum( len( p ) for p in c ) )


def corridor_stats( tiles, paths, pred, linked, hint=None ):
    """paths: lists of tiles in order (the largest cluster of one name is measured).
    -> coverage (share of its tiles with a matching tile within one), continuity (share of the
    matched line in the one linked piece that holds most of it), breaks (changes of linked piece
    along the line) and the longest gap (tiles in a row with no match within one)."""
    if not paths:
        return None
    groups = clusters( paths )
    paths = groups[0]
    if hint:
        paths = min( groups, key=lambda g: min( ( p[0] - hint[0] ) ** 2 + ( p[1] - hint[1] ) ** 2 for q in g for p in q ) )
    pts = { p for path in paths for p in path }
    hit = sum( 1 for p in pts if near( tiles, p, pred ) )
    corridor = { ( p[0] + dx, p[1] + dy ) for p in pts for dx in ( -1, 0, 1 ) for dy in ( -1, 0, 1 ) }
    cells = { p for p in corridor if pred( tiles.get( p, '' ) ) }
    comp = {}
    for s in cells:
        if s in comp:
            continue
        stack = [ s ]
        comp[s] = s
        while stack:
            c = stack.pop()
            for q in linked( tiles, c ):
                if q in cells and q not in comp:
                    comp[q] = s
                    stack.append( q )
    gap = breaks = 0
    seq_count = {}
    for path in paths:
        run, last = 0, None
        for p in path:
            m = p if p in cells else next( ( q for q in ( ( p[0] + dx, p[1] + dy ) for dx, dy in
                                                          ( ( 0, -1 ), ( 1, 0 ), ( 0, 1 ), ( -1, 0 ), ( 1, 1 ), ( -1, -1 ), ( 1, -1 ), ( -1, 1 ) ) )
                                            if q in cells ), None )
            if m is None:
                run += 1
                gap = max( gap, run )
                continue
            run = 0
            c = comp[m]
            seq_count[c] = seq_count.get( c, 0 ) + 1
            if last is not None and c != last:
                breaks += 1
            last = c
    matched = sum( seq_count.values() )
    return { 'tiles': len( pts ), 'coverage': hit / len( pts ),
             'continuity': max( seq_count.values() ) / matched if matched else 0.0,
             'breaks': breaks, 'longest_gap_tiles': gap }


def road_links( tiles, c ):
    out = []
    for d in conn( tiles[c] ) or '':
        q = ( c[0] + DIRS[d][0], c[1] + DIRS[d][1] )
        if q in tiles and conn( tiles[q] ) is not None:
            out.append( q )
    return out


def water_links( tiles, c ):
    return [ ( c[0] + dx, c[1] + dy ) for dx, dy in DIRS.values() if is_water( tiles.get( ( c[0] + dx, c[1] + dy ), '' ) ) ]


def haversine( a, b ):
    R = 6371008.8
    p1, p2 = math.radians( a[0] ), math.radians( b[0] )
    dp, dl = p2 - p1, math.radians( b[1] - a[1] )
    h = math.sin( dp / 2 ) ** 2 + math.cos( p1 ) * math.cos( p2 ) * math.sin( dl / 2 ) ** 2
    return 2 * R * math.asin( math.sqrt( h ) )


def centre_of( e ):
    if e['type'] == 'node':
        return e['lat'], e['lon']
    if 'bounds' in e:
        b = e['bounds']
        return ( b['minlat'] + b['maxlat'] ) / 2, ( b['minlon'] + b['maxlon'] ) / 2
    g = e.get( 'geometry' )
    if g:
        return sum( p['lat'] for p in g ) / len( g ), sum( p['lon'] for p in g ) / len( g )
    return None


def audit( folder ):
    tiles = load_map( folder )
    roads = load_osm( 'roads' )
    land = load_osm( 'land' )
    places = load_osm( 'places' )
    rep = {}

    # ---- scale and orientation
    pairs = [ ( 'Bến Thành - Suối Tiên', ( 10.77252, 106.69802 ), ( 10.863885, 106.802173 ) ),
              ( 'Bến Thành - Đầm Sen', ( 10.77252, 106.69802 ), ( 10.7659, 106.63864 ) ),
              ( 'Bến Thành - Tân Sơn Nhất terminal', ( 10.77252, 106.69802 ), ( 10.8146, 106.6585 ) ),
              ( 'area NW - SE corner', ( C.ORIGIN_LAT, C.ORIGIN_LON ),
                ( C.ORIGIN_LAT - H * C.TILE_M / C.M_PER_DEG_LAT, C.ORIGIN_LON + W * C.TILE_M / C.M_PER_DEG_LON ) ) ]
    scale = []
    for name, a, b in pairs:
        ta, tb = C.latlon_to_tile( *a ), C.latlon_to_tile( *b )
        game = C.TILE_M * math.hypot( tb[0] - ta[0], tb[1] - ta[1] )
        real = haversine( a, b )
        scale.append( { 'pair': name, 'real_m': round( real ), 'map_m': round( game ), 'error_pct': round( 100 * ( game - real ) / real, 2 ) } )
    se = ( C.ORIGIN_LAT - H * C.TILE_M / C.M_PER_DEG_LAT, C.ORIGIN_LON + W * C.TILE_M / C.M_PER_DEG_LON )
    rep['scale'] = { 'tile_m': C.TILE_M, 'area_km': [ W * C.TILE_M / 1000, H * C.TILE_M / 1000 ],
                     'box': { 'N': C.ORIGIN_LAT, 'W': C.ORIGIN_LON, 'S': round( se[0], 4 ), 'E': round( se[1], 4 ) },
                     'north_up': True, 'pairs': scale }

    # ---- key roads
    by_name = {}
    for e in roads:
        n = bare( e['tags'].get( 'name', '' ) )
        if n:
            by_name.setdefault( n, [] ).append( e )
    rr = {}
    for key in KEY_ROADS:
        name, hint = ( key, None ) if isinstance( key, str ) else ( key[0], C.latlon_to_tile( key[1], key[2] ) )
        ways = by_name.get( bare( name ), [] )
        paths = [ walk( e['geometry'] ) for e in ways if e['tags'].get( 'tunnel' ) not in ( 'yes', ) ]
        st = corridor_stats( tiles, [ p for p in paths if p ], is_road, road_links, hint )
        rr[name] = st or { 'missing_in_osm': True }
    rep['roads'] = rr

    # ---- water
    wr = {}
    for label, keys in KEY_WATER:
        paths = []
        for e in land:
            t = e.get( 'tags', {} )
            if not any( k in low( t.get( 'name' ) ) for k in keys ):
                continue
            if t.get( 'waterway' ) in ( 'river', 'canal', 'stream' ) and e.get( 'geometry' ):
                paths.append( walk( e['geometry'] ) )
        st = corridor_stats( tiles, [ p for p in paths if p ], is_water, water_links )
        wr[label] = st or { 'no_centre_line_in_osm': True }
    rep['water'] = wr

    # ---- bridges
    br = {}
    for e in roads:
        t = e['tags']
        if t.get( 'bridge' ) in ( None, 'no' ):
            continue
        n = nfc( t.get( 'bridge:name' ) or t.get( 'name' ) )
        if n not in KEY_BRIDGES:
            continue
        br.setdefault( n, [] ).extend( walk( e['geometry'] ) )
    bres = {}
    # tiles of the bridges that stood in 2009: a later bridge built right beside one (Sài Gòn 2)
    # is only counted where it strays more than a tile from them
    old = { ( p[0] + dx, p[1] + dy ) for n, ( year, _ ) in KEY_BRIDGES.items() if year != 'after'
            for p in br.get( n, [] ) for dx in ( -1, 0, 1 ) for dy in ( -1, 0, 1 ) }
    for n, ( year, note ) in KEY_BRIDGES.items():
        pts = br.get( n, [] )
        if year == 'after':
            pts = [ p for p in pts if p not in old ]
        if not pts:
            bres[n] = { 'opened': year, 'in_osm': False }
            continue
        on_map = sum( 1 for p in set( pts ) if near( tiles, p, lambda t: t.startswith( 'bridge_' ), 1 ) )
        road = sum( 1 for p in set( pts ) if near( tiles, p, is_road, 1 ) )
        bres[n] = { 'opened': year, 'note': note, 'in_osm': True, 'tiles': len( set( pts ) ),
                    'bridge_tiles_near': on_map, 'road_near_share': round( road / len( set( pts ) ), 2 ),
                    'on_map': on_map > 0 or ( year != 'after' and road / len( set( pts ) ) > 0.6 ) }
    rep['bridges'] = bres

    # ---- landmarks
    data = json.load( open( os.path.join( HERE, 'landmarks_2009.json' ) ) )['landmarks']
    lm = {}
    named = []
    for e in land + places:
        n = low( e.get( 'tags', {} ).get( 'name' ) )
        if n:
            named.append( ( n, e ) )
    for d in data:
        lid = d['id']
        mine = [ p for p, t in tiles.items() if t.startswith( lid + '_' ) ]
        ax, ay = C.latlon_to_tile( d['lat'], d['lon'] )
        out = { 'anchor_source': d.get( 'source', '' ) }
        if mine:
            cx = sum( p[0] + 0.5 for p in mine ) / len( mine )
            cy = sum( p[1] + 0.5 for p in mine ) / len( mine )
            out['placed_vs_anchor_m'] = round( C.TILE_M * math.hypot( cx - ax, cy - ay ) )
            keys = LANDMARK_OSM.get( lid )
            if keys:
                cands = [ centre_of( e ) for n, e in named if any( k in n for k in keys ) ]
                cands = [ c for c in cands if c ]
                if cands:
                    best = min( cands, key=lambda c: haversine( c, ( d['lat'], d['lon'] ) ) )
                    ox, oy = C.latlon_to_tile( *best )
                    out['osm_vs_anchor_m'] = round( haversine( best, ( d['lat'], d['lon'] ) ) )
                    out['placed_vs_osm_m'] = round( C.TILE_M * math.hypot( cx - ox, cy - oy ) )
        else:
            out['placed'] = False
        lm[lid] = out
    rep['landmarks'] = lm
    kp = {}
    for label, key, prefix in KEY_PLACES:
        cands = [ centre_of( e ) for n, e in named if key in n ]
        cands = [ c for c in cands if c ]
        if not cands:
            kp[label] = { 'in_osm': False }
            continue
        x, y = C.latlon_to_tile( *cands[0] )
        best = None
        for ( tx, ty ), t in tiles.items():
            if abs( tx - x ) < 12 and abs( ty - y ) < 12 and t.startswith( prefix ) and not t.startswith( 'sgn_lm_' ):
                d = C.TILE_M * math.hypot( tx + 0.5 - x, ty + 0.5 - y )
                if best is None or d < best:
                    best = d
        kp[label] = { 'nearest_building_m': round( best ) if best is not None else None }
    rep['places'] = kp

    # ---- districts: land use mix by nearest centre
    dists = json.load( open( os.path.join( HERE, 'districts_2009.json' ) ) )['districts']
    cen = [ ( d['name'], C.latlon_to_tile( d['lat'], d['lon'] ) ) for d in dists ]
    kinds = [ ( 'road', lambda t: t.startswith( 'road_' ) or t.startswith( 'bridge_' ) ),
              ( 'nha_ong', lambda t: t.startswith( 'sgn_nh_' ) ),
              ( 'hem', lambda t: t.startswith( 'sgn_hem' ) ),
              ( 'water', lambda t: t.startswith( 'lake' ) or t.startswith( 'sgn_ben_pha' ) ),
              ( 'park', lambda t: t.startswith( 'sgn_pl_cong_vien' ) ),
              ( 'industrial', lambda t: t.startswith( 'sgn_pl_kho' ) ),
              ( 'field', lambda t: t == 'field' ),
              ( 'marsh', lambda t: t.startswith( 'forest_water' ) ),
              ( 'places', lambda t: t.startswith( 'sgn_' ) ) ]
    mix = {}
    for p, t in tiles.items():
        name = min( cen, key=lambda c: ( c[1][0] - p[0] ) ** 2 + ( c[1][1] - p[1] ) ** 2 )[0]
        # only count tiles within 3 km of the centre, so the area's edge does not fall to the nearest one
        c = dict( cen )[name]
        if math.hypot( c[0] - p[0], c[1] - p[1] ) * C.TILE_M > 3000:
            continue
        k = next( ( k for k, f in kinds if f( t ) ), 'other' )
        m = mix.setdefault( name, {} )
        m[k] = m.get( k, 0 ) + 1
    rep['districts'] = { n: { k: round( 100 * v / sum( m.values() ), 1 ) for k, v in sorted( m.items() ) } | { 'tiles': sum( m.values() ) }
                         for n, m in mix.items() }

    # ---- anachronisms: post-2009 roads still drawn
    ana = {}
    for frag in POST_2009_ROADS:
        ways = [ e for e in roads if frag.lower() in low( e['tags'].get( 'name' ) ) ]
        pts = { p for e in ways for p in walk( e['geometry'] ) }
        if not pts:
            continue
        ana[frag] = { 'osm_tiles': len( pts ), 'road_on_map_share': round( sum( 1 for p in pts if is_road( tiles.get( p, '' ) ) ) / len( pts ), 2 ) }
    rep['post_2009_roads'] = ana
    after = [ n for n, ( y, _ ) in KEY_BRIDGES.items() if y == 'after' and bres[n].get( 'bridge_tiles_near' ) ]
    rep['post_2009_bridges_on_map'] = after

    # ---- totals
    tot = {}
    for t in tiles.values():
        k = next( ( k for k, f in kinds if f( t ) ), 'other' )
        tot[k] = tot.get( k, 0 ) + 1
    rep['totals'] = { k: round( 100 * v / len( tiles ), 1 ) for k, v in sorted( tot.items() ) }
    return rep


def summary( rep ):
    out = []
    s = rep['scale']
    out.append( 'scale: %g m per tile, area %.1f x %.1f km, north up; projection error %s' % (
        s['tile_m'], s['area_km'][0], s['area_km'][1], ', '.join( '%s %+.2f%%' % ( p['pair'], p['error_pct'] ) for p in s['pairs'] ) ) )
    rs = [ v for v in rep['roads'].values() if 'coverage' in v ]
    out.append( 'roads: %d key streets, mean coverage %.1f %%, mean continuity %.1f %%, %d breaks in all, %d fully continuous, '
                '%d with a gap > 3 tiles' % (
                    len( rs ), 100 * sum( v['coverage'] for v in rs ) / len( rs ), 100 * sum( v['continuity'] for v in rs ) / len( rs ),
                    sum( v['breaks'] for v in rs ), sum( v['breaks'] == 0 for v in rs ), sum( v['longest_gap_tiles'] > 3 for v in rs ) ) )
    ws = [ v for v in rep['water'].values() if 'coverage' in v ]
    out.append( 'water: %d waterways, mean coverage %.1f %%, mean continuity %.1f %%, %d breaks in all' % (
        len( ws ), 100 * sum( v['coverage'] for v in ws ) / len( ws ), 100 * sum( v['continuity'] for v in ws ) / len( ws ),
        sum( v['breaks'] for v in ws ) ) )
    for n, v in rep['roads'].items():
        if 'coverage' in v:
            out.append( '  %-22s %4d tiles  coverage %5.1f %%  continuity %5.1f %%  breaks %2d  gap %d' % (
                n, v['tiles'], 100 * v['coverage'], 100 * v['continuity'], v['breaks'], v['longest_gap_tiles'] ) )
        else:
            out.append( '  %-22s not in the OSM extract' % n )
    out.append( 'water:' )
    for n, v in rep['water'].items():
        if 'coverage' in v:
            out.append( '  %-22s %4d tiles  coverage %5.1f %%  continuity %5.1f %%  breaks %2d  gap %d' % (
                n, v['tiles'], 100 * v['coverage'], 100 * v['continuity'], v['breaks'], v['longest_gap_tiles'] ) )
        else:
            out.append( '  %-22s no centre line in the extract' % n )
    out.append( 'bridges:' )
    for n, v in rep['bridges'].items():
        out.append( '  %-20s opened %-5s %s' % ( n, v['opened'], ( 'on map (%d bridge tiles, road %.0f %%)' % (
            v['bridge_tiles_near'], 100 * v['road_near_share'] ) if v.get( 'on_map' ) else 'NOT on map' ) if v['in_osm'] else 'not in OSM' ) )
    out.append( 'landmarks (placed vs anchor / OSM vs anchor / placed vs OSM, m):' )
    for n, v in rep['landmarks'].items():
        out.append( '  %-22s %5s %5s %5s  %s' % ( n, v.get( 'placed_vs_anchor_m', '-' ), v.get( 'osm_vs_anchor_m', '-' ),
                                                 v.get( 'placed_vs_osm_m', '-' ), v['anchor_source'][:40] ) )
    out.append( 'places: ' + ', '.join( '%s %s m' % ( n, v.get( 'nearest_building_m' ) ) for n, v in rep['places'].items() ) )
    out.append( 'districts (%% of tiles within 3 km of the centre):' )
    for n, m in sorted( rep['districts'].items() ):
        out.append( '  %-12s ' % n + ' '.join( '%s %.1f' % ( k, v ) for k, v in m.items() if k != 'tiles' ) )
    out.append( 'post-2009 roads still drawn: ' + ', '.join( '%s %.0f %%' % ( k, 100 * v['road_on_map_share'] )
                                                           for k, v in rep['post_2009_roads'].items() ) )
    out.append( 'post-2009 bridges on the map: %s' % ( ', '.join( rep['post_2009_bridges_on_map'] ) or 'none' ) )
    out.append( 'totals: ' + ', '.join( '%s %.1f %%' % kv for kv in rep['totals'].items() ) )
    return '\n'.join( out )


def main():
    args = [ a for a in sys.argv[1:] ]
    js = None
    if '--json' in args:
        i = args.index( '--json' )
        js = args[i + 1]
        del args[i:i + 2]
    folder = args[0] if args else os.path.join( ROOT, 'data/mods/saigon_2000s/realmap_2009' )
    rep = audit( folder )
    print( summary( rep ) )
    if js:
        json.dump( rep, open( js, 'w' ), ensure_ascii=False, indent=1 )


if __name__ == '__main__':
    main()
