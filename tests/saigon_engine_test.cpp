#include <array>
#include <filesystem>
#include <initializer_list>
#include <map>
#include <memory>
#include <optional>
#include <set>
#include <stddef.h>
#include <string>
#include <utility>
#include <vector>

#include "avatar.h"
#include "calendar.h"
#include "cata_catch.h"
#include "cata_path.h"
#include "character_creator_ui.h"
#include "coordinates.h"
#include "creature_tracker.h"
#include "enums.h"
#include "filesystem.h"
#include "flexbuffer_json.h"
#include "game.h"
#include "global_vars.h"
#include "json_loader.h"
#include "level_cache.h"
#include "map.h"
#include "map_helpers.h"
#include "map_scale_constants.h"
#include "math_parser_diag_value.h"
#include "memory_fast.h"
#include "monster.h"
#include "mtype.h"
#include "omdata.h"
#include "options_helpers.h"
#include "overmap.h"
#include "overmapbuffer.h"
#include "path_info.h"
#include "player_helpers.h"
#include "point.h"
#include "skill.h"
#include "type_id.h"
#include "units.h"
#include "vehicle.h"
#include "weather_gen.h"
#include "worldfactory.h"

static const mtype_id mon_test_base( "mon_test_base" );
static const mtype_id mon_zombie( "mon_zombie" );

// Saigon 2000s fork, F1-C: direct tests for the engine patches in doc/saigon/ENGINE_PATCHES.md
// that had none of their own (the others are covered by the weather, realmap, mouse and perf
// tests; see doc/saigon/TEST_MATRIX.md).  Each case fails, or logs an error and so fails the run,
// with its patch reverted.
// Run with: tests/cata_test --mods=dda,saigon_2000s "[saigon_engine]"

// The default test world is the Vietmap megacity, whose overmap (0, 0) takes about 100 s to
// generate.  The real map's loads in about a second, so these cases stand on it, and leave
// without regenerating anything (the next test that needs a fresh world clears it itself).
static bool sgn_quick_world()
{
    const cata_path file = PATH_INFO::moddir() / "saigon_2000s/realmap_2009/overmap_0_0.omap.gz";
    if( !file_exist( file.get_unrelative_path() ) ) {
        return false;
    }
    // an overmap saved earlier in the run (any test whose turns autosave) would load instead
    for( int x = -1; x <= 3; x++ ) {
        for( int y = -2; y <= 1; y++ ) {
            const point_abs_om om( x, y );
            for( const cata_path &saved : {
                     PATH_INFO::current_dimension_save_path() / zzip_overmap_directory /
                     ( overmapbuffer::terrain_filename( om ) + std::string( zzip_suffix ) ),
                     PATH_INFO::current_dimension_save_path() / overmapbuffer::terrain_filename( om )
                 } ) {
                if( file_exist( saved ) ) {
                    remove_file( saved.get_unrelative_path().u8string() );
                }
            }
        }
    }
    get_globals().set_global_value( "overmap_pregenerated_path",
                                    diag_value( std::string( "saigon_2000s/realmap_2009" ) ) );
    get_globals().set_global_value( "overmap_outside_region",
                                    diag_value( std::string( "sgn_saigon_delta" ) ) );
    clear_creatures();
    clear_avatar();
    clear_overmaps();
    clear_map();
    return true;
}

static void sgn_leave_world()
{
    get_globals().remove_global_value( "overmap_pregenerated_path" );
    get_globals().remove_global_value( "overmap_outside_region" );
    clear_creatures();
    clear_map();
}

// a TEST_DATA monster: nothing in Saigon mapgen spawns it, so any left after the clear are ours

// src/game.cpp item 3: place_critter_around( ..., forced ) skips the terrain and sight rules but
// not the rule that the square is free.  Upstream placed a forced creature on the centre even
// when another stood there, and creature_tracker::add logged "there's already a monster at" and
// dropped it.
TEST_CASE( "saigon_engine_forced_placement_keeps_occupancy", "[saigon][saigon_engine]" )
{
    if( !sgn_quick_world() ) {
        WARN( "saigon_2000s or its real map is not present; skipping" );
        return;
    }
    const tripoint_bub_ms centre = get_avatar().pos_bub() + tripoint( 6, 6, 0 );
    monster *first = g->place_critter_at( mon_zombie, centre );
    REQUIRE( first != nullptr );
    const shared_ptr_fast<monster> second = make_shared_fast<monster>( mon_zombie );
    monster *placed = g->place_critter_around( second, centre, 2, true );
    REQUIRE( placed != nullptr );
    CHECK( placed->pos_bub() != centre );
    CHECK( rl_dist( placed->pos_bub(), centre ) <= 2 );
    CHECK( get_creature_tracker().creature_at<monster>( centre ) == first );
    CHECK( get_creature_tracker().get_monsters_list().size() == 2 );
    sgn_leave_world();
}

// src/map_helpers.cpp: clear_overmaps() drops the creatures a previous test left behind.
// Upstream despawned them into the new overmap's horde map (two on one square logged
// "Attempted to insert a zombie at ..."), and the static spawns of the reloaded bubble then
// brought them back into the next test.
TEST_CASE( "saigon_engine_clear_overmaps_drops_creatures", "[saigon][saigon_engine]" )
{
    if( !sgn_quick_world() ) {
        WARN( "saigon_2000s or its real map is not present; skipping" );
        return;
    }
    const tripoint_bub_ms near = get_avatar().pos_bub() + tripoint( 3, 0, 0 );
    REQUIRE( g->place_critter_at( mon_test_base, near ) != nullptr );
    REQUIRE( g->place_critter_at( mon_test_base, near + tripoint::east ) != nullptr );
    clear_overmaps();
    int left = 0;
    for( const shared_ptr_fast<monster> &m : get_creature_tracker().get_monsters_list() ) {
        left += m->type->id == mon_test_base;
    }
    CHECK( left == 0 );
    sgn_leave_world();
}

// src/map.cpp item 1 (QA2): map::resync_vehicle_lists_from_submaps() makes the level caches list
// exactly the vehicles the loaded submaps own.  A vehicle freed while map::load ran stayed in a
// cache and build_map_cache walked it (SIGSEGV at New game).  A stray vehicle stands in for the
// freed one here: owned by no submap, it must leave the caches and the dirty list; the real one
// must come back if a cache lost it.
TEST_CASE( "saigon_engine_resync_vehicle_lists", "[saigon][saigon_engine]" )
{
    if( !sgn_quick_world() ) {
        WARN( "saigon_2000s or its real map is not present; skipping" );
        return;
    }
    map &here = get_map();
    const tripoint_bub_ms at = get_avatar().pos_bub() + tripoint( 8, 8, 0 );
    vehicle *veh = here.add_vehicle( vproto_id( "bicycle" ), at, 0_degrees, 0,
                                     veh_spawn_status::UNDAMAGED );
    REQUIRE( veh != nullptr );
    level_cache &ch = const_cast<level_cache &>( here.get_cache_ref( at.z() ) );
    REQUIRE( ch.vehicle_list.count( veh ) == 1 );
    vehicle stray( vproto_id( "bicycle" ) );
    ch.vehicle_list.clear();
    ch.vehicle_list.insert( &stray );
    ch.zone_vehicles.insert( &stray );
    here.dirty_vehicle_list.insert( &stray );
    here.resync_vehicle_lists_from_submaps();
    CHECK( ch.vehicle_list.count( veh ) == 1 );
    CHECK( ch.vehicle_list.count( &stray ) == 0 );
    CHECK( ch.zone_vehicles.count( &stray ) == 0 );
    CHECK( here.dirty_vehicle_list.count( &stray ) == 0 );
    // and nothing else is listed: one vehicle on the map, one in the caches
    size_t listed = 0;
    for( int z = -OVERMAP_DEPTH; z <= OVERMAP_HEIGHT; z++ ) {
        listed += here.get_cache_ref( z ).vehicle_list.size();
    }
    CHECK( listed == 1 );
    here.dirty_vehicle_list.erase( &stray );
    sgn_leave_world();
}

// src/do_turn.cpp: game::do_turn() runs without a gamemode (tests never call start_game, so
// there is none); upstream dereferenced it on every turn after the first.
TEST_CASE( "saigon_engine_do_turn_without_gamemode", "[saigon][saigon_engine]" )
{
    if( !sgn_quick_world() ) {
        WARN( "saigon_2000s or its real map is not present; skipping" );
        return;
    }
    // a turn may autosave, and a saved overmap would shadow the real map's files later in the run
    override_option autosave( "AUTOSAVE", "false" );
    const time_point before = calendar::turn;
    // the first call may take the new-game branch, which does not advance the clock
    for( int i = 0; i < 2; i++ ) {
        get_avatar().set_moves( 0 );    // no input: the player just waits
        g->do_turn();
    }
    CHECK( calendar::turn > before );
    sgn_leave_world();
}

// src/weather_gen.cpp: a monthly curve must have exactly 12 values.  The positive control
// proves the rejection comes from the curve, not from a missing mandatory field.
TEST_CASE( "saigon_engine_monthly_curve_needs_12_values", "[saigon][saigon_engine]" )
{
    const std::string head = R"({ "base_temperature": 27, "base_humidity": 75, "base_pressure": 1010,)"
                             R"( "base_wind": 3, "monthly_temperature": [)";
    const std::string twelve = "26,27,28,29,29,28,28,28,27,27,27,26";
    const std::string eleven = "26,27,28,29,29,28,28,28,27,27,27";
    {
        JsonObject jo = json_loader::from_string( head + twelve + "] }" ).get_object();
        jo.allow_omitted_members();
        weather_generator wg;
        wg.load( jo, "" );
        REQUIRE( wg.monthly_temperature );
        CHECK( ( *wg.monthly_temperature )[3] == 29 );
    }
    {
        JsonObject jo = json_loader::from_string( head + eleven + "] }" ).get_object();
        jo.allow_omitted_members();
        weather_generator wg;
        CHECK_THROWS( wg.load( jo, "" ) );
    }
}

// src/savegame.cpp: a final hand-made overmap records the roads that leave it as inter-city road
// exits (connections_out), so the generated countryside joins its roads to them.  The realmap
// tests check the countryside's region; nothing asserted the exits.  Overmap (3, 0) is the real
// map's east edge, with roads leaving it.
TEST_CASE( "saigon_engine_realmap_edge_road_exits", "[saigon][saigon_engine]" )
{
    if( !sgn_quick_world() ) {
        WARN( "saigon_2000s or its real map is not present; skipping" );
        return;
    }
    overmap &om = overmap_buffer.get( point_abs_om( 3, 0 ) );
    REQUIRE( om.pregenerated_final );
    int exits = 0;
    for( const auto &conn : om.connections_out ) {
        for( const tripoint_om_omt &p : conn.second ) {
            CAPTURE( p.to_string() );
            CHECK( om.ter( p ).id().str().rfind( "road", 0 ) == 0 );
            // on the overmap's edge, and the road really leaves across that edge
            bool leaves = false;
            leaves = leaves || ( p.x() == 0 && om.ter( p )->has_connection( om_direction::type::west ) );
            leaves = leaves || ( p.x() == OMAPX - 1 &&
                                 om.ter( p )->has_connection( om_direction::type::east ) );
            leaves = leaves || ( p.y() == 0 && om.ter( p )->has_connection( om_direction::type::north ) );
            leaves = leaves || ( p.y() == OMAPY - 1 &&
                                 om.ter( p )->has_connection( om_direction::type::south ) );
            CHECK( leaves );
            exits++;
        }
    }
    CHECK( exits > 0 );
    sgn_leave_world();
}

// newcharacter.cpp (PT1): character_creator_callback::select writes the active menu's index into
// the current tab's slot.  When the tab changed while another tab's menu was still being queried
// (the trait-variant menu is one way), the skills slot got a trait index and draw_skills read
// sorted_skills past its end: the playtest's SIGSEGV in character creation.  The getters now
// treat an index past the list as nothing selected.
TEST_CASE( "saigon_engine_creator_selection_out_of_range", "[saigon][saigon_engine]" )
{
    character_creator_uistate ui;
    ui.selected_scenario_index = 3;
    ui.selected_profession_index = 3;
    ui.selected_hobby_index = 3;
    ui.selected_trait_index = 3;
    ui.selected_skill_index = 80;
    CHECK( ui.get_selected_scenario() == nullptr );
    CHECK( ui.get_selected_profession().is_null() );
    CHECK( ui.get_selected_hobby().is_null() );
    CHECK( ui.get_selected_trait().is_null() );
    CHECK( ui.get_selected_skill().is_null() );
    // and an index inside the list still selects
    ui.recalc_skill_list();
    REQUIRE( !ui.sorted_skills.empty() );
    ui.selected_skill_index = 0;
    CHECK( ui.get_selected_skill() == ui.sorted_skills[0]->ident() );
}
