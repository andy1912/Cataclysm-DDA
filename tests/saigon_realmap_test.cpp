#include <algorithm>
#include <array>
#include <chrono>
#include <filesystem>
#include <functional>
#include <initializer_list>
#include <map>
#include <set>
#include <memory>
#include <cstddef>
#include <string>
#include <string_view>
#include <unordered_map>
#include <utility>
#include <vector>

#include "achievement.h"
#include "avatar.h"
#include "cata_catch.h"
#include "cata_path.h"
#include "character_id.h"
#include "city.h"
#include "cata_utility.h"
#include "filesystem.h"
#include "flexbuffer_json.h"
#include "game.h"
#include "map_scale_constants.h"
#include "path_info.h"
#include "coordinates.h"
#include "global_vars.h"
#include "map.h"
#include "map_helpers.h"
#include "mapbuffer.h"
#include "math_parser_diag_value.h"
#include "omdata.h"
#include "overmap.h"
#include "overmapbuffer.h"
#include "pathfinding.h"
#include "point.h"
#include "player_helpers.h"
#include "scenario.h"
#include "simple_pathfinding.h"
#include "start_location.h"
#include "stats_tracker.h"
#include "worldfactory.h"
#include "type_id.h"

static const oter_str_id oter_sgn_ben_pha_north( "sgn_ben_pha_north" );
static const oter_str_id oter_sgn_hem_block_north( "sgn_hem_block_north" );
static const oter_str_id oter_sgn_nh_solo_z5_south( "sgn_nh_solo_z5_south" );
static const region_settings_id region_settings_sgn_saigon_delta( "sgn_saigon_delta" );
static const start_location_id start_location_sgn_sloc_nha_ong( "sgn_sloc_nha_ong" );
static const string_id<scenario> scenario_sgn_saigon_2009( "sgn_saigon_2009" );

// Saigon 2000s mod: pregenerated ("real-map") overmaps (doc/saigon/REALMAP_PLAN.md, R1).
// Loads the fixture data/mods/saigon_2000s/realmap_test/overmap_40_40.omap.gz (written by
// tools/saigon/realmap/make_test_fixture.py): a field with one road and a five-storey shophouse
// column.  Checks that every z level of the file loads, that the "final" flag keeps generate()
// from adding procedural cities, rivers or forests, and that the world's choice (the global set
// by game::start_game from the scenario) is what selects the map.  Without that choice the
// Vietmap megacity is generated as before (covered by saigon_cities_use_shophouses).

TEST_CASE( "saigon_realmap_loads_every_layer", "[overmap][saigon]" )
{
    if( !oter_sgn_nh_solo_z5_south.is_valid() ) {
        WARN( "saigon_2000s is not loaded; skipping" );
        return;
    }
    clear_overmaps();
    const cata_path fixture = PATH_INFO::moddir() / "saigon_2000s/realmap_test/overmap_40_40.omap.gz";
    REQUIRE( file_exist( fixture.get_unrelative_path() ) );
    get_globals().set_global_value( "overmap_pregenerated_path",
                                    diag_value( std::string( "saigon_2000s/realmap_test" ) ) );
    // overmap (40, 40): no other test saves it, and a saved overmap would load before the file
    overmap &om = overmap_buffer.get( point_abs_om( 40, 40 ) );
    for( int z = 0; z <= 5; z++ ) {
        CAPTURE( z );
        CHECK( om.ter( tripoint_om_omt( 90, 89,
                                        z ) ).id().str() == "sgn_nh_solo_z" + std::to_string( z ) + "_south" );
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
            same += family( om.ter( tripoint_om_omt( x, y,
                                    0 ) ).id().str() ) == family( expected[y * OMAPX + x] );
        }
    }
    CAPTURE( same );
    CHECK( same == OMAPX * OMAPY );
}

// The real 2009 map itself (data/mods/saigon_2000s/realmap_2009, written by
// tools/saigon/realmap/write_omaps.py from OpenStreetMap). Overmap (0, 0) is central Saigon
// (District 1 west, 3, 10): it loads with its streets, river, shophouses and bridges; the game
// adds the bridge decks; Bến Thành stands on its site; a new game's start location is found there;
// and the map generates without errors at Tân Sơn Nhất's terminal and runway, at Bến Thành, on a
// bridge over the Saigon River and on the railway.
// An overmap saved earlier in this test run (any test whose turns autosave) would be loaded
// instead of the pregenerated file.
static void remove_saved_overmap( const point_abs_om &om )
{
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

static void remove_saved_origin_overmap()
{
    remove_saved_overmap( point_abs_om() );
}

// Every overmap a 2009 game touches - the real map (-1..3 x -2..1) and the countryside a ring
// around it - so a new world never reloads an earlier game's saved overmap and its people.
static void remove_saved_realmap_overmaps()
{
    for( int x = -3; x <= 5; x++ ) {
        for( int y = -4; y <= 3; y++ ) {
            remove_saved_overmap( point_abs_om( x, y ) );
        }
    }
}

TEST_CASE( "saigon_realmap_2009_loads", "[saigon]" )
{
    const cata_path file = PATH_INFO::moddir() / "saigon_2000s/realmap_2009/overmap_0_0.omap.gz";
    if( !oter_sgn_nh_solo_z5_south.is_valid() ||
        !file_exist( file.get_unrelative_path() ) ) {
        WARN( "saigon_2000s or its real map is not present; skipping" );
        return;
    }
    // an overmap (0, 0) saved earlier in this test run (any test whose turns autosave) would be
    // loaded instead of the pregenerated file
    remove_saved_origin_overmap();
    // choose the map first: clearing places the player at the origin, which loads overmap (0, 0)
    get_globals().set_global_value( "overmap_pregenerated_path",
                                    diag_value( std::string( "saigon_2000s/realmap_2009" ) ) );
    clear_avatar();
    clear_map();
    clear_overmaps();
    overmap &om = overmap_buffer.get( point_abs_om() );
    std::map<std::string, int> count;
    tripoint_om_omt bridge = tripoint_om_omt::invalid;
    tripoint_om_omt rail = tripoint_om_omt::invalid;
    for( int x = 0; x < OMAPX; x++ ) {
        for( int y = 0; y < OMAPY; y++ ) {
            const std::string id = om.ter( tripoint_om_omt( x, y, 0 ) ).id().str();
            const std::string kind = id.rfind( "road", 0 ) == 0 ? "road" : id.rfind( "bridge",
                                     0 ) == 0 ? "bridge" :
                                     id.rfind( "lake", 0 ) == 0 ? "water" : id.rfind( "sgn_nh_solo", 0 ) == 0 ? "nha_ong" :
                                     id.rfind( "sgn_hem", 0 ) == 0 ? "hem" : id.rfind( "sgn_chua", 0 ) == 0 ? "pagoda" :
                                     id.rfind( "sgn_truong", 0 ) == 0 ? "school" : id.rfind( "sgn_pl_cay_xang", 0 ) == 0 ? "fuel" :
                                     id.rfind( "sgn_cho", 0 ) == 0 ? "market" : id.rfind( "sgn_duong_sat", 0 ) == 0 ? "rail" : id;
            count[kind]++;
            if( kind == "bridge" && bridge.is_invalid() ) {
                bridge = tripoint_om_omt( x, y, 0 );
            }
            if( kind == "rail" && rail.is_invalid() ) {
                rail = tripoint_om_omt( x, y, 0 );
            }
        }
    }
    int decks = 0;
    for( int x = 0; x < OMAPX; x++ ) {
        for( int y = 0; y < OMAPY; y++ ) {
            decks += om.ter( tripoint_om_omt( x, y, 1 ) ).id().str().rfind( "bridge_road", 0 ) == 0;
        }
    }
    CAPTURE( count["road"], count["bridge"], count["water"], count["nha_ong"], count["hem"],
             count["field"], decks );
    CHECK( count["road"] > 3000 );
    CHECK( count["nha_ong"] > 3000 );
    CHECK( count["water"] > 200 );
    // canal crossings of 1-2 tiles are culverts; only the longer crossings are bridges with decks
    CHECK( count["bridge"] > 0 );
    CHECK( decks > 0 );
    // places from the data (R4): central Saigon has its pagodas, schools, petrol stations, markets
    CAPTURE( count["pagoda"], count["school"], count["fuel"], count["market"] );
    CHECK( count["pagoda"] >= 10 );
    CHECK( count["school"] >= 20 );
    CHECK( count["fuel"] >= 10 );
    CHECK( count["market"] >= 4 * 5 );
    // the railway runs through to Ga Sài Gòn
    CHECK( count["rail"] > 20 );
    // W3: district police headquarters and army guard posts from OpenStreetMap (place_places.py);
    // each north-west ground piece has its upper floor above it
    int police_hq = 0;
    int army_posts = 0;
    for( int x = 0; x < OMAPX; x++ ) {
        for( int y = 0; y < OMAPY; y++ ) {
            const std::string id = om.ter( tripoint_om_omt( x, y, 0 ) ).id().str();
            for( const std::string site : {
                     "sgn_pa_cong_an_quan_00_", "sgn_pa_don_quan_su_00_"
                 } ) {
                if( id.rfind( site, 0 ) == 0 ) {
                    ( site == "sgn_pa_cong_an_quan_00_" ? police_hq : army_posts )++;
                    CAPTURE( id );
                    CHECK( om.ter( tripoint_om_omt( x, y, 1 ) ).id().str().rfind( site + "z1_", 0 ) == 0 );
                }
            }
        }
    }
    CAPTURE( police_hq, army_posts );
    CHECK( police_hq >= 1 );
    CHECK( army_posts >= 1 );
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
    // the 2009 districts are the overmap's cities: their names on the map, their hordes
    std::set<std::string> names;
    for( const city &c : om.cities ) {
        names.insert( c.name );
    }
    CHECK( names.count( "Quận 1" ) == 1 );
    CHECK( names.count( "Quận 3" ) == 1 );
    // Bến Thành (10.7725 N, 106.6980 E) is tile (158, 161) of overmap (0, 0): the market stands
    // within 5 tiles (120 m) of it (tools/saigon/realmap/landmarks_2009.json)
    const tripoint_abs_omt ben_thanh( 158, 161, 0 );
    int market = 0;
    for( int dx = -5; dx <= 5; dx++ ) {
        for( int dy = -5; dy <= 5; dy++ ) {
            market += overmap_buffer.ter( ben_thanh + point( dx, dy ) ).id().str().rfind( "sgn_lm_ben_thanh",
                      0 ) == 0;
        }
    }
    CHECK( market == 9 );
    // a new game looks for its start from the world origin outwards: it starts in central Saigon
    const tripoint_abs_omt start =
        start_location_sgn_sloc_nha_ong->find_player_initial_location(
            point_abs_om() ).first;
    CAPTURE( start.to_string() );
    CHECK( project_to<coords::om>( start.xy() ) == point_abs_om() );
    // the 2009 scenario's other starts are on the real map too: an inner hẻm, Ga Sài Gòn's hall,
    // Tân Sơn Nhất's departures hall
    for( const char *loc : {
             "sgn_sloc_hem", "sgn_sloc_ga_sai_gon", "sgn_sloc_san_bay"
         } ) {
        CAPTURE( loc );
        CHECK_FALSE( start_location_id( loc )->find_player_initial_location(
                         point_abs_om() ).first.is_invalid() );
    }
    // and it reveals a wide neighbourhood at the start (a getter that returned bool cut every
    // scenario's radius to 1)
    CHECK( scenario_sgn_saigon_2009->get_distance_initial_visibility() == 40 );
    // and character creation offers it: the mod's scenario whitelist hid every scenario it did not
    // name, and it named only Vietmap's
    for( const char *scen : {
             "sgn_saigon_2004", "sgn_saigon_2009"
         } ) {
        CAPTURE( scen );
        CHECK_FALSE( string_id<scenario>( scen )->scen_is_blacklisted() );
    }
    // Tân Sơn Nhất (overmap (-1, -1)): runways and the terminal (gen_san_bay.py, sgn_lm_san_bay)
    overmap &airport = overmap_buffer.get( point_abs_om( -1, -1 ) );
    int runway = 0;
    tripoint_om_omt terminal = tripoint_om_omt::invalid;
    tripoint_om_omt tarmac = tripoint_om_omt::invalid;
    for( int x = 0; x < OMAPX; x++ ) {
        for( int y = 0; y < OMAPY; y++ ) {
            const std::string id = airport.ter( tripoint_om_omt( x, y, 0 ) ).id().str();
            if( id == "sgn_sb_runway" ) {
                runway++;
                tarmac = tripoint_om_omt( x, y, 0 );
            } else if( id.rfind( "sgn_lm_san_bay", 0 ) == 0 && terminal.is_invalid() ) {
                terminal = tripoint_om_omt( x, y, 0 );
            }
        }
    }
    CAPTURE( runway );
    CHECK( runway > 200 );
    REQUIRE_FALSE( terminal.is_invalid() );
    g->place_player_overmap( project_combine( point_abs_om( -1, -1 ), terminal ) );
    g->place_player_overmap( project_combine( point_abs_om( -1, -1 ), tarmac ) );
    g->place_player_overmap( ben_thanh );
    REQUIRE_FALSE( bridge.is_invalid() );
    g->place_player_overmap( project_combine( point_abs_om(), bridge ) );
    REQUIRE_FALSE( rail.is_invalid() );
    g->place_player_overmap( project_combine( point_abs_om(), rail ) );
    get_globals().remove_global_value( "overmap_pregenerated_path" );
    clear_avatar();
    clear_map();
    clear_overmaps();
}

// R7: beyond the real map's 5 x 4 overmaps the scenario's outside region (sgn_saigon_delta:
// small towns far apart) is generated instead of Vietmap's megacity.
TEST_CASE( "saigon_realmap_2009_countryside", "[saigon]" )
{
    if( !region_settings_sgn_saigon_delta.is_valid() ) {
        WARN( "saigon_2000s is not loaded; skipping" );
        return;
    }
    get_globals().set_global_value( "overmap_pregenerated_path",
                                    diag_value( std::string( "saigon_2000s/realmap_2009" ) ) );
    get_globals().set_global_value( "overmap_outside_region",
                                    diag_value( std::string( "sgn_saigon_delta" ) ) );
    clear_avatar();
    clear_map();
    clear_overmaps();
    CHECK( overmap_buffer.get_overmap_region( tripoint_abs_om( 0, 0, 0 ) ).str() == "sgn_saigon" );
    CHECK( overmap_buffer.get_overmap_region( tripoint_abs_om( 4, 0,
            0 ) ).str() == "sgn_saigon_delta" );
    CHECK( overmap_buffer.get_overmap_region( tripoint_abs_om( -2, -3,
            0 ) ).str() == "sgn_saigon_delta" );
    // east of Thủ Đức: land with a town or two (not dda's water fill for missing files), not
    // wall-to-wall shophouses
    overmap &om = overmap_buffer.get( point_abs_om( 4, 0 ) );
    int town = 0;
    int water = 0;
    for( int x = 0; x < OMAPX; x++ ) {
        for( int y = 0; y < OMAPY; y++ ) {
            const oter_id &t = om.ter( tripoint_om_omt( x, y, 0 ) );
            const std::string id = t.id().str();
            town += id.rfind( "sgn_nh_", 0 ) == 0 || id.rfind( "sgn_hem", 0 ) == 0;
            water += t->is_water();
        }
    }
    CAPTURE( town, water );
    CHECK( town > 0 );
    CHECK( town < OMAPX * OMAPY / 5 );
    CHECK( water < OMAPX * OMAPY / 2 );
    get_globals().remove_global_value( "overmap_pregenerated_path" );
    get_globals().remove_global_value( "overmap_outside_region" );
    clear_avatar();
    clear_map();
    clear_overmaps();
}

// Review 2026-10-06: the real map could not be walked.  Every hẻm network was sealed (a hẻm block
// opens its alleys only towards roads, canals and other hẻm blocks, and every street front was a
// shophouse) and most bridges had no ramps (one-tile runs, bends).  This walks, with the game's
// own pathfinding on the generated map, from a street over a bridge to the far bank, and from a
// street through an alley mouth into an inner hẻm block.
static tripoint_bub_ms omt_centre( const tripoint_abs_omt &p )
{
    return get_map().get_bub( project_to<coords::ms>( p ) + point( 12, 12 ) );
}

TEST_CASE( "saigon_realmap_2009_walkable", "[saigon]" )
{
    const cata_path file = PATH_INFO::moddir() / "saigon_2000s/realmap_2009/overmap_0_0.omap.gz";
    if( !oter_sgn_hem_block_north.is_valid() ||
        !file_exist( file.get_unrelative_path() ) ) {
        WARN( "saigon_2000s or its real map is not present; skipping" );
        return;
    }
    get_globals().set_global_value( "overmap_pregenerated_path",
                                    diag_value( std::string( "saigon_2000s/realmap_2009" ) ) );
    clear_avatar();
    clear_map();
    clear_overmaps();
    overmap &om = overmap_buffer.get( point_abs_om() );
    const auto id_at = [&]( const point_om_omt & p ) {
        return om.ter( tripoint_om_omt( p, 0 ) ).id().str();
    };
    const auto starts = [&]( const point_om_omt & p, const std::string & prefix ) {
        return overmap::inbounds( tripoint_om_omt( p, 0 ) ) && id_at( p ).rfind( prefix, 0 ) == 0;
    };
    // a short bridge with a road beyond each end, anywhere on the real map (central Saigon's
    // canal crossings are culverts)
    tripoint_abs_omt bank_a = tripoint_abs_omt::invalid;
    tripoint_abs_omt bank_b = tripoint_abs_omt::invalid;
    for( int ox = -1; ox <= 3 && bank_a.is_invalid(); ox++ ) {
        for( int oy = -2; oy <= 1 && bank_a.is_invalid(); oy++ ) {
            overmap &o = overmap_buffer.get( point_abs_om( ox, oy ) );
            const auto ter_at = [&]( const point_om_omt & p ) {
                return overmap::inbounds( tripoint_om_omt( p, 0 ) ) ? o.ter( tripoint_om_omt( p, 0 ) ).id().str() :
                       std::string();
            };
            for( int x = 6; x < OMAPX - 6 && bank_a.is_invalid(); x++ ) {
                for( int y = 6; y < OMAPY - 6 && bank_a.is_invalid(); y++ ) {
                    // the game turns the end tiles of a run into ramps (bridgehead_ground)
                    const point_om_omt p( x, y );
                    if( ter_at( p ).rfind( "bridgehead_ground", 0 ) != 0 ) {
                        continue;
                    }
                    for( const point &d : {
                             point::east, point::south
                         } ) {
                        point_om_omt end = p + d;
                        while( ter_at( end ).rfind( "bridge_", 0 ) == 0 ) {
                            end += d;
                        }
                        if( end != p + d && ter_at( end ).rfind( "bridgehead_ground", 0 ) == 0 &&
                            ter_at( p - d ).rfind( "road", 0 ) == 0 && ter_at( end + d ).rfind( "road", 0 ) == 0 &&
                            ( end - p ).x() + ( end - p ).y() <= 3 && bank_a.is_invalid() ) {
                            bank_a = project_combine( point_abs_om( ox, oy ), tripoint_om_omt( p - d, 0 ) );
                            bank_b = project_combine( point_abs_om( ox, oy ), tripoint_om_omt( end + d, 0 ) );
                        }
                    }
                }
            }
        }
    }
    REQUIRE_FALSE( bank_a.is_invalid() );
    {
        // the player stands mid-bridge so both banks are inside the reality bubble (it reaches
        // about 66 tiles each way); walk from the near bank's road to the far bank's road
        const point step( ( bank_b.x() > bank_a.x() ) - ( bank_b.x() < bank_a.x() ),
                          ( bank_b.y() > bank_a.y() ) - ( bank_b.y() < bank_a.y() ) );
        g->place_player_overmap( tripoint_abs_omt( ( bank_a.x() + bank_b.x() ) / 2,
                                 ( bank_a.y() + bank_b.y() ) / 2, 0 ) );
        map &here = get_map();
        avatar &u = get_avatar();
        const tripoint_bub_ms from = omt_centre( bank_a ) + step * 10;
        const tripoint_bub_ms to = omt_centre( bank_b ) - step * 10;
        u.setpos( here, from );
        CAPTURE( bank_a.to_string(), bank_b.to_string() );
        const std::vector<tripoint_bub_ms> path = here.route( u, pathfinding_target::point( to ) );
        CHECK_FALSE( path.empty() );
    }
    // an alley mouth: a hẻm block between a road and an inner hẻm block
    tripoint_abs_omt street = tripoint_abs_omt::invalid;
    tripoint_abs_omt inner = tripoint_abs_omt::invalid;
    for( int x = 6; x < OMAPX - 6 && street.is_invalid(); x++ ) {
        for( int y = 6; y < OMAPY - 6 && street.is_invalid(); y++ ) {
            const point_om_omt p( x, y );
            if( !starts( p, "sgn_hem_block" ) ) {
                continue;
            }
            for( const point &d : four_adjacent_offsets ) {
                if( starts( p + d, "road" ) && starts( p - d, "sgn_hem_block" ) ) {
                    street = project_combine( point_abs_om(), tripoint_om_omt( p + d, 0 ) );
                    inner = project_combine( point_abs_om(), tripoint_om_omt( p - d, 0 ) );
                    break;
                }
            }
        }
    }
    REQUIRE_FALSE( street.is_invalid() );
    clear_avatar();                                    // out of the river under the bridge
    g->place_player_overmap( street );
    {
        map &here = get_map();
        avatar &u = get_avatar();
        u.setpos( here, omt_centre( street ) );
        CAPTURE( street.to_string(), inner.to_string() );
        const std::vector<tripoint_bub_ms> path = here.route( u,
                pathfinding_target::point( omt_centre( inner ) ) );
        CHECK_FALSE( path.empty() );
    }
    get_globals().remove_global_value( "overmap_pregenerated_path" );
    clear_avatar();
    clear_map();
    clear_overmaps();
}

// The Thủ Thiêm ferry of 2009 (tools/saigon/realmap/ferries_2009.json): its landing at Bến Bạch
// Đằng is on the map and generates (a dock with river boats) without errors.
TEST_CASE( "saigon_realmap_2009_ferry", "[saigon]" )
{
    const cata_path file = PATH_INFO::moddir() / "saigon_2000s/realmap_2009/overmap_1_0.omap.gz";
    if( !oter_sgn_ben_pha_north.is_valid() || !file_exist( file.get_unrelative_path() ) ) {
        WARN( "saigon_2000s or its real map is not present; skipping" );
        return;
    }
    get_globals().set_global_value( "overmap_pregenerated_path",
                                    diag_value( std::string( "saigon_2000s/realmap_2009" ) ) );
    clear_avatar();
    clear_map();
    clear_overmaps();
    overmap &om = overmap_buffer.get( point_abs_om( 1, 0 ) );
    tripoint_om_omt dock = tripoint_om_omt::invalid;
    for( int x = 0; x < OMAPX && dock.is_invalid(); x++ ) {
        for( int y = 0; y < OMAPY && dock.is_invalid(); y++ ) {
            if( om.ter( tripoint_om_omt( x, y, 0 ) ).id().str().rfind( "sgn_ben_pha", 0 ) == 0 ) {
                dock = tripoint_om_omt( x, y, 0 );
            }
        }
    }
    REQUIRE_FALSE( dock.is_invalid() );
    g->place_player_overmap( project_combine( point_abs_om( 1, 0 ), dock ) );
    get_globals().remove_global_value( "overmap_pregenerated_path" );
    clear_avatar();
    clear_map();
    clear_overmaps();
}

// Driving across the 2009 city: the game's own overmap travel (as auto-travel and autodrive use
// it, roads only) finds a route from Bến Thành to each of these, including across the Saigon
// River (Thủ Đức, Thanh Đa, Quận 7) and the canals (Chợ Lớn, Gò Vấp).
TEST_CASE( "saigon_realmap_2009_routes", "[saigon]" )
{
    const cata_path file = PATH_INFO::moddir() / "saigon_2000s/realmap_2009/overmap_0_0.omap.gz";
    if( !oter_sgn_hem_block_north.is_valid() ||
        !file_exist( file.get_unrelative_path() ) ) {
        WARN( "saigon_2000s or its real map is not present; skipping" );
        return;
    }
    get_globals().set_global_value( "overmap_pregenerated_path",
                                    diag_value( std::string( "saigon_2000s/realmap_2009" ) ) );
    get_globals().set_global_value( "overmap_outside_region",
                                    diag_value( std::string( "sgn_saigon_delta" ) ) );
    clear_avatar();
    clear_map();
    clear_overmaps();
    // the road tile nearest a place (absolute overmap tiles, from its real coordinates)
    const auto road_near = []( const point_abs_omt & p ) {
        for( int r = 0; r <= 8; r++ ) {
            for( int dx = -r; dx <= r; dx++ ) {
                for( int dy = -r; dy <= r; dy++ ) {
                    const tripoint_abs_omt q( p + point( dx, dy ), 0 );
                    if( overmap_buffer.ter( q ).id().str().rfind( "road", 0 ) == 0 ) {
                        return q;
                    }
                }
            }
        }
        return tripoint_abs_omt::invalid;
    };
    // overmap travel only routes through overmaps that exist, as in a game the city has been
    // generated as the player went: load the whole real map first
    for( int ox = -1; ox <= 3; ox++ ) {
        for( int oy = -2; oy <= 1; oy++ ) {
            overmap_buffer.get( point_abs_om( ox, oy ) );
        }
    }
    overmap_path_params params = overmap_path_params::for_land_vehicle( 0.0f, false, false );
    params.only_known_by_player = false;
    params.avoid_danger = false;
    const tripoint_abs_omt from = road_near( point_abs_omt( 158, 161 ) );   // Bến Thành
    REQUIRE_FALSE( from.is_invalid() );
    const std::vector<std::pair<std::string, point_abs_omt>> places = {
        { "Ga Sài Gòn", point_abs_omt( 62, 116 ) },
        { "Tân Sơn Nhất", point_abs_omt( -2, -40 ) },        // the 2007 terminal (R-fid: was the apron, 430 m west)
        { "Thảo Cầm Viên", point_abs_omt( 197, 90 ) },
        { "Chợ Lớn", point_abs_omt( -56, 267 ) },
        { "Gò Vấp", point_abs_omt( 9, -144 ) },
        { "Thanh Đa", point_abs_omt( 272, -49 ) },
        { "Chợ Thủ Đức", point_abs_omt( 418, -199 ) },
        { "Phú Mỹ Hưng", point_abs_omt( 249, 330 ) },
    };
    for( const auto &pl : places ) {
        const tripoint_abs_omt to = road_near( pl.second );
        CAPTURE( pl.first, to.to_string() );
        REQUIRE_FALSE( to.is_invalid() );
        const std::chrono::steady_clock::time_point t0 = std::chrono::steady_clock::now();
        const size_t length = overmap_buffer.get_travel_path( from, to, params ).points.size();
        const long long ms = std::chrono::duration_cast<std::chrono::milliseconds>
                             ( std::chrono::steady_clock::now() - t0 ).count();
        CAPTURE( length );
        CHECK( length > 0 );
        WARN( "Bến Thành -> " << pl.first << ": " << length << " overmap tiles by road, planned in " <<
              ms << " ms" );
    }
    get_globals().remove_global_value( "overmap_pregenerated_path" );
    get_globals().remove_global_value( "overmap_outside_region" );
    clear_avatar();
    clear_map();
    clear_overmaps();
}

// A2: the way a player reaches the real map.  Character creation picks "Sài Gòn, 2009" and a
// start; "New game" runs game::start_game, which fixes the world's map from the scenario, finds
// the start, builds the reality bubble and places the player.  The other real-map tests set the
// map themselves, and the QA load opens a saved game, so a break anywhere on this path (the
// scenario hidden from the picker, its map choice dropped, a start that can't be found) went
// unseen until a player tried it.
TEST_CASE( "saigon_new_game_realmap_2009", "[saigon]" )
{
    const cata_path file = PATH_INFO::moddir() / "saigon_2000s/realmap_2009/overmap_0_0.omap.gz";
    if( !scenario_sgn_saigon_2009.is_valid() || !file_exist( file.get_unrelative_path() ) ) {
        WARN( "saigon_2000s or its real map is not present; skipping" );
        return;
    }
    const scenario *before = get_scenario();
    // offered in character creation (RF4)
    CHECK_FALSE( scenario_sgn_saigon_2009->scen_is_blacklisted() );
    const std::vector<std::string> starts = {
        "sgn_sloc_nha_ong", "sgn_sloc_nha_ong_shuttered", "sgn_sloc_hem", "sgn_sloc_cho",
        "sgn_sloc_ga_sai_gon", "sgn_sloc_san_bay"
    };
    CHECK( scenario_sgn_saigon_2009->start_location_count() == static_cast<int>( starts.size() ) );
    for( const std::string &sloc : starts ) {
        CAPTURE( sloc );
        CHECK( scenario_sgn_saigon_2009->allowed_start( start_location_id( sloc ) ) );
    }
    // a new world: nothing generated or saved, then no map chosen.  The old world is cleared
    // first, while a map is still chosen, so the reset itself generates no procedural overmaps
    clear_npcs();
    clear_creatures();
    clear_avatar();
    clear_map();
    clear_overmaps();
    get_globals().remove_global_value( "overmap_pregenerated_path" );
    get_globals().remove_global_value( "overmap_outside_region" );
    remove_saved_realmap_overmaps();
    overmap_buffer.clear();
    MAPBUFFER.clear();
    get_stats().clear();
    get_achievements().clear();
    set_scenario( &scenario_sgn_saigon_2009.obj() );
    avatar &u = get_avatar();
    // a fresh character has no id yet; start_game gives it one
    u.setID( character_id(), true );
    u.random_start_location = false;
    u.start_location = start_location_id( starts.front() );
    // "New game" (game::start_game runs once per process: player ids, starting scores)
    REQUIRE( start_new_game_for_tests() );
    // the scenario chose the real map for this world
    const diag_value *path = get_globals().maybe_get_global_value( "overmap_pregenerated_path" );
    REQUIRE( path != nullptr );
    CHECK( path->str() == "saigon_2000s/realmap_2009" );
    // and it is the real 2009 city, not a generated one: its districts, and Bến Thành market
    // within 5 tiles of its site (as in saigon_realmap_2009_loads)
    std::set<std::string> districts;
    for( const city &c : overmap_buffer.get( point_abs_om() ).cities ) {
        districts.insert( c.name );
    }
    CHECK( districts.count( "Quận 1" ) == 1 );
    int market = 0;
    for( int dx = -5; dx <= 5; dx++ ) {
        for( int dy = -5; dy <= 5; dy++ ) {
            market += overmap_buffer.ter( tripoint_abs_omt( 158 + dx, 161 + dy, 0 ) ).id().str().rfind(
                          "sgn_lm_ben_thanh", 0 ) == 0;
        }
    }
    CHECK( market == 9 );
    // the player stands on the real map (overmaps -1..3 x -2..1), on a Saigon tile, on their
    // feet; every other start of the scenario, placed the way start_game places one, too.
    // QA2: reloading the bubble at these far-off sites used to crash at random (SIGSEGV in
    // map::do_vehicle_caching): map::loadn freed vehicles wrecked to no parts but left them in
    // the level caches.  This loop is what found it, so it stays.
    for( const std::string &sloc : starts ) {
        CAPTURE( sloc );
        if( sloc != starts.front() ) {
            // the creatures of the last start would be left outside the newly loaded map
            clear_npcs();
            clear_creatures();
            const start_location &start = start_location_id( sloc ).obj();
            const std::pair<tripoint_abs_omt, std::unordered_map<std::string, std::string>> found =
                        start.find_player_initial_location( point_abs_om() );
            REQUIRE_FALSE( found.first.is_invalid() );
            start.set_parameters( found.first, found.second );
            start.prepare_map( found.first );
            tripoint_abs_sm lev = project_to<coords::sm>( found.first );
            lev -= point( HALF_MAPSIZE, HALF_MAPSIZE );
            g->load_map( lev );
            start.place_player( u, found.first );
        }
        const point_abs_om om = project_to<coords::om>( u.pos_abs_omt().xy() );
        CAPTURE( om.to_string() );
        CHECK( om.x() >= -1 );
        CHECK( om.x() <= 3 );
        CHECK( om.y() >= -2 );
        CHECK( om.y() <= 1 );
        CHECK( overmap_buffer.ter( u.pos_abs_omt() ).id().str().rfind( "sgn_", 0 ) == 0 );
        CHECK( get_map().passable( u.pos_bub() ) );
    }
    // back to a default world: drop this one first (a fresh map), then the player and the map
    clear_npcs();
    clear_creatures();
    set_scenario( before );
    get_stats().clear();
    get_achievements().clear();
    get_globals().remove_global_value( "overmap_pregenerated_path" );
    get_globals().remove_global_value( "overmap_outside_region" );
    clear_overmaps();
    clear_avatar();
    clear_map();
}

// R-fid: the 2009 map resembles the real city (doc/saigon/REALMAP_FIDELITY.md).  Absolute overmap
// tiles below are the real sites projected at 24 m per tile, north up (tools/saigon/realmap/
// classify.py latlon_to_tile, minus the area's origin overmap (-1, -2)).
//  - the landmarks stand within 4 tiles (about 100 m) of their real sites, and Chợ Rẫy hospital's
//    site has a hospital;
//  - the main streets are drawn without a break: along each (its OpenStreetMap line simplified to
//    a few points), the road tiles within 3 tiles of the line join the street's two ends (on the
//    first real map Lê Lợi was cut by the 2015 fountain at Nguyễn Huệ, Võ Văn Tần and Nguyễn Hữu
//    Cảnh by a staircase step and by the Vinhomes estate zone);
//  - Bình Thạnh's riverside ward north of the Ba Son bend is city, Thủ Thiêm across the river
//    still marsh, the 2008 Thủ Thiêm bridge is there, Tân Sơn Nhất's 2025 terminal 3 is not.
TEST_CASE( "saigon_realmap_2009_fidelity", "[saigon]" )
{
    const cata_path file = PATH_INFO::moddir() / "saigon_2000s/realmap_2009/overmap_0_0.omap.gz";
    if( !oter_sgn_hem_block_north.is_valid() ||
        !file_exist( file.get_unrelative_path() ) ) {
        WARN( "saigon_2000s or its real map is not present; skipping" );
        return;
    }
    get_globals().set_global_value( "overmap_pregenerated_path",
                                    diag_value( std::string( "saigon_2000s/realmap_2009" ) ) );
    clear_avatar();
    clear_map();
    clear_overmaps();
    for( int ox = -1; ox <= 3; ox++ ) {
        for( int oy = -2; oy <= 1; oy++ ) {
            overmap_buffer.get( point_abs_om( ox, oy ) );
        }
    }
    const auto ter = []( const point_abs_omt & p ) {
        return overmap_buffer.ter( tripoint_abs_omt( p, 0 ) ).id().str();
    };
    const auto starts = []( std::string_view id, std::string_view prefix ) {
        return id.rfind( prefix, 0 ) == 0;
    };
    const auto near_site = [&]( const point_abs_omt & site, std::string_view prefix, int radius ) {
        for( int dx = -radius; dx <= radius; dx++ ) {
            for( int dy = -radius; dy <= radius; dy++ ) {
                if( starts( ter( site + point( dx, dy ) ), prefix ) ) {
                    return true;
                }
            }
        }
        return false;
    };
    const std::vector<std::pair<std::string, point_abs_omt>> landmarks = {
        { "sgn_lm_ben_thanh_", point_abs_omt( 158, 161 ) },      // Chợ Bến Thành
        { "sgn_lm_duc_ba_", point_abs_omt( 163, 127 ) },         // Nhà thờ Đức Bà
        { "sgn_lm_buu_dien_", point_abs_omt( 167, 126 ) },       // Bưu điện
        { "sgn_lm_dinh_doc_lap_", point_abs_omt( 146, 140 ) },   // Dinh Độc Lập
        { "sgn_lm_nha_hat_", point_abs_omt( 182, 141 ) },        // Nhà hát Thành phố
        { "sgn_lm_binh_tay_", point_abs_omt( -56, 267 ) },       // Chợ Bình Tây (Chợ Lớn)
        { "sgn_lm_thien_hau_", point_abs_omt( -10, 248 ) },      // Chùa Bà Thiên Hậu
        { "sgn_lm_ga_sai_gon_", point_abs_omt( 62, 116 ) },      // Ga Sài Gòn
        { "sgn_lm_san_bay_", point_abs_omt( -2, -40 ) },         // Tân Sơn Nhất, 2007 terminal
        { "sgn_lm_thao_cam_vien_", point_abs_omt( 197, 90 ) },   // Thảo Cầm Viên
        { "sgn_lm_dam_sen_", point_abs_omt( -112, 191 ) },       // Đầm Sen
    };
    for( const auto &lm : landmarks ) {
        CAPTURE( lm.first );
        CHECK( near_site( lm.second, lm.first, 4 ) );
    }
    CHECK( near_site( point_abs_omt( -16, 232 ), "sgn_pl_benh_vien",
                      4 ) );   // Bệnh viện Chợ Rẫy
    const std::vector<std::pair<std::string, std::vector<point>>> streets = {
        { "Lê Lợi", { { 163, 163 }, { 162, 161 }, { 180, 144 } } },
        { "Nguyễn Huệ", { { 172, 143 }, { 175, 144 }, { 196, 163 } } },
        { "Đồng Khởi", { { 167, 131 }, { 196, 158 } } },
        { "Hai Bà Trưng", { { 106, 69 }, { 155, 109 }, { 194, 146 } } },
        { "Cách Mạng Tháng Tám", { { -45, 67 }, { 114, 152 }, { 135, 165 } } },
        { "Nam Kỳ Khởi Nghĩa", { { 85, 74 }, { 96, 82 }, { 135, 119 } } },
        { "Võ Văn Tần", { { 91, 176 }, { 147, 115 } } },
        { "Lê Duẩn", { { 151, 134 }, { 190, 93 } } },
        { "Nguyễn Thị Minh Khai", { { 85, 193 }, { 86, 190 }, { 97, 178 }, { 193, 76 } } },
        { "Trần Hưng Đạo", { { -40, 255 }, { -5, 255 }, { 28, 251 }, { 40, 251 }, { 97, 235 }, { 106, 227 }, { 139, 188 }, { 159, 167 } } },
        { "Nguyễn Văn Cừ", { { 84, 194 }, { 88, 208 }, { 99, 235 }, { 109, 247 } } },
        { "Nguyễn Hữu Cảnh", { { 230, 83 }, { 240, 83 }, { 246, 80 }, { 249, 74 }, { 249, 62 }, { 251, 56 }, { 263, 44 }, { 266, 46 }, { 272, 46 }, { 275, 45 }, { 279, 40 } } },
        { "Xô Viết Nghệ Tĩnh", { { 197, 70 }, { 213, 53 }, { 218, 38 }, { 221, -7 }, { 241, -28 }, { 244, -29 } } },
    };
    const auto is_road = [&]( const point_abs_omt & p ) {
        const std::string id = ter( p );
        return starts( id, "road_" ) || starts( id, "bridge" );
    };
    for( const auto &st : streets ) {
        CAPTURE( st.first );
        const std::vector<point> &line = st.second;
        // tiles within 3 of the polyline
        const auto in_corridor = [&]( const point & p ) {
            for( size_t i = 0; i + 1 < line.size(); i++ ) {
                const point a = line[i];
                const point b = line[i + 1];
                const double l2 = ( b - a ).x * static_cast<double>( ( b - a ).x ) + ( b - a ).y *
                                  static_cast<double>( ( b - a ).y );
                double t = l2 == 0 ? 0.0 : ( ( p - a ).x * static_cast<double>( ( b - a ).x ) +
                                             ( p - a ).y * static_cast<double>( ( b - a ).y ) ) / l2;
                t = std::max( 0.0, std::min( 1.0, t ) );
                const double dx = p.x - ( a.x + t * ( b - a ).x );
                const double dy = p.y - ( a.y + t * ( b - a ).y );
                if( dx * dx + dy * dy <= 9.0 ) {
                    return true;
                }
            }
            return false;
        };
        const auto nearest_road = [&]( const point & p ) {
            for( int r = 0; r <= 3; r++ ) {
                for( int dx = -r; dx <= r; dx++ ) {
                    for( int dy = -r; dy <= r; dy++ ) {
                        const point q = p + point( dx, dy );
                        if( in_corridor( q ) && is_road( point_abs_omt( q ) ) ) {
                            return q;
                        }
                    }
                }
            }
            return point::invalid;
        };
        const point from = nearest_road( line.front() );
        const point to = nearest_road( line.back() );
        REQUIRE( from != point::invalid );
        REQUIRE( to != point::invalid );
        std::set<point> seen = { from };
        std::vector<point> todo = { from };
        while( !todo.empty() && !seen.count( to ) ) {
            const point c = todo.back();
            todo.pop_back();
            for( const point &d : four_adjacent_offsets ) {
                const point q = c + d;
                if( !seen.count( q ) && in_corridor( q ) && is_road( point_abs_omt( q ) ) ) {
                    seen.insert( q );
                    todo.push_back( q );
                }
            }
        }
        CHECK( seen.count( to ) == 1 );
    }
    // 2009: Bình Thạnh's ward 22 (Nguyễn Hữu Cảnh) is city, Thủ Thiêm across the river is marsh
    CHECK( is_road( point_abs_omt( 238, 85 ) ) );
    CHECK( starts( ter( point_abs_omt( 242, 80 ) ), "sgn_" ) );
    CHECK( starts( ter( point_abs_omt( 260, 140 ) ), "forest_water" ) );
    // the Thủ Thiêm bridge (2008) crosses the river from ward 22
    CHECK( near_site( point_abs_omt( 247, 100 ), "bridge", 4 ) );
    // Tân Sơn Nhất's terminal 3 (2025) and its roads are not there
    int t3_roads = 0;
    for( int x = 112 - 180; x <= 160 - 180; x++ ) {
        for( int y = 333 - 360; y <= 356 - 360; y++ ) {
            t3_roads += is_road( point_abs_omt( x, y ) );
        }
    }
    CHECK( t3_roads == 0 );
    get_globals().remove_global_value( "overmap_pregenerated_path" );
    clear_avatar();
    clear_map();
    clear_overmaps();
}
