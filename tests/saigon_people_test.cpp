#include <algorithm>
#include <functional>
#include <initializer_list>
#include <map>
#include <memory>
#include <set>
#include <stddef.h>
#include <string>
#include <utility>
#include <vector>

#include "avatar.h"
#include "calendar.h"
#include "cata_catch.h"
#include "character_id.h"
#include "dialogue_chatbin.h"
#include "math_parser_diag_value.h"
#include "global_vars.h"
#include "map_scale_constants.h"
#include "coordinates.h"
#include "dialogue.h"
#include "faction.h"
#include "game.h"
#include "item.h"
#include "item_group.h"
#include "item_location.h"
#include "itype.h"
#include "map.h"
#include "map_helpers.h"
#include "mapbuffer.h"
#include "memory_fast.h"
#include "mission.h"
#include "npc.h"
#include "npc_class.h"
#include "npctalk.h"
#include "overmap.h"
#include "overmapbuffer.h"
#include "pimpl.h"
#include "player_helpers.h"
#include "point.h"
#include "rng.h"
#include "type_id.h"
#include "value_ptr.h"
#include "visitable.h"

static const faction_id faction_no_faction( "no_faction" );
static const faction_id faction_sgn_giang_ho( "sgn_giang_ho" );
static const faction_id faction_sgn_hoi_cua( "sgn_hoi_cua" );
static const mission_type_id mission_MISSION_NULL( "MISSION_NULL" );
static const npc_template_id npc_template_sgn_npc_dai_ca( "sgn_npc_dai_ca" );
static const npc_template_id npc_template_sgn_npc_guard( "sgn_npc_guard" );
static const npc_template_id npc_template_sgn_npc_hung( "sgn_npc_hung" );
static const npc_template_id npc_template_sgn_npc_loc( "sgn_npc_loc" );
static const npc_template_id npc_template_sgn_npc_shopkeeper( "sgn_npc_shopkeeper" );
static const oter_str_id oter_sgn_people_giang_ho_z0_north( "sgn_people_giang_ho_z0_north" );

// Saigon 2000s mod, E1: the people of Saigon (npcs/factions.json, npcs/people_*.json,
// npcs/places.json, itemgroups/npc_people.json, overmap/sgn_people_specials.json,
// mapgen/people/).  Six factions, traders who can actually stock a shop, three three-step mission
// chains that each end in a recruit, two hostile sites (a giang hồ row and a looted nhà thuốc)
// whose people fight with blades and pipes, and four companions.  check_refs.py proves the ids
// resolve; these tests prove the content does what the ledger says it does.
// Run with: tests/cata_test --mods=dda,saigon_2000s "[saigon]"

// A cheap place to build on.  Generating a Saigon overmap takes about 100 s (megacity mode, with
// the neighbours it pulls in), so instead of clear_overmaps() these tests load the real-map test
// fixture (realmap_test/overmap_40_40.omap.gz: a field with one road and one shophouse column,
// marked "final" so nothing procedural is added; see saigon_realmap_test.cpp) as overmap (40, 40)
// and set their own terrain on it, away from that road (x 85-90) and column (y 89).
static tripoint_abs_omt sgn_people_spot( const point_rel_omt &offset )
{
    const point_abs_om om( 40, 40 );
    if( !overmap_buffer.has( om ) ) {
        get_globals().set_global_value( "overmap_pregenerated_path",
                                        diag_value( std::string( "saigon_2000s/realmap_test" ) ) );
        overmap_buffer.get( om );
        get_globals().remove_global_value( "overmap_pregenerated_path" );
    }
    return tripoint_abs_omt( 40 * OMAPX + offset.x(), 40 * OMAPY + offset.y(), 0 );
}

// A gun in the strict sense: anything with a GUN slot, slingshots and crossbows included.  The
// gang and the looters are melee-only, so even a primitive ranged weapon in their hands is a bug.
static bool sgn_is_any_gun( const itype *t )
{
    return t != nullptr && static_cast<bool>( t->gun );
}

static std::string sgn_guns_in_group( const item_group_id &group )
{
    std::string guns;
    for( const itype *t : item_group::every_possible_item_from( group ) ) {
        if( sgn_is_any_gun( t ) ) {
            guns += t->get_id().str() + " ";
        }
    }
    return guns;
}

static std::string sgn_guns_carried( const npc &guy )
{
    std::string guns;
    guy.visit_items( [&guns]( const item_location & it ) {
        if( it->is_gun() ) {
            guns += it->typeId().str() + " ";
        }
        return VisitResponse::NEXT;
    } );
    return guns;
}

// E1: "staff out of no_faction, whose wealth 1 starved their shops".  npc::shop_restock budgets a
// restock at faction wealth * 0.0075 and hands out faction currency at rng(5, 15) % of that
// budget, so a trader in a faction with no wealth opens with an empty counter, and one whose
// currency is worth more than the budget never has change to give.  This replays shop_restock's
// value loop (npc.cpp) on each trader's real groups, without the map zones it then fills.
// Breaks if: a trader is moved back into no_faction (wealth 1) or a faction's wealth is cut, a
// faction's currency id goes stale or is priced above what the budget can pay out, or a shop
// group is emptied or pointed at a missing group.
TEST_CASE( "saigon_traders_have_wealth_and_stock", "[saigon][npc]" )
{
    if( !npc_template_sgn_npc_shopkeeper.is_valid() ) {
        WARN( "saigon_2000s is not loaded; skipping" );
        return;
    }
    g->faction_manager_ptr->create_if_needed();
    // the six factions of E1 exist (a typo in a template's "faction" silently drops the NPC
    // into no_faction, so check the ids the templates are meant to use)
    for( const char *fid : {
             "sgn_phuong", "sgn_cho", "sgn_chua", "sgn_benh_vien", "sgn_giang_ho", "sgn_hoi_cua"
         } ) {
        CAPTURE( fid );
        const faction *fac = g->faction_manager_ptr->get( faction_id( fid ), false );
        REQUIRE( fac != nullptr );
        // wealth 1 was the original bug; give every faction a real treasury
        CHECK( fac->wealth >= 100000 );
    }

    int traders = 0;
    std::set<std::string> trader_ids;
    for( const auto &pair : npc_template::get_npc_templates() ) {
        const std::string id = pair.first.str();
        const npc &guy = pair.second.guy;
        if( id.rfind( "sgn_npc_", 0 ) != 0 || !guy.myclass.is_valid() ) {
            continue;
        }
        const std::vector<shopkeeper_item_group> &shop = guy.myclass->get_shopkeeper_items();
        // a SHOPKEEP mission with no shop groups is a counter with nothing on it
        if( guy.mission == npc_mission::NPC_MISSION_SHOPKEEP ) {
            CAPTURE( id );
            CHECK( !shop.empty() );
        }
        if( shop.empty() ) {
            continue;
        }
        CAPTURE( id );
        traders++;
        trader_ids.insert( id );
        // a trader belongs to a real Saigon faction, never no_faction
        CHECK( guy.get_fac_id().str().rfind( "sgn_", 0 ) == 0 );
        const faction *fac = g->faction_manager_ptr->get( guy.get_fac_id(), false );
        REQUIRE( fac != nullptr );
        const int shop_value = fac->wealth * 0.0075;
        CAPTURE( fac->id.str(), fac->wealth, shop_value );
        REQUIRE( shop_value > 0 );
        if( !fac->currency.is_empty() ) {
            REQUIRE( fac->currency.is_valid() );
            const int price = item( fac->currency ).price( true );
            CAPTURE( fac->currency.str(), price );
            REQUIRE( price > 0 );
            // the median roll, rng(5, 15) = 10, must hand the trader at least one coin
            CHECK( 10 * shop_value / 100 / price >= 1 );
        }
        std::vector<item_group_id> value_groups;
        for( const shopkeeper_item_group &sg : shop ) {
            CAPTURE( sg.id.str() );
            REQUIRE( item_group::group_is_defined( sg.id ) );
            CHECK( !item_group::every_possible_item_from( sg.id ).empty() );
            if( !sg.rigid ) {
                value_groups.push_back( sg.id );
            }
        }
        REQUIRE( !value_groups.empty() );
        // shop_restock's loop: draw from the value groups until the budget is spent
        rng_set_engine_seed( 7 );
        int budget = shop_value;
        int goods = 0;
        for( int tries = 0; budget > 0 && tries < 2000; tries++ ) {
            const item it = item_group::item_from( random_entry( value_groups ), calendar::turn );
            if( !it.is_null() ) {
                goods++;
                budget -= it.price( true );
            }
        }
        CAPTURE( goods );
        // a counter worth visiting: a handful of things at least
        CHECK( goods >= 5 );
    }
    // the chợ shopkeeper, the hospital's pharmacy counter and chú Tư's petrol bottles
    CHECK( trader_ids.count( "sgn_npc_shopkeeper" ) == 1 );
    CHECK( trader_ids.count( "sgn_npc_doctor" ) == 1 );
    CHECK( trader_ids.count( "sgn_npc_chu_tu" ) == 1 );
    CHECK( traders >= 3 );
}

// E1: three chains, one per faction that has something to ask: the ward (guard), the hospital
// (doctor) and the chợ (vendor).  Each is offered by its staff member, runs three steps through
// "followup" and ends in recruiting a companion.  Breaks if: a followup is dropped or misspelt (the
// chain stops at step 1 or 2), a step is added or a chain loops, the last step stops being a
// recruit, the offer moves off the staff template, or a step leaks into a random-NPC pool
// (ORIGIN_ANY_NPC / OPENER), where a stranger would offer step 2 out of context.
TEST_CASE( "saigon_mission_chains_end_in_recruits", "[saigon][npc][mission]" )
{
    if( !npc_template_sgn_npc_guard.is_valid() ) {
        WARN( "saigon_2000s is not loaded; skipping" );
        return;
    }
    const std::vector<std::pair<std::string, std::string>> chains = {
        { "sgn_npc_guard", "MISSION_SGN_PHUONG_DONG_CHI" },
        { "sgn_npc_doctor", "MISSION_SGN_BV_KHANG_SINH" },
        { "sgn_npc_vendor", "MISSION_SGN_CHO_CAN_NUOC" },
    };
    std::set<mission_type_id> all_steps;
    for( const auto &chain : chains ) {
        CAPTURE( chain.first, chain.second );
        const npc_template_id giver( chain.first );
        REQUIRE( giver.is_valid() );
        const std::vector<mission_type_id> &offered =
            npc_template::get_npc_templates().at( giver ).guy.miss_ids;
        CHECK( std::find( offered.begin(), offered.end(),
                          mission_type_id( chain.second ) ) != offered.end() );
        std::vector<const mission_type *> steps;
        mission_type_id at( chain.second );
        while( !at.is_null() && at != mission_MISSION_NULL && steps.size() < 10 ) {
            const mission_type *t = mission_type::get( at );
            CAPTURE( at.str() );
            REQUIRE( t != nullptr );
            steps.push_back( t );
            // each step is a mission of its own, not shared with another chain
            CHECK( all_steps.insert( at ).second );
            at = t->follow_up;
        }
        REQUIRE( steps.size() == 3 );
        for( size_t i = 0; i < steps.size(); i++ ) {
            const mission_type &t = *steps[i];
            CAPTURE( t.id.str() );
            // only ever offered as a follow-up or by its own NPC
            for( const mission_origin o : t.origins ) {
                CHECK( o == ORIGIN_SECONDARY );
            }
            // the recruit is the payoff: it is the last step and only the last
            if( i + 1 == steps.size() ) {
                CHECK( t.goal == mission_goal::MGOAL_RECRUIT_NPC );
            } else {
                CHECK( t.goal != mission_goal::MGOAL_RECRUIT_NPC );
            }
        }
    }
}

// E1: the two hostile sites, generated for real.  mapgen place_npcs puts the gang (sgn_npc_giang_ho,
// with Hùng locked in their back room) and the looters (sgn_npc_hoi_cua) onto the overmap, where
// map::place_npc leaves them.  Asserts: every NPC that appears is the site's faction (or Hùng),
// none carries any gun, no gun lies on the floor, and the item groups behind them can never yield
// one (the rolls are random, so the groups are checked exhaustively as well).
// Breaks if: a site places another faction's template or a vanilla one, a class's weapon/worn/carry
// group or a site loot group gains a firearm, slingshot or crossbow, or Hùng is dropped from the
// gang's row (he is one of the four companions and this is the only place he exists).
TEST_CASE( "saigon_people_sites_are_their_factions_and_melee_only", "[mapgen][saigon][npc]" )
{
    if( !oter_sgn_people_giang_ho_z0_north.is_valid() ) {
        WARN( "saigon_2000s is not loaded; skipping" );
        return;
    }
    // the groups, exhaustively: every class at these sites and their loot
    for( const char *cls : {
             "sgn_class_giang_ho", "sgn_class_dai_ca", "sgn_class_hoi_cua"
         } ) {
        CAPTURE( cls );
        const npc_class &c = npc_class_id( cls ).obj();
        for( const item_group_id &grp : {
                 c.weapon_override, c.worn_override, c.carry_override
             } ) {
            CAPTURE( grp.str() );
            REQUIRE( item_group::group_is_defined( grp ) );
            CHECK( sgn_guns_in_group( grp ).empty() );
        }
    }
    for( const char *loot : {
             "sgn_people_giang_ho_loot", "sgn_people_nha_thuoc_scraps", "sgn_people_nha_thuoc_stash"
         } ) {
        CAPTURE( loot );
        REQUIRE( item_group::group_is_defined( item_group_id( loot ) ) );
        CHECK( sgn_guns_in_group( item_group_id( loot ) ).empty() );
    }
    // the mission targets placed by update_mapgen belong to the site's faction too
    CHECK( npc_template::get_npc_templates().at( npc_template_sgn_npc_dai_ca )
           .guy.get_fac_id() == faction_sgn_giang_ho );
    CHECK( npc_template::get_npc_templates().at( npc_template_id( "sgn_npc_hoi_cua_dau" ) )
           .guy.get_fac_id() == faction_sgn_hoi_cua );

    clear_avatar();
    struct site {
        std::vector<std::string> levels;
        faction_id fac;
        int per_visit;      // NPCs the site's mapgen places every time (place_npcs, no chance)
    };
    const std::vector<site> sites = {
        {
            { "sgn_people_giang_ho_z0_north", "sgn_people_giang_ho_z1_north", "sgn_people_giang_ho_z2_north" },
            faction_sgn_giang_ho, 6
        },
        { { "sgn_people_nha_thuoc_z0_north", "sgn_people_nha_thuoc_z1_north" }, faction_sgn_hoi_cua, 3 },
    };
    // Hùng is placed with unique_id: if an earlier test made him, mapgen would skip him
    g->unique_npc_despawn( "sgn_unique_hung" );
    bool hung_seen = false;
    std::set<character_id> seen;
    int column = 0;
    for( const site &s : sites ) {
        CAPTURE( s.levels[0] );
        const tripoint_abs_omt pos = sgn_people_spot( point_rel_omt( 30 + 3 * column++, 40 ) );
        for( size_t z = 0; z < s.levels.size(); z++ ) {
            overmap_buffer.ter_set( pos + tripoint( 0, 0, z ), oter_str_id( s.levels[z] ).id() );
        }
        int people = 0;
        int floor_guns = 0;
        std::string floor_gun_ids;
        for( int seed = 1; seed <= 3; seed++ ) {
            rng_set_engine_seed( seed );
            MAPBUFFER.clear_outside_reality_bubble();
            smallmap tm;
            tm.generate( pos, calendar::turn, true, true );
            map &m = *tm.cast_to_map();
            for( int z = 0; z < static_cast<int>( s.levels.size() ); z++ ) {
                for( int x = 0; x < SEEX * 2; x++ ) {
                    for( int y = 0; y < SEEY * 2; y++ ) {
                        for( const item &it : m.i_at( tripoint_bub_ms( x, y, z ) ) ) {
                            if( it.is_gun() || it.has_item_with( []( const item & e ) {
                            return e.is_gun();
                            } ) ) {
                                floor_guns++;
                                floor_gun_ids += it.typeId().str() + " ";
                            }
                        }
                    }
                }
            }
            const point_abs_om om = project_to<coords::om>( pos.xy() );
            for( const shared_ptr_fast<npc> &who : overmap_buffer.get( om ).get_npcs() ) {
                if( who->pos_abs_omt().xy() != pos.xy() || !seen.insert( who->getID() ).second ) {
                    continue;
                }
                people++;
                CAPTURE( who->idz.str(), who->get_fac_id().str() );
                if( who->idz == npc_template_sgn_npc_hung ) {
                    hung_seen = true;
                } else {
                    CHECK( who->get_fac_id() == s.fac );
                }
                CHECK( sgn_guns_carried( *who ).empty() );
            }
        }
        CAPTURE( floor_gun_ids );
        CHECK( floor_guns == 0 );
        // 4 + 2 gang members (plus Hùng once), or 3 looters, per generation: a site that
        // places nobody would pass every check above
        CHECK( people >= 3 * s.per_visit );
    }
    CHECK( hung_seen );
}

// E1: the four companions (Lộc, Ngọc Anh, Hùng, chú Sáu), the reward of each chain and of the gang
// row.  Each one is talked to for real: his or her first topic must offer a response that leads to
// the _YES topic, and applying it must make the NPC follow you.  The vars a chain sets on the way
// (the đại ca dead, the hospital's trust, the question about the trucks) are set first, since the
// recruiting line is conditional on them.
// Breaks if: a companion's template or chat is renamed, a companion is put in a hostile faction,
// the recruit line loses its "follow" effect, or its condition names a var no chain sets.
TEST_CASE( "saigon_companions_can_be_recruited", "[saigon][npc]" )
{
    if( !npc_template_sgn_npc_loc.is_valid() ) {
        WARN( "saigon_2000s is not loaded; skipping" );
        return;
    }
    clear_avatar();
    clear_map_without_vision();
    g->faction_manager_ptr->create_if_needed();
    avatar &you = get_avatar();
    you.setpos( get_map(), tripoint_bub_ms( 15, 15, 0 ) );
    you.set_value( "sgn_dai_ca_dead", "yes" );
    you.set_value( "sgn_bv_trust", "yes" );
    you.set_value( "sgn_chu_sau_trucks", "yes" );
    int x = 20;
    for( const char *who : {
             "sgn_npc_loc", "sgn_npc_ngoc_anh", "sgn_npc_hung", "sgn_npc_chu_sau"
         } ) {
        CAPTURE( who );
        REQUIRE( npc_template_id( who ).is_valid() );
        npc &guy = spawn_npc( point_bub_ms( x, 15 ), who );
        x += 3;
        // a companion is nobody's soldier: not in a hostile faction, not out to kill you
        CHECK( guy.get_fac_id() == faction_no_faction );
        CHECK( guy.get_attitude() != NPCATT_KILL );
        CHECK_FALSE( guy.is_player_ally() );
        const std::string first = guy.chatbin.first_topic;
        REQUIRE( get_talk_topic( first ) != nullptr );
        dialogue d( get_talker_for( you ), get_talker_for( guy ) );
        d.add_topic( first );
        d.gen_responses( d.topic_stack.back() );
        const talk_response *yes = nullptr;
        for( const talk_response &r : d.responses ) {
            if( r.success.next_topic.id == first + "_YES" ) {
                yes = &r;
            }
        }
        REQUIRE( yes != nullptr );
        yes->success.apply( d );
        CHECK( guy.is_player_ally() );
    }
}
