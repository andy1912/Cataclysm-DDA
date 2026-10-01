#include <queue>
#include <set>

#include "avatar.h"
#include "calendar.h"
#include "cata_catch.h"
#include "coordinates.h"
#include "map.h"
#include "map_helpers.h"
#include "map_scale_constants.h"
#include "mapbuffer.h"
#include "omdata.h"
#include "overmapbuffer.h"
#include "player_helpers.h"
#include "point.h"
#include "rng.h"
#include "type_id.h"

// Saigon 2000s mod: structural checks for the nhà ống shophouse row
// (tools/saigon/gen_nha_ong.py, design doc/saigon/analysis/d2_r3.md §4.a).
// Run with: tests/cata_test --mods=dda,saigon_2000s "[saigon]"

static const furn_str_id furn_f_standing_tank( "f_standing_tank" );

static const oter_str_id oter_field( "field" );

static const ter_str_id ter_t_open_air( "t_open_air" );
static const ter_str_id ter_t_stairs_down( "t_stairs_down" );
static const ter_str_id ter_t_stairs_up( "t_stairs_up" );

static constexpr int sgn_lots = 6;
static constexpr int sgn_top_z = 5;

static oter_str_id sgn_nh_solo( int z )
{
    return oter_str_id( "sgn_nh_solo_z" + std::to_string( z ) + "_north" );
}

static int count_ter( map &m, const ter_str_id &ter, int z )
{
    int n = 0;
    for( int x = 0; x < SEEX * 2; x++ ) {
        for( int y = 0; y < SEEY * 2; y++ ) {
            n += m.ter( tripoint_bub_ms( x, y, z ) ) == ter.id();
        }
    }
    return n;
}

// Walkable z-level BFS inside the OMT; returns the set of reached points.
static std::set<point> reachable( map &m, const point &start, int z )
{
    std::set<point> seen;
    std::queue<point> todo;
    todo.push( start );
    seen.insert( start );
    while( !todo.empty() ) {
        const point p = todo.front();
        todo.pop();
        for( const point &d : four_adjacent_offsets ) {
            const point q = p + d;
            if( q.x < 0 || q.y < 0 || q.x >= SEEX * 2 || q.y >= SEEY * 2 || seen.count( q ) ) {
                continue;
            }
            const tripoint_bub_ms tq( q.x, q.y, z );
            if( m.move_cost( tq ) <= 0 || m.ter( tq ) == ter_t_open_air.id() ) {
                continue;
            }
            seen.insert( q );
            todo.push( q );
        }
    }
    return seen;
}

static void sgn_clear_map_and_reset_player()
{
    // Same ordering as tests/mapgen_post_process_test.cpp: avoid regenerating far overmaps.
    get_avatar().move_to( tripoint_abs_ms::zero );
    get_avatar().in_vehicle = false;
    get_avatar().controlling_vehicle = false;
    clear_overmaps();
    clear_map();
    clear_avatar();
}

TEST_CASE( "saigon_nha_ong_row_structure", "[mapgen][saigon]" )
{
    if( !sgn_nh_solo( 0 ).is_valid() ) {
        WARN( "saigon_2000s is not loaded; skipping" );
        return;
    }
    sgn_clear_map_and_reset_player();
    const tripoint_abs_omt pos( 60, 60, 0 );
    for( int z = 0; z <= sgn_top_z; z++ ) {
        overmap_buffer.ter_set( pos + tripoint( 0, 0, z ), sgn_nh_solo( z ).id() );
    }
    for( const tripoint &d : eight_horizontal_neighbors ) {
        overmap_buffer.ter_set( pos + d, oter_field.id() );
    }

    for( unsigned seed = 1; seed <= 10; seed++ ) {
        CAPTURE( seed );
        rng_set_engine_seed( seed );
        MAPBUFFER.clear_outside_reality_bubble();
        smallmap tm;
        tm.generate( pos, calendar::turn, false, true );
        map &m = *tm.cast_to_map();

        // Every lot has at least three storeys, so the first three levels each
        // have one up-stair per lot.
        for( int z = 0; z <= 2; z++ ) {
            CAPTURE( z );
            CHECK( count_ter( m, ter_t_stairs_up, z ) == sgn_lots );
        }
        // Stairs line up vertically: every up-stair has a down-stair directly above.
        for( int z = 0; z < sgn_top_z; z++ ) {
            for( int x = 0; x < SEEX * 2; x++ ) {
                for( int y = 0; y < SEEY * 2; y++ ) {
                    if( m.ter( tripoint_bub_ms( x, y, z ) ) == ter_t_stairs_up.id() ) {
                        CAPTURE( x, y, z );
                        CHECK( m.ter( tripoint_bub_ms( x, y, z + 1 ) ) == ter_t_stairs_down.id() );
                    }
                }
            }
        }
        // The z3 roof walk (rows 16-19) runs the full width between the end caps.
        const std::set<point> walk = reachable( m, point( 1, 17 ), 3 );
        CHECK( walk.count( point( 22, 17 ) ) == 1 );
        // One rooftop tank per lot, and it holds water.
        int tanks = 0;
        int filled = 0;
        for( int z = 3; z <= sgn_top_z; z++ ) {
            for( int x = 0; x < SEEX * 2; x++ ) {
                for( int y = 0; y < SEEY * 2; y++ ) {
                    const tripoint_bub_ms p( x, y, z );
                    if( m.furn( p ) == furn_f_standing_tank.id() ) {
                        tanks++;
                        filled += !m.i_at( p ).empty();
                    }
                }
            }
        }
        CHECK( tanks == sgn_lots );
        CHECK( filled == tanks );
        tm.delete_unmerged_submaps();
    }
}
