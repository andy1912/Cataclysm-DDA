#include <algorithm>
#include <set>
#include <string>
#include <vector>

#include "cata_catch.h"
#include "mongroup.h"
#include "mtype.h"
#include "type_id.h"

// Saigon 2000s mod, L-loc7: the delta's wildlife (data/mods/saigon_2000s/monsters/wildlife*.json).
// The fields, swamps and rivers around Saigon spawn dda's wilderness groups, and fishing catches
// from GROUP_FISH; the mod overrides them, so the engine's own expansion of those groups holds
// no North American wildlife, and the fish you catch are the delta's.
// Run with: tests/cata_test --mods=dda,saigon_2000s "[saigon]"

static std::set<std::string> expand( const char *group )
{
    std::set<std::string> out;
    for( const mtype_id &m : MonsterGroupManager::GetMonstersFromGroup( mongroup_id( group ), true ) ) {
        out.insert( m.str() );
    }
    return out;
}

TEST_CASE( "saigon_delta_wildlife", "[saigon]" )
{
    const std::vector<std::string> north_american = {
        "mon_moose", "mon_deer", "mon_reindeer", "mon_bobcat", "mon_cougar", "mon_coyote", "mon_raccoon",
        "mon_opossum", "mon_skunk", "mon_chipmunk", "mon_groundhog", "mon_beaver", "mon_muskrat", "mon_mink",
        "mon_goose_canadian", "mon_turkey", "mon_bear", "mon_zoose", "mon_zougar", "mon_zeer", "mon_lemming",
        "mon_rattlesnake", "mon_fish_rainbow_trout", "mon_fish_salmon", "mon_fish_walleye", "mon_fish_pike",
        "mon_fish_perch", "mon_fish_sbass", "mon_fish_muskellunge", "mon_leo_frog", "mon_peeper_frog"
    };
    for( const char *group : { "GROUP_FOREST", "GROUP_SWAMP", "GROUP_RIVER", "GROUP_FISH" } ) {
        CAPTURE( group );
        const std::set<std::string> animals = expand( group );
        CHECK_FALSE( animals.empty() );
        for( const std::string &m : north_american ) {
            CAPTURE( m );
            CHECK( animals.count( m ) == 0 );
        }
    }
    // the delta's own: rice-field rats in the fields, egrets on the river
    CHECK( expand( "GROUP_FOREST" ).count( "sgn_mon_chuot_dong" ) == 1 );
    CHECK( expand( "GROUP_SWAMP" ).count( "sgn_mon_chuot_dong" ) == 1 );
    CHECK( expand( "GROUP_RIVER" ).count( "sgn_mon_co" ) == 1 );
    // what you catch: cá lóc, cá rô phi, cá tra, cá trê, cá rô đồng, lươn, cá chép, cá trắm cỏ
    const std::set<std::string> fish = expand( "GROUP_FISH" );
    CHECK( fish.count( "mon_fish_bowfin" ) == 1 );
    CHECK( mtype_id( "mon_fish_bowfin" )->nname() == "snakehead" );
    CHECK( mtype_id( "mon_fish_bluegill" )->nname() == "tilapia" );
    CHECK( mtype_id( "mon_fish_bullhead" )->nname() == "walking catfish" );
    // the zoo's animals do not breed into the wild (an elephant copied from dda's moose had moose
    // calves, the python rattlesnakes, the crocodile snapping turtles, the tiger cougar kittens)
    for( const char *zoo : { "sgn_mon_voi", "sgn_mon_tran", "sgn_mon_ca_sau", "mon_tiger", "mon_bear", "mon_deer" } ) {
        CAPTURE( zoo );
        CHECK( mtype_id( zoo )->has_flag( mon_flag_NO_BREED ) );
    }
    // a cobra's young grow into cobras, not timber rattlesnakes
    const mtype &young = *mtype_id( "sgn_mon_ran_ho_mang_con" );
    CHECK( young.upgrade_into == mtype_id( "sgn_mon_ran_ho_mang" ) );
    CHECK( mtype_id( "sgn_mon_ran_ho_mang" )->baby_type.baby_monster == mtype_id( "sgn_mon_ran_ho_mang_con" ) );
}
