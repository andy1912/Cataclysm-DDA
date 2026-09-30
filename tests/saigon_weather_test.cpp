#include <array>
#include <memory>
#include <vector>

#include "calendar.h"
#include "cata_catch.h"
#include "cata_scope_helpers.h"
#include "coordinates.h"
#include "options_helpers.h"
#include "pimpl.h"
#include "units.h"
#include "weather.h"
#include "weather_gen.h"
#include "weather_type.h"

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
    double min_temp_c = 1000;
    double max_temp_c = -1000;
    double sum_temp_c = 0;
    int samples = 0;
};

} // namespace

// Day-of-year window used by the mod's sgn_wet() jmath function (turn 0 = spring equinox).
static bool saigon_is_wet_season( int doy )
{
    return doy >= 41 && doy <= 254;
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
        const bool rains = wgen.get_weather_conditions( w )->rains;
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
        CAPTURE( wet_share, dry_share, afternoon_share, mean_c, y.min_temp_c, y.max_temp_c );

        // Tropical mean, never frost.
        CHECK( mean_c >= 24 );
        CHECK( mean_c <= 31 );
        CHECK( y.min_temp_c > 5 );
        // Monsoon: the wet season rains far more often than the dry season.
        CHECK( wet_share >= 0.05 );
        CHECK( dry_share <= 0.02 );
        CHECK( wet_share >= 4 * dry_share );
        // Wet-season rain is concentrated in afternoon thunderstorms.
        CHECK( afternoon_share >= 0.5 );
    }
}
