#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <map>
#include <string>
#include <vector>

#include "calendar.h"
#include "cata_catch.h"
#include "coordinates.h"
#include "enums.h"
#include "global_vars.h"
#include "item.h"
#include "itype.h"
#include "map.h"
#include "map_helpers.h"
#include "mapdata.h"
#include "math_parser_diag_value.h"
#include "omdata.h"
#include "overmap.h"
#include "overmapbuffer.h"
#include "player_helpers.h"
#include "point.h"
#include "rng.h"
#include "type_id.h"
#include "units.h"
#include "units_utility.h"
#include "veh_type.h"
#include "vehicle.h"
#include "vpart_position.h"

// Saigon 2000s mod: dump a generated Saigon block for the offline scene renderer
// (tools/saigon/art/render_scene.py), so the tileset can be checked without driving
// the game window.  Hidden test; run with:
//   SAIGON_SCENE_OUT=scene.json tests/cata_test --mods=dda,saigon_2000s "[saigon_scene]"

static std::string quoted( const std::string &s )
{
    std::string out = "\"";
    for( const char c : s ) {
        if( c == '"' || c == '\\' ) {
            out += '\\';
        }
        out += c;
    }
    return out + "\"";
}

template<typename T>
static int connections( map &here, const tripoint_bub_ms &p, const T &obj_at,
                        const std::bitset<NUM_TERCONN> &group )
{
    if( group.none() ) {
        return 0;
    }
    int val = 0;
    // same order as map::get_known_connections: S, E, W, N -> bits 1, 2, 4, 8
    for( int i = 0; i < 4; i++ ) {
        const tripoint_bub_ms q( p.x() + offsets[i].x, p.y() + offsets[i].y, p.z() );
        if( here.inbounds( q ) && obj_at( q ).in_connect_groups( group ) ) {
            val += 1 << i;
        }
    }
    return val;
}

template<typename T>
static int rotation_targets( map &here, const tripoint_bub_ms &p, const T &obj_at,
                             const std::bitset<NUM_TERCONN> &group )
{
    // CHAR_MAX means "no rotation group" (map::get_known_rotates_to)
    return group.none() ? 127 : connections( here, p, obj_at, group );
}

// Write the z0 tiles of the loaded map, (0,0)-(width,height), as the renderer's JSON.
static void dump_scene( const char *out_path, const int width, const int height )
{
    map &here = get_map();
    std::map<std::string, std::string> looks_like;
    std::ofstream out( out_path );
    out << "{\"width\": " << width << ", \"height\": " << height << ", \"tiles\": [\n";
    for( int y = 0; y < height; y++ ) {
        for( int x = 0; x < width; x++ ) {
            const tripoint_bub_ms p( x, y, 0 );
            const ter_t &ter = here.ter( p ).obj();
            const furn_t &furn = here.furn( p ).obj();
            const auto ter_at = [&]( const tripoint_bub_ms & q ) -> const ter_t & {
                return here.ter( q ).obj();
            };
            const auto furn_at = [&]( const tripoint_bub_ms & q ) -> const furn_t & {
                return here.furn( q ).obj();
            };
            looks_like[ter.id.str()] = ter.looks_like;
            out << "[" << quoted( ter.id.str() ) << "," << connections( here, p, ter_at, ter.connect_to_groups )
                << "," << rotation_targets( here, p, ter_at, ter.rotate_to_groups ) << ",";
            if( furn.id.str() == "f_null" ) {
                out << "\"\",0,127,";
            } else {
                looks_like[furn.id.str()] = furn.looks_like;
                out << quoted( furn.id.str() ) << "," << connections( here, p, furn_at, furn.connect_to_groups )
                    << "," << rotation_targets( here, p, furn_at, furn.rotate_to_groups ) << ",";
            }
            const map_stack items = here.i_at( p );
            if( items.empty() ) {
                out << "\"\",";
            } else {
                const itype &it = *items.begin()->type;
                looks_like[it.get_id().str()] = it.looks_like.str();
                out << quoted( it.get_id().str() ) << ",";
            }
            const optional_vpart_position ovp = here.veh_at( p );
            const vpart_display vd = ovp ? ovp->vehicle().get_display_of_tile( ovp->mount_pos() ) :
                                     vpart_display();
            if( ovp && !vd.id.is_null() ) {
                looks_like["vp_" + vd.id.str()] = vd.id->looks_like;
                out << quoted( "vp_" + vd.id.str() ) << "," << quoted( vd.variant.id ) << ","
                    << angle_to_dir4( ovp->vehicle().face.dir() - 270_degrees ) << "]";
            } else {
                out << "\"\",\"\",0]";
            }
            out << ( x + 1 < width || y + 1 < height ? ",\n" : "\n" );
        }
    }
    out << "], \"looks_like\": {";
    bool first = true;
    for( const auto &kv : looks_like ) {
        out << ( first ? "" : ",\n" ) << quoted( kv.first ) << ": " << quoted( kv.second );
        first = false;
    }
    out << "}}\n";
    CHECK( out.good() );
}

TEST_CASE( "saigon_scene_dump", "[.][saigon_scene]" )
{
    const char *out_path = std::getenv( "SAIGON_SCENE_OUT" );
    if( out_path == nullptr || !oter_str_id( "sgn_chua_north" ).is_valid() ) {
        WARN( "set SAIGON_SCENE_OUT and load saigon_2000s" );
        return;
    }
    clear_overmaps();
    clear_avatar();
    // street on top, buildings fronting it, a chợ, a canal and the landmarks below
    const tripoint_abs_omt base( 200, 200, 0 );
    const std::vector<std::vector<std::string>> layout = {
        { "road_ew", "road_ew", "road_ew", "road_ew", "road_ew" },
        { "sgn_nh_solo", "sgn_nh_solo", "sgn_hem_block", "sgn_chungcu", "sgn_chua" },
        { "sgn_cho_nw", "sgn_cho_ne", "sgn_kenh", "sgn_kenh", "sgn_kenh" },
        { "sgn_cho_sw", "sgn_cho_se", "sgn_nha_tho", "sgn_ubnd", "sgn_truong" },
    };
    for( size_t y = 0; y < layout.size(); y++ ) {
        for( size_t x = 0; x < layout[y].size(); x++ ) {
            const std::string &id = layout[y][x];
            const tripoint_abs_omt pos = base + tripoint( static_cast<int>( x ), static_cast<int>( y ), 0 );
            const bool rotatable = id.rfind( "sgn_", 0 ) == 0;
            if( id == "sgn_nh_solo" || id == "sgn_chungcu" ) {
                for( int z = 0; z <= 5; z++ ) {
                    overmap_buffer.ter_set( pos + tripoint( 0, 0, z ),
                                            oter_str_id( id + "_z" + std::to_string( z ) + "_north" ).id() );
                }
            } else {
                overmap_buffer.ter_set( pos, oter_str_id( rotatable ? id + "_north" : id ).id() );
                const std::string roof = id.rfind( "sgn_cho_", 0 ) == 0 ? "sgn_cho_roof_" + id.substr( 8 ) :
                                         id == "sgn_hem_block" ? "sgn_hem_block_roof" : id == "sgn_chua" ? "sgn_chua_roof" :
                                         id == "sgn_kenh" ? "sgn_kenh_roof" : id == "sgn_nha_tho" || id == "sgn_ubnd" ||
                                         id == "sgn_truong" ? id + "_roof" : "";
                if( !roof.empty() ) {
                    overmap_buffer.ter_set( pos + tripoint::above, oter_str_id( roof + "_north" ).id() );
                }
            }
        }
    }
    rng_set_engine_seed( 2004 );
    map &here = get_map();
    here.load( project_to<coords::sm>( base ), true );
    // a showroom row of every Saigon vehicle on the near lane, facing east
    int x = 4;
    for( const std::string vid : {
             "sgn_veh_underbone", "sgn_veh_xe_tay_ga", "sgn_veh_ba_gac_may", "sgn_veh_xich_lo",
             "sgn_veh_xe_dap", "sgn_veh_xuong", "sgn_veh_ghe"
         } ) {
        here.add_vehicle( vproto_id( vid ), tripoint_bub_ms( x, 17, 0 ), 0_degrees, 0,
                          veh_spawn_status::UNDAMAGED, false, true );
        x += 9;
    }
    here.build_map_cache( 0 );

    dump_scene( out_path, 5 * 24, 4 * 24 );
}

// One landmark on its own: SAIGON_LANDMARK=<id> SAIGON_LANDMARK_SIZE=<w>x<h>x<zmin>x<zmax>
TEST_CASE( "saigon_landmark_dump", "[.][saigon_landmark_scene]" )
{
    const char *out_path = std::getenv( "SAIGON_SCENE_OUT" );
    const char *lid = std::getenv( "SAIGON_LANDMARK" );
    const char *size = std::getenv( "SAIGON_LANDMARK_SIZE" );
    if( out_path == nullptr || lid == nullptr || size == nullptr ) {
        WARN( "set SAIGON_SCENE_OUT, SAIGON_LANDMARK and SAIGON_LANDMARK_SIZE" );
        return;
    }
    int w = 0;
    int h = 0;
    int zmin = 0;
    int zmax = 0;
    REQUIRE( std::sscanf( size, "%dx%dx%dx%d", &w, &h, &zmin, &zmax ) == 4 );
    clear_overmaps();
    clear_avatar();
    const tripoint_abs_omt base( 200, 200, 0 );
    for( int z = zmin; z <= zmax; z++ ) {
        for( int x = 0; x < w; x++ ) {
            for( int y = 0; y < h; y++ ) {
                std::string id = std::string( lid ) + "_" + std::to_string( x ) + std::to_string( y );
                if( z < 0 ) {
                    id += "_b";
                } else if( z > 0 ) {
                    id += "_z" + std::to_string( z );
                }
                overmap_buffer.ter_set( base + tripoint( x, y, z ), oter_str_id( id + "_north" ).id() );
            }
        }
    }
    rng_set_engine_seed( 2004 );
    get_map().load( project_to<coords::sm>( base ), true );
    get_map().build_map_cache( 0 );
    dump_scene( out_path, w * 24, h * 24 );
}

// One whole generated overmap for tools/saigon/art/render_overmap.py: per OMT the tileset id
// (the oter type, as cata_tiles::get_omt_id_rotation_and_subtile asks for it), plus either
// its rotation or, for connected and water terrain, the S/E/W/N connection bits that the
// renderer turns into a subtile.  Hidden test; run with:
//   SAIGON_OVERMAP_OUT=om.json [SAIGON_OVERMAP_SEED=4242] [SAIGON_OVERMAP_AT=x,y]
//       [SAIGON_OVERMAP_SPAN=w,h] [SAIGON_OVERMAP_MAP=saigon_2000s/realmap_2009]
//       tests/cata_test --mods=dda,saigon_2000s "[saigon_overmap]"
// Lakes and rivers come from noise keyed on the overmap's position, so SAIGON_OVERMAP_AT
// (overmap coordinates) is what gives a different landscape; the seed varies the cities.
// SPAN dumps w x h overmaps from AT as one picture; MAP picks a pregenerated map (as the
// scenario would) instead of the generated Vietmap.
TEST_CASE( "saigon_overmap_dump", "[.][saigon_overmap]" )
{
    const char *out_path = std::getenv( "SAIGON_OVERMAP_OUT" );
    if( out_path == nullptr ) {
        WARN( "set SAIGON_OVERMAP_OUT" );
        return;
    }
    const char *seed = std::getenv( "SAIGON_OVERMAP_SEED" );
    rng_set_engine_seed( seed ? std::atoi( seed ) : 4242 );
    const char *at = std::getenv( "SAIGON_OVERMAP_AT" );
    point_abs_om where;
    if( at != nullptr ) {
        int ox = 0;
        int oy = 0;
        REQUIRE( std::sscanf( at, "%d,%d", &ox, &oy ) == 2 );
        where = point_abs_om( ox, oy );
    }
    int span_x = 1;
    int span_y = 1;
    if( const char *span = std::getenv( "SAIGON_OVERMAP_SPAN" ) ) {
        REQUIRE( std::sscanf( span, "%d,%d", &span_x, &span_y ) == 2 );
    }
    const char *map = std::getenv( "SAIGON_OVERMAP_MAP" );
    if( map != nullptr ) {
        get_globals().set_global_value( "overmap_pregenerated_path", diag_value( std::string( map ) ) );
    }
    overmap_buffer.clear();
    const auto t0 = std::chrono::steady_clock::now();
    for( int oy = 0; oy < span_y; oy++ ) {
        for( int ox = 0; ox < span_x; ox++ ) {
            overmap_buffer.get( where + point( ox, oy ) );
        }
    }
    const auto ms = std::chrono::duration_cast<std::chrono::milliseconds>( std::chrono::steady_clock::now() - t0 );
    WARN( span_x * span_y << " overmap(s) generated in " << ms.count() << " ms" );
    const tripoint_abs_omt corner( project_to<coords::omt>( where ), 0 );
    const int W = OMAPX * span_x;
    const int H = OMAPY * span_y;
    std::map<std::string, std::vector<std::string>> looks_like;
    std::ofstream out( out_path );
    out << "{\"width\":" << W << ",\"height\":" << H << ",\"tiles\":[";
    for( int y = 0; y < H; y++ ) {
        for( int x = 0; x < W; x++ ) {
            const tripoint_abs_omt here = corner + point( x, y );
            const oter_t &ot = *overmap_buffer.ter( here );
            const oter_type_t &type = ot.get_type_id().obj();
            const std::string id = ot.get_type_id().str();
            looks_like.emplace( id, type.looks_like );
            int rot = 0;
            int conn = -1;
            if( type.has_connections() || type.has_flag( oter_flags::water ) ) {
                conn = 0;
                // same order as get_omt_id_rotation_and_subtile: S, E, W, N -> bits 1, 2, 4, 8
                for( int i = 0; i < 4; i++ ) {
                    const point q( x + offsets[i].x, y + offsets[i].y );
                    if( q.x < 0 || q.y < 0 || q.x >= W || q.y >= H ) {
                        continue;
                    }
                    const oter_type_t &other = overmap_buffer.ter( corner + q )->get_type_id().obj();
                    if( type.has_connections() ? type.connects_to( other.id.id() ) : other.has_flag( oter_flags::water ) ) {
                        conn += 1 << i;
                    }
                }
            } else {
                int subtile = 0;
                ot.get_rotation_and_subtile( rot, subtile );
            }
            out << ( x || y ? "," : "" ) << "[" << quoted( id ) << "," << rot << "," << conn << "]";
        }
    }
    out << "],\"looks_like\":{";
    bool first = true;
    for( const auto &ll : looks_like ) {
        out << ( first ? "" : "," ) << quoted( ll.first ) << ":[";
        for( size_t i = 0; i < ll.second.size(); i++ ) {
            out << ( i ? "," : "" ) << quoted( ll.second[i] );
        }
        out << "]";
        first = false;
    }
    out << "}}\n";
    CHECK( out.good() );
    if( map != nullptr ) {
        get_globals().remove_global_value( "overmap_pregenerated_path" );
    }
}
