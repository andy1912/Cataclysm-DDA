#include <filesystem>
#include <map>
#include <set>
#include <string>
#include <utility>
#include <vector>

#include "avatar.h"
#include "cata_catch.h"
#include "coordinates.h"
#include "filesystem.h"
#include "flag.h"
#include "global_vars.h"
#include "item.h"
#include "item_factory.h"
#include "item_group.h"
#include "itype.h"
#include "map.h"
#include "map_helpers.h"
#include "math_parser_diag_value.h"
#include "monstergenerator.h"
#include "mtype.h"
#include "npc_class.h"
#include "omdata.h"
#include "overmap.h"
#include "overmapbuffer.h"
#include "path_info.h"
#include "player_helpers.h"
#include "pocket_type.h"
#include "point.h"
#include "recipe.h"
#include "recipe_dictionary.h"
#include "requirements.h"
#include "ret_val.h"
#include "rng.h"
#include "type_id.h"
#include "veh_type.h"

// Saigon 2000s mod, W1-W4 (doc/saigon/PROGRESS.md): Vietnamese weapons (W1), weapons in the
// world (W2), the police and army sites with their guns (W3), everyday Vietnam (W4).  The firearm
// policy is doc/saigon/CONTENT_BIBLE.md section 12: civilians and random NPCs are unarmed, the
// guard class (sgn_class_guard) alone carries a gun, and otherwise firearms exist only as loot at
// police and army sites - the item groups tools/saigon/audit_us_content.py names in
// POLICE_ARMY_GUN_GROUPS.  The audit enforces that on the JSON; the firearm-reach case below is
// the second line of defence, on the item groups as the game actually loaded them.
// Run with: tests/cata_test --mods=dda,saigon_2000s "[saigon]"

// Mirror of POLICE_ARMY_GUN_GROUPS in tools/saigon/audit_us_content.py.  Keep the two in step:
// a group added there and not here fails saigon_firearms_only_at_police_and_army.
static const std::set<std::string> police_army_gun_groups = {
    "sgn_pa_guns_police", "sgn_pa_guns_army", "sgn_pa_mags_police", "sgn_pa_mags_army",
    "sgn_pa_armory_police", "sgn_pa_ammo_police", "sgn_pa_armory_army", "sgn_pa_ammo_army",
    "sgn_drops_pa_cong_an_quan", "sgn_drops_pa_co_dong", "sgn_drops_pa_bo_doi",
};

static bool sgn( const std::string &id )
{
    return id.rfind( "sgn_", 0 ) == 0;
}

// The audit's firearm_ids(): a gun that is not a slingshot or crossbow (PRIMITIVE_RANGED_WEAPON,
// item::is_firearm), or a magazine for cartridges (battery cells are MAGAZINE items too).
static bool firearm( const itype &t )
{
    if( t.gun ) {
        return !t.has_flag( flag_PRIMITIVE_RANGED_WEAPON );
    }
    return t.magazine && !t.magazine->type.empty() && !t.magazine->type.count( ammotype( "battery" ) );
}

static std::set<itype_id> ids_from( const item_group_id &g )
{
    std::set<itype_id> out;
    for( const itype *t : item_group::every_possible_item_from( g ) ) {
        out.insert( t->get_id() );
    }
    return out;
}

// Every string after a loot key ("group", "item", "items", "death_drops", "contents-group",
// "container-group") in the mod's JSON: the audit's regex, without std::regex on megabytes.
static void named_after_loot_keys( const std::string &text, std::set<std::string> &out )
{
    for( const char *key : {
             "\"group\"", "\"item\"", "\"items\"", "\"death_drops\"", "\"contents-group\"", "\"container-group\""
         } ) {
        const std::string k( key );
        for( size_t at = text.find( k ); at != std::string::npos; at = text.find( k, at + 1 ) ) {
            size_t p = at + k.size();
            while( p < text.size() && ( text[p] == ' ' || text[p] == '\n' ) ) {
                p++;
            }
            if( p >= text.size() || text[p] != ':' ) {
                continue;
            }
            p++;
            while( p < text.size() && ( text[p] == ' ' || text[p] == '\n' ) ) {
                p++;
            }
            if( p >= text.size() || text[p] != '"' ) {
                continue;
            }
            const size_t end = text.find( '"', p + 1 );
            if( end != std::string::npos ) {
                out.insert( text.substr( p + 1, end - p - 1 ) );
            }
        }
    }
}

// W3: only the police and army loot, and the guard's weapon group, may reach a firearm or a gun
// magazine.  The roots are every sgn_ item group, every group the mod's JSON names as loot
// (mapgen, furniture, death drops, dda groups it overrides such as NC_NONE_*), the gear of every
// sgn_ npc class, the death drops of every sgn_ monster and the trunks of every sgn_ vehicle.
// Adding a gun to a shophouse drawer, a zombie's pockets or a wanderer's kit fails here.
// item_group::every_possible_item_from follows nested groups but not "contents-group" /
// "container-group"; the audit covers those.
TEST_CASE( "saigon_firearms_only_at_police_and_army", "[saigon]" )
{
    if( !npc_class_id( "sgn_class_guard" ).is_valid() ) {
        WARN( "saigon_2000s is not loaded; skipping" );
        return;
    }
    std::set<item_group_id> allowed;
    for( const std::string &g : police_army_gun_groups ) {
        CAPTURE( g );
        REQUIRE( item_group::group_is_defined( item_group_id( g ) ) );
        allowed.insert( item_group_id( g ) );
    }
    allowed.insert( npc_class_id( "sgn_class_guard" )->weapon_override );

    std::set<item_group_id> roots;
    for( const item_group_id &g : item_controller->get_all_group_names() ) {
        if( sgn( g.str() ) || g.str().rfind( "NC_NONE", 0 ) == 0 ) {
            roots.insert( g );
        }
    }
    std::set<std::string> named;
    const std::filesystem::path mod = ( PATH_INFO::moddir() / "saigon_2000s" ).get_unrelative_path();
    for( const auto &entry : std::filesystem::recursive_directory_iterator( mod ) ) {
        if( entry.is_regular_file() && entry.path().extension() == ".json" ) {
            named_after_loot_keys( read_entire_file( entry.path() ), named );
        }
    }
    int named_groups = 0;
    for( const std::string &n : named ) {
        // an id that is also an item is that item ("item": "pants"), not a group of that name
        if( item_group::group_is_defined( item_group_id( n ) ) && !itype_id( n ).is_valid() ) {
            roots.insert( item_group_id( n ) );
            named_groups++;
        }
    }
    for( const npc_class &c : npc_class::get_all() ) {
        if( sgn( c.id.str() ) ) {
            for( const item_group_id &g : {
                     c.worn_override, c.carry_override, c.weapon_override
                 } ) {
                if( !g.is_null() && item_group::group_is_defined( g ) ) {
                    roots.insert( g );
                }
            }
        }
    }
    for( const mtype &m : MonsterGenerator::generator().get_all_mtypes() ) {
        if( sgn( m.id.str() ) && !m.death_drops.is_null() &&
            item_group::group_is_defined( m.death_drops ) ) {
            roots.insert( m.death_drops );
        }
    }
    for( const vehicle_prototype &v : vehicles::get_all_prototypes() ) {
        if( sgn( v.id.str() ) ) {
            for( const vehicle_item_spawn &s : v.item_spawns ) {
                roots.insert( s.item_groups.begin(), s.item_groups.end() );
            }
        }
    }
    CAPTURE( roots.size(), named_groups );
    // the scan found the mod's loot, or this would pass on nothing
    CHECK( named_groups > 100 );
    CHECK( roots.size() > 200 );

    std::set<itype_id> reached_by_allowed;
    for( const item_group_id &g : roots ) {
        const std::set<itype_id> reach = ids_from( g );
        if( allowed.count( g ) ) {
            for( const itype_id &i : reach ) {
                if( firearm( *i ) ) {
                    reached_by_allowed.insert( i );
                }
            }
            continue;
        }
        for( const itype_id &i : reach ) {
            if( firearm( *i ) ) {
                CAPTURE( g.str(), i.str() );
                FAIL_CHECK( "a group outside POLICE_ARMY_GUN_GROUPS and the guard's reaches a firearm" );
            }
        }
    }
    // and the allowed groups really do hold the guns (not vacuous)
    CHECK( reached_by_allowed.size() >= 5 );
}

// Can `gun` be loaded and made ready from the items in `given` (a magazine and its rounds, or
// rounds straight into an integral magazine)?  Returns the first working combination, loaded.
static bool loadable_from( const itype_id &gun_id, const std::set<itype_id> &given,
                           std::string &how )
{
    const item gun_proto( gun_id );
    for( const itype_id &a : given ) {
        if( !a->ammo ) {
            continue;
        }
        if( gun_proto.magazine_integral() ) {
            if( !gun_proto.ammo_types().count( a->ammo->type ) ) {
                continue;
            }
            item gun( gun_id );
            gun.ammo_set( a );
            if( gun.ammo_remaining() > 0 && gun.ammo_current() == a ) {
                how = a.str();
                return true;
            }
            continue;
        }
        for( const itype_id &m : given ) {
            if( !m->magazine || !gun_proto.magazine_compatible().count( m ) ||
                !m->magazine->type.count( a->ammo->type ) ) {
                continue;
            }
            item mag( m );
            mag.ammo_set( a );
            item gun( gun_id );
            if( gun.put_in( mag, pocket_type::MAGAZINE_WELL ).success() && gun.ammo_remaining() > 0 &&
                gun.ammo_current() == a ) {
                how = m.str() + " + " + a.str();
                return true;
            }
        }
    }
    return false;
}

// The other way a gun gets loaded: a group entry with "charges" spawns its magazine already
// loaded.  Sample the groups and seat the first loaded, compatible magazine that turns up.
static bool loaded_magazine_from( const itype_id &gun_id, const std::vector<item_group_id> &groups,
                                  std::string &how )
{
    const item gun_proto( gun_id );
    if( gun_proto.magazine_integral() ) {
        return false;
    }
    for( int i = 0; i < 500; i++ ) {
        for( const item_group_id &g : groups ) {
            for( const item &it : item_group::items_from( g ) ) {
                if( !it.is_magazine() || it.ammo_remaining() <= 0 ||
                    !gun_proto.magazine_compatible().count( it.typeId() ) ) {
                    continue;
                }
                item gun( gun_id );
                if( gun.put_in( it, pocket_type::MAGAZINE_WELL ).success() && gun.ammo_remaining() > 0 ) {
                    how = it.typeId().str() + " (spawned loaded)";
                    return true;
                }
            }
        }
    }
    return false;
}

// W3: the district police armory and the army rack each yield every gun of their gun list, and
// for each gun the armory and its ammunition shelf give something to load it with.  A gun whose
// magazine or cartridge is missing from the shelves is a club.
TEST_CASE( "saigon_armories_yield_loadable_guns", "[saigon]" )
{
    if( !item_group::group_is_defined( item_group_id( "sgn_pa_armory_police" ) ) ) {
        WARN( "saigon_2000s is not loaded; skipping" );
        return;
    }
    const std::vector<std::vector<std::string>> sites = {
        // gun list, armory cupboards, ammunition shelf
        { "sgn_pa_guns_police", "sgn_pa_armory_police", "sgn_pa_ammo_police" },
        { "sgn_pa_guns_army", "sgn_pa_armory_army", "sgn_pa_ammo_army" },
    };
    for( const std::vector<std::string> &site : sites ) {
        CAPTURE( site[1] );
        const std::set<itype_id> guns = ids_from( item_group_id( site[0] ) );
        const std::set<itype_id> armory = ids_from( item_group_id( site[1] ) );
        std::set<itype_id> given = armory;
        for( const itype_id &i : ids_from( item_group_id( site[2] ) ) ) {
            given.insert( i );
        }
        CHECK( guns.size() >= 4 );
        for( const itype_id &gun : guns ) {
            CAPTURE( gun.str() );
            CHECK( item( gun ).is_firearm() );
            CHECK( armory.count( gun ) == 1 );
            std::string how;
            const bool loose = loadable_from( gun, given, how );
            if( !loose ) {
                // e.g. the army rack's rare service pistol: the shelves hold its magazine, which
                // may spawn loaded, but no loose 9x18mm rounds
                WARN( gun.str() << " at " << site[1] << ": no loose rounds for it, only loaded magazines" );
            }
            CHECK( ( loose || loaded_magazine_from( gun, { item_group_id( site[1] ), item_group_id( site[2] ) },
                                                    how ) ) );
            CAPTURE( how );
        }
    }
}

// W1: the Vietnamese weapons.  Every sgn_ weapon the W1 groups hand out can be wielded; the ná
// thun (slingshot) and nỏ (crossbow) load the ammunition their groups give and fire it; and they
// are not firearms (PRIMITIVE_RANGED_WEAPON), so a farmer with a nỏ breaks no policy.
TEST_CASE( "saigon_vn_weapons_wield_and_shoot", "[saigon]" )
{
    if( !itype_id( "sgn_na_thun" ).is_valid() ) {
        WARN( "saigon_2000s is not loaded; skipping" );
        return;
    }
    std::set<itype_id> weapons;
    std::set<itype_id> ammo;
    for( const char *g : {
             "sgn_weapons_melee_common", "sgn_weapons_melee_rare", "sgn_weapons_ranged_primitive",
             "sgn_weapons_ammo_primitive"
         } ) {
        CAPTURE( g );
        const std::set<itype_id> got = ids_from( item_group_id( g ) );
        CHECK( !got.empty() );
        for( const itype_id &i : got ) {
            ( i->ammo ? ammo : weapons ).insert( i );
        }
    }
    CHECK( weapons.size() >= 15 );
    for( const itype_id &w : weapons ) {
        CAPTURE( w.str() );
        CHECK( sgn( w.str() ) );
        clear_avatar();
        avatar &u = get_avatar();
        item it( w );
        CHECK( u.can_wield( it ).success() );
        CHECK( u.wield( it ) );
        CHECK( u.get_wielded_item() );
        if( u.get_wielded_item() ) {
            CHECK( u.get_wielded_item()->typeId() == w );
        }
    }
    const std::vector<itype_id> primitive = { itype_id( "sgn_na_thun" ), itype_id( "sgn_no" ) };
    std::map<itype_id, int> fits;
    for( const itype_id &a : ammo ) {
        CAPTURE( a.str() );
        int shooters = 0;
        for( const itype_id &g : primitive ) {
            if( item( g ).ammo_types().count( a->ammo->type ) ) {
                shooters++;
                fits[g]++;
            }
        }
        // every round the groups hand out fits a weapon they hand out
        CHECK( shooters > 0 );
    }
    clear_map();
    for( const itype_id &g : primitive ) {
        CAPTURE( g.str() );
        CHECK( item( g ).is_gun() );
        CHECK_FALSE( item( g ).is_firearm() );
        CHECK( fits[g] > 0 );
        for( const itype_id &a : ammo ) {
            if( !item( g ).ammo_types().count( a->ammo->type ) ) {
                continue;
            }
            CAPTURE( a.str() );
            clear_avatar();
            avatar &u = get_avatar();
            item gun( g );
            gun.ammo_set( a );
            REQUIRE( gun.ammo_remaining() > 0 );
            REQUIRE( u.wield( gun ) );
            const int before = u.get_wielded_item()->ammo_remaining();
            u.set_moves( 100 );
            CHECK( u.fire_gun( u.pos_bub() + tripoint( 5, 0, 0 ), 1 ) == 1 );
            CHECK( u.get_wielded_item()->ammo_remaining() < before );
        }
    }
}

// W1: the recipes in recipes/vn_weapons.json.  Each is learnable, and every component group has
// at least one alternative a player can get: an item that is neither obsolete nor blacklisted
// and that some item group spawns or some recipe makes.
TEST_CASE( "saigon_vn_weapon_recipes_obtainable", "[saigon]" )
{
    if( !itype_id( "sgn_na_thun" ).is_valid() ) {
        WARN( "saigon_2000s is not loaded; skipping" );
        return;
    }
    std::set<itype_id> obtainable;
    for( const item_group_id &g : item_controller->get_all_group_names() ) {
        for( const itype *t : item_group::every_possible_item_from( g ) ) {
            obtainable.insert( t->get_id() );
        }
    }
    for( const auto &r : recipe_dict ) {
        if( !r.second.obsolete ) {
            obtainable.insert( r.second.result() );
        }
    }
    const std::set<std::string> results = {
        "sgn_na_thun", "sgn_gay_tre", "sgn_mac_tre", "sgn_chia", "sgn_con_nhi_khuc", "sgn_ten_tre", "sgn_no"
    };
    std::set<std::string> seen;
    for( const auto &pair : recipe_dict ) {
        const recipe &r = pair.second;
        if( !results.count( r.result().str() ) || r.obsolete ) {
            continue;
        }
        CAPTURE( r.ident().str() );
        seen.insert( r.result().str() );
        CHECK_FALSE( r.is_blacklisted() );
        CHECK_FALSE( r.never_learn );
        CHECK( ( !r.autolearn_requirements.empty() || !r.booksets.empty() ) );
        const auto &comps = r.simple_requirements().get_components();
        CHECK( !comps.empty() );
        for( const std::vector<item_comp> &alts : comps ) {
            std::string names;
            bool any = false;
            for( const item_comp &c : alts ) {
                names += c.type.str() + " ";
                any |= c.type.is_valid() && !item_is_blacklisted( c.type ) && obtainable.count( c.type );
            }
            CAPTURE( names );
            CHECK( any );
        }
    }
    CHECK( seen == results );
}

// W3: the district police headquarters (city building sgn_pa_cong_an_quan, CITY_UNIQUE) and the
// army guard post (overmap special sgn_pa_don_quan_su_ngoai_o, city_distance 2+) are placed by
// overmap generation: in the Vietmap megacity, and the guard post also in the delta region around
// the real 2009 map (scenario sgn_saigon_2009).  Seed 4242 gave 2 HQs / 3 posts in the megacity
// and 1 to 3 HQs and 3 posts in the delta (the delta overmap is not reseeded).
TEST_CASE( "saigon_police_army_placed_by_overmap_generation", "[overmap][saigon]" )
{
    if( !oter_str_id( "sgn_pa_cong_an_quan_00_north" ).is_valid() ||
        !region_settings_id( "sgn_saigon_delta" ).is_valid() ) {
        WARN( "saigon_2000s is not loaded; skipping" );
        return;
    }
    const auto count = []( overmap & om, const std::string & prefix ) {
        int n = 0;
        for( int x = 0; x < OMAPX; x++ ) {
            for( int y = 0; y < OMAPY; y++ ) {
                n += om.ter( tripoint_om_omt( x, y, 0 ) ).id().str().rfind( prefix, 0 ) == 0;
            }
        }
        return n;
    };
    const std::string hq = "sgn_pa_cong_an_quan_00_";
    const std::string army = "sgn_pa_don_quan_su_00_";
    // the megacity (saigon_cities_use_shophouses' overmap)
    rng_set_engine_seed( 4242 );
    overmap_buffer.clear();
    overmap &city = overmap_buffer.get( point_abs_om() );
    const int city_hq = count( city, hq );
    const int city_army = count( city, army );
    const int cities = static_cast<int>( city.cities.size() );
    // the delta, beyond the real map (saigon_realmap_2009_countryside's overmap)
    get_globals().set_global_value( "overmap_pregenerated_path",
                                    diag_value( std::string( "saigon_2000s/realmap_2009" ) ) );
    get_globals().set_global_value( "overmap_outside_region",
                                    diag_value( std::string( "sgn_saigon_delta" ) ) );
    clear_avatar();
    clear_map();
    clear_overmaps();
    REQUIRE( overmap_buffer.get_overmap_region( tripoint_abs_om( 4, 0,
             0 ) ).str() == "sgn_saigon_delta" );
    overmap &delta = overmap_buffer.get( point_abs_om( 4, 0 ) );
    const int delta_hq = count( delta, hq );
    const int delta_army = count( delta, army );
    get_globals().remove_global_value( "overmap_pregenerated_path" );
    get_globals().remove_global_value( "overmap_outside_region" );
    clear_avatar();
    clear_map();
    clear_overmaps();
    CAPTURE( city_hq, city_army, cities, delta_hq, delta_army );
    WARN( "police HQs / army posts: megacity " << city_hq << " / " << city_army << ", delta " <<
          delta_hq << " / " << delta_army );
    // the megacity is several cities that grow together; the HQ is CITY_UNIQUE, so at most one each
    CHECK( city_hq >= 1 );
    CHECK( city_hq <= cities );
    CHECK( city_army >= 1 );
    CHECK( delta_army >= 1 );
}

// Ledger W-tests: sgn_ao_cong_an copied dress_shirt and with it dress_shirt's colour variants, so
// a công an shirt spawned as a "black dress shirt" or a "blue dress shirt".
TEST_CASE( "saigon_cong_an_shirt_has_no_variants", "[saigon]" )
{
    if( !itype_id( "sgn_ao_cong_an" ).is_valid() ) {
        WARN( "saigon_2000s is not loaded; skipping" );
        return;
    }
    CHECK( itype_id( "sgn_ao_cong_an" )->variants.empty() );
    item shirt( itype_id( "sgn_ao_cong_an" ) );
    CHECK( shirt.tname().find( "dress shirt" ) == std::string::npos );
    CHECK( shirt.tname().find( "công an" ) != std::string::npos );
}

// The same bug in general: an sgn_ item made with copy-from inherits its parent's variants, and
// a variant replaces the item's name and description when it spawns.  The áo thun came out with
// dda's 35 T-shirt prints, the thuốc lá with American cigarette brands, the áo dài as dda's
// dresses.  The mod defines no variants of its own, so none of its items may have any; an item
// that later gets Saigon variants on purpose belongs in the list below.
TEST_CASE( "saigon_items_inherit_no_variants", "[saigon]" )
{
    if( !itype_id( "sgn_ao_cong_an" ).is_valid() ) {
        WARN( "saigon_2000s is not loaded; skipping" );
        return;
    }
    const std::set<std::string> own_variants = {};
    int checked = 0;
    for( const itype *t : item_controller->all() ) {
        const std::string id = t->get_id().str();
        if( id.rfind( "sgn_", 0 ) != 0 || own_variants.count( id ) ) {
            continue;
        }
        checked++;
        CAPTURE( id );
        CHECK( t->variants.empty() );
    }
    CHECK( checked > 200 );
}
