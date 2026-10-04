#include <queue>
#include <set>
#include <string>
#include <vector>

#include "calendar.h"
#include "cata_catch.h"
#include "coordinates.h"
#include "map.h"
#include "map_helpers.h"
#include "mapdata.h"
#include "omdata.h"
#include "overmapbuffer.h"
#include "player_helpers.h"
#include "point.h"
#include "rng.h"
#include "string_formatter.h"
#include "type_id.h"

// Saigon 2000s mod: the real District 1 landmarks (tools/saigon/gen_saigon_landmarks.py,
// doc/saigon/LANDMARKS.md phases L1 and L2).  Each one is generated on the real map at every
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
    };
    const ter_str_id open_air( "t_open_air" );
    const ter_str_id up( "t_stairs_up" );
    const ter_str_id down( "t_stairs_down" );
    for( const landmark &l : landmarks ) {
        CAPTURE( l.id );
        clear_overmaps();
        clear_avatar();
        clear_map();
        const tripoint_abs_omt base( 140, 140, 0 );
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
        CHECK( doors > 0 );
        CHECK( doors_reached == doors );
        CAPTURE( indoor, roofed, first_unroofed );
        CHECK( indoor > 0 );
        CHECK( roofed == indoor );
    }
}
