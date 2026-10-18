#include <map>
#include <optional>
#include <set>
#include <string>
#include <utility>
#include <vector>

#include "avatar.h"
#include "avatar_action.h"
#include "calendar.h"
#include "cata_catch.h"
#include "cata_path.h"
#include "cata_utility.h"
#include "character.h"
#include "coordinates.h"
#include "flexbuffer_json.h"
#include "itype.h"
#include "map.h"
#include "map_helpers.h"
#include "map_helpers_tests.h"
#include "player_helpers.h"
#include "point.h"
#include "type_id.h"
#include "units.h"
#include "veh_type.h"
#include "vehicle.h"
#include "vehicle_group.h"
#include "vpart_position.h"
#include "vpart_range.h"

// Saigon 2000s mod, V4 "on the road and the river" (vehicles/, mapgen/roads/road_traffic.json):
// the period vehicles drive, steer and float; engine power and fuel; spawn state; traffic mix.
// Run with: tests/cata_test --mods=dda,saigon_2000s "[saigon][vehicle]"

static const efftype_id effect_blind( "blind" );

static const itype_id itype_gasoline( "gasoline" );

static const proficiency_id proficiency_prof_boat_pilot( "prof_boat_pilot" );
static const proficiency_id proficiency_prof_driver( "prof_driver" );

static const skill_id skill_driving( "driving" );

static const vproto_id vehicle_prototype_sgn_veh_ba_gac_may( "sgn_veh_ba_gac_may" );
static const vproto_id vehicle_prototype_sgn_veh_ghe( "sgn_veh_ghe" );
static const vproto_id vehicle_prototype_sgn_veh_ghe_may( "sgn_veh_ghe_may" );
static const vproto_id vehicle_prototype_sgn_veh_xa_lan( "sgn_veh_xa_lan" );
static const vproto_id vehicle_prototype_sgn_veh_xe_ba_banh( "sgn_veh_xe_ba_banh" );
static const vproto_id vehicle_prototype_sgn_veh_xe_lam( "sgn_veh_xe_lam" );
static const vproto_id vehicle_prototype_sgn_veh_xe_rac( "sgn_veh_xe_rac" );
static const vproto_id vehicle_prototype_sgn_veh_xich_lo( "sgn_veh_xich_lo" );
static const vproto_id vehicle_prototype_sgn_veh_xuong( "sgn_veh_xuong" );

static bool saigon_loaded()
{
    if( !vehicle_prototype_sgn_veh_xich_lo.is_valid() ) {
        WARN( "saigon_2000s is not loaded; skipping" );
        return false;
    }
    return true;
}

static void clear_scene( const ter_id &terrain )
{
    map &here = get_map();
    calendar::turn = calendar::turn_zero + 12_hours;
    clear_creatures();
    clear_npcs();
    clear_avatar();
    Character &you = get_player_character();
    if( you.in_vehicle ) {
        here.unboard_vehicle( you.pos_bub() );
    }
    clear_vehicles();
    you.setpos( here, tripoint_bub_ms( 10, 10, 0 ) );
    you.add_effect( effect_blind, 1_turns, true );
    build_test_map( terrain );
}

// fill every fuel tank with its engines' liquid fuel, and every battery
static void fuel_up( vehicle &veh )
{
    itype_id fuel = itype_gasoline;
    for( const int e : veh.engines ) {
        const itype_id f = veh.part( e ).fuel_current();
        if( !f.is_null() && f->phase == phase_id::LIQUID ) {
            fuel = f;
        }
    }
    for( const vpart_reference &vp : veh.get_all_parts() ) {
        vehicle_part &pt = vp.part();
        if( pt.is_tank() ) {
            pt.ammo_set( fuel );
        } else if( pt.is_battery() ) {
            pt.ammo_set( pt.ammo_current().is_null() ? itype_id( "battery" ) : pt.ammo_current() );
        }
    }
    veh.invalidate_mass();
}

// A skilled driver at the controls, engines running.
static void take_the_wheel( vehicle &veh )
{
    map &here = get_map();
    avatar &you = get_avatar();
    you.set_skill_level( skill_driving, 10 );
    you.add_proficiency( proficiency_prof_driver, true );
    you.add_proficiency( proficiency_prof_boat_pilot, true );
    you.set_str_base( 10 );
    you.set_dex_base( 10 );
    you.set_per_base( 10 );
    std::optional<tripoint_bub_ms> found;
    for( const vpart_reference &vp : veh.get_avail_parts( "CONTROLS" ) ) {
        found = vp.pos_bub( here );
        break;
    }
    REQUIRE( found );
    const tripoint_bub_ms seat = *found;
    you.setpos( here, seat );
    here.board_vehicle( seat, &you );
    REQUIRE( you.in_vehicle );
    you.controlling_vehicle = true;
    veh.engine_on = true;
    for( const int e : veh.engines ) {
        veh.part( e ).enabled = true;
    }
}

struct drive_result {
    int tiles = 0;
    units::angle turned = 0_degrees;
    bool skidded = false;
};

// Accelerate for `turns` turns, then steer right for `turns` turns.  Returns how far the
// vehicle got and how far it turned.
static drive_result drive( vehicle &veh, int turns )
{
    map &here = get_map();
    avatar &you = get_avatar();
    drive_result r;
    const tripoint_abs_ms start = veh.pos_abs();
    const units::angle face0 = veh.face.dir();
    for( int i = 0; i < turns; i++ ) {
        you.set_moves( 100 );
        veh.pldrive( here, you, 0, 1 );
        here.vehmove();
        r.skidded |= veh.skidding;
    }
    for( int i = 0; i < turns; i++ ) {
        you.set_moves( 100 );
        veh.pldrive( here, you, 1, 0 );
        here.vehmove();
        r.skidded |= veh.skidding;
    }
    r.tiles = rl_dist( start, veh.pos_abs() );
    r.turned = veh.face.dir() - face0;
    return r;
}

static void get_out()
{
    map &here = get_map();
    avatar &you = get_avatar();
    if( you.in_vehicle ) {
        here.unboard_vehicle( you.pos_bub() );
    }
    you.controlling_vehicle = false;
    clear_vehicles();
}

TEST_CASE( "saigon_road_vehicles_drive_and_steer", "[saigon][vehicle]" )
{
    if( !saigon_loaded() ) {
        return;
    }
    const time_point start = calendar::turn;
    const std::vector<vproto_id> road = {
        vehicle_prototype_sgn_veh_xich_lo, vehicle_prototype_sgn_veh_xe_ba_banh,
        vehicle_prototype_sgn_veh_xe_lam, vehicle_prototype_sgn_veh_ba_gac_may
    };
    for( const vproto_id &id : road ) {
        CAPTURE( id.str() );
        clear_scene( ter_id( "t_pavement" ) );
        map &here = get_map();
        vehicle *veh = here.add_vehicle( id, tripoint_bub_ms( 60, 60, 0 ), 0_degrees, 100,
                                         veh_spawn_status::UNDAMAGED );
        REQUIRE( veh != nullptr );
        CHECK( veh->sufficient_wheel_config() );
        CHECK( veh->valid_wheel_config( here ) );
        CHECK( veh->steering_effectiveness( here ) > 0.0f );
        fuel_up( *veh );
        take_the_wheel( *veh );
        CHECK( veh->total_power( here ) > 0_W );
        CHECK( veh->safe_ground_velocity( here ) > 0 );
        const drive_result r = drive( *veh, 15 );
        INFO( "travelled " << r.tiles << " tiles, turned " << units::to_degrees( r.turned ) );
        CHECK( r.tiles >= 5 );
        CHECK( r.turned != 0_degrees );
        CHECK_FALSE( r.skidded );
        get_out();
    }
    calendar::turn = start;
}

// The garbage handcart has no engine: it is pushed by hand (grabbed), like dda's wheelbarrow.
TEST_CASE( "saigon_garbage_handcart_pushes", "[saigon][vehicle]" )
{
    if( !saigon_loaded() ) {
        return;
    }
    clear_scene( ter_id( "t_pavement" ) );
    map &here = get_map();
    avatar &you = get_avatar();
    const tripoint_bub_ms you_at( 60, 60, 0 );
    you.setpos( here, you_at );
    // the cart east of the player, its handle (x -1) towards the player
    vehicle *veh = here.add_vehicle( vehicle_prototype_sgn_veh_xe_rac, you_at + point( 2, 0 ),
                                     0_degrees, 0, veh_spawn_status::UNDAMAGED );
    REQUIRE( veh != nullptr );
    CHECK( veh->sufficient_wheel_config() );
    CHECK( veh->valid_wheel_config( here ) );
    CHECK( veh->engines.empty() );
    REQUIRE( here.veh_at( you_at + tripoint::east ) );
    you.grab( object_type::VEHICLE, tripoint_rel_ms::east );
    REQUIRE( you.get_grab_type() == object_type::VEHICLE );
    const tripoint_abs_ms cart0 = veh->pos_abs();
    // push it east three times
    for( int i = 0; i < 3; i++ ) {
        you.set_moves( 100 );
        avatar_action::move( you, here, tripoint_rel_ms::east );
    }
    CHECK( rl_dist( cart0, veh->pos_abs() ) >= 2 );
    // then pull it round to the south: the cart follows and turns
    const units::angle face0 = veh->face.dir();
    const tripoint_abs_ms cart1 = veh->pos_abs();
    for( int i = 0; i < 3; i++ ) {
        you.set_moves( 100 );
        avatar_action::move( you, here, tripoint_rel_ms::south );
    }
    CHECK( veh->pos_abs() != cart1 );
    INFO( "face before " << units::to_degrees( face0 ) << " after " <<
          units::to_degrees( veh->face.dir() ) );
    CHECK( veh->face.dir() != face0 );
    you.grab( object_type::NONE );
    clear_vehicles();
}

TEST_CASE( "saigon_boats_float_and_motor", "[saigon][vehicle]" )
{
    if( !saigon_loaded() ) {
        return;
    }
    const time_point start = calendar::turn;
    const std::vector<std::pair<vproto_id, bool>> boats = {
        { vehicle_prototype_sgn_veh_xuong, false }, { vehicle_prototype_sgn_veh_ghe, true },
        { vehicle_prototype_sgn_veh_ghe_may, true }, { vehicle_prototype_sgn_veh_xa_lan, true }
    };
    for( const std::pair<vproto_id, bool> &b : boats ) {
        CAPTURE( b.first.str() );
        clear_scene( ter_id( "t_water_dp" ) );
        map &here = get_map();
        vehicle *veh = here.add_vehicle( b.first, tripoint_bub_ms( 60, 60, 0 ), 0_degrees, 100,
                                         veh_spawn_status::UNDAMAGED );
        REQUIRE( veh != nullptr );
        CHECK( veh->can_float( here ) );
        veh->check_falling_or_floating();
        CHECK( veh->is_in_water( true ) );
        CHECK( veh->is_watercraft() );
        fuel_up( *veh );
        take_the_wheel( *veh );
        // with the rower or the pilot aboard
        CHECK( veh->safe_water_velocity( here ) > 0 );
        const drive_result r = drive( *veh, 15 );
        INFO( "travelled " << r.tiles << " tiles, turned " << units::to_degrees( r.turned ) );
        // still afloat, still in one piece
        CHECK( veh->is_in_water( true ) );
        CHECK( veh->pos_abs().z() == 0 );
        if( b.second ) {
            CHECK( veh->total_power( here ) > 0_W );
            CHECK( r.tiles >= 5 );
            CHECK( r.turned != 0_degrees );
        } else {
            // the xuồng is rowed: it moves, if slowly
            CHECK( r.tiles >= 1 );
        }
        get_out();
    }
    calendar::turn = start;
}

TEST_CASE( "saigon_engine_power_and_fuel", "[saigon][vehicle]" )
{
    if( !saigon_loaded() ) {
        return;
    }
    const vpart_id e50( "sgn_engine_50cc" );
    const vpart_id e110( "sgn_engine_110cc" );
    const vpart_id e125( "sgn_engine_125cc" );
    const vpart_id longtail( "sgn_longtail" );
    REQUIRE( e50.is_valid() );
    REQUIRE( e110.is_valid() );
    REQUIRE( e125.is_valid() );
    REQUIRE( longtail.is_valid() );
    // a ba gác máy runs on a 125cc motorbike engine (B6: 7.5 kW), not a car engine
    CHECK( e125->power > 0_W );
    CHECK( e125->power <= 9_kW );
    // the ghe's long-tail is a converted small engine (B6: 9.7 kW)
    CHECK( longtail->power > 0_W );
    CHECK( longtail->power <= 11_kW );
    // a 50cc burns less than a 110cc at full power, and is weaker
    CHECK( e50->energy_consumption > 0_W );
    CHECK( e50->energy_consumption < e110->energy_consumption );
    CHECK( e50->power < e110->power );
    CHECK( e50->fuel_type == e110->fuel_type );

    // and the vehicles use them
    bool ba_gac_has_125 = false;
    for( const vehicle_prototype::part_def &pd : vehicle_prototype_sgn_veh_ba_gac_may->parts ) {
        ba_gac_has_125 |= pd.part == e125;
    }
    CHECK( ba_gac_has_125 );
    bool ghe_has_longtail = false;
    for( const vehicle_prototype::part_def &pd : vehicle_prototype_sgn_veh_ghe->parts ) {
        ghe_has_longtail |= pd.part == longtail;
    }
    CHECK( ghe_has_longtail );
}

TEST_CASE( "saigon_xe_lam_spawns_dry", "[saigon][vehicle]" )
{
    if( !saigon_loaded() ) {
        return;
    }
    // whatever fuel the spawner asks for (random, none, full), the abandoned xe lam's tank is dry
    for( const int fuel : { -1, 0, 50, 100 } ) {
        CAPTURE( fuel );
        clear_scene( ter_id( "t_pavement" ) );
        map &here = get_map();
        vehicle *veh = here.add_vehicle( vehicle_prototype_sgn_veh_xe_lam, tripoint_bub_ms( 60, 60, 0 ),
                                         0_degrees, fuel, veh_spawn_status::UNDAMAGED );
        REQUIRE( veh != nullptr );
        int tanks = 0;
        for( const vpart_reference &vp : veh->get_all_parts() ) {
            if( vp.part().is_tank() ) {
                tanks++;
                CHECK( vp.part().ammo_remaining() == 0 );
            }
        }
        CHECK( tanks == 1 );
        CHECK( veh->fuel_left( here, itype_gasoline ) == 0 );
        clear_vehicles();
    }
}

// The weights of a vehicle group, read from the mod's JSON (the loaded group keeps them private).
static std::map<std::string, int> group_weights( const std::string &group )
{
    std::map<std::string, int> w;
    const cata_path file( cata_path::root_path::data,
                          "mods/saigon_2000s/mapgen/roads/road_traffic.json" );
    REQUIRE( read_from_file_json( file, [&]( const JsonValue & jv ) {
        for( JsonObject jo : jv.get_array() ) {
            jo.allow_omitted_members();
            if( jo.get_string( "type" ) != "vehicle_group" || jo.get_string( "id" ) != group ) {
                continue;
            }
            for( JsonArray pair : jo.get_array( "vehicles" ) ) {
                w[pair.get_string( 0 )] += pair.get_int( 1 );
            }
        }
    } ) );
    REQUIRE( !w.empty() );
    // the loaded group has exactly these vehicles
    const vgroup_id gid( group );
    REQUIRE( gid.is_valid() );
    std::set<std::string> loaded;
    for( const vproto_id &v : gid->all_possible_results() ) {
        loaded.insert( v.str() );
    }
    std::set<std::string> in_json;
    for( const std::pair<const std::string, int> &e : w ) {
        if( e.second > 0 ) {
            in_json.insert( e.first );
        }
    }
    CHECK( loaded == in_json );
    return w;
}

static int wheels_of( const vproto_id &id )
{
    int n = 0;
    for( const vehicle_prototype::part_def &pd : id->parts ) {
        if( pd.part->has_flag( "WHEEL" ) ) {
            n++;
        }
    }
    return n;
}

static bool emergency( const std::string &id )
{
    return id == "sgn_veh_xe_cuu_thuong" || id == "sgn_veh_xe_cuu_hoa";
}

TEST_CASE( "saigon_traffic_mix", "[saigon][vehicle]" )
{
    if( !saigon_loaded() ) {
        return;
    }
    SECTION( "ambulances and fire engines are rare in city traffic" ) {
        const std::map<std::string, int> w = group_weights( "sgn_vg_city_traffic" );
        int total = 0;
        int urgent = 0;
        for( const std::pair<const std::string, int> &e : w ) {
            total += e.second;
            urgent += emergency( e.first ) ? e.second : 0;
        }
        CAPTURE( urgent, total );
        CHECK( urgent > 0 );
        CHECK( urgent * 100 < total );
        // and the loaded group picks them about that often
        const vgroup_id gid( "sgn_vg_city_traffic" );
        int picked = 0;
        const int draws = 20000;
        for( int i = 0; i < draws; i++ ) {
            picked += emergency( gid->pick().str() ) ? 1 : 0;
        }
        CAPTURE( picked );
        CHECK( picked * 100 < draws );
    }

    SECTION( "at most one vehicle in ten on the road has four wheels" ) {
        for( const std::string group : {
                 "sgn_vg_street_traffic", "sgn_vg_city_traffic"
             } ) {
            CAPTURE( group );
            const std::map<std::string, int> w = group_weights( group );
            int total = 0;
            int four = 0;
            for( const std::pair<const std::string, int> &e : w ) {
                const vproto_id id( e.first );
                REQUIRE( id.is_valid() );
                const int wheels = wheels_of( id );
                CAPTURE( e.first, wheels );
                CHECK( wheels >= 2 );
                // the rare emergency vehicles are counted apart (city traffic only)
                if( emergency( e.first ) ) {
                    continue;
                }
                total += e.second;
                four += wheels >= 4 ? e.second : 0;
            }
            CAPTURE( four, total );
            CHECK( four * 10 <= total );
        }
    }
}
