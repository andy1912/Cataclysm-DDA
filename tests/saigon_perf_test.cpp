#include <algorithm>
#include <chrono>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <optional>
#include <string>
#include <vector>

#include "avatar.h"
#include "calendar.h"
#include "cata_catch.h"
#include "coordinates.h"
#include "game.h"
#include "map.h"
#include "map_helpers.h"
#include "monster.h"
#include "omdata.h"
#include "options_helpers.h"
#include "overmap.h"
#include "overmapbuffer.h"
#include "player_helpers.h"
#include "point.h"
#include "type_id.h"
#include "zzip.h"
#include "zstd/zstd.h"

// Saigon 2000s mod: turn-time harness (I-B5perf, doc/saigon/analysis/integration.md §10.24).
// Puts the player in three generated Saigon places (a shophouse street, the Bến Thành
// downtown, a chợ) at dusk in the wet season, in rain, sealed in a concrete box so the
// run cannot end in death, then times whole game turns (game::do_turn: weather, fields,
// vehicles, map caches, every monster's move).  Exit gate (tier a): p50 <= 40 ms where at
// most 100 monsters are awake.  Rendering is not included: the test build has no tiles.
// Hidden test; run with:
//   [SAIGON_PERF_WEATHER=clear] tests/cata_test --mods=dda,saigon_2000s "[saigon_perf]"

namespace
{
struct site {
    const char *name;
    std::string prefix;
};
} // namespace

// The first OMT whose oter id starts with `prefix`, away from the overmap edges so the
// whole reality bubble stays on this overmap.
static bool find_site( overmap &om, const std::string &prefix, tripoint_abs_omt &out )
{
    for( int y = 20; y < OMAPY - 20; y++ ) {
        for( int x = 20; x < OMAPX - 20; x++ ) {
            if( om.ter( tripoint_om_omt( x, y, 0 ) ).id().str().rfind( prefix, 0 ) == 0 ) {
                out = tripoint_abs_omt( x, y, 0 );
                return true;
            }
        }
    }
    return false;
}

// How many of overmap (0,0) and its eight neighbours exist: a spike is explained if a
// neighbour got generated during the run.
static int generated_neighbours()
{
    int n = 0;
    for( int x = -1; x <= 1; x++ ) {
        for( int y = -1; y <= 1; y++ ) {
            n += overmap_buffer.has( point_abs_om( x, y ) );
        }
    }
    return n;
}

static double percentile( std::vector<double> v, double p )
{
    std::sort( v.begin(), v.end() );
    return v[std::min( v.size() - 1, static_cast<size_t>( p * v.size() ) )];
}

TEST_CASE( "saigon_turn_time", "[.][saigon_perf]" )
{
    if( !oter_str_id( "sgn_lm_ben_thanh_11_north" ).is_valid() ) {
        WARN( "saigon_2000s is not loaded; skipping" );
        return;
    }
    const std::vector<site> sites = {
        { "shophouse street", "sgn_nh_solo_z0" },
        { "Bến Thành downtown", "sgn_lm_ben_thanh_11" },
        { "chợ", "sgn_cho_" },
    };
    clear_avatar();
    clear_map();
    clear_overmaps();
    // wet season (CDDA summer) at dusk, raining
    calendar::turn = sunset( calendar::turn_zero + calendar::season_length() * 1.5 );
    const char *weather = std::getenv( "SAIGON_PERF_WEATHER" );   // default rain; "clear" for comparison
    scoped_weather_override rain( weather_type_id( weather ? weather : "rain" ) );
    overmap &om = overmap_buffer.get( point_abs_om() );
    const ter_id wall = ter_str_id( "t_concrete_wall" ).id();
    const ter_id floor = ter_str_id( "t_thconc_floor" ).id();
    for( const site &s : sites ) {
        CAPTURE( s.name );
        tripoint_abs_omt pos;
        if( !find_site( om, s.prefix, pos ) ) {
            WARN( s.name << ": no " << s.prefix << " on this overmap" );
            continue;
        }
        const int before = generated_neighbours();
        g->place_player_overmap( pos );
        WARN( s.name << ": overmaps generated before placing the player " << before << ", after " << generated_neighbours() );
        avatar &u = get_avatar();
        map &here = get_map();
        for( const tripoint_bub_ms &p : here.points_in_radius( u.pos_bub(), 1 ) ) {
            if( p != u.pos_bub() ) {
                here.ter_set( p, wall );
            }
        }
        here.ter_set( u.pos_bub(), floor );
        here.furn_set( u.pos_bub(), furn_str_id::NULL_ID() );

        auto one_turn = [&]() {
            u.set_moves( 0 );                          // no input: the player just waits
            const auto t0 = std::chrono::steady_clock::now();
            g->do_turn();
            return std::chrono::duration<double, std::milli>( std::chrono::steady_clock::now() - t0 ).count();
        };
        for( int i = 0; i < 20; i++ ) {               // warm-up: caches, first monster moves
            one_turn();
        }
        std::vector<double> ms;
        for( int i = 0; i < 300 && !u.is_dead_state(); i++ ) {
            ms.push_back( one_turn() );
        }
        int monsters = 0;
        for( monster &m : g->all_monsters() ) {
            monsters += !m.is_dead();
        }
        REQUIRE( !ms.empty() );
        std::string spikes;                            // one-off stalls, e.g. a neighbour overmap generating
        for( size_t i = 0; i < ms.size(); i++ ) {
            if( ms[i] > 100.0 ) {
                spikes += "turn " + std::to_string( i ) + ": " + std::to_string( static_cast<int>( ms[i] ) ) + " ms; ";
            }
        }
        const double p50 = percentile( ms, 0.50 );
        const double p95 = percentile( ms, 0.95 );
        const double worst = *std::max_element( ms.begin(), ms.end() );
        WARN( s.name << " (" << s.prefix << "): " << monsters << " monsters in the bubble, " << ms.size()
              << " turns, p50 " << p50 << " ms, p95 " << p95 << " ms, max " << worst << " ms"
              << ( spikes.empty() ? "" : ", spikes over 100 ms: " + spikes )
              << " (overmaps generated around (0,0): " << generated_neighbours() << " of 9)" );
        if( monsters <= 100 ) {
            CHECK( p50 <= 40.0 );
        }
    }
}

// Compression level trade-off for save files (doc/saigon/PERF.md): unpack a saved zzip
// (a copy; the world is not touched) and recompress every entry with the same dictionary at
// zstd levels 3 and 7, reporting total size and time.  Hidden; run with:
//   SAIGON_ZZIP=copy/of/o.0.0.zzip SAIGON_ZZIP_DICT=world/overmaps.dict \
//       tests/cata_test --mods=dda,saigon_2000s "[saigon_zzip_level]"
TEST_CASE( "saigon_zzip_level", "[.][saigon_zzip_level]" )
{
    const char *path = std::getenv( "SAIGON_ZZIP" );
    const char *dict_path = std::getenv( "SAIGON_ZZIP_DICT" );
    if( path == nullptr || dict_path == nullptr ) {
        WARN( "set SAIGON_ZZIP and SAIGON_ZZIP_DICT" );
        return;
    }
    std::optional<zzip> z = zzip::load( path, dict_path );
    REQUIRE( z.has_value() );
    std::ifstream df( dict_path, std::ios::binary );
    const std::string dict( ( std::istreambuf_iterator<char>( df ) ), std::istreambuf_iterator<char>() );
    size_t raw = 0;
    std::vector<std::vector<std::byte>> files;
    for( const std::filesystem::path &e : z->get_entries() ) {
        files.push_back( z->get_file( e ) );
        raw += files.back().size();
    }
    REQUIRE( !files.empty() );
    for( int level : { 3, 7 } ) {
        ZSTD_CCtx *cctx = ZSTD_createCCtx();
        ZSTD_CCtx_setParameter( cctx, ZSTD_c_compressionLevel, level );
        size_t packed = 0;
        const auto t0 = std::chrono::steady_clock::now();
        for( int rep = 0; rep < 5; rep++ ) {
            packed = 0;
            for( const std::vector<std::byte> &f : files ) {
                ZSTD_CCtx_loadDictionary( cctx, dict.data(), dict.size() );
                std::vector<char> out( ZSTD_compressBound( f.size() ) );
                const size_t n = ZSTD_compress2( cctx, out.data(), out.size(), f.data(), f.size() );
                REQUIRE( !ZSTD_isError( n ) );
                packed += n;
            }
        }
        const double ms = std::chrono::duration<double, std::milli>( std::chrono::steady_clock::now() - t0 ).count() / 5;
        ZSTD_freeCCtx( cctx );
        WARN( "level " << level << ": " << files.size() << " files, " << raw << " bytes -> " << packed
              << " bytes (" << 100.0 * packed / raw << " %), " << ms << " ms" );
    }
}
