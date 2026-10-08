#include <memory>
#include <set>
#include <string>

#include "cata_catch.h"
#include "item.h"
#include "memory_fast.h"
#include "mission.h"
#include "npc.h"
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
