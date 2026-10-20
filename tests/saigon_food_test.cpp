#include <algorithm>
#include <functional>
#include <initializer_list>
#include <list>
#include <map>
#include <optional>
#include <set>
#include <string>
#include <utility>
#include <vector>

#include "avatar.h"
#include "calendar.h"
#include "cata_catch.h"
#include "character.h"
#include "character_attire.h"
#include "coordinates.h"
#include "debug.h"
#include "enums.h"
#include "item.h"
#include "item_group.h"
#include "item_transformation.h"
#include "itype.h"
#include "map.h"
#include "map_helpers.h"
#include "map_helpers_tests.h"
#include "output.h"
#include "player_activity.h"
#include "player_helpers.h"
#include "pocket_type.h"
#include "point.h"
#include "recipe.h"
#include "requirements.h"
#include "ret_val.h"
#include "type_id.h"
#include "units.h"
#include "value_ptr.h"

static const itype_id itype_debug_backpack( "debug_backpack" );
static const itype_id itype_hammer( "hammer" );
static const itype_id itype_jug_plastic( "jug_plastic" );
static const itype_id itype_knife_huge( "knife_huge" );
static const itype_id itype_mortar_pestle( "mortar_pestle" );
static const itype_id itype_popcan_stove( "popcan_stove" );
static const itype_id itype_pot_canning( "pot_canning" );
static const itype_id itype_sgn_da_bao( "sgn_da_bao" );
static const itype_id itype_sgn_da_cay( "sgn_da_cay" );
static const itype_id itype_sgn_da_vien( "sgn_da_vien" );
static const itype_id itype_water( "water" );
static const itype_id itype_water_clean( "water_clean" );
static const flag_id json_flag_CONTAINER( "CONTAINER" );

// Saigon 2000s mod, V1 "the southern table" (items/food/vn_food_*.json, recipes/vn_food.json,
// itemgroups/vn_food.json): melting ice, the new dishes' recipes, and the four food groups.
// Run with: tests/cata_test --mods=dda,saigon_2000s "[saigon][food]"

static const activity_id ACT_CRAFT( "ACT_CRAFT" );

static const trait_id trait_DEBUG_CNF( "DEBUG_CNF" );

static bool saigon_loaded()
{
    if( !itype_sgn_da_cay.is_valid() ) {
        WARN( "saigon_2000s is not loaded; skipping" );
        return false;
    }
    return true;
}

TEST_CASE( "saigon_ice_melts_into_water", "[saigon][food]" )
{
    if( !saigon_loaded() ) {
        return;
    }
    struct ice_case {
        itype_id ice;
        time_duration melt;
        itype_id water;
        int charges;
    };
    const std::vector<ice_case> cases = {
        { itype_sgn_da_cay, 10_hours, itype_water, 20 },
        { itype_sgn_da_vien, 4_hours, itype_water_clean, 8 },
        { itype_sgn_da_bao, 45_minutes, itype_water, 1 },
    };
    map &here = get_map();
    const time_point start = calendar::turn;
    for( const ice_case &c : cases ) {
        CAPTURE( c.ice.str() );
        calendar::turn = start;
        item ice( c.ice );
        // SPAWN_ACTIVE: the ice is processed (and so melts) from the moment it spawns
        REQUIRE( ice.active );
        REQUIRE( ice.countdown_point == start + c.melt );

        // a minute before its time it is still ice
        calendar::turn = start + c.melt - 1_minutes;
        CHECK_FALSE( ice.process( here, nullptr, tripoint_bub_ms( 60, 60, 0 ) ) );
        CHECK( ice.typeId() == c.ice );

        // at its time it is water, of the right kind, and the item is not destroyed
        calendar::turn = start + c.melt;
        CHECK_FALSE( ice.process( here, nullptr, tripoint_bub_ms( 60, 60, 0 ) ) );
        CHECK( ice.typeId() == c.water );
        CHECK( ice.made_of( phase_id::LIQUID ) );
        CHECK( ice.countdown_point == calendar::turn_max );
    }
    calendar::turn = start;
}

// How much water the ice leaves: as many 250 ml charges as the ice weighed.
TEST_CASE( "saigon_ice_melt_charges", "[saigon][food]" )
{
    if( !saigon_loaded() ) {
        return;
    }
    const std::vector<std::pair<itype_id, int>> cases = {
        { itype_sgn_da_cay, 20 }, { itype_sgn_da_vien, 8 }, { itype_sgn_da_bao, 1 }
    };
    map &here = get_map();
    const time_point start = calendar::turn;
    for( const std::pair<itype_id, int> &c : cases ) {
        CAPTURE( c.first.str() );
        calendar::turn = start;
        item ice( c.first );
        calendar::turn = start + 1_days;
        ice.process( here, nullptr, tripoint_bub_ms( 60, 60, 0 ) );
        CHECK( ice.charges == c.second );
        // the mass of the water left is the mass of the ice
        CHECK( to_gram( ice.weight() ) == to_gram( item( c.first ).weight() ) );
    }
    calendar::turn = start;
}

// Ice lying on the floor of the map melts as the game processes the map's active items.
TEST_CASE( "saigon_ice_melts_on_the_map", "[saigon][food]" )
{
    if( !saigon_loaded() ) {
        return;
    }
    clear_map_without_vision();
    map &here = get_map();
    const time_point start = calendar::turn;
    const tripoint_bub_ms spot( 62, 60, 0 );
    here.add_item( spot, item( itype_sgn_da_vien ) );
    REQUIRE( here.i_at( spot ).size() == 1 );
    calendar::turn = start + 4_hours + 1_turns;
    here.process_items();
    bool found_water = false;
    for( const item &it : here.i_at( spot ) ) {
        CHECK( it.typeId() != itype_sgn_da_vien );
        found_water |= it.typeId() == itype_water_clean;
    }
    CHECK( found_water );
    clear_items( 0 );
    calendar::turn = start;
}

static const std::set<std::string> vn_food_groups = {
    "sgn_vn_food_street", "sgn_vn_food_fruit", "sgn_vn_drinks", "sgn_vn_ice"
};

TEST_CASE( "saigon_vn_food_groups", "[saigon][food]" )
{
    if( !saigon_loaded() ) {
        return;
    }
    for( const std::string &g : vn_food_groups ) {
        CAPTURE( g );
        const item_group_id gid( g );
        REQUIRE( item_group::group_is_defined( gid ) );
        const std::set<const itype *> all = item_group::every_possible_item_from( gid );
        CHECK( !all.empty() );
        for( const itype *t : all ) {
            CAPTURE( t->get_id().str() );
            // food or drink, the bag, bottle or jar it spawns in, or ice (not itself food: it
            // melts into water)
            const bool comestible = !!t->comestible;
            const bool container = t->has_flag( json_flag_CONTAINER ) || !t->pockets.empty();
            const bool melts = t->transform_into && t->countdown_interval > 0_seconds &&
                               t->transform_into->target.is_valid() &&
                               !!t->transform_into->target->comestible;
            CHECK( ( comestible || container || melts ) );
        }
        // what actually spawns: every top-level item is a comestible or holds only comestibles
        for( int i = 0; i < 40; i++ ) {
            for( const item &it : item_group::items_from( gid, calendar::turn ) ) {
                CAPTURE( it.typeId().str() );
                if( it.is_comestible() || ( it.type->transform_into &&
                                            it.countdown_point != calendar::turn_max ) ) {
                    continue;
                }
                const std::list<const item *> inside = it.all_items_top();
                CHECK( !inside.empty() );
                for( const item *in : inside ) {
                    CAPTURE( in->typeId().str() );
                    CHECK( in->is_comestible() );
                }
            }
        }
    }
}

// the 22 recipes of recipes/vn_food.json
static const std::vector<std::string> vn_food_recipes = {
    "sgn_da_bao_sgn_from_block", "sgn_da_bao_sgn_from_bag", "sgn_tra_da_sgn_with_ice",
    "sgn_ca_phe_sua_da_sgn_with_ice", "sgn_che_sgn_with_ice", "sgn_bun_rieu", "sgn_banh_canh",
    "sgn_com_chien", "sgn_chao_vit", "sgn_oc_luoc", "sgn_oc_xao", "sgn_goi_du_du",
    "sgn_banh_trang_tron", "sgn_bot_chien", "sgn_ca_kho_to", "sgn_canh_chua",
    "sgn_thit_kho_trung", "sgn_sinh_to", "sgn_nuoc_rau_ma", "sgn_nuoc_sam", "sgn_sua_bap",
    "sgn_ruou_thuoc"
};

// A kitchen that covers the recipes' qualities and heat: COOK 3/BOIL 2 (canning pot), CUT 2,
// FINE_GRIND 1 (mortar), HAMMER 3, and ten fuelled pop-can stoves for water_boiling_heat and
// surface_heat.
static void give_kitchen( Character &you )
{
    you.clear_worn();
    you.remove_weapon();
    you.worn.wear_item( you, item( itype_debug_backpack ), false, false );
    REQUIRE( you.i_add( item( itype_knife_huge ) ) );
    REQUIRE( you.i_add( item( itype_hammer ) ) );
    for( int i = 0; i < 10; i++ ) {
        REQUIRE( you.i_add( tool_with_ammo( itype_popcan_stove, 500 ) ) );
    }
    // BOIL tools last, so that nothing is put inside them
    REQUIRE( you.i_add( item( itype_pot_canning ) ) );
    REQUIRE( you.i_add( item( itype_mortar_pestle ) ) );
}

// Put `count` of `id` (charges or pieces) on the floor beside the cook; liquids in a jug.
static void place_component( map &here, const tripoint_bub_ms &spot, const itype_id &id,
                             int count )
{
    item it( id, calendar::turn );
    if( it.count_by_charges() ) {
        it.charges = count;
        if( it.made_of( phase_id::LIQUID ) ) {
            item jug( itype_jug_plastic );
            REQUIRE( jug.put_in( it, pocket_type::CONTAINER ).success() );
            here.add_item( spot, jug );
        } else {
            here.add_item( spot, it );
        }
    } else {
        for( int i = 0; i < count; i++ ) {
            here.add_item( spot, it );
        }
    }
}

// Give the cook alternative `pick` (first or last) of every component group; tools from the
// kitchen, or else alternative `pick` of the group.
static void stock_for( const recipe &r, bool last )
{
    map &here = get_map();
    Character &you = get_player_character();
    const tripoint_bub_ms spot = you.pos_bub() + tripoint::east;
    const requirement_data &req = r.simple_requirements();
    for( const std::vector<item_comp> &alts : req.get_components() ) {
        REQUIRE( !alts.empty() );
        const item_comp &c = last ? alts.back() : alts.front();
        INFO( "component " << c.type.str() );
        REQUIRE( c.type.is_valid() );
        place_component( here, spot, c.type, c.count );
    }
    const std::set<itype_id> kitchen = {
        itype_knife_huge, itype_hammer, itype_popcan_stove, itype_pot_canning, itype_mortar_pestle
    };
    for( const std::vector<tool_comp> &alts : req.get_tools() ) {
        bool have = false;
        for( const tool_comp &t : alts ) {
            have |= kitchen.count( t.type ) > 0;
        }
        if( !have ) {
            const tool_comp &t = last ? alts.back() : alts.front();
            INFO( "tool " << t.type.str() );
            REQUIRE( t.type.is_valid() );
            here.add_item( spot, t.count > 0 ? tool_with_ammo( t.type, t.count * 2 ) : item( t.type ) );
        }
    }
}

static void prep_cook( const recipe &r )
{
    clear_avatar();
    clear_items( 0 );
    Character &you = get_player_character();
    you.toggle_trait( trait_DEBUG_CNF );
    for( const std::pair<const skill_id, int> &skl : r.required_skills ) {
        you.set_skill_level( skl.first, skl.second );
        you.set_knowledge_level( skl.first, skl.second );
    }
    you.set_skill_level( r.skill_used, std::max( r.difficulty, 1 ) );
    you.set_knowledge_level( r.skill_used, std::max( r.difficulty, 1 ) );
    for( const recipe_proficiency &rprof : r.get_proficiencies() ) {
        you.add_proficiency( rprof.id, true );
    }
    give_kitchen( you );
}

static bool can_make_now( const recipe &r )
{
    Character &you = get_player_character();
    you.invalidate_crafting_inventory();
    const deduped_requirement_data &req = r.deduped_requirements();
    const std::string missing = enumerate_as_string( req.alternatives(),
    []( const requirement_data & rd ) {
        return rd.list_missing();
    } );
    CAPTURE( missing );
    const bool ok = req.can_make_with_inventory( &you, you.crafting_inventory(),
                    r.get_component_filter() );
    CHECK( ok );
    return ok;
}

// A recipe that makes several portions must take each charged component in a multiple of them:
// the engine splits components between the results (item_components::split) and raises a
// debugmsg when it cannot.  sgn_thit_kho_trung made 2 from 1 nước dừa until this test found it.

TEST_CASE( "saigon_vn_food_recipes_craftable", "[saigon][food]" )
{
    if( !saigon_loaded() ) {
        return;
    }
    clear_map_without_vision();
    const time_point start = calendar::turn;
    set_time( calendar::turn_zero + 12_hours );
    avatar &you = get_avatar();
    for( const std::string &rs : vn_food_recipes ) {
        CAPTURE( rs );
        const recipe_id rid( rs );
        REQUIRE( rid.is_valid() );
        const recipe &r = rid.obj();
        CHECK_FALSE( r.is_blacklisted() );
        CHECK( r.result().is_valid() );

        // with nothing but the kitchen, it cannot be made (it really needs its components)
        prep_cook( r );
        you.invalidate_crafting_inventory();
        CHECK_FALSE( r.deduped_requirements().can_make_with_inventory( &you, you.crafting_inventory(),
                     r.get_component_filter() ) );

        // the first and the last alternative of every component group each make it
        for( const bool last : {
                 false, true
             } ) {
            CAPTURE( last );
            prep_cook( r );
            stock_for( r, last );
            can_make_now( r );
        }

        // and the craft runs to the end, with the first and with the last alternatives, without
        // an error.  Liquid results are left out: putting a crafted liquid away asks the player
        // for a container (a menu).
        if( item( r.result() ).made_of( phase_id::LIQUID ) ) {
            continue;
        }
        for( const bool last : {
                 false, true
             } ) {
            CAPTURE( last );
            prep_cook( r );
            stock_for( r, last );
            if( !can_make_now( r ) ) {
                continue;
            }
            you.learn_recipe( &r );
            REQUIRE( you.has_recipe( &r ) );
            int turns = 0;
            const std::string errors = capture_debugmsg_during( [&]() {
                you.make_craft( rid, 1 );
                REQUIRE( you.activity );
                REQUIRE( you.activity.id() == ACT_CRAFT );
                while( you.activity.id() == ACT_CRAFT && turns < 100000 ) {
                    ++turns;
                    you.set_moves( 100 );
                    you.activity.do_turn( you );
                }
            } );
            CAPTURE( errors );
            CHECK( errors.empty() );
            CHECK( turns < 100000 );
            bool made = you.has_item_with( [&]( const item & it ) {
                return it.typeId() == r.result();
            } );
            for( const item &it : get_map().i_at( you.pos_bub() ) ) {
                made |= it.typeId() == r.result();
            }
            CHECK( made );
        }
    }
    clear_items( 0 );
    clear_avatar();
    calendar::turn = start;
}
