#include <algorithm>
#include <array>
#include <cstdlib>
#include <memory>
#include <optional>
#include <utility>

#include "calendar.h"
#include "cata_catch.h"
#include "cata_scope_helpers.h"
#include "coordinates.h"
#include "options_helpers.h"
#include "pimpl.h"
#include "type_id.h"
#include "units.h"
#include "weather.h"
#include "weather_gen.h"
#include "weather_type.h"

static const weather_type_id weather_lightning( "lightning" );
static const weather_type_id weather_thunder( "thunder" );

// Saigon 2000s mod: checks the monsoon climate against doc/saigon/CONTENT_BIBLE.md §9.
// Run with: tests/cata_test --mods=dda,saigon_2000s "[saigon]"
// Without the mod loaded the region uses the New England generator and the test is skipped.

namespace
{

struct saigon_year {
    int wet_hours = 0;
    int dry_hours = 0;
    int wet_rain_hours = 0;
    int dry_rain_hours = 0;
    int wet_rain_afternoon_hours = 0;
    int wet_storm_hours = 0;
    double min_temp_c = 1000;
    double max_temp_c = -1000;
    double sum_temp_c = 0;
    int samples = 0;
};

} // namespace

// Day-of-year window used by the mod's sgn_wet() jmath function (turn 0 = spring equinox).
static bool saigon_is_wet_season( int doy )
{
    return doy >= 41 && doy <= 252;
}

static saigon_year collect_saigon_year( unsigned seed )
{
    scoped_weather_override null_weather( WEATHER_NULL );
    const weather_generator &wgen = get_weather().get_cur_weather_gen();
    // Weather conditions read time('now') from calendar::turn, so it must follow the sample.
    restore_on_out_of_scope restore_turn( calendar::turn );

    saigon_year result;
    const time_point begin = calendar::turn_zero;
    const time_point end = begin + calendar::year_length();
    for( time_point t = begin; t < end; t += 1_hours ) {
        calendar::turn = t;
        const w_point w = wgen.get_weather( tripoint_abs_ms::zero, t, seed );
        *get_weather().weather_precise = w;
        const weather_type_id conditions = wgen.get_weather_conditions( w );
        const bool rains = conditions->rains;
        const bool storm = conditions == weather_thunder ||
                           conditions == weather_lightning;
        const int doy = to_days<int>( t - begin ) % 364;
        const int hour = to_hours<int>( time_past_midnight( t ) );
        const bool wet = saigon_is_wet_season( doy );
        const double temp_c = units::to_celsius( w.temperature );

        result.min_temp_c = std::min( result.min_temp_c, temp_c );
        result.max_temp_c = std::max( result.max_temp_c, temp_c );
        result.sum_temp_c += temp_c;
        result.samples++;
        if( wet ) {
            result.wet_hours++;
            if( rains ) {
                result.wet_rain_hours++;
                result.wet_storm_hours += storm;
                if( hour >= 13 && hour < 19 ) {
                    result.wet_rain_afternoon_hours++;
                }
            }
        } else {
            result.dry_hours++;
            if( rains ) {
                result.dry_rain_hours++;
            }
        }
    }
    return result;
}

static const std::array<unsigned, 3> saigon_seeds = { {317'024'741, 870'078'684, 1'192'447'748} };

TEST_CASE( "saigon_monsoon_climate", "[weather][saigon]" )
{
    const weather_generator &wgen = get_weather().get_cur_weather_gen();
    if( wgen.base_temperature < 25 ) {
        WARN( "saigon_2000s region weather is not active; skipping" );
        return;
    }

    for( unsigned seed : saigon_seeds ) {
        CAPTURE( seed );
        const saigon_year y = collect_saigon_year( seed );
        const double wet_share = static_cast<double>( y.wet_rain_hours ) / y.wet_hours;
        const double dry_share = static_cast<double>( y.dry_rain_hours ) / y.dry_hours;
        const double afternoon_share = y.wet_rain_hours == 0 ? 0.0 :
                                       static_cast<double>( y.wet_rain_afternoon_hours ) / y.wet_rain_hours;
        const double mean_c = y.sum_temp_c / y.samples;
        const double storm_share = y.wet_rain_hours == 0 ? 0.0 :
                                   static_cast<double>( y.wet_storm_hours ) / y.wet_rain_hours;
        CAPTURE( wet_share, dry_share, afternoon_share, storm_share, mean_c, y.min_temp_c, y.max_temp_c );

        // Tropical: narrow annual range, never cold (B4b monthly curves).
        CHECK( mean_c >= 26.5 );
        CHECK( mean_c <= 28.5 );
        CHECK( y.min_temp_c >= 18 );
        CHECK( y.max_temp_c <= 40 );
        // Monsoon: two-sided bands so a degenerate climate cannot pass (critic_d3 D2).
        CHECK( wet_share >= 0.12 );
        CHECK( wet_share <= 0.35 );
        CHECK( dry_share >= 0.002 );
        CHECK( dry_share <= 0.02 );
        CHECK( wet_share >= 4 * dry_share );
        // Wet-season rain is concentrated in afternoon thunderstorms.
        CHECK( afternoon_share >= 0.5 );
        CHECK( storm_share >= 0.10 );
        CHECK( storm_share <= 0.60 );
    }
}

TEST_CASE( "saigon_water_is_warm", "[weather][saigon]" )
{
    restore_on_out_of_scope restore_turn( calendar::turn );
    // Turn-days 237 (15 Nov, the dda water minimum) and 318 (5 Feb), at 06:00.
    const std::array<int, 2> turn_days = { { 237, 318 } };
    // Without a curve the dda New England water model is unchanged (bit-for-bit seam).
    const weather_generator dda_gen;
    for( const int turn_day : turn_days ) {
        CAPTURE( turn_day );
        calendar::turn = calendar::turn_zero + 1_days * turn_day + 6_hours;
        const double dda_c = units::to_celsius( dda_gen.get_water_temperature() );
        CHECK( dda_c < 15 );
    }
    const weather_generator &wgen = get_weather().get_cur_weather_gen();
    if( wgen.base_temperature < 25 ) {
        WARN( "saigon_2000s region weather is not active; skipping the Saigon half" );
        return;
    }
    // With the Saigon region active the curve must exist, so removing the JSON key fails.
    REQUIRE( wgen.monthly_water_temperature );
    for( const int turn_day : turn_days ) {
        CAPTURE( turn_day );
        calendar::turn = calendar::turn_zero + 1_days * turn_day + 6_hours;
        CHECK( units::to_celsius( wgen.get_water_temperature() ) >= 25 );
    }
}

TEST_CASE( "monthly_climate_curve", "[weather][saigon]" )
{
    const weather_generator &wgen = get_weather().get_cur_weather_gen();
    if( wgen.base_temperature < 25 ) {
        WARN( "saigon_2000s region weather is not active; skipping" );
        return;
    }
    REQUIRE( wgen.monthly_temperature );
    REQUIRE( wgen.monthly_humidity );
    restore_on_out_of_scope restore_turn( calendar::turn );
    for( unsigned seed : saigon_seeds ) {
        CAPTURE( seed );
        std::array<double, 12> sum_t{};
        std::array<double, 12> sum_h{};
        std::array<int, 12> n{};
        const time_point begin = calendar::turn_zero;
        for( time_point t = begin; t < begin + calendar::year_length(); t += 1_hours ) {
            calendar::turn = t;
            const w_point w = wgen.get_weather( tripoint_abs_ms::zero, t, seed );
            const int m = static_cast<int>( month_and_day( t ).first );
            sum_t[m] += units::to_celsius( w.temperature );
            sum_h[m] += w.humidity;
            n[m]++;
        }
        double lo = 1000;
        double hi = -1000;
        for( int m = 0; m < 12; m++ ) {
            CAPTURE( m );
            REQUIRE( n[m] > 0 );
            const double mean_t = sum_t[m] / n[m];
            const double mean_h = sum_h[m] / n[m];
            lo = std::min( lo, mean_t );
            hi = std::max( hi, mean_t );
            // Monthly means follow the anchors; the noise and daily cycle average out.
            CHECK( std::abs( mean_t - ( *wgen.monthly_temperature )[m] ) <= 1.0 );
            CHECK( std::abs( mean_h - ( *wgen.monthly_humidity )[m] ) <= 4.0 );
        }
        // Tropical: the annual range of monthly means stays small.
        CHECK( hi - lo <= 3.5 );
    }
}
