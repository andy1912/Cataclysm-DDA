#include <map>
#include <memory>
#include <string>
#include <vector>

#include "cata_catch.h"
#include "cata_utility.h"
#include "filesystem.h"
#include "game.h"
#include "json.h"
#include "path_info.h"
#include "coordinates.h"
#include "global_vars.h"
#include "map_helpers.h"
#include "math_parser_diag_value.h"
#include "omdata.h"
#include "overmap.h"
#include "overmapbuffer.h"
#include "player_helpers.h"
#include "start_location.h"
#include "worldfactory.h"
#include "type_id.h"

// Saigon 2000s mod: pregenerated ("real-map") overmaps (doc/saigon/REALMAP_PLAN.md, R1).
// Loads the fixture data/mods/saigon_2000s/realmap_test/overmap_40_40.omap.gz (written by
// tools/saigon/realmap/make_test_fixture.py): a field with one road and a five-storey shophouse
// column.  Checks that every z level of the file loads, that the "final" flag keeps generate()
// from adding procedural cities, rivers or forests, and that the world's choice (the global set
// by game::start_game from the scenario) is what selects the map.  Without that choice the
// Vietmap megacity is generated as before (covered by saigon_cities_use_shophouses).

TEST_CASE( "saigon_realmap_loads_every_layer", "[overmap][saigon]" )
{
    if( !oter_str_id( "sgn_nh_solo_z5_south" ).is_valid() ) {
        WARN( "saigon_2000s is not loaded; skipping" );
        return;
    }
    clear_overmaps();
    const cata_path fixture = PATH_INFO::moddir() / "saigon_2000s/realmap_test/overmap_40_40.omap.gz";
    REQUIRE( file_exist( fixture.get_unrelative_path() ) );
    get_globals().set_global_value( "overmap_pregenerated_path", diag_value( std::string( "saigon_2000s/realmap_test" ) ) );
    // overmap (40, 40): no other test saves it, and a saved overmap would load before the file
    overmap &om = overmap_buffer.get( point_abs_om( 40, 40 ) );
    for( int z = 0; z <= 5; z++ ) {
        CAPTURE( z );
        CHECK( om.ter( tripoint_om_omt( 90, 89, z ) ).id().str() == "sgn_nh_solo_z" + std::to_string( z ) + "_south" );
    }
    CHECK( om.ter( tripoint_om_omt( 85, 90, 0 ) ).id().str().rfind( "road", 0 ) == 0 );
    // "final": no procedural city, river, lake or forest was added on top of the file
    int other = 0;
    std::string first_other;
    for( int x = 0; x < OMAPX; x++ ) {
        for( int y = 0; y < OMAPY; y++ ) {
            const std::string id = om.ter( tripoint_om_omt( x, y, 0 ) ).id().str();
            const bool ours = id == "field" || id.rfind( "road", 0 ) == 0 || id.rfind( "sgn_nh_solo", 0 ) == 0;
            if( !ours ) {
                other++;
                if( first_other.empty() ) {
                    first_other = id;
                }
            }
        }
    }
    CAPTURE( other, first_other );
    CHECK( other == 0 );
    get_globals().remove_global_value( "overmap_pregenerated_path" );
    clear_overmaps();
}

// The loader change (every object in the file, not only the first) must keep reading dda's own
// single-layer pregenerated maps, which have no "z" and no "final": the MA mod's map.  The loader
// is checked on its own (generate() would go on to add dda's ocean east of its shoreline, which the
// MA mod switches off in its region settings): every tile must match the file, and a file without
// "final" must leave the overmap open to generation.
TEST_CASE( "saigon_realmap_reads_dda_single_layer_maps", "[overmap][saigon]" )
{
    const cata_path file = PATH_INFO::moddir() / "MA/MA_overmap/overmap_45_18.omap.gz";
    if( !file_exist( file.get_unrelative_path() ) ) {
        WARN( "dda's MA map is not present; skipping" );
        return;
    }
    std::vector<std::string> expected;
    REQUIRE( read_from_file_optional_json( file, [&expected]( const JsonValue & jv ) {
        JsonArray ja = jv.get_array();
        JsonObject jo = ja.next_object();
        jo.allow_omitted_members();
        for( JsonArray run : jo.get_array( "layers" ) ) {
            const std::string id = run.next_string();
            expected.insert( expected.end(), run.next_int(), id );
        }
    } ) );
    REQUIRE( expected.size() == static_cast<size_t>( OMAPX * OMAPY ) );
    clear_overmaps();
    // far too big for the stack
    std::unique_ptr<overmap> omp = std::make_unique<overmap>( point_abs_om( 45, 18 ) );
    overmap &om = *omp;
    REQUIRE( read_from_file_optional_json( file, [&om, &file]( const JsonValue & jv ) {
        om.unserialize_omap( jv, file );
    } ) );
    CHECK_FALSE( om.pregenerated_final );
    // dda's own pass after loading re-derives forest edges and lake shores from their neighbours, so
    // compare families: every field stays a field, forest stays forest, water stays water
    const auto family = []( const std::string & id ) {
        return id.rfind( "forest", 0 ) == 0 ? std::string( "forest" ) :
               id.rfind( "lake", 0 ) == 0 ? std::string( "lake" ) : id;
    };
    int same = 0;
    for( int y = 0; y < OMAPY; y++ ) {
        for( int x = 0; x < OMAPX; x++ ) {
            same += family( om.ter( tripoint_om_omt( x, y, 0 ) ).id().str() ) == family( expected[y * OMAPX + x] );
        }
    }
    CAPTURE( same );
    CHECK( same == OMAPX * OMAPY );
}

// The real 2009 map itself (data/mods/saigon_2000s/realmap_2009, written by
// tools/saigon/realmap/write_omaps.py from OpenStreetMap). Overmap (0, 0) is central Saigon
// (District 1 west, 3, 10): it loads with its streets, river, shophouses and bridges; the game
// adds the bridge decks; Bến Thành stands on its site; a new game's start location is found there;
// and the map generates without errors at Bến Thành and on a bridge over the Saigon River.
TEST_CASE( "saigon_realmap_2009_loads", "[saigon]" )
{
    const cata_path file = PATH_INFO::moddir() / "saigon_2000s/realmap_2009/overmap_0_0.omap.gz";
    if( !oter_str_id( "sgn_nh_solo_z5_south" ).is_valid() || !file_exist( file.get_unrelative_path() ) ) {
        WARN( "saigon_2000s or its real map is not present; skipping" );
        return;
    }
    // an overmap (0, 0) saved earlier in this test run (any test whose turns autosave) would be
    // loaded instead of the pregenerated file
    for( const cata_path &saved : {
             PATH_INFO::current_dimension_save_path() / zzip_overmap_directory /
             ( overmapbuffer::terrain_filename( point_abs_om() ) + std::string( zzip_suffix ) ),
             PATH_INFO::current_dimension_save_path() / overmapbuffer::terrain_filename( point_abs_om() )
         } ) {
        if( file_exist( saved ) ) {
            remove_file( saved.get_unrelative_path().u8string() );
        }
    }
    // choose the map first: clearing places the player at the origin, which loads overmap (0, 0)
    get_globals().set_global_value( "overmap_pregenerated_path", diag_value( std::string( "saigon_2000s/realmap_2009" ) ) );
    clear_avatar();
    clear_map();
    clear_overmaps();
    overmap &om = overmap_buffer.get( point_abs_om() );
    std::map<std::string, int> count;
    tripoint_om_omt bridge = tripoint_om_omt::invalid;
    for( int x = 0; x < OMAPX; x++ ) {
        for( int y = 0; y < OMAPY; y++ ) {
            const std::string id = om.ter( tripoint_om_omt( x, y, 0 ) ).id().str();
            const std::string kind = id.rfind( "road", 0 ) == 0 ? "road" : id.rfind( "bridge", 0 ) == 0 ? "bridge" :
                                     id.rfind( "lake", 0 ) == 0 ? "water" : id.rfind( "sgn_nh_solo", 0 ) == 0 ? "nha_ong" :
                                     id.rfind( "sgn_hem", 0 ) == 0 ? "hem" : id.rfind( "sgn_chua", 0 ) == 0 ? "pagoda" :
                                     id.rfind( "sgn_truong", 0 ) == 0 ? "school" : id.rfind( "sgn_pl_cay_xang", 0 ) == 0 ? "fuel" :
                                     id.rfind( "sgn_cho", 0 ) == 0 ? "market" : id;
            count[kind]++;
            if( kind == "bridge" && bridge.is_invalid() ) {
                bridge = tripoint_om_omt( x, y, 0 );
            }
        }
    }
    int decks = 0;
    for( int x = 0; x < OMAPX; x++ ) {
        for( int y = 0; y < OMAPY; y++ ) {
            decks += om.ter( tripoint_om_omt( x, y, 1 ) ).id().str().rfind( "bridge_road", 0 ) == 0;
        }
    }
    CAPTURE( count["road"], count["bridge"], count["water"], count["nha_ong"], count["hem"], count["field"], decks );
    CHECK( count["road"] > 3000 );
    CHECK( count["nha_ong"] > 3000 );
    CHECK( count["water"] > 200 );
    CHECK( count["bridge"] > 5 );
    CHECK( decks > 5 );
    // places from the data (R4): central Saigon has its pagodas, schools, petrol stations, markets
    CAPTURE( count["pagoda"], count["school"], count["fuel"], count["market"] );
    CHECK( count["pagoda"] >= 10 );
    CHECK( count["school"] >= 20 );
    CHECK( count["fuel"] >= 10 );
    CHECK( count["market"] >= 4 * 5 );
    // the 2009 outskirts (R3): overmap (2, 0), Quận 2 east, is mostly fields
    overmap &east = overmap_buffer.get( point_abs_om( 2, 0 ) );
    int fields = 0;
    for( int x = 0; x < OMAPX; x++ ) {
        for( int y = 0; y < OMAPY; y++ ) {
            fields += east.ter( tripoint_om_omt( x, y, 0 ) ).id().str() == "field";
        }
    }
    CAPTURE( fields );
    CHECK( fields > OMAPX * OMAPY / 3 );
    // Bến Thành (10.7725 N, 106.6980 E) is tile (158, 161) of overmap (0, 0): the market stands
    // within 5 tiles (120 m) of it (tools/saigon/realmap/landmarks_2009.json)
    const tripoint_abs_omt ben_thanh( 158, 161, 0 );
    int market = 0;
    for( int dx = -5; dx <= 5; dx++ ) {
        for( int dy = -5; dy <= 5; dy++ ) {
            market += overmap_buffer.ter( ben_thanh + point( dx, dy ) ).id().str().rfind( "sgn_lm_ben_thanh", 0 ) == 0;
        }
    }
    CHECK( market == 9 );
    // a new game looks for its start from the world origin outwards: it starts in central Saigon
    const tripoint_abs_omt start = start_location_id( "sgn_sloc_nha_ong" )->find_player_initial_location(
                                       point_abs_om() ).first;
    CAPTURE( start.to_string() );
    CHECK( project_to<coords::om>( start.xy() ) == point_abs_om() );
    g->place_player_overmap( ben_thanh );
    REQUIRE_FALSE( bridge.is_invalid() );
    g->place_player_overmap( project_combine( point_abs_om(), bridge ) );
    get_globals().remove_global_value( "overmap_pregenerated_path" );
    clear_avatar();
    clear_map();
    clear_overmaps();
}
