#include <string>

#include "avatar.h"
#include "calendar.h"
#include "cata_catch.h"
#include "coordinates.h"
#include "dialogue.h"
#include "effect_on_condition.h"
#include "global_vars.h"
#include "map.h"
#include "map_helpers.h"
#include "mapdata.h"
#include "options_helpers.h"
#include "player_helpers.h"
#include "point.h"
#include "type_id.h"
#include "weather_type.h"

// Saigon 2000s mod: wet-season street flooding (G30, data/mods/saigon_2000s/region/flood.json).
// Heavy rain in the wet season (sgn_wet() in region/weather.json) floods the paved streets
// around the player with wadeable murky water; once the rain stops it drains away; the
// same rain in the dry season does not flood.
// Run with: tests/cata_test --mods=dda,saigon_2000s "[saigon]"

static int count_ter( map &m, const tripoint_bub_ms &centre, int radius, const ter_str_id &ter )
{
    int n = 0;
    for( int dx = -radius; dx <= radius; dx++ ) {
        for( int dy = -radius; dy <= radius; dy++ ) {
            n += m.ter( centre + tripoint( dx, dy, 0 ) ) == ter.id();
        }
    }
    return n;
}

TEST_CASE( "saigon_flood_season", "[saigon][weather]" )
{
    const effect_on_condition_id flood( "sgn_eoc_flood" );
    const effect_on_condition_id drain( "sgn_eoc_drain" );
    if( !flood.is_valid() ) {
        WARN( "saigon_2000s is not loaded; skipping" );
        return;
    }
    const ter_str_id pavement( "t_pavement" );
    const ter_str_id flooded( "t_sgn_ngap_duong" );
    clear_map();
    clear_avatar();
    avatar &you = get_avatar();
    map &here = get_map();
    const tripoint_bub_ms centre = you.pos_bub();
    const int r = 10;
    for( int dx = -r; dx <= r; dx++ ) {
        for( int dy = -r; dy <= r; dy++ ) {
            here.ter_set( centre + tripoint( dx, dy, 0 ), pavement.id() );
        }
    }
    get_globals().set_global_value( "sgn_flooding", 0 );
    dialogue d( get_talker_for( you ), nullptr );
    const time_point saved_turn = calendar::turn;

    SECTION( "dry season rain does not flood" ) {
        calendar::turn = calendar::turn_zero + 300_days;   // sgn_doy() = 300: January
        scoped_weather_override rain( weather_type_id( "rain" ) );
        flood->activate( d );
        CHECK( count_ter( here, centre, r, flooded ) == 0 );
    }
    SECTION( "wet season rain floods, and the water drains when it stops" ) {
        calendar::turn = calendar::turn_zero + 120_days;   // sgn_doy() = 120: mid-July
        {
            scoped_weather_override rain( weather_type_id( "rain" ) );
            for( int i = 0; i < 3; i++ ) {
                flood->activate( d );
            }
        }
        const int wet = count_ter( here, centre, r, flooded );
        CAPTURE( wet );
        // patchy at first, spreading with every check that it rains on (3 of 5 per check)
        CHECK( wet > ( 2 * r + 1 ) * ( 2 * r + 1 ) / 2 );
        const tripoint_bub_ms p = centre + tripoint::east;
        here.ter_set( p, flooded.id() );
        CHECK( here.ter( p ).obj().has_flag( ter_furn_flag::TFLAG_SHALLOW_WATER ) );
        CHECK( here.passable( p ) );
        CHECK( here.move_cost( p ) == 4 );
        {
            scoped_weather_override clear( weather_type_id( "clear" ) );
            drain->activate( d );
        }
        CHECK( count_ter( here, centre, r, flooded ) == 0 );
        CHECK( count_ter( here, centre, r, pavement ) == ( 2 * r + 1 ) * ( 2 * r + 1 ) );
    }
    calendar::turn = saved_turn;
    get_globals().set_global_value( "sgn_flooding", 0 );
}
