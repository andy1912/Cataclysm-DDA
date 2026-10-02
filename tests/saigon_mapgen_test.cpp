#include <queue>
#include <set>
#include <string>
#include <utility>
#include <vector>

#include "avatar.h"
#include "calendar.h"
#include "cata_catch.h"
#include "coordinates.h"
#include "map.h"
#include "map_helpers.h"
#include "map_scale_constants.h"
#include "mapbuffer.h"
#include "omdata.h"
#include "overmap.h"
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

TEST_CASE( "saigon_cities_use_shophouses", "[overmap][saigon]" )
{
    if( !sgn_nh_solo( 0 ).is_valid() ) {
        WARN( "saigon_2000s is not loaded; skipping" );
        return;
    }
    overmap_buffer.clear();
    overmap &om = overmap_buffer.get( point_abs_om() );
    int shophouses = 0;
    int dda_houses = 0;
    std::string dda_house_ids;
    for( int x = 0; x < OMAPX; x++ ) {
        for( int y = 0; y < OMAPY; y++ ) {
            const std::string id = om.ter( tripoint_om_omt( x, y, 0 ) ).id().str();
            if( id.rfind( "sgn_nh_solo_z0", 0 ) == 0 ) {
                shophouses++;
            } else if( id.rfind( "house", 0 ) == 0 || id.rfind( "2story", 0 ) == 0 ) {
                dda_houses++;
                dda_house_ids += id + " ";
            }
        }
    }
    CAPTURE( shophouses, dda_houses, dda_house_ids );
    // The Saigon region routes every city house slot to nhà ống rows (~540-600 per
    // overmap).  The few remaining dda houses come from dda overmap specials (farms
    // etc.), which the SAIGON feature-flag whitelist removes in B10; tighten to 0 then.
    CHECK( shophouses >= 300 );
    CHECK( dda_houses <= 5 );
}

static const ter_str_id ter_t_door_c( "t_door_c" );

// BFS over walkable tiles; closed doors count as traversable (they open).
static std::set<point> reachable_through_doors( map &m, const point &start, int z )
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
            if( m.move_cost( tq ) <= 0 && m.ter( tq ) != ter_t_door_c.id() ) {
                continue;
            }
            seen.insert( q );
            todo.push( q );
        }
    }
    return seen;
}

TEST_CASE( "saigon_hem_connectivity", "[mapgen][saigon]" )
{
    const oter_str_id hem_north( "sgn_hem_block_north" );
    if( !hem_north.is_valid() ) {
        WARN( "saigon_2000s is not loaded; skipping" );
        return;
    }
    const std::vector<std::string> rotations = { "north", "east", "south", "west" };
    // Edge ports are the spine arm ends; their positions are rotation-invariant.
    const std::vector<point> ports = { { 11, 0 }, { 12, 0 }, { 11, 23 }, { 12, 23 },
        { 0, 11 }, { 0, 12 }, { 23, 11 }, { 23, 12 }
    };
    const std::vector<std::pair<std::string, bool>> configs = {
        { "sgn_hem_block_north", true }, { "road_nesw", true }, { "field", false }
    };
    sgn_clear_map_and_reset_player();
    const tripoint_abs_omt pos( 70, 70, 0 );
    for( const std::string &rot : rotations ) {
        for( const std::pair<std::string, bool> &cfg : configs ) {
            CAPTURE( rot, cfg.first );
            overmap_buffer.ter_set( pos, oter_str_id( "sgn_hem_block_" + rot ).id() );
            for( const tripoint &d : eight_horizontal_neighbors ) {
                const bool orthogonal = d.x == 0 || d.y == 0;
                overmap_buffer.ter_set( pos + d, orthogonal ? oter_str_id( cfg.first ).id() : oter_field.id() );
            }
            for( unsigned seed = 1; seed <= 10; seed++ ) {
                CAPTURE( seed );
                rng_set_engine_seed( seed );
                MAPBUFFER.clear_outside_reality_bubble();
                smallmap tm;
                tm.generate( pos, calendar::turn, false, true );
                map &m = *tm.cast_to_map();
                const std::set<point> reach = reachable_through_doors( m, point( 11, 11 ), 0 );
                int doors = 0;
                int doors_reached = 0;
                for( int x = 0; x < SEEX * 2; x++ ) {
                    for( int y = 0; y < SEEY * 2; y++ ) {
                        if( m.ter( tripoint_bub_ms( x, y, 0 ) ) == ter_t_door_c.id() ) {
                            doors++;
                            doors_reached += reach.count( point( x, y ) );
                        }
                    }
                }
                CHECK( doors > 0 );
                CHECK( doors_reached == doors );
                for( const point &p : ports ) {
                    CAPTURE( p );
                    CHECK( ( reach.count( p ) == 1 ) == cfg.second );
                }
                tm.delete_unmerged_submaps();
            }
        }
    }
}
