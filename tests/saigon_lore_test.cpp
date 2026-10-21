#include <algorithm>
#include <array>
#include <memory>
#include <cstddef>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#include "avatar.h"
#include "calendar.h"
#include "cata_catch.h"
#include "character.h"
#include "character_attire.h"
#include "coordinates.h"
#include "dialogue.h"
#include "effect_on_condition.h"
#include "item.h"
#include "item_location.h"
#include "itype.h"
#include "map.h"
#include "map_helpers.h"
#include "mapdata.h"
#include "messages.h"
#include "overmapbuffer.h"
#include "player_helpers.h"
#include "pocket_type.h"
#include "point.h"
#include "ret_val.h"
#include "sounds.h"
#include "talker.h"
#include "text_snippets.h"
#include "type_id.h"

// Saigon 2000s mod, V3 "the city speaks" (eoc/v3_city_voice.json, scenario/eoc_intro.json,
// snippets/lore_*.json): the ward loudspeaker (loa phường), the cassette radio, incense at the
// altar and the start-location intro.
// Headless limits: u_query (the "Light a stick of incense?" question) always answers no in test
// mode (query_popup returns at once), so the altar's lighting is tested by running that EOC's
// effects directly; run_eoc_selector in test mode cancels when allow_cancel is set, so using the
// radio runs the cancelled path, and its two choices are tested as EOCs.
// Run with: tests/cata_test --mods=dda,saigon_2000s "[saigon][lore]"

static const effect_on_condition_id effect_on_condition_SGN_EOC_intro( "SGN_EOC_intro" );
static const effect_on_condition_id
effect_on_condition_SGN_EOC_v3_altar_light( "SGN_EOC_v3_altar_light" );
static const effect_on_condition_id
effect_on_condition_SGN_EOC_v3_loa_schedule( "SGN_EOC_v3_loa_schedule" );
static const effect_on_condition_id
effect_on_condition_SGN_EOC_v3_radio_tape( "SGN_EOC_v3_radio_tape" );
static const effect_on_condition_id
effect_on_condition_SGN_EOC_v3_radio_tune( "SGN_EOC_v3_radio_tune" );

static const furn_str_id furn_f_sgn_ban_tho( "f_sgn_ban_tho" );
static const furn_str_id furn_f_sgn_ban_tho_than_tai( "f_sgn_ban_tho_than_tai" );
static const furn_str_id furn_f_sgn_loa_phuong( "f_sgn_loa_phuong" );

static const itype_id itype_debug_backpack( "debug_backpack" );
static const itype_id itype_incense( "incense" );
static const itype_id itype_lighter( "lighter" );
static const itype_id itype_sgn_radio_cassette( "sgn_radio_cassette" );

static const morale_type morale_music( "morale_music" );
static const morale_type morale_sgn_remember( "morale_sgn_remember" );
static const morale_type morale_sgn_than_tai( "morale_sgn_than_tai" );

static bool saigon_loaded()
{
    if( !furn_f_sgn_loa_phuong.is_valid() ) {
        WARN( "saigon_2000s is not loaded; skipping" );
        return false;
    }
    return true;
}

static std::vector<std::string> all_messages()
{
    std::vector<std::string> out;
    for( const std::pair<std::string, std::string> &m : Messages::recent_messages( 0 ) ) {
        out.push_back( m.second );
    }
    return out;
}

// the opening words of a snippet, enough to tell it apart (snippets may hold tags, which the
// message has expanded)
static std::string head_of( std::string_view text )
{
    std::string h( text.substr( 0, std::min<size_t>( text.size(), 30 ) ) );
    const size_t tag = h.find( '<' );
    return tag == std::string::npos ? h : h.substr( 0, tag );
}

// does any message start with (contain) a snippet of this category?
static bool said_from( const std::string &category )
{
    const std::vector<std::pair<snippet_id, std::string>> snips =
                SNIPPET.get_snippets_by_category( category );
    REQUIRE( !snips.empty() );
    for( const std::string &msg : all_messages() ) {
        for( const std::pair<snippet_id, std::string> &s : snips ) {
            const std::string h = head_of( s.second );
            if( !h.empty() && msg.find( h ) != std::string::npos ) {
                return true;
            }
        }
    }
    return false;
}

static bool sound_at( const tripoint_bub_ms &p )
{
    for( const tripoint_bub_ms &s : sounds::get_monster_sounds().first ) {
        if( s == p ) {
            return true;
        }
    }
    return false;
}

static void at_day( int day, int hour, int minute = 0 )
{
    calendar::turn = calendar::start_of_cataclysm + time_duration::from_days( day ) +
                     time_duration::from_hours( hour ) + time_duration::from_minutes( minute );
    // start_of_cataclysm need not be midnight: line up with the clock
    calendar::turn = calendar::turn - time_past_midnight( calendar::turn ) +
                     time_duration::from_hours( hour ) + time_duration::from_minutes( minute );
}

static void fresh_scene()
{
    clear_map_without_vision();
    clear_avatar();
    Messages::clear_messages();
    sounds::reset_sounds();
}

TEST_CASE( "saigon_loa_examine_by_phase", "[saigon][lore]" )
{
    if( !saigon_loaded() ) {
        return;
    }
    const time_point start = calendar::turn;
    fresh_scene();
    map &here = get_map();
    avatar &you = get_avatar();
    const tripoint_bub_ms pole( 61, 60, 0 );
    you.setpos( here, tripoint_bub_ms( 60, 60, 0 ) );
    here.furn_set( pole, furn_f_sgn_loa_phuong );
    REQUIRE( here.furn( pole ) == furn_f_sgn_loa_phuong );
    REQUIRE( here.furn( pole ).obj().can_examine( pole ) );

    // fixed-size and string_view: GCC 16 reports a false -Wfree-nonheap-object for a vector of
    // structs holding std::string built from an initializer list here
    struct phase {
        int day;
        std::string_view category;
        bool loud;
    };
    const std::array<phase, 4> phases = { {
            { 4, "sgn_loa_v3_early", true }, { 10, "sgn_loa_v3_evac", true },
            { 20, "sgn_loa_v3_loop", true }, { 35, "sgn_loa_v3_silent", false }
        }
    };
    const std::array<std::string_view, 4> cats = {
        "sgn_loa_v3_early", "sgn_loa_v3_evac", "sgn_loa_v3_loop", "sgn_loa_v3_silent"
    };
    for( const phase &ph : phases ) {
        CAPTURE( ph.day );
        at_day( ph.day, 12 );
        Messages::clear_messages();
        sounds::reset_sounds();
        here.furn( pole ).obj().examine( you, pole );
        CAPTURE( all_messages() );
        CHECK( said_from( std::string( ph.category ) ) );
        for( const std::string_view other : cats ) {
            if( other != ph.category ) {
                CHECK_FALSE( said_from( std::string( other ) ) );
            }
        }
        // the broadcast is a sound at the pole, not at the player; silence makes none
        CHECK( sound_at( pole ) == ph.loud );
        CHECK_FALSE( sounds::get_monster_sounds().first.empty() == ph.loud );
    }
    calendar::turn = start;
}

TEST_CASE( "saigon_loa_schedule", "[saigon][lore]" )
{
    if( !saigon_loaded() ) {
        return;
    }
    const time_point start = calendar::turn;
    fresh_scene();
    map &here = get_map();
    avatar &you = get_avatar();
    you.setpos( here, tripoint_bub_ms( 60, 60, 0 ) );
    dialogue d( get_talker_for( you ), nullptr );
    const effect_on_condition &sched = effect_on_condition_SGN_EOC_v3_loa_schedule.obj();
    REQUIRE( sched.has_condition );

    SECTION( "the condition holds at 06:xx and 17:xx before day 30, only" ) {
        struct when {
            int day;
            int hour;
            int minute;
            bool fires;
        };
        const std::vector<when> times = {
            { 10, 5, 59, false }, { 10, 6, 0, true }, { 10, 6, 59, true }, { 10, 7, 0, false },
            { 10, 12, 0, false }, { 10, 16, 59, false }, { 10, 17, 0, true }, { 10, 17, 30, true },
            { 10, 18, 0, false }, { 10, 0, 0, false }, { 4, 6, 30, true }, { 29, 17, 30, true },
            { 30, 6, 30, false }, { 31, 17, 30, false }
        };
        for( const when &w : times ) {
            CAPTURE( w.day, w.hour, w.minute );
            at_day( w.day, w.hour, w.minute );
            CHECK( sched.test_condition( d ) == w.fires );
        }
    }

    SECTION( "at its hour, a pole within 18 tiles broadcasts" ) {
        const tripoint_bub_ms pole( 72, 60, 0 );
        here.furn_set( pole, furn_f_sgn_loa_phuong );
        at_day( 10, 6, 5 );
        Messages::clear_messages();
        sounds::reset_sounds();
        sched.activate( d );
        CAPTURE( all_messages() );
        CHECK( sound_at( pole ) );
        CHECK( said_from( "sgn_loa_v3_evac" ) );
        // at noon the same pole is quiet
        at_day( 10, 12, 0 );
        Messages::clear_messages();
        sounds::reset_sounds();
        sched.activate( d );
        CHECK( sounds::get_monster_sounds().first.empty() );
        CHECK( all_messages().empty() );
    }

    SECTION( "a pole 25 tiles away is out of range" ) {
        const tripoint_bub_ms pole( 85, 60, 0 );
        here.furn_set( pole, furn_f_sgn_loa_phuong );
        at_day( 10, 17, 5 );
        Messages::clear_messages();
        sounds::reset_sounds();
        sched.activate( d );
        CHECK( sounds::get_monster_sounds().first.empty() );
        CHECK_FALSE( said_from( "sgn_loa_v3_evac" ) );
    }
    calendar::turn = start;
}

TEST_CASE( "saigon_cassette_radio", "[saigon][lore]" )
{
    if( !saigon_loaded() ) {
        return;
    }
    const time_point start = calendar::turn;
    fresh_scene();
    avatar &you = get_avatar();
    at_day( 4, 12 );

    SECTION( "using it costs one battery charge, and without a battery it is refused" ) {
        item radio( itype_sgn_radio_cassette );
        REQUIRE( radio.type->charges_to_use() == 1 );
        item_location loc = you.i_add( radio );
        REQUIRE( loc );
        REQUIRE( loc->ammo_remaining() == 0 );
        Messages::clear_messages();
        you.invoke_item( loc.get_item() );
        CAPTURE( all_messages() );
        CHECK( loc->ammo_remaining() == 0 );
        CHECK_FALSE( said_from( "sgn_radio_v3_city" ) );
        CHECK_FALSE( sound_at( you.pos_bub() ) );

        item battery( loc->magazine_default() );
        REQUIRE( !battery.is_null() );
        battery.ammo_set( battery.ammo_default(), 10 );
        REQUIRE( loc->put_in( battery, pocket_type::MAGAZINE_WELL ).success() );
        REQUIRE( loc->ammo_remaining() == 10 );
        // in test mode the selector menu is cancelled (allow_cancel): the use still costs a charge
        you.invoke_item( loc.get_item() );
        CHECK( loc->ammo_remaining() == 9 );
    }

    SECTION( "the dial plays the phase's broadcast" ) {
        struct phase {
            int day;
            std::vector<std::string> cats;
        };
        const std::vector<phase> phases = {
            { 4, { "sgn_radio_v3_city" } },
            { 15, { "sgn_radio_v3_emergency", "sgn_radio" } },
            { 30, { "sgn_radio_v3_voices", "sgn_radio" } },
            { 50, { "sgn_radio_v3_static" } }
        };
        dialogue d( get_talker_for( you ), nullptr );
        for( const phase &ph : phases ) {
            CAPTURE( ph.day );
            at_day( ph.day, 12 );
            Messages::clear_messages();
            sounds::reset_sounds();
            effect_on_condition_SGN_EOC_v3_radio_tune->activate( d );
            CAPTURE( all_messages() );
            bool heard = false;
            for( const std::string &c : ph.cats ) {
                heard |= said_from( c );
            }
            CHECK( heard );
            if( ph.day != 4 ) {
                CHECK_FALSE( said_from( "sgn_radio_v3_city" ) );
            }
            CHECK( sound_at( you.pos_bub() ) );
        }
    }

    SECTION( "the tape cheers the listener up a little" ) {
        dialogue d( get_talker_for( you ), nullptr );
        REQUIRE( you.has_morale( morale_music ) == 0 );
        effect_on_condition_SGN_EOC_v3_radio_tape->activate( d );
        CHECK( said_from( "sgn_radio_v3_tape" ) );
        CHECK( you.has_morale( morale_music ) > 0 );
        CHECK( you.has_morale( morale_music ) <= 12 );
    }
    you.clear_morale();
    calendar::turn = start;
}

static int incense_left( const Character &you )
{
    return item( itype_incense ).count_by_charges() ? you.charges_of( itype_incense ) :
           you.amount_of( itype_incense );
}

TEST_CASE( "saigon_altar_incense", "[saigon][lore]" )
{
    if( !saigon_loaded() ) {
        return;
    }
    const time_point start = calendar::turn;
    fresh_scene();
    map &here = get_map();
    avatar &you = get_avatar();
    you.clear_morale();
    you.setpos( here, tripoint_bub_ms( 60, 60, 0 ) );
    const tripoint_bub_ms altar( 61, 60, 0 );
    at_day( 5, 9 );
    you.worn.wear_item( you, item( itype_debug_backpack ), false, false );
    item sticks( itype_incense );
    if( sticks.count_by_charges() ) {
        sticks.charges = 5;
        REQUIRE( you.i_add( sticks ) );
    } else {
        for( int i = 0; i < 5; i++ ) {
            REQUIRE( you.i_add( item( itype_incense ) ) );
        }
    }
    REQUIRE( incense_left( you ) == 5 );

    SECTION( "examining with incense but no fire only says so" ) {
        here.furn_set( altar, furn_f_sgn_ban_tho );
        here.furn( altar ).obj().examine( you, altar );
        CAPTURE( all_messages() );
        CHECK( said_from( "sgn_altar_v3_look" ) );
        bool told = false;
        for( const std::string &m : all_messages() ) {
            told |= m.find( "nothing to light it with" ) != std::string::npos;
        }
        CHECK( told );
        CHECK( incense_left( you ) == 5 );
        CHECK( you.has_morale( morale_sgn_remember ) == 0 );
    }

    SECTION( "with a lighter, the examine asks (test mode answers no): nothing is burned" ) {
        REQUIRE( you.i_add( item( itype_lighter ) ) );
        here.furn_set( altar, furn_f_sgn_ban_tho );
        here.furn( altar ).obj().examine( you, altar );
        CHECK( said_from( "sgn_altar_v3_look" ) );
        CHECK( incense_left( you ) == 5 );
    }

    SECTION( "lighting a stick: one incense, morale once per 12 hours" ) {
        REQUIRE( you.i_add( item( itype_lighter ) ) );
        here.furn_set( altar, furn_f_sgn_ban_tho );
        dialogue d( get_talker_for( you ), nullptr );
        d.set_value( "this", furn_f_sgn_ban_tho.str() );
        d.set_value( "pos", here.get_abs( altar ) );
        const effect_on_condition &light = effect_on_condition_SGN_EOC_v3_altar_light.obj();

        light.apply_true_effects( d );
        CHECK( incense_left( you ) == 4 );
        CHECK( said_from( "sgn_altar_v3_incense" ) );
        const int first = you.has_morale( morale_sgn_remember );
        CHECK( first > 0 );

        // an hour later: another stick burns, but no more morale
        calendar::turn += 1_hours;
        Messages::clear_messages();
        light.apply_true_effects( d );
        CHECK( incense_left( you ) == 3 );
        CHECK_FALSE( said_from( "sgn_altar_v3_incense" ) );
        CHECK( you.has_morale( morale_sgn_remember ) <= first );

        // eleven hours after that (12 h after the first): it counts again
        calendar::turn += 11_hours;
        you.clear_morale();
        Messages::clear_messages();
        light.apply_true_effects( d );
        CHECK( incense_left( you ) == 2 );
        CHECK( said_from( "sgn_altar_v3_incense" ) );
        CHECK( you.has_morale( morale_sgn_remember ) > 0 );
    }

    SECTION( "the Thần Tài shrine has its own text and morale" ) {
        REQUIRE( you.i_add( item( itype_lighter ) ) );
        here.furn_set( altar, furn_f_sgn_ban_tho_than_tai );
        here.furn( altar ).obj().examine( you, altar );
        CHECK( said_from( "sgn_altar_v3_than_tai" ) );
        dialogue d( get_talker_for( you ), nullptr );
        d.set_value( "this", furn_f_sgn_ban_tho_than_tai.str() );
        Messages::clear_messages();
        effect_on_condition_SGN_EOC_v3_altar_light->apply_true_effects( d );
        CHECK( incense_left( you ) == 4 );
        CHECK( said_from( "sgn_altar_v3_than_tai_incense" ) );
        CHECK( you.has_morale( morale_sgn_than_tai ) > 0 );
        CHECK( you.has_morale( morale_sgn_remember ) == 0 );
    }
    you.clear_morale();
    clear_avatar();
    calendar::turn = start;
}

static oter_id om_terrain( const std::string &base )
{
    const oter_str_id rotated( base + "_north" );
    const oter_str_id plain( base );
    REQUIRE( ( rotated.is_valid() || plain.is_valid() ) );
    return rotated.is_valid() ? rotated.id() : plain.id();
}

TEST_CASE( "saigon_intro_by_start", "[saigon][lore]" )
{
    if( !saigon_loaded() ) {
        return;
    }
    fresh_scene();
    avatar &you = get_avatar();
    const tripoint_abs_omt omt = you.pos_abs_omt();
    const oter_id before = overmap_buffer.ter( omt );
    const std::vector<std::pair<std::string, std::string>> starts = {
        { "sgn_cho_nw", "sgn_intro_v3_cho" }, { "sgn_hem_block", "sgn_intro_v3_hem" },
        { "sgn_lm_ga_sai_gon_10", "sgn_intro_v3_ga" }, { "sgn_lm_san_bay_10", "sgn_intro_v3_san_bay" },
        { "field", "sgn_intro" }
    };
    const std::vector<std::string> cats = {
        "sgn_intro_v3_cho", "sgn_intro_v3_hem", "sgn_intro_v3_ga", "sgn_intro_v3_san_bay", "sgn_intro"
    };
    for( const std::pair<std::string, std::string> &s : starts ) {
        CAPTURE( s.first );
        const oter_id ter = om_terrain( s.first );
        overmap_buffer.ter_set( omt, ter );
        Messages::clear_messages();
        dialogue d( get_talker_for( you ), nullptr );
        effect_on_condition_SGN_EOC_intro->activate( d );
        CAPTURE( all_messages() );
        CHECK( said_from( s.second ) );
        for( const std::string &c : cats ) {
            if( c != s.second ) {
                CHECK_FALSE( said_from( c ) );
            }
        }
    }
    overmap_buffer.ter_set( omt, before );
    // the intro queues the first broadcast five minutes on; drop it
    effect_on_conditions::clear( you );
}
