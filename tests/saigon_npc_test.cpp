#include <memory>
#include <set>
#include <string>
#include <utility>
#include <vector>

#include "cata_catch.h"
#include "creature_tracker.h"
#include "item.h"
#include "item_group.h"
#include "item_location.h"
#include "memory_fast.h"
#include "map.h"
#include "map_helpers.h"
#include "mission.h"
#include "npc.h"
#include "npc_class.h"
#include "npctalk.h"
#include "dialogue.h"
#include "omdata.h"
#include "overmapbuffer.h"
#include "player_helpers.h"
#include "profession.h"
#include "scenario.h"
#include "type_id.h"
#include "visitable.h"

// Saigon 2000s mod, N0/N1: the people who wander Saigon's streets.  A random NPC
// (game::perhaps_add_random_npc, and the starting NPC) is classless: Character::randomize gives
// it a profession the scenario allows (Saigon's), npc::starting_inv_passtime dresses and arms it
// from the item groups NC_NONE_* / NC_NONE_HARDENED_* (itemgroups/npc_wanderer.json: dda's gave
// American handguns, rifles and bows), and it offers one mission from the ORIGIN_ANY_NPC pool
// (a starting NPC: ORIGIN_OPENER_NPC), from which npcs/vanilla_off.json takes dda's American-flag,
// Jabberwock and Zombie Mom missions.  2009 Saigon civilians carried no guns.
// Names (N2): snippets/names.json puts Vietnamese names, family name first, ahead of dda's
// English ones about 97 to 3.
// Run with: tests/cata_test --mods=dda,saigon_2000s "[saigon]"

// the test run also loads TEST_DATA (test_* ids), which the game never has
static bool test_only( const std::string &id )
{
    return id.rfind( "test_", 0 ) == 0;
}

TEST_CASE( "saigon_random_npcs", "[saigon]" )
{
    const string_id<scenario> saigon( "sgn_saigon_2009" );
    if( !saigon.is_valid() ) {
        WARN( "saigon_2000s is not loaded; skipping" );
        return;
    }
    const std::set<std::string> family = {
        "Nguyễn", "Trần", "Lê", "Phạm", "Huỳnh", "Võ", "Phan", "Trương", "Bùi", "Đặng", "Đỗ", "Ngô",
        "Hồ", "Dương", "Lý", "Lâm", "Châu", "Tạ"
    };
    int vietnamese = 0;
    const scenario *before = get_scenario();
    set_scenario( &saigon.obj() );
    // a random NPC, made the way the game makes one: a Saigon profession, no firearm
    for( int i = 0; i < 60; i++ ) {
        shared_ptr_fast<npc> guy = make_shared_fast<npc>();
        guy->normalize();
        guy->randomize();
        CAPTURE( guy->get_name() );
        vietnamese += family.count( guy->get_name().substr( 0, guy->get_name().find( ' ' ) ) );
        CAPTURE( guy->prof->ident().str() );
        CHECK( guy->prof->ident().str().rfind( "sgn_", 0 ) == 0 );
        int guns = 0;
        std::string gun;
        guy->visit_items( [&guns, &gun]( const item * it, item * ) {
            if( it->is_gun() ) {
                guns++;
                gun = it->typeId().str();
            }
            return VisitResponse::NEXT;
        } );
        CAPTURE( gun );
        CHECK( guns == 0 );
    }
    // about 97 % Vietnamese: at least 50 of 60
    CHECK( vietnamese >= 50 );
    set_scenario( before );
    // the missions random and starting NPCs can offer are Saigon's
    for( const mission_type &t : mission_type::get_all() ) {
        for( const mission_origin origin : t.origins ) {
            if( origin == ORIGIN_ANY_NPC || origin == ORIGIN_OPENER_NPC ) {
                CAPTURE( t.id.str() );
                CHECK( ( t.id.str().rfind( "MISSION_SGN_", 0 ) == 0 || test_only( t.id.str() ) ) );
            }
        }
    }
}

// N5: npcs/vanilla_off.json took dda's fourteen ORIGIN_OPENER_NPC and ten ORIGIN_ANY_NPC
// missions out of the pools in N1, which left every random NPC with nothing to offer.  The
// check above only proves the pools hold no American missions; it happily passes on an empty
// pool, which is how that went unnoticed.  So assert they are actually filled.
TEST_CASE( "saigon_npc_mission_pools", "[saigon]" )
{
    const string_id<scenario> saigon( "sgn_saigon_2009" );
    if( !saigon.is_valid() ) {
        WARN( "saigon_2000s is not loaded; skipping" );
        return;
    }
    // the guarantor at the start location draws from OPENER (game.cpp: the starting NPC), every
    // other civilian on the street draws from ANY_NPC, so both have to be non-empty or the game
    // opens with no one to talk to
    int opener = 0;
    int any_npc = 0;
    for( const mission_type &t : mission_type::get_all() ) {
        if( test_only( t.id.str() ) ) {
            continue;       // TEST_DATA's missions are not in the pool a player sees
        }
        for( const mission_origin origin : t.origins ) {
            if( origin == ORIGIN_OPENER_NPC ) {
                CAPTURE( t.id.str() );
                opener++;
            } else if( origin == ORIGIN_ANY_NPC ) {
                CAPTURE( t.id.str() );
                any_npc++;
            }
        }
    }
    CHECK( opener >= 2 );
    CHECK( any_npc >= 5 );
}

// N6: the people who hold a place.  gen_saigon_landmarks.py's STAFF table and gen_places.py's
// builders put an npc template (npcs/places.json) into the mapgen with place_npcs, so a
// landmark is not an abandoned shell.  check_refs.py asserts that every one of the mod's
// buildings names at least one such template; this generates the cheapest of them for real and
// counts who showed up.  Mapgen-placed NPCs are held on the overmap, not in the loaded map's
// submaps - map::place_npc ends in overmapbuffer::insert_npc - so that is where they are.
TEST_CASE( "saigon_place_spawns_people", "[mapgen][saigon]" )
{
    if( !oter_str_id( "sgn_pl_cong_an_00_north" ).is_valid() ) {
        WARN( "saigon_2000s is not loaded; skipping" );
        return;
    }
    clear_overmaps();
    clear_avatar();
    clear_map();
    const tripoint_abs_omt base( 20, 30, 0 );
    overmap_buffer.ter_set( base, oter_str_id( "sgn_pl_cong_an_00_north" ).id() );
    rng_set_engine_seed( 3 );
    get_map().load( project_to<coords::sm>( base ), false );
    const point_abs_om om = project_to<coords::om>( base.xy() );
    int people = 0;
    for( const shared_ptr_fast<npc> &who : overmap_buffer.get( om ).get_npcs() ) {
        if( project_to<coords::om>( who->pos_abs_omt().xy() ) == om ) {
            people++;
        }
    }
    CHECK( people >= 2 );
}

// N4: the mod has exactly one firearm, sgn_sung_9x18, and exactly one class may carry it.
// 2009 Saigon civilians carried no guns; a ward policeman kept a service pistol in a desk
// drawer, and a guard away from the desk is the man holding it.  audit_us_content.py proves the
// same thing across the mod's loot groups as well (that the pistol reaches nothing else), so
// this covers the other half: that it reaches somebody, and that it is only ever him.
// Adding a gun to any other sgn_* class fails here and in the audit.
TEST_CASE( "saigon_only_the_guard_is_armed", "[saigon]" )
{
    if( !npc_class_id( "sgn_class_guard" ).is_valid() ) {
        WARN( "saigon_2000s is not loaded; skipping" );
        return;
    }
    REQUIRE( itype_id( "sgn_sung_9x18" ).is_valid() );
    const itype_id pistol( "sgn_sung_9x18" );
    std::set<npc_class_id> armed;
    for( const npc_class &c : npc_class::get_all() ) {
        if( c.id.str().rfind( "sgn_", 0 ) != 0 || !c.weapon_override.is_valid() ) {
            continue;
        }
        if( item_group::group_contains_item( c.weapon_override, pistol ) ) {
            CAPTURE( c.id.str() );
            armed.insert( c.id );
        }
    }
    for( const npc_class_id &who : armed ) {
        CAPTURE( who.str() );
        CHECK( who == npc_class_id( "sgn_class_guard" ) );
    }
    // and the guard's group really does hand him one, or this test would pass vacuously
    CHECK( item_group::group_contains_item(
               item_group_id( "sgn_npc_guard_weapon" ), pistol ) );
    // and it is loaded: a guard with an empty pistol is worse than one with a club.  A
    // weapon_override yields one item and a class with a carry_override never reaches
    // starting_inv_ammo, so the group's "charges" seats a loaded magazine; check that on real
    // guards.  One in five is armed, so 60 tries miss with odds of about 1 in 600,000.
    bool armed_guard = false;
    for( int i = 0; i < 60 && !armed_guard; i++ ) {
        shared_ptr_fast<npc> guard = make_shared_fast<npc>();
        guard->normalize();
        guard->randomize( npc_class_id( "sgn_class_guard" ) );
        const item_location held = guard->get_wielded_item();
        if( !held || held->typeId() != pistol ) {
            continue;
        }
        armed_guard = true;
        CHECK( held->magazine_current() != nullptr );
        if( held->magazine_current() != nullptr ) {
            CHECK( held->magazine_current()->typeId() == itype_id( "sgn_mag_9x18" ) );
        }
        CHECK( held->ammo_remaining() == 8 );
    }
    CHECK( armed_guard );
}

// N7: the people of Quận 1 have something to say.  N6 left all nineteen staff templates on
// chat TALK_DONE, which is only a bye message, so talking to the monk or the postal clerk got
// you nothing; worse, the doctor and the shopkeeper were given mission SHOPKEEP and could not be
// traded with at all, because a shop is reached by chaining the first topic to TALK_MISSION_LIST
// and TALK_DONE chains nowhere.  This checks the wiring, which is where that bug lives.
TEST_CASE( "saigon_staff_have_voices", "[saigon]" )
{
    if( !npc_template_id( "sgn_npc_monk" ).is_valid() ) {
        WARN( "saigon_2000s is not loaded; skipping" );
        return;
    }
    for( const auto &pair : npc_template::get_npc_templates() ) {
        const npc_template_id &id = pair.first;
        const npc_template &t = pair.second;
        if( id.str().rfind( "sgn_npc_", 0 ) != 0 ) {
            continue;
        }
        CAPTURE( id.str() );
        const std::string &first = t.guy.chatbin.first_topic;
        // TALK_DONE only ends the conversation, so a staff member on it has nothing to say
        CHECK( first != "TALK_DONE" );
        const json_talk_topic *topic = get_talk_topic( first );
        REQUIRE( topic != nullptr );
        // and if it runs a shop, the stock has to be reachable.  A SHOPKEEP mission offers no
        // shop of its own: the player has to be shown a response leading to TALK_MISSION_LIST,
        // which is where the shop is listed, so require it directly off the first topic rather
        // than two hops away, which is what a real conversation does.
        if( t.guy.mission == npc_mission::NPC_MISSION_SHOPKEEP ) {
            CHECK( topic->get_directly_reachable_topics( true ).count( "TALK_MISSION_LIST" ) > 0 );
        }
    }
}
