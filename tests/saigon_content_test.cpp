#include <algorithm>
#include <list>
#include <map>
#include <set>
#include <string>
#include <vector>

#include <queue>

#include "avatar.h"
#include "calendar.h"
#include "coordinates.h"
#include "global_vars.h"
#include "map.h"
#include "map_helpers.h"
#include "map_scale_constants.h"
#include "mapbuffer.h"
#include "mapdata.h"
#include "math_parser_diag_value.h"
#include "overmapbuffer.h"
#include "player_helpers.h"
#include "point.h"
#include "rng.h"
#include "cata_catch.h"
#include "effect_on_condition.h"
#include "flag.h"
#include "harvest.h"
#include "item.h"
#include "item_factory.h"
#include "item_group.h"
#include "item_transformation.h"
#include "iuse.h"
#include "iuse_actor.h"
#include "itype.h"
#include "omdata.h"
#include "profession.h"
#include "recipe.h"
#include "recipe_dictionary.h"
#include "requirements.h"
#include "scenario.h"
#include "start_location.h"
#include "stomach.h"
#include "filesystem.h"
#include "path_info.h"
#include "text_snippets.h"
#include "type_id.h"
#include "vehicle.h"
#include "visitable.h"
#include "worldfactory.h"

// Saigon 2000s mod, F1-C: content-wide invariants that no other gate checks (doc/saigon/
// TEST_MATRIX.md).  The engine's own load-time checks prove that ids resolve; these prove what
// the mod promises on top of that: a Saigon character starts with Saigon things and no gun, every
// recipe the mod adds can be learned and made from things that exist in the world, every book
// that teaches is somewhere to be found, and every item and loot group of the mod spawns.
// Content owned by the F1-E/W/V test units (people, encounters, weapons, food, lore, vehicles)
// is tested there; these cases only hold the mod-wide rules.
// Run with: tests/cata_test --mods=dda,saigon_2000s "[saigon_content]"

static const mod_id mod_saigon( "saigon_2000s" );

static bool sgn_id( const std::string &id )
{
    return id.rfind( "sgn_", 0 ) == 0;
}

// defined by the mod (the first source), not a dda item the mod only overrides
static bool item_from_saigon( const itype &t )
{
    return !t.src.empty() && t.src.front().second == mod_saigon;
}

// recipe::src is private: a recipe of the mod makes one of the mod's items, or carries an
// "sgn_" id_suffix on a dda result (tea_green_sgn_bao_loc, rehydration_drink_sgn_oresol)
static bool from_saigon( const recipe &r )
{
    return ( r.result().is_valid() && item_from_saigon( *r.result() ) ) ||
           r.ident().str().find( "_sgn_" ) != std::string::npos;
}

// a firearm by the mod's policy (audit_us_content.py firearm_ids): a gun that is not a
// slingshot or crossbow, or a magazine that is not a battery
static bool is_firearm( const item &it )
{
    if( it.is_gun() && !it.has_flag( flag_PRIMITIVE_RANGED_WEAPON ) ) {
        return true;
    }
    // a gun magazine is a MAGAZINE item; a lighter's or a stove's fuel pocket is not one
    return it.type->magazine && !it.is_battery() && !it.ammo_types().empty();
}

// Everything the world can hand a player: anything any item group can spawn, anything a recipe
// makes (result or byproduct), anything a harvest (butchery, foraging) drops, and then, until
// nothing new turns up, what those items take apart into or turn into when used (a coconut
// splits into bowls, a torch lights).  Pseudo tools (fire, a stove's heat) come from terrain and
// furniture.  dda's groups count too: a component found only in dda loot is still found.
static const std::set<itype_id> &obtainable_items()
{
    static std::set<itype_id> out;
    if( !out.empty() ) {
        return out;
    }
    for( const item_group_id &g : item_controller->get_all_group_names() ) {
        for( const itype *t : item_group::every_possible_item_from( g ) ) {
            out.insert( t->get_id() );
        }
    }
    for( const auto &pr : recipe_dict ) {
        const recipe &r = pr.second;
        if( r.obsolete ) {
            continue;
        }
        out.insert( r.result() );
        for( const std::pair<const itype_id, int> &b : r.get_byproducts() ) {
            out.insert( b.first );
        }
    }
    for( const harvest_list &h : harvest_list::get_all() ) {
        for( const harvest_entry &e : h.entries() ) {
            const itype_id as_item( e.drop );
            if( as_item.is_valid() ) {
                out.insert( as_item );
            } else if( item_group::group_is_defined( item_group_id( e.drop ) ) ) {
                for( const itype *t : item_group::every_possible_item_from( item_group_id( e.drop ) ) ) {
                    out.insert( t->get_id() );
                }
            }
        }
    }
    for( const itype *t : item_controller->all() ) {
        if( t->has_flag( flag_PSEUDO ) ) {
            out.insert( t->get_id() );
        }
    }
    for( size_t before = 0; before != out.size(); ) {
        before = out.size();
        const std::vector<itype_id> now( out.begin(), out.end() );
        for( const itype_id &id : now ) {
            // what taking it apart yields (an uncraft recipe lists its yield as components)
            const recipe &un = recipe_dictionary::get_uncraft( id );
            if( !un.is_null() ) {
                for( const std::vector<item_comp> &slot : un.simple_requirements().get_components() ) {
                    for( const item_comp &c : slot ) {
                        out.insert( c.type );
                    }
                }
            }
            for( const std::pair<const std::string, use_function> &use : id->use_methods ) {
                const iuse_transform *tr = dynamic_cast<const iuse_transform *>( use.second.get_actor_ptr() );
                if( tr != nullptr && !tr->transform.target.is_null() ) {
                    out.insert( tr->transform.target );
                }
            }
        }
    }
    return out;
}

TEST_CASE( "saigon_scenarios_and_starts", "[saigon][saigon_content]" )
{
    const string_id<scenario> s2004( "sgn_saigon_2004" );
    const string_id<scenario> s2009( "sgn_saigon_2009" );
    if( !s2004.is_valid() ) {
        WARN( "saigon_2000s is not loaded; skipping" );
        return;
    }
    REQUIRE( s2009.is_valid() );
    for( const string_id<scenario> &sid : { s2004, s2009 } ) {
        const scenario &scen = sid.obj();
        CAPTURE( sid.str() );
        // offered in character creation, with the intro that sets the scene
        CHECK_FALSE( scen.scen_is_blacklisted() );
        CHECK_FALSE( scen.eoc().empty() );
        for( const effect_on_condition_id &e : scen.eoc() ) {
            CAPTURE( e.str() );
            CHECK( e.is_valid() );
        }
        // every start is the mod's, on a Saigon building that exists
        REQUIRE( scen.start_location_count() > 0 );
        CHECK( scen.allowed_start( scen.start_location() ) );
        int starts = 0;
        for( const start_location &loc : start_locations::get_all() ) {
            if( !scen.allowed_start( loc.id ) ) {
                continue;
            }
            starts++;
            CAPTURE( loc.id.str() );
            CHECK( sgn_id( loc.id.str() ) );
            REQUIRE( loc.targets_count() > 0 );
            for( int i = 0; i < 4 * loc.targets_count(); i++ ) {
                const omt_types_parameters t = loc.random_target();
                CAPTURE( t.omt );
                // a TYPE match names an overmap terrain type; its rotations carry the suffix
                const bool exists = oter_type_str_id( t.omt ).is_valid() || oter_str_id( t.omt ).is_valid();
                CHECK( exists );
                CHECK( sgn_id( t.omt ) );
            }
        }
        CHECK( starts == scen.start_location_count() );
        // every profession a player can pick is a Saigon one
        const std::vector<string_id<profession>> profs = scen.permitted_professions();
        CHECK( profs.size() >= 12 );
        for( const string_id<profession> &p : profs ) {
            CAPTURE( p.str() );
            CHECK( sgn_id( p.str() ) );
        }
    }
    // the 2004 Vietmap has no hẻm-block or landmark starts of its own; the 2009 map has six
    CHECK( s2004->start_location_count() == 3 );
    CHECK( s2009->start_location_count() == 6 );
}

// B3/D3 B3-1: a Saigon kit.  profession::items is what game::start_game hands the player.
TEST_CASE( "saigon_profession_kits", "[saigon][saigon_content]" )
{
    const string_id<scenario> s2009( "sgn_saigon_2009" );
    if( !s2009.is_valid() ) {
        WARN( "saigon_2000s is not loaded; skipping" );
        return;
    }
    std::set<string_id<profession>> profs;
    for( const char *s : { "sgn_saigon_2004", "sgn_saigon_2009" } ) {
        for( const string_id<profession> &p : string_id<scenario>( s )->permitted_professions() ) {
            profs.insert( p );
        }
    }
    // the hobbies the whitelist lets a Saigon player pick hand out items too
    std::set<string_id<profession>> hobbies;
    for( const string_id<profession> &h : profession::get_all_hobbies() ) {
        if( !h->is_blacklisted() ) {
            hobbies.insert( h );
        }
    }
    CHECK( hobbies.size() >= 10 );
    for( const bool hobby : { false, true } ) {
        for( const string_id<profession> &p : hobby ? hobbies : profs ) {
            CAPTURE( p.str() );
            for( const bool male : { true, false } ) {
                CAPTURE( male );
                const std::list<item> kit = p->items( male, {} );
                int saigon = 0;
                std::string guns;
                for( const item &top : kit ) {
                    top.visit_items( [&]( const item * it, item * ) {
                        CHECK( it->type != nullptr );
                        CHECK_FALSE( it->typeId().is_null() );
                        saigon += sgn_id( it->typeId().str() );
                        if( is_firearm( *it ) ) {
                            guns += it->typeId().str() + " ";
                        }
                        return VisitResponse::NEXT;
                    } );
                }
                CAPTURE( guns );
                CHECK( guns.empty() );
                if( !hobby ) {
                    // dressed and equipped, with something of the city's own (at least the wallet).
                    // The wallet (sgn_wallet) rolls empty about one time in twenty, so a kit whose
                    // only Saigon item is the money gets a few more rolls before this fails.
                    CHECK( kit.size() >= 4 );
                    for( int roll = 0; roll < 10 && saigon == 0; roll++ ) {
                        for( const item &top : p->items( male, {} ) ) {
                            top.visit_items( [&]( const item * it, item * ) {
                                saigon += sgn_id( it->typeId().str() );
                                return VisitResponse::NEXT;
                            } );
                        }
                    }
                    CHECK( saigon >= 1 );
                }
            }
            // a starting vehicle is a Saigon one
            if( !p->vehicle().is_null() ) {
                CAPTURE( p->vehicle().str() );
                CHECK( p->vehicle().is_valid() );
                CHECK( p->vehicle().str().rfind( "sgn_veh_", 0 ) == 0 );
            }
        }
    }
}

// Every recipe the mod adds or changes: makes something, can be learned, and can be made from
// things the world holds.
TEST_CASE( "saigon_recipes_learnable_and_makeable", "[saigon][saigon_content]" )
{
    if( !itype_id( "sgn_pho_bo" ).is_valid() ) {
        WARN( "saigon_2000s is not loaded; skipping" );
        return;
    }
    std::set<recipe_id> granted;
    for( const profession &p : profession::get_all() ) {
        for( const recipe_id &r : p.recipes() ) {
            granted.insert( r );
        }
    }
    const std::set<itype_id> &obtainable = obtainable_items();
    int count = 0;
    for( const auto &pr : recipe_dict ) {
        const recipe &r = pr.second;
        if( !from_saigon( r ) || r.obsolete ) {
            continue;
        }
        count++;
        CAPTURE( r.ident().str() );
        CHECK( r.result().is_valid() );
        CHECK_FALSE( r.result().is_null() );
        CHECK_FALSE( r.is_blacklisted() );
        if( r.is_practice() || r.is_nested() || r.is_blueprint() ) {
            continue;
        }
        // learned somehow: by skill, from a book, from a profession
        const bool learnable = recipe_dict.all_autolearn().count( &r ) || !r.booksets.empty() || granted.count( r.ident() ) ||
                               r.never_learn;
        CHECK( learnable );
        // every book that teaches it is a book, and one a player can find
        for( const std::pair<const itype_id, book_recipe_data> &b : r.booksets ) {
            CAPTURE( b.first.str() );
            REQUIRE( b.first.is_valid() );
            CHECK( b.first->book );
            CHECK( obtainable.count( b.first ) == 1 );
        }
        // each component slot has at least one alternative that exists in the world
        const requirement_data &req = r.simple_requirements();
        for( const std::vector<item_comp> &slot : req.get_components() ) {
            std::string alternatives;
            bool found = false;
            for( const item_comp &c : slot ) {
                alternatives += c.type.str() + " ";
                found = found || obtainable.count( c.type ) > 0;
            }
            CAPTURE( alternatives );
            CHECK( found );
        }
        for( const std::vector<tool_comp> &slot : req.get_tools() ) {
            std::string alternatives;
            bool found = false;
            for( const tool_comp &c : slot ) {
                alternatives += c.type.str() + " ";
                found = found || obtainable.count( c.type ) > 0;
            }
            CAPTURE( alternatives );
            CHECK( found );
        }
    }
    // the mod's own recipes are many; a load that dropped them would pass vacuously
    CHECK( count >= 30 );
}

// B7: a book with book_learn teaches recipes that exist, and every book of the mod that teaches
// something or trains a skill spawns somewhere.
TEST_CASE( "saigon_books_teach_and_can_be_found", "[saigon][saigon_content]" )
{
    if( !itype_id( "sgn_book_southern_cooking" ).is_valid() ) {
        WARN( "saigon_2000s is not loaded; skipping" );
        return;
    }
    const std::set<itype_id> &obtainable = obtainable_items();
    int teaching = 0;
    for( const itype *t : item_controller->all() ) {
        if( !t->book || !item_from_saigon( *t ) ) {
            continue;
        }
        CAPTURE( t->get_id().str() );
        for( const islot_book::recipe_with_description_t &rd : t->book->recipes ) {
            REQUIRE( rd.recipe != nullptr );
            CAPTURE( rd.recipe->ident().str() );
            CHECK_FALSE( rd.recipe->is_null() );
            CHECK( rd.recipe->result().is_valid() );
            CHECK( rd.recipe->booksets.count( t->get_id() ) == 1 );
        }
        teaching += !t->book->recipes.empty();
        if( !t->book->recipes.empty() || !t->book->skill.is_null() ) {
            CHECK( obtainable.count( t->get_id() ) == 1 );
        }
    }
    CHECK( teaching >= 1 );
    CHECK( itype_id( "sgn_book_southern_cooking" )->book->recipes.size() >= 10 );
}

// Every item the mod defines spawns cleanly (a bad default, container, ammo or snippet logs an
// error, which fails the run), every comestible has sane nutrition, and a cooked dish of meat,
// egg or milk spoils.
TEST_CASE( "saigon_items_spawn_and_food_is_sane", "[saigon][saigon_content]" )
{
    if( !itype_id( "sgn_pho_bo" ).is_valid() ) {
        WARN( "saigon_2000s is not loaded; skipping" );
        return;
    }
    std::set<itype_id> dishes;
    for( const auto &pr : recipe_dict ) {
        if( from_saigon( pr.second ) && !pr.second.obsolete ) {
            dishes.insert( pr.second.result() );
        }
    }
    const std::set<material_id> perishable = {
        material_id( "flesh" ), material_id( "iflesh" ), material_id( "hflesh" ), material_id( "egg" ),
        material_id( "milk" )
    };
    int items = 0;
    int food = 0;
    for( const itype *t : item_controller->all() ) {
        if( !item_from_saigon( *t ) ) {
            continue;
        }
        items++;
        CAPTURE( t->get_id().str() );
        const item it( t, calendar::turn );
        CHECK_FALSE( it.tname().empty() );
        CHECK_FALSE( it.type->description.empty() );
        if( !t->snippet_category.empty() ) {
            CAPTURE( t->snippet_category );
            CHECK( SNIPPET.has_category( t->snippet_category ) );
        }
        if( !t->comestible ) {
            continue;
        }
        food++;
        const nutrients n = t->comestible->default_nutrition_read_only();
        CHECK( n.calories >= 0 );
        for( const std::pair<const vitamin_id, int> &v : n.vitamins() ) {
            CAPTURE( v.first.str() );
            CHECK( v.second >= 0 );
        }
        // a dish the player cooks from meat, egg or milk goes off; dried, salted and fermented
        // things (khô bò, lạp xưởng, mắm) are not recipe results here
        if( dishes.count( t->get_id() ) && t->comestible->comesttype == "FOOD" ) {
            bool spoils_by_material = false;
            for( const std::pair<const material_id, int> &m : t->materials ) {
                spoils_by_material = spoils_by_material || perishable.count( m.first );
            }
            if( spoils_by_material ) {
                CHECK( t->comestible->spoils > 0_turns );
                CHECK( t->comestible->spoils <= 7_days );
            }
        }
    }
    CHECK( items >= 200 );
    CHECK( food >= 50 );
}

// Every loot group the mod defines can be rolled without error (an empty or broken entry logs),
// and the name and lore snippet categories the mod's people and items draw from exist.
TEST_CASE( "saigon_item_groups_spawn", "[saigon][saigon_content]" )
{
    if( !item_group::group_is_defined( item_group_id( "sgn_wallet" ) ) ) {
        WARN( "saigon_2000s is not loaded; skipping" );
        return;
    }
    int groups = 0;
    for( const item_group_id &g : item_controller->get_all_group_names() ) {
        if( !sgn_id( g.str() ) ) {
            continue;
        }
        groups++;
        CAPTURE( g.str() );
        CHECK_FALSE( item_group::every_possible_item_from( g ).empty() );
        for( int i = 0; i < 3; i++ ) {
            item_group::items_from( g, calendar::turn );
        }
    }
    CHECK( groups >= 150 );
    for( const char *cat : {
             "<sgn_family_name>", "<sgn_male_given_name>", "<sgn_female_given_name>",
             "<sgn_male_middle_name>", "<sgn_female_middle_name>", "<sgn_nick_name>", "<sgn_city_name>",
             "sgn_newspaper", "sgn_note", "sgn_loa_phuong"
         } ) {
        CAPTURE( cat );
        CHECK( SNIPPET.has_category( cat ) );
        CHECK( SNIPPET.random_from_category( cat ).has_value() );
    }
}

// P1/P2 and V2: the shophouse businesses (tools/saigon/gen_places.py, sgn_pl_*) and the everyday
// places (tools/saigon/gen_vn_places.py, sgn_vp_*) had no structure test; only one of them (the
// ward police post) was ever generated by a test.  Every ground piece, with the floors the
// overmap stacks on it, must generate without error, be enterable from the edge of its tile, and
// keep the rain off every indoor tile.
static std::set<point> reachable_from_edge( map &m, int z )
{
    std::set<point> seen;
    std::queue<point> todo;
    const auto open = [&m, z]( const point & q ) {
        const tripoint_bub_ms p( q.x, q.y, z );
        return m.passable( p ) || m.ter( p ).obj().has_flag( ter_furn_flag::TFLAG_DOOR ) ||
               m.furn( p ).obj().has_flag( ter_furn_flag::TFLAG_DOOR );
    };
    for( int i = 0; i < SEEX * 2; i++ ) {
        for( const point &q : { point( i, 0 ), point( i, SEEY * 2 - 1 ), point( 0, i ), point( SEEX * 2 - 1, i ) } ) {
            if( !seen.count( q ) && open( q ) ) {
                seen.insert( q );
                todo.push( q );
            }
        }
    }
    while( !todo.empty() ) {
        const point p = todo.front();
        todo.pop();
        for( const point &d : four_adjacent_offsets ) {
            const point q = p + d;
            if( q.x < 0 || q.y < 0 || q.x >= SEEX * 2 || q.y >= SEEY * 2 || seen.count( q ) || !open( q ) ) {
                continue;
            }
            seen.insert( q );
            todo.push( q );
        }
    }
    return seen;
}

TEST_CASE( "saigon_places_enterable_and_roofed", "[mapgen][saigon][saigon_content]" )
{
    const cata_path file = PATH_INFO::moddir() / "saigon_2000s/realmap_2009/overmap_0_0.omap.gz";
    if( !oter_str_id( "sgn_vp_bia_hoi_00_north" ).is_valid() || !file_exist( file.get_unrelative_path() ) ) {
        WARN( "saigon_2000s or its real map is not present; skipping" );
        return;
    }
    // overmap (0, 0) of the real map loads in a second; a generated Saigon overmap takes ~100 s.
    // An overmap saved earlier in the run (a test whose turns autosave) would load instead.
    for( int x = -1; x <= 0; x++ ) {
        for( int y = -1; y <= 0; y++ ) {
            const point_abs_om om( x, y );
            for( const cata_path &saved : {
                     PATH_INFO::current_dimension_save_path() / zzip_overmap_directory /
                     ( overmapbuffer::terrain_filename( om ) + std::string( zzip_suffix ) ),
                     PATH_INFO::current_dimension_save_path() / overmapbuffer::terrain_filename( om )
                 } ) {
                if( file_exist( saved ) ) {
                    remove_file( saved.get_unrelative_path().u8string() );
                }
            }
        }
    }
    get_globals().set_global_value( "overmap_pregenerated_path",
                                    diag_value( std::string( "saigon_2000s/realmap_2009" ) ) );
    clear_avatar();
    clear_map();
    clear_overmaps();
    std::vector<std::string> grounds;
    for( const oter_t &t : overmap_terrains::get_all() ) {
        const std::string id = t.get_type_id().str();
        if( ( id.rfind( "sgn_pl_", 0 ) == 0 || id.rfind( "sgn_vp_", 0 ) == 0 ) &&
            id.find( "_z" ) == std::string::npos &&
            t.id.str() == id + "_north" ) {
            grounds.push_back( id );
        }
    }
    CHECK( grounds.size() >= 30 );
    const ter_id open_air = ter_str_id( "t_open_air" ).id();
    int column = 0;
    for( const std::string &id : grounds ) {
        CAPTURE( id );
        const tripoint_abs_omt pos( 20 + 3 * ( column % 40 ), 20 + 3 * ( column / 40 ), 0 );
        column++;
        int top = 0;
        overmap_buffer.ter_set( pos, oter_str_id( id + "_north" ).id() );
        for( int z = 1; z <= 8; z++ ) {
            const oter_str_id up( id + "_z" + std::to_string( z ) + "_north" );
            if( !up.is_valid() ) {
                break;
            }
            overmap_buffer.ter_set( pos + tripoint( 0, 0, z ), up.id() );
            top = z;
        }
        for( int z = top + 1; z <= top + 1; z++ ) {
            overmap_buffer.ter_set( pos + tripoint( 0, 0, z ), oter_str_id( "open_air" ).id() );
        }
        rng_set_engine_seed( 11 );
        MAPBUFFER.clear_outside_reality_bubble();
        smallmap tm;
        tm.generate( pos, calendar::turn, false, true );
        map &m = *tm.cast_to_map();
        const std::set<point> reach = reachable_from_edge( m, 0 );
        CHECK_FALSE( reach.empty() );
        for( int z = 0; z <= top; z++ ) {
            CAPTURE( z );
            int indoor = 0;
            int uncovered = 0;
            int reached = 0;
            for( int x = 0; x < SEEX * 2; x++ ) {
                for( int y = 0; y < SEEY * 2; y++ ) {
                    const tripoint_bub_ms p( x, y, z );
                    if( !m.ter( p ).obj().has_flag( ter_furn_flag::TFLAG_INDOORS ) ) {
                        continue;
                    }
                    indoor++;
                    uncovered += m.ter( p + tripoint::above ) == open_air;
                    reached += z == 0 && reach.count( point( x, y ) );
                }
            }
            CAPTURE( indoor, uncovered, reached );
            CHECK( uncovered == 0 );
            if( z == 0 && indoor > 0 ) {
                CHECK( reached > 0 );
            }
        }
        tm.delete_unmerged_submaps();
    }
    // leave without regenerating the megacity; the next test that needs a fresh world clears it
    get_globals().remove_global_value( "overmap_pregenerated_path" );
    clear_avatar();
    clear_map();
}
