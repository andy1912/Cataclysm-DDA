#include <map>
#include <queue>
#include <set>
#include <string>
#include <vector>

#include "calendar.h"
#include "cata_catch.h"
#include "coordinates.h"
#include "map.h"
#include "map_helpers.h"
#include "mapbuffer.h"
#include "mapdata.h"
#include "omdata.h"
#include "overmapbuffer.h"
#include "player_helpers.h"
#include "point.h"
#include "rng.h"
#include "string_formatter.h"
#include "submap.h"
#include "type_id.h"

// Saigon 2000s mod: the real District 1 landmarks (tools/saigon/gen_saigon_landmarks.py,
// doc/saigon/LANDMARKS.md phases L1-L4).  Each one is generated on the real map at every
// z-level, then checked: every door is reachable from the street, every indoor tile is
// roofed, and every up staircase meets a down staircase directly above it.
// Run with: tests/cata_test --mods=dda,saigon_2000s "[saigon]"

namespace
{
struct landmark {
    std::string id;
    int w;
    int h;
    int zmin;
    int zmax;
    bool open_air = false;      // a park: no doors or rooms to check
};
} // namespace

static std::string piece( const landmark &l, int x, int y, int z )
{
    std::string s = l.id + "_" + std::to_string( x ) + std::to_string( y );
    if( z < 0 ) {
        s += "_b";
    } else if( z > 0 ) {
        s += "_z" + std::to_string( z );
    }
    return s + "_north";
}

TEST_CASE( "saigon_district1_landmarks", "[mapgen][saigon]" )
{
    if( !oter_str_id( "sgn_lm_ben_thanh_00_north" ).is_valid() ) {
        WARN( "saigon_2000s is not loaded; skipping" );
        return;
    }
    const std::vector<landmark> landmarks = {
        { "sgn_lm_ben_thanh", 3, 3, 0, 3 }, { "sgn_lm_duc_ba", 2, 3, 0, 4 }, { "sgn_lm_buu_dien", 3, 2, 0, 1 },
        { "sgn_lm_nha_hat", 2, 2, 0, 1 }, { "sgn_lm_ubnd_tp", 3, 2, 0, 3 }, { "sgn_lm_dinh_doc_lap", 3, 3, -1, 3 },
        { "sgn_lm_thien_hau", 2, 2, 0, 1 }, { "sgn_lm_ngoc_hoang", 2, 2, 0, 1 }, { "sgn_lm_binh_tay", 3, 3, 0, 3 },
        { "sgn_lm_ga_sai_gon", 3, 3, 0, 1 }, { "sgn_lm_ben_xe_md", 3, 3, 0, 1 }, { "sgn_lm_tao_dan", 3, 3, 0, 1 },
        { "sgn_lm_ho_con_rua", 1, 1, 0, 1 }, { "sgn_lm_stc", 1, 1, 0, 10 }, { "sgn_lm_diamond", 2, 2, 0, 3 },
        { "sgn_lm_bui_vien", 3, 1, 0, 3 },
        { "sgn_lm_thao_cam_vien", 4, 4, 0, 1 }, { "sgn_lm_dam_sen", 4, 4, 0, 1 }, { "sgn_lm_suoi_tien", 4, 4, 0, 1 },
        // R12: Tân Sơn Nhất's terminal (real map only)
        { "sgn_lm_san_bay", 3, 2, 0, 1 },
        // L-loc3: Nhà thờ Tân Định, Chợ Tân Định, Bến Nhà Rồng, Khách sạn Rex
        { "sgn_lm_tan_dinh", 2, 2, 0, 4 }, { "sgn_lm_cho_tan_dinh", 2, 2, 0, 1 },
        { "sgn_lm_nha_rong", 2, 2, 0, 2 }, { "sgn_lm_rex", 2, 2, 0, 5 },
        // L-loc6: Chùa Vĩnh Nghiêm, Lăng Ông, Sân vận động Thống Nhất, Chợ An Đông
        { "sgn_lm_vinh_nghiem", 3, 3, 0, 7 }, { "sgn_lm_lang_ong", 2, 3, 0, 1 },
        { "sgn_lm_thong_nhat", 4, 4, 0, 1 }, { "sgn_lm_an_dong", 2, 2, 0, 4 },
        // P2 everyday places (tools/saigon/gen_places.py), same piece naming
        { "sgn_pl_cay_xang", 1, 1, 0, 1 }, { "sgn_pl_coopmart", 2, 2, 0, 1 }, { "sgn_pl_benh_vien", 2, 2, 0, 2 },
        { "sgn_pl_cong_an", 1, 1, 0, 1 }, { "sgn_pl_nghia_trang", 2, 2, 0, 1 }, { "sgn_pl_nha_sach", 1, 1, 0, 1 },
        { "sgn_pl_xe_may", 1, 1, 0, 1 },
        // L-loc1 parks, warehouse and container yard
        { "sgn_pl_cong_vien", 1, 1, 0, 1, true }, { "sgn_pl_cong_vien_ho", 1, 1, 0, 1, true },
        { "sgn_pl_cong_vien_the_duc", 1, 1, 0, 1, true }, { "sgn_pl_kho", 1, 1, 0, 1 }, { "sgn_pl_kho_cang", 1, 1, 0, 1 },
        // V2 the city's corners (tools/saigon/gen_vn_places.py)
        { "sgn_vp_cafe_vong", 1, 1, 0, 1 }, { "sgn_vp_bia_hoi", 1, 1, 0, 1 }, { "sgn_vp_hot_toc", 1, 1, 0, 1 },
        { "sgn_vp_nha_tro", 1, 1, 0, 2 }, { "sgn_vp_dinh", 1, 1, 0, 1 }, { "sgn_vp_nha_tho_ho", 1, 1, 0, 1 },
        { "sgn_vp_dien_thoai", 1, 1, 0, 1 }, { "sgn_vp_cho_tam", 1, 1, 0, 1, true }, { "sgn_vp_lo_da", 1, 1, 0, 1 },
        { "sgn_vp_giu_xe", 1, 1, 0, 1 }, { "sgn_vp_tram_xe_buyt", 1, 1, 0, 1 },
    };
    const ter_str_id open_air( "t_open_air" );
    const ter_str_id up( "t_stairs_up" );
    const ter_str_id down( "t_stairs_down" );
    // One overmap for all landmarks: generating a Saigon overmap is slow in megacity mode,
    // so each landmark gets its own spot on the same overmap instead of a fresh one.
    clear_overmaps();
    int slot = 0;
    for( const landmark &l : landmarks ) {
        CAPTURE( l.id );
        clear_avatar();
        clear_map();
        const tripoint_abs_omt base( 10 + 8 * ( slot % 20 ), 20 + 8 * ( slot / 20 ), 0 );
        slot++;
        for( int z = l.zmin; z <= l.zmax; z++ ) {
            for( int x = 0; x < l.w; x++ ) {
                for( int y = 0; y < l.h; y++ ) {
                    overmap_buffer.ter_set( base + tripoint( x, y, z ), oter_str_id( piece( l, x, y, z ) ).id() );
                }
            }
        }
        rng_set_engine_seed( 3 );
        map &here = get_map();
        here.load( project_to<coords::sm>( base ), false );
        const int W = l.w * 24;
        const int H = l.h * 24;
        // BFS on z0 from the street edge; closed doors count as passable
        std::set<point> seen;
        std::queue<point> todo;
        for( int x = 0; x < W; x++ ) {
            if( here.passable( tripoint_bub_ms( x, 0, 0 ) ) ) {
                todo.emplace( x, 0 );
                seen.emplace( x, 0 );
            }
        }
        while( !todo.empty() ) {
            const point p = todo.front();
            todo.pop();
            for( const point &d : four_adjacent_offsets ) {
                const point q = p + d;
                if( q.x < 0 || q.y < 0 || q.x >= W || q.y >= H || seen.count( q ) ) {
                    continue;
                }
                const tripoint_bub_ms tq( q.x, q.y, 0 );
                if( here.move_cost( tq ) <= 0 && !here.ter( tq ).obj().has_flag( ter_furn_flag::TFLAG_DOOR ) ) {
                    continue;
                }
                seen.insert( q );
                todo.push( q );
            }
        }
        int doors = 0;
        int doors_reached = 0;
        int indoor = 0;
        int roofed = 0;
        std::string first_unroofed;
        for( int x = 0; x < W; x++ ) {
            for( int y = 0; y < H; y++ ) {
                const tripoint_bub_ms p( x, y, 0 );
                if( here.ter( p ).obj().has_flag( ter_furn_flag::TFLAG_DOOR ) ) {
                    doors++;
                    doors_reached += seen.count( point( x, y ) );
                }
                for( int z = l.zmin; z < l.zmax; z++ ) {
                    const tripoint_bub_ms pz( x, y, z );
                    if( here.ter( pz ).obj().has_flag( ter_furn_flag::TFLAG_INDOORS ) ) {
                        indoor++;
                        const bool has_roof = here.ter( pz + tripoint::above ) != open_air.id();
                        roofed += has_roof;
                        if( !has_roof && first_unroofed.empty() ) {
                            first_unroofed = string_format( "%d,%d,%d %s", x, y, z, here.ter( pz ).id().str() );
                        }
                    }
                    if( here.ter( pz ) == up.id() ) {
                        CAPTURE( x, y, z );
                        CHECK( here.ter( pz + tripoint::above ) == down.id() );
                    }
                }
            }
        }
        CHECK( doors_reached == doors );
        CAPTURE( indoor, roofed, first_unroofed );
        CHECK( roofed == indoor );
        if( !l.open_air ) {
            CHECK( doors > 0 );
            CHECK( indoor > 0 );
        }
    }
}

// L4: the zoo's and Suối Tiên's animals really spawn.  Every map tile of the park is
// generated with its submaps saved, over a few seeds, and the mapgen spawn points are
// counted by monster type.
TEST_CASE( "saigon_zoo_animals", "[mapgen][saigon]" )
{
    if( !mtype_id( "sgn_mon_voi" ).is_valid() ) {
        WARN( "saigon_2000s is not loaded; skipping" );
        return;
    }
    const std::vector<std::pair<std::string, std::vector<std::string>>> parks = {
        { "sgn_lm_thao_cam_vien", { "sgn_mon_voi", "sgn_mon_ca_sau", "sgn_mon_khi", "sgn_mon_tran", "mon_tiger", "mon_bear", "mon_deer" } },
        { "sgn_lm_suoi_tien", { "sgn_mon_ca_sau" } },
    };
    clear_overmaps();   // once: see saigon_district1_landmarks
    int slot = 0;
    for( const auto &park : parks ) {
        CAPTURE( park.first );
        const landmark l{ park.first, 4, 4, 0, 1 };
        std::map<std::string, int> seen;
        for( int seed = 1; seed <= 3; seed++ ) {
            clear_map();
            clear_avatar();
            const tripoint_abs_omt base( 10 + 8 * slot++, 60, 0 );
            for( int z = l.zmin; z <= l.zmax; z++ ) {
                for( int x = 0; x < l.w; x++ ) {
                    for( int y = 0; y < l.h; y++ ) {
                        overmap_buffer.ter_set( base + tripoint( x, y, z ), oter_str_id( piece( l, x, y, z ) ).id() );
                    }
                }
            }
            rng_set_engine_seed( seed );
            for( int x = 0; x < l.w; x++ ) {
                for( int y = 0; y < l.h; y++ ) {
                    const tripoint_abs_omt pos = base + tripoint( x, y, 0 );
                    MAPBUFFER.clear_outside_reality_bubble();
                    smallmap tm;
                    tm.generate( pos, calendar::turn, true, true );
                    const tripoint_abs_sm origin = project_to<coords::sm>( pos );
                    for( const point &d : { point( 0, 0 ), point( 1, 0 ), point( 0, 1 ), point( 1, 1 ) } ) {
                        submap *sub = MAPBUFFER.lookup_submap( origin + tripoint( d, 0 ) );
                        if( sub != nullptr ) {
                            for( const spawn_point &sp : sub->spawns ) {
                                seen[sp.type.str()] += sp.count;
                            }
                        }
                    }
                }
            }
        }
        std::string counts;
        for( const auto &kv : seen ) {
            counts += kv.first + "=" + std::to_string( kv.second ) + " ";
        }
        CAPTURE( counts );
        for( const std::string &mon : park.second ) {
            CAPTURE( mon );
            CHECK( seen[mon] > 0 );
        }
    }
}
