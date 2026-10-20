#include <queue>
#include <set>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

#include "avatar.h"
#include "calendar.h"
#include "cata_catch.h"
#include "coordinates.h"
#include "item.h"
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
#include "start_location.h"
#include "submap.h"
#include "type_id.h"
#include "vehicle.h"
#include "vehicle_group.h"

// Saigon 2000s mod: structural checks for the nhà ống shophouse row
// (tools/saigon/gen_nha_ong.py, design doc/saigon/analysis/d2_r3.md §4.a).
// Run with: tests/cata_test --mods=dda,saigon_2000s "[saigon]"

static const furn_str_id furn_f_standing_tank( "f_standing_tank" );

static const oter_str_id oter_field( "field" );

static const ter_str_id ter_t_brick_wall( "t_brick_wall" );
static const ter_str_id ter_t_concrete_roof( "t_concrete_roof" );
static const ter_str_id ter_t_open_air( "t_open_air" );
static const ter_str_id ter_t_sgn_tree_bo_de( "t_sgn_tree_bo_de" );
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

static void sgn_clear_map_and_reset_player()
{
    // Same ordering as tests/mapgen_post_process_test.cpp: avoid regenerating far overmaps.
    get_avatar().move_to( tripoint_abs_ms::zero );
    get_avatar().in_vehicle = false;
    get_avatar().controlling_vehicle = false;
    // A Saigon overmap is slow to generate in megacity mode (about 100 s with the neighbours
    // it pulls in), so it is generated once per run; later calls wipe overmap (0,0) back to
    // plain field, open air and earth, which is all these tests assume around their buildings.
    static bool generated = false;
    if( !generated || !overmap_buffer.has( point_abs_om() ) ) {
        clear_overmaps();
        generated = true;
    } else {
        const oter_id field = oter_str_id( "field" ).id();
        const oter_id air = oter_str_id( "open_air" ).id();
        const oter_id earth = oter_str_id( "solid_earth" ).id();
        for( int z = -2; z <= 10; z++ ) {
            const oter_id &blank = z == 0 ? field : z > 0 ? air : earth;
            for( int x = 0; x < OMAPX; x++ ) {
                for( int y = 0; y < OMAPY; y++ ) {
                    overmap_buffer.ter_set( tripoint_abs_omt( x, y, z ), blank );
                }
            }
        }
    }
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
        // Every down-stair lands on an up-stair directly below.
        for( int z = 1; z <= sgn_top_z; z++ ) {
            for( int x = 0; x < SEEX * 2; x++ ) {
                for( int y = 0; y < SEEY * 2; y++ ) {
                    if( m.ter( tripoint_bub_ms( x, y, z ) ) == ter_t_stairs_down.id() ) {
                        CAPTURE( x, y, z );
                        CHECK( m.ter( tripoint_bub_ms( x, y, z - 1 ) ) == ter_t_stairs_up.id() );
                    }
                }
            }
        }
        // No loot buried in walls (integration I7-2: lot 5 vs the east end cap).
        for( int z = 0; z <= 2; z++ ) {
            for( int x = 0; x < SEEX * 2; x++ ) {
                for( int y = 0; y < SEEY * 2; y++ ) {
                    const tripoint_bub_ms p( x, y, z );
                    if( m.ter( p ) == ter_t_brick_wall.id() ) {
                        CAPTURE( x, y, z );
                        CHECK( m.i_at( p ).empty() );
                    }
                }
            }
        }
        // The z3 roof walk (rows 16-19) runs the full width between the end caps over
        // bare roof only; railings are dividers, not walkway (critic_d2 D6a).
        std::set<point> walk;
        std::queue<point> todo;
        todo.push( point( 1, 17 ) );
        walk.insert( point( 1, 17 ) );
        while( !todo.empty() ) {
            const point p = todo.front();
            todo.pop();
            for( const point &d : four_adjacent_offsets ) {
                const point q = p + d;
                if( q.x < 0 || q.y < 16 || q.x >= SEEX * 2 || q.y > 19 || walk.count( q ) ) {
                    continue;
                }
                if( m.ter( tripoint_bub_ms( q.x, q.y, 3 ) ) != ter_t_concrete_roof.id() ||
                    m.furn( tripoint_bub_ms( q.x, q.y, 3 ) ) != furn_str_id::NULL_ID() ) {
                    continue;
                }
                walk.insert( q );
                todo.push( q );
            }
        }
        CHECK( walk.count( point( 22, 17 ) ) == 1 );
        // The end caps really are walls at both ends of the walk.
        for( int y = 16; y <= 19; y++ ) {
            CHECK( m.ter( tripoint_bub_ms( 0, y, 3 ) ) == ter_t_brick_wall.id() );
            CHECK( m.ter( tripoint_bub_ms( 23, y, 3 ) ) == ter_t_brick_wall.id() );
        }
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
    rng_set_engine_seed( 4242 );
    overmap_buffer.clear();
    overmap &om = overmap_buffer.get( point_abs_om() );
    int shophouses = 0;
    int hem_blocks = 0;
    int cho_cells = 0;
    int dda_houses = 0;
    std::string dda_house_ids;
    std::string landmarks;
    for( int x = 0; x < OMAPX; x++ ) {
        for( int y = 0; y < OMAPY; y++ ) {
            const std::string id = om.ter( tripoint_om_omt( x, y, 0 ) ).id().str();
            if( id.rfind( "sgn_nh_solo_z0", 0 ) == 0 ) {
                shophouses++;
            } else if( id.rfind( "sgn_hem_block", 0 ) == 0 ) {
                hem_blocks++;
            } else if( id.rfind( "sgn_cho_", 0 ) == 0 ) {
                cho_cells++;
            } else if( id.rfind( "sgn_lm_", 0 ) == 0 ) {
                // the landmarks (L1, L2): count each by its north-west piece
                if( id.find( "_00_" ) != std::string::npos ) {
                    landmarks += id.substr( 7, id.find( "_00_" ) - 7 ) + " ";
                }
            } else {
                // dda city buildings and US specials that the Saigon region must not place
                for( const char *prefix : {
                         "house", "2story", "s_", "hw_", "police", "bank", "church", "mansion",
                         "mil_", "lab_", "evac", "school", "fire_station", "hospital"
                     } ) {
                    if( id.rfind( prefix, 0 ) == 0 ) {
                        dda_houses++;
                        dda_house_ids += id + " ";
                        break;
                    }
                }
            }
        }
    }
    CAPTURE( shophouses, hem_blocks, cho_cells, dda_houses, dda_house_ids );
    // The 2x2 chợ only fits 2-deep blocks, so it is reported rather than required.
    WARN( "chợ cells on this overmap: " << cho_cells );
    // The landmarks are OVERMAP_UNIQUE and up to 3x3, so they are reported rather than required.
    WARN( "Saigon landmarks on this overmap: " << landmarks );
    // The Saigon region routes every city slot to Saigon buildings, and its SAIGON
    // feature-flag whitelist (B8g-2) removes every dda overmap special, highway and
    // US store, so no dda building may appear at all.
    CHECK( shophouses + hem_blocks >= 300 );
    CHECK( shophouses > hem_blocks );
    CHECK( hem_blocks > 0 );
    CHECK( dda_houses == 0 );
}


// Any door: plain doors, the accordion iron gates of hẻm homes (G22), roller shutters.
static bool is_door( map &m, const tripoint_bub_ms &p )
{
    return m.ter( p ).obj().has_flag( ter_furn_flag::TFLAG_DOOR );
}

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
            if( m.move_cost( tq ) <= 0 && !is_door( m, tq ) ) {
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
                        if( is_door( m, tripoint_bub_ms( x, y, 0 ) ) ) {
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

static const furn_str_id furn_f_counter( "f_counter" );
static const itype_id itype_sgn_thung_xop( "sgn_thung_xop" );

TEST_CASE( "saigon_cho_market_structure", "[mapgen][saigon]" )
{
    const oter_str_id cho_nw( "sgn_cho_nw_north" );
    if( !cho_nw.is_valid() ) {
        WARN( "saigon_2000s is not loaded; skipping" );
        return;
    }
    sgn_clear_map_and_reset_player();
    const tripoint_abs_omt pos( 80, 80, 0 );
    const std::vector<std::pair<point, std::string>> parts = {
        { { 0, 0 }, "nw" }, { { 1, 0 }, "ne" }, { { 0, 1 }, "sw" }, { { 1, 1 }, "se" }
    };
    for( const std::pair<point, std::string> &part : parts ) {
        overmap_buffer.ter_set( pos + tripoint( part.first, 0 ),
                                oter_str_id( "sgn_cho_" + part.second + "_north" ).id() );
    }
    int counters = 0;
    int coolers = 0;
    rng_set_engine_seed( 7 );
    for( const std::pair<point, std::string> &part : parts ) {
        CAPTURE( part.second );
        MAPBUFFER.clear_outside_reality_bubble();
        smallmap tm;
        tm.generate( pos + tripoint( part.first, 0 ), calendar::turn, false, true );
        map &m = *tm.cast_to_map();
        for( int x = 0; x < SEEX * 2; x++ ) {
            for( int y = 0; y < SEEY * 2; y++ ) {
                const tripoint_bub_ms p( x, y, 0 );
                counters += m.furn( p ) == furn_f_counter.id();
                for( const item &it : m.i_at( p ) ) {
                    coolers += it.typeId() == itype_sgn_thung_xop;
                }
            }
        }
        // Every quarter of the hall has a 2-tile half of a 4-wide entrance on its outer
        // north or south wall (x 22-25 of the 48-wide hall).
        const int entrance_y = part.first.y == 0 ? 0 : SEEY * 2 - 1;
        const int entrance_x = part.first.x == 0 ? 22 : 0;
        CHECK( m.move_cost( tripoint_bub_ms( entrance_x, entrance_y, 0 ) ) > 0 );
        CHECK( m.move_cost( tripoint_bub_ms( entrance_x + 1, entrance_y, 0 ) ) > 0 );
        tm.delete_unmerged_submaps();
    }
    CHECK( counters >= 40 );
    CHECK( coolers >= 1 );
}

static const furn_str_id furn_f_statue( "f_statue" );

TEST_CASE( "saigon_chungcu_and_chua_structure", "[mapgen][saigon]" )
{
    const oter_str_id chua( "sgn_chua_north" );
    if( !chua.is_valid() ) {
        WARN( "saigon_2000s is not loaded; skipping" );
        return;
    }
    sgn_clear_map_and_reset_player();
    const tripoint_abs_omt pos( 90, 90, 0 );
    for( int z = 0; z <= 5; z++ ) {
        overmap_buffer.ter_set( pos + tripoint( 0, 0, z ),
                                oter_str_id( "sgn_chungcu_z" + std::to_string( z ) + "_north" ).id() );
    }
    overmap_buffer.ter_set( pos + tripoint( 2, 0, 0 ), chua.id() );
    rng_set_engine_seed( 11 );
    {
        MAPBUFFER.clear_outside_reality_bubble();
        smallmap tm;
        tm.generate( pos, calendar::turn, false, true );
        map &m = *tm.cast_to_map();
        int tanks = 0;
        int filled = 0;
        for( int z = 0; z <= 5; z++ ) {
            CAPTURE( z );
            if( z < 5 ) {
                CHECK( count_ter( m, ter_t_stairs_up, z ) == 1 );
            }
            if( z > 0 ) {
                CHECK( count_ter( m, ter_t_stairs_down, z ) == 1 );
            }
            for( int x = 0; x < SEEX * 2; x++ ) {
                for( int y = 0; y < SEEY * 2; y++ ) {
                    const tripoint_bub_ms p( x, y, z );
                    if( z < 5 && m.ter( p ) == ter_t_stairs_up.id() ) {
                        CHECK( m.ter( tripoint_bub_ms( x, y, z + 1 ) ) == ter_t_stairs_down.id() );
                    }
                    if( m.furn( p ) == furn_f_standing_tank.id() ) {
                        tanks++;
                        filled += !m.i_at( p ).empty();
                    }
                }
            }
        }
        CHECK( tanks == 2 );
        CHECK( filled == tanks );
        tm.delete_unmerged_submaps();
    }
    {
        MAPBUFFER.clear_outside_reality_bubble();
        smallmap tm;
        tm.generate( pos + tripoint( 2, 0, 0 ), calendar::turn, false, true );
        map &m = *tm.cast_to_map();
        int statues = 0;
        for( int x = 0; x < SEEX * 2; x++ ) {
            for( int y = 0; y < SEEY * 2; y++ ) {
                statues += m.furn( tripoint_bub_ms( x, y, 0 ) ) == furn_f_statue.id();
            }
        }
        CHECK( statues == 1 );
        // The tam quan gate is open to the street.
        CHECK( m.move_cost( tripoint_bub_ms( 11, 0, 0 ) ) > 0 );
        const std::set<point> inside = reachable_through_doors( m, point( 11, 0 ), 0 );
        // The main hall is reachable from the gate through its double doors.
        CHECK( inside.count( point( 11, 12 ) ) == 1 );
        // Saigon flora (G12): the courtyard's two trees are bồ đề, and the decorative
        // shrubs resolve through the Saigon region's mapping, never to New England trees.
        CHECK( count_ter( m, ter_t_sgn_tree_bo_de, 0 ) == 2 );
        int shrubs = 0;
        int dda_trees = 0;
        for( int x = 0; x < SEEX * 2; x++ ) {
            for( int y = 0; y < SEEY * 2; y++ ) {
                const std::string id = m.ter( tripoint_bub_ms( x, y, 0 ) ).id().str();
                dda_trees += id.rfind( "t_tree", 0 ) == 0;
                shrubs += id == "t_sgn_shrub_hoa_giay" || id == "t_shrub" || id == "t_bamboo_long" ||
                          id == "t_fern";
            }
        }
        CHECK( dda_trees == 0 );
        CHECK( shrubs == 4 );
        tm.delete_unmerged_submaps();
    }
}

TEST_CASE( "saigon_traffic_is_mostly_two_wheelers", "[vehicle][saigon]" )
{
    if( !vproto_id( "sgn_veh_underbone" ).is_valid() ) {
        WARN( "saigon_2000s is not loaded; skipping" );
        return;
    }
    rng_set_engine_seed( 3 );
    for( const std::string gid : {
             "city_vehicles", "city_pileup", "police_pileup", "highway", "parkinglot"
         } ) {
        CAPTURE( gid );
        int saigon = 0;
        const int samples = 2000;
        for( int i = 0; i < samples; i++ ) {
            saigon += vgroup_id( gid )->pick().str().rfind( "sgn_veh_", 0 ) == 0;
        }
        CAPTURE( saigon );
        // Dilution at 100x the dda total weight leaves ~1% dda vehicles.
        CHECK( saigon >= samples * 95 / 100 );
    }
}

static const ter_str_id ter_t_thconc_floor( "t_thconc_floor" );

// Every indoor floor tile at level z has something other than open air above it.
static int uncovered_indoor_tiles( map &m, int z )
{
    int n = 0;
    for( int x = 0; x < SEEX * 2; x++ ) {
        for( int y = 0; y < SEEY * 2; y++ ) {
            if( m.ter( tripoint_bub_ms( x, y, z ) ) == ter_t_thconc_floor.id() &&
                m.ter( tripoint_bub_ms( x, y, z + 1 ) ) == ter_t_open_air.id() ) {
                n++;
            }
        }
    }
    return n;
}

TEST_CASE( "saigon_buildings_have_roofs", "[mapgen][saigon]" )
{
    if( !oter_str_id( "sgn_hem_block_roof_north" ).is_valid() ) {
        WARN( "saigon_2000s is not loaded; skipping" );
        return;
    }
    sgn_clear_map_and_reset_player();
    struct stack_def {
        std::string name;
        std::vector<std::string> levels;
    };
    const std::vector<stack_def> stacks = {
        { "hem", { "sgn_hem_block_north", "sgn_hem_block_roof_north" } },
        { "cho", { "sgn_cho_nw_north", "sgn_cho_roof_nw_north" } },
        { "chua", { "sgn_chua_north", "sgn_chua_roof_north" } },
        {
            "nha_ong", { "sgn_nh_solo_z0_north", "sgn_nh_solo_z1_north", "sgn_nh_solo_z2_north",
                "sgn_nh_solo_z3_north", "sgn_nh_solo_z4_north", "sgn_nh_solo_z5_north"
            }
        },
        {
            "chungcu", { "sgn_chungcu_z0_north", "sgn_chungcu_z1_north", "sgn_chungcu_z2_north",
                "sgn_chungcu_z3_north", "sgn_chungcu_z4_north", "sgn_chungcu_z5_north"
            }
        },
    };
    int column = 0;
    for( const stack_def &st : stacks ) {
        const tripoint_abs_omt pos( 100 + 3 * column++, 100, 0 );
        for( size_t z = 0; z < st.levels.size(); z++ ) {
            overmap_buffer.ter_set( pos + tripoint( 0, 0, z ), oter_str_id( st.levels[z] ).id() );
        }
        for( unsigned seed = 1; seed <= 5; seed++ ) {
            CAPTURE( st.name, seed );
            rng_set_engine_seed( seed );
            MAPBUFFER.clear_outside_reality_bubble();
            smallmap tm;
            tm.generate( pos, calendar::turn, false, true );
            map &m = *tm.cast_to_map();
            for( size_t z = 0; z + 1 < st.levels.size(); z++ ) {
                CAPTURE( z );
                CHECK( uncovered_indoor_tiles( m, z ) == 0 );
            }
            tm.delete_unmerged_submaps();
        }
    }
}

// Counts mapgen spawn points in one generated OMT column (all z), split into
// dormant (pseudo-dormant corpses) and awake monsters.  Generated submaps are stored
// in MAPBUFFER, so they are read from there.
static std::pair<int, int> count_spawns( const tripoint_abs_omt &pos, int top_z )
{
    int awake = 0;
    int dormant = 0;
    const tripoint_abs_sm origin = project_to<coords::sm>( pos );
    for( int z = 0; z <= top_z; z++ ) {
        for( const point &d : {
                 point( 0, 0 ), point( 1, 0 ), point( 0, 1 ), point( 1, 1 )
             } ) {
            submap *sub = MAPBUFFER.lookup_submap( origin + tripoint( d, z ) );
            if( sub == nullptr ) {
                continue;
            }
            for( const spawn_point &sp : sub->spawns ) {
                const bool is_dormant = sp.type.str().find( "pseudo_dormant" ) != std::string::npos;
                ( is_dormant ? dormant : awake ) += sp.count;
            }
        }
    }
    return { awake, dormant };
}

TEST_CASE( "saigon_monster_budget_per_omt", "[mapgen][monster][saigon]" )
{
    if( !mtype_id( "sgn_mon_zombie_xe_om" ).is_valid() ) {
        WARN( "saigon_2000s is not loaded; skipping" );
        return;
    }
    sgn_clear_map_and_reset_player();
    // d3_r3 §6.2 tiers per OMT: rows/hẻm <= 4 awake and <= 20 dormant; chợ <= 20 / <= 60.
    // D-fix (doc/saigon/DIFFICULTY.md, side check): the dormant layer of the city fabric was cut
    // (gen_nha_ong.py repeat [1,3] -> [1,2], gen_hem.py [2,5] -> [1,3]), so rows and hẻm also
    // carry a tighter dormant ceiling.  Expected now: row 4.5 dormant (was 6; 10 seeds measure
    // 3.7, were 5.8), hẻm 1.6 (was 2.8; 10 seeds measure 1.1, were 2.9).  The ceilings sit about
    // one old-to-new step above the new means, so the old numbers fail them.
    struct tier {
        std::vector<std::string> levels;
        double max_awake;
        double max_dormant;
        double dfix_max_dormant;
    };
    const std::vector<tier> tiers = {
        {
            {
                "sgn_nh_solo_z0_north", "sgn_nh_solo_z1_north", "sgn_nh_solo_z2_north",
                "sgn_nh_solo_z3_north", "sgn_nh_solo_z4_north", "sgn_nh_solo_z5_north"
            }, 4, 20, 5.5
        },
        { { "sgn_hem_block_north", "sgn_hem_block_roof_north" }, 4, 20, 2.4 },
        { { "sgn_cho_nw_north", "sgn_cho_roof_nw_north" }, 20, 60, 60 },
    };
    int column = 0;
    for( const tier &t : tiers ) {
        CAPTURE( t.levels[0] );
        const tripoint_abs_omt pos( 120 + 3 * column++, 120, 0 );
        for( size_t z = 0; z < t.levels.size(); z++ ) {
            overmap_buffer.ter_set( pos + tripoint( 0, 0, z ), oter_str_id( t.levels[z] ).id() );
        }
        const int seeds = 10;
        double awake = 0;
        double dormant = 0;
        for( int seed = 1; seed <= seeds; seed++ ) {
            rng_set_engine_seed( seed );
            MAPBUFFER.clear_outside_reality_bubble();
            smallmap tm;
            // save_results = true so the submaps, and their spawn points, land in MAPBUFFER
            tm.generate( pos, calendar::turn, true, true );
            const std::pair<int, int> c = count_spawns( pos, t.levels.size() - 1 );
            awake += c.first;
            dormant += c.second;
        }
        awake /= seeds;
        dormant /= seeds;
        CAPTURE( awake, dormant );
        CHECK( awake > 0 );
        CHECK( dormant > 0 );
        CHECK( awake <= t.max_awake );
        CHECK( dormant <= t.max_dormant );
        CHECK( dormant <= t.dfix_max_dormant );
    }
}

TEST_CASE( "saigon_road_traffic_is_saigon", "[mapgen][vehicle][saigon]" )
{
    if( !vproto_id( "sgn_veh_underbone" ).is_valid() ) {
        WARN( "saigon_2000s is not loaded; skipping" );
        return;
    }
    sgn_clear_map_and_reset_player();
    int saigon = 0;
    int other = 0;
    std::string other_ids;
    int column = 0;
    for( const std::string road : {
             "road_nesw", "road_ns", "road_ew"
         } ) {
        const tripoint_abs_omt pos( 140 + 3 * column++, 140, 0 );
        overmap_buffer.ter_set( pos, oter_str_id( road ).id() );
        // City neighbours carry SIDEWALK, which selects the city traffic chunks.
        for( const tripoint &d : eight_horizontal_neighbors ) {
            overmap_buffer.ter_set( pos + d, sgn_nh_solo( 0 ).id() );
        }
        for( int seed = 1; seed <= 40; seed++ ) {
            rng_set_engine_seed( seed );
            MAPBUFFER.clear_outside_reality_bubble();
            smallmap tm;
            tm.generate( pos, calendar::turn, true, true );
            const tripoint_abs_sm origin = project_to<coords::sm>( pos );
            for( const point &d : {
                     point( 0, 0 ), point( 1, 0 ), point( 0, 1 ), point( 1, 1 )
                 } ) {
                submap *sub = MAPBUFFER.lookup_submap( origin + tripoint( d, 0 ) );
                if( sub == nullptr ) {
                    continue;
                }
                for( const std::unique_ptr<vehicle> &veh : sub->vehicles ) {
                    if( veh->type.str().rfind( "sgn_veh_", 0 ) == 0 ) {
                        saigon++;
                    } else {
                        other++;
                        other_ids += veh->type.str() + " ";
                    }
                }
            }
        }
    }
    CAPTURE( saigon, other, other_ids );
    CHECK( saigon > 20 );
    // dda chunks keep weight 1000 against 1,000,000 (0.1%), plus 1% group residue.
    CHECK( other <= saigon / 20 );
}

// The new-game path of game::start_game for every Saigon start location: find a site on a
// fresh overmap, prepare the map, load the reality bubble, place the player.  A player who
// can't stand where they are placed, or a site that can't be found, breaks "New character".
TEST_CASE( "saigon_new_game_start_locations", "[saigon][start_location]" )
{
    if( !start_location_id( "sgn_sloc_nha_ong" ).is_valid() ) {
        WARN( "saigon_2000s is not loaded; skipping" );
        return;
    }
    for( const std::string sloc : {
             "sgn_sloc_nha_ong", "sgn_sloc_nha_ong_shuttered", "sgn_sloc_cho"
         } ) {
        CAPTURE( sloc );
        sgn_clear_map_and_reset_player();
        rng_set_engine_seed( 4 );
        const start_location &start = start_location_id( sloc ).obj();
        const std::pair<tripoint_abs_omt, std::unordered_map<std::string, std::string>> found =
                    start.find_player_initial_location( point_abs_om() );
        const tripoint_abs_omt omtstart = found.first;
        REQUIRE_FALSE( omtstart.is_invalid() );
        start.set_parameters( omtstart, found.second );
        start.prepare_map( omtstart );
        tripoint_abs_sm lev = project_to<coords::sm>( omtstart );
        lev -= point( HALF_MAPSIZE, HALF_MAPSIZE );
        map &here = get_map();
        here.load( lev, false );
        avatar &u = get_avatar();
        start.place_player( u, omtstart );
        CHECK( u.pos_abs_omt() == omtstart );
        CHECK( here.passable( u.pos_bub() ) );
        CHECK( here.ter( u.pos_bub() ).obj().roof.str() != "" );
        CHECK( overmap_buffer.ter( omtstart ).id().str().rfind( "sgn_", 0 ) == 0 );
    }
}

// B8f canal (tools/saigon/gen_kenh.py, d2_r3 §4.d): an 8-row channel of wadeable murky water
// between two walkable embankments, shacks with tin roofs at z1.
TEST_CASE( "saigon_kenh_structure", "[mapgen][saigon]" )
{
    const oter_str_id kenh( "sgn_kenh_north" );
    if( !kenh.is_valid() ) {
        WARN( "saigon_2000s is not loaded; skipping" );
        return;
    }
    const ter_str_id water( "t_water_murky" );
    const ter_str_id tin_roof( "t_sgn_mai_ton" );
    const ter_str_id wood_wall( "t_wall_wood" );
    sgn_clear_map_and_reset_player();
    const tripoint_abs_omt pos( 110, 110, 0 );
    overmap_buffer.ter_set( pos, kenh.id() );
    overmap_buffer.ter_set( pos + tripoint::above, oter_str_id( "sgn_kenh_roof_north" ).id() );
    for( unsigned seed = 1; seed <= 5; seed++ ) {
        CAPTURE( seed );
        rng_set_engine_seed( seed );
        MAPBUFFER.clear_outside_reality_bubble();
        smallmap tm;
        tm.generate( pos, calendar::turn, false, true );
        map &m = *tm.cast_to_map();
        int channel = 0;
        int water_elsewhere = 0;
        int walls = 0;
        int roofed_walls = 0;
        for( int x = 0; x < SEEX * 2; x++ ) {
            for( int y = 0; y < SEEY * 2; y++ ) {
                const bool is_water = m.ter( tripoint_bub_ms( x, y, 0 ) ) == water.id();
                ( y >= 8 && y <= 15 ? channel : water_elsewhere ) += is_water;
                if( m.ter( tripoint_bub_ms( x, y, 0 ) ) == wood_wall.id() ) {
                    walls++;
                    roofed_walls += m.ter( tripoint_bub_ms( x, y, 1 ) ) == tin_roof.id();
                }
            }
            // both embankment walks are walkable along their whole length
            CHECK( m.passable( tripoint_bub_ms( x, 0, 0 ) ) );
            CHECK( m.passable( tripoint_bub_ms( x, 23, 0 ) ) );
        }
        CHECK( channel == 24 * 8 );
        CHECK( water_elsewhere == 0 );
        CHECK( walls > 0 );
        CHECK( roofed_walls == walls );
        tm.delete_unmerged_submaps();
    }
}

// B8h landmarks (tools/saigon/gen_landmarks.py): every door is reachable from the street
// gate and every building tile has its roof at z1.
TEST_CASE( "saigon_landmarks_structure", "[mapgen][saigon]" )
{
    if( !oter_str_id( "sgn_nha_tho_north" ).is_valid() ) {
        WARN( "saigon_2000s is not loaded; skipping" );
        return;
    }
    const ter_str_id open_air( "t_open_air" );
    for( const std::string id : {
             "sgn_nha_tho", "sgn_ubnd", "sgn_truong"
         } ) {
        CAPTURE( id );
        sgn_clear_map_and_reset_player();
        const tripoint_abs_omt pos( 120, 120, 0 );
        overmap_buffer.ter_set( pos, oter_str_id( id + "_north" ).id() );
        overmap_buffer.ter_set( pos + tripoint::above, oter_str_id( id + "_roof_north" ).id() );
        rng_set_engine_seed( 7 );
        MAPBUFFER.clear_outside_reality_bubble();
        smallmap tm;
        tm.generate( pos, calendar::turn, false, true );
        map &m = *tm.cast_to_map();
        const std::set<point> reach = reachable_through_doors( m, point( 11, 1 ), 0 );
        int doors = 0;
        int doors_reached = 0;
        int indoor = 0;
        int roofed = 0;
        for( int x = 0; x < SEEX * 2; x++ ) {
            for( int y = 0; y < SEEY * 2; y++ ) {
                const tripoint_bub_ms p( x, y, 0 );
                if( is_door( m, p ) ) {
                    doors++;
                    doors_reached += reach.count( point( x, y ) );
                }
                const ter_t &t = m.ter( p ).obj();
                if( t.has_flag( ter_furn_flag::TFLAG_INDOORS ) ) {
                    indoor++;
                    roofed += m.ter( tripoint_bub_ms( x, y, 1 ) ) != open_air.id();
                }
            }
        }
        CHECK( doors > 0 );
        CHECK( doors_reached == doors );
        CHECK( indoor > 100 );
        CHECK( roofed == indoor );
        tm.delete_unmerged_submaps();
    }
}
