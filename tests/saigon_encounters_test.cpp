#include <algorithm>
#include <array>
#include <initializer_list>
#include <map>
#include <set>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

#include "calendar.h"
#include "cata_catch.h"
#include "flat_set.h"
#include "math_parser_diag_value.h"
#include "global_vars.h"
#include "map_scale_constants.h"
#include "coordinates.h"
#include "flag.h"
#include "item_group.h"
#include "itype.h"
#include "map.h"
#include "map_extras.h"
#include "map_helpers.h"
#include "mapbuffer.h"
#include "mongroup.h"
#include "mtype.h"
#include "overmapbuffer.h"
#include "player_helpers.h"
#include "point.h"
#include "regional_settings.h"
#include "rng.h"
#include "type_id.h"
#include "value_ptr.h"
#include "vehicle.h"
#include "vehicle_group.h"
#include "weighted_list.h"

static const mongroup_id GROUP_ZOMBIE( "GROUP_ZOMBIE" );
static const mongroup_id GROUP_ZOMBIE_HORDE( "GROUP_ZOMBIE_HORDE" );
static const mtype_id sgn_mon_zombie_xe_om( "sgn_mon_zombie_xe_om" );
static const oter_str_id oter_field( "field" );
static const oter_str_id oter_road_ns( "road_ns" );
static const oter_str_id oter_sgn_nh_solo_z0_north( "sgn_nh_solo_z0_north" );
static const region_settings_id region_settings_sgn_saigon( "sgn_saigon" );
static const region_settings_map_extras_id
region_settings_map_extras_sgn_map_extras( "sgn_map_extras" );
static const vproto_id vehicle_prototype_none( "none" );


// Saigon 2000s mod, E2: the dead and the road (monsters/, itemgroups/zombie_drops.json,
// mapgen/map_extras/sgn_encounters.json, region/region_settings.json).  Twelve road and field
// encounters as map extras, and GROUP_ZOMBIE / GROUP_ZOMBIE_HORDE overridden to Saigon's dead,
// none of whom (nor anything they turn into) drops a firearm.
// Run with: tests/cata_test --mods=dda,saigon_2000s "[saigon]"

// A cheap place to build on.  Generating a Saigon overmap takes about 100 s (megacity mode, with
// the neighbours it pulls in), so instead of clear_overmaps() these tests load the real-map test
// fixture (realmap_test/overmap_40_40.omap.gz: a field with one road and one shophouse column,
// marked "final" so nothing procedural is added; see saigon_realmap_test.cpp) as overmap (40, 40)
// and set their own terrain on it, away from that road (x 85-90) and column (y 89).
static tripoint_abs_omt sgn_encounter_spot( const point_rel_omt &offset )
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

// The map extras that can actually fire in a Saigon region: map_extra::is_valid_for drops every
// extra whose flags miss the region's feature-flag whitelist (SAIGON) or hit its blacklist.  The
// collections "road" and "field" still list dda's own extras; only the filter keeps them out.
static std::map<map_extra_id, map_extra_collection_id> sgn_live_extras( const region_settings &rs )
{
    std::map<map_extra_id, map_extra_collection_id> live;
    const region_settings_feature_flag &ff = rs.overmap_feature_flag;
    for( const map_extra_collection_id &coll : rs.get_settings_map_extras().extras ) {
        for( const auto &entry : coll->values ) {
            const map_extra &mx = entry.first.obj();
            bool ok = true;
            for( const std::string &f : mx.get_flags() ) {
                ok &= ff.blacklist.count( f ) == 0;
            }
            if( !ff.whitelist.empty() ) {
                bool listed = false;
                for( const std::string &f : mx.get_flags() ) {
                    listed |= ff.whitelist.count( f ) > 0;
                }
                ok &= listed;
            }
            if( ok ) {
                live.emplace( mx.id, coll );
            }
        }
    }
    return live;
}

// E2: the region's map-extra collection is Saigon's and fires only Saigon's encounters.
// Breaks if: region_settings stops pointing at sgn_map_extras, the SAIGON whitelist is dropped
// (dda's car wrecks, crashed helicopters and army roadblocks with rifles come back), a dda extra
// gains the SAIGON flag, or one of the mod's extras falls out of the road/field collections.
TEST_CASE( "saigon_region_map_extras_are_saigon", "[saigon][map_extra]" )
{
    if( !region_settings_sgn_saigon.is_valid() ) {
        WARN( "saigon_2000s is not loaded; skipping" );
        return;
    }
    for( const char *rid : {
             "sgn_saigon", "sgn_saigon_delta"
         } ) {
        CAPTURE( rid );
        const region_settings &rs = region_settings_id( rid ).obj();
        CHECK( rs.region_extras == region_settings_map_extras_sgn_map_extras );
        const std::map<map_extra_id, map_extra_collection_id> live = sgn_live_extras( rs );
        for( const auto &pair : live ) {
            CAPTURE( pair.first.str() );
            CHECK( pair.first.str().rfind( "mx_sgn_", 0 ) == 0 );
        }
        // 11 road and 2 field encounters (the ledger's "12" counts the altar pair as one idea)
        CHECK( live.size() == 13 );
    }
}

// E2: every live extra runs, on the terrain its collection belongs to, without a debugmsg (the
// test harness fails on one), and records itself on the overmap (MapExtras::apply_function only
// does that when the update_mapgen succeeded).  Road extras run on a city road (nhà ống on every
// side, so the SIDEWALK-flagged neighbours pick the city chunk) and on a country road (fields, the
// else_chunk); field extras on a field.  Every vehicle an extra adds has to be one of the mod's.
// Breaks if: an extra's mapgen names a missing terrain, furniture, item group, monster group or
// vehicle (debugmsg / failed update), a vehicle group gains a dda car, an extra that is meant to
// leave a wreck stops placing one, or a road extra stops working on one of its two road kinds.
TEST_CASE( "saigon_map_extras_generate_on_their_terrain", "[mapgen][saigon][map_extra]" )
{
    if( !region_settings_sgn_saigon.is_valid() ) {
        WARN( "saigon_2000s is not loaded; skipping" );
        return;
    }
    // the vehicle groups the extras use (in place_vehicles; mapgen is not introspectable)
    for( const char *grp : {
             "sgn_vg_sidewalk_parked", "sgn_vg_street_traffic"
         } ) {
        CAPTURE( grp );
        REQUIRE( vgroups.count( vgroup_id( grp ) ) == 1 );
        const std::vector<vproto_id> all = vgroups[vgroup_id( grp )].all_possible_results();
        CHECK( !all.empty() );
        for( const vproto_id &v : all ) {
            CAPTURE( v.str() );
            CHECK( v.str().rfind( "sgn_veh_", 0 ) == 0 );
        }
    }

    const std::map<map_extra_id, map_extra_collection_id> live =
        sgn_live_extras( region_settings_sgn_saigon.obj() );
    REQUIRE( !live.empty() );
    clear_avatar();
    const oter_id city = oter_sgn_nh_solo_z0_north.id();
    const oter_id field = oter_field.id();
    const oter_id road = oter_road_ns.id();
    // the extras whose whole point is a wreck: each must leave at least one vehicle
    const std::set<std::string> wrecks = {
        "mx_sgn_xe_khach", "mx_sgn_ba_gac", "mx_sgn_cap_cuu", "mx_sgn_don_xe"
    };
    int column = 0;
    for( const auto &pair : live ) {
        const map_extra_id &id = pair.first;
        const bool on_road = pair.second.str() == "road";
        CAPTURE( id.str(), pair.second.str() );
        REQUIRE( ( on_road || pair.second.str() == "field" ) );
        int new_vehicles = 0;
        // city and country for a road extra; a field extra just a field
        for( const oter_id &around : on_road ? std::vector<oter_id> { city, field } :
             std::vector<oter_id> { field } ) {
            CAPTURE( around.id().str() );
            const tripoint_abs_omt pos = sgn_encounter_spot( point_rel_omt( 20 + 3 * ( column % 20 ),
                                         20 + 3 * ( column / 20 ) ) );
            column++;
            overmap_buffer.ter_set( pos, on_road ? road : field );
            for( const tripoint &d : eight_horizontal_neighbors ) {
                overmap_buffer.ter_set( pos + d, around );
            }
            for( int seed = 1; seed <= 2; seed++ ) {
                CAPTURE( seed );
                rng_set_engine_seed( seed );
                MAPBUFFER.clear_outside_reality_bubble();
                smallmap tm;
                tm.generate( pos, calendar::turn, true, true );
                // generation itself may roll an extra (one road OMT in 30); start clean
                overmap_buffer.delete_extra( pos );
                // and the road's own parked bikes go: update_mapgen refuses to put terrain or
                // furniture on a vehicle tile (has_vehicle_collision) and the whole extra fails,
                // which in play just means no encounter on that tile, not a broken one
                clear_vehicles( tm.cast_to_map() );
                MapExtras::apply_function( id, tm, pos );
                CHECK( overmap_buffer.has_extra( pos ) );
                if( overmap_buffer.has_extra( pos ) ) {
                    CHECK( overmap_buffer.extra( pos ) == id );
                }
                for( const wrapped_vehicle &wv : tm.get_vehicles() ) {
                    new_vehicles++;
                    // wrecks placed on top of each other merge (map::add_vehicle_to_map,
                    // merge_wrecks) and what splits off has prototype "none"; its parts came from
                    // the mod's vehicles, which the vgroup check above covers
                    if( wv.v->type == vehicle_prototype_none ) {
                        continue;
                    }
                    CAPTURE( wv.v->type.str() );
                    CHECK( wv.v->type.str().rfind( "sgn_veh_", 0 ) == 0 );
                }
            }
        }
        if( wrecks.count( id.str() ) ) {
            CHECK( new_vehicles > 0 );
        }
    }
}

// The dda zombies Saigon keeps: generic dead with nothing American about them and no gear.  Every
// other member of the city groups is the mod's own (sgn_*), or one of their dormant twins
// (pseudo_dormant_*, made by MonsterGenerator for each zombie), or comes out of dda's cocoons.
static const std::set<std::string> sgn_kept_dda_zombies = {
    "mon_zombie", "mon_zombie_fat", "mon_zombie_tough", "mon_zombie_child", "mon_zombie_rot",
    "mon_zombie_crawler", "mon_zombie_dog", "mon_dog_zombie_rot", "mon_zombie_static",
    "mon_zombie_runner", "mon_zombie_brainless",
};

// dda's cocoons (GROUP_COCOON_*, kept by date as in dda) hatch amalgamations, and an empty
// cocoon roll is mon_null; none of that is American or armed
static bool sgn_from_cocoon( const mtype_id &m )
{
    static const std::set<mtype_id> hatched = [] {
        std::set<mtype_id> ret;
        for( const char *grp : {
        "GROUP_COCOON_TINY", "GROUP_COCOON_SMALL", "GROUP_COCOON_MED_1",
        "GROUP_COCOON_MED_2", "GROUP_COCOON_LARGE"
    } )
        {
            for( const mtype_id &h : MonsterGroupManager::GetMonstersFromGroup( mongroup_id( grp ), true ) ) {
                ret.insert( h );
            }
        }
        return ret;
    }();
    return hatched.count( m ) > 0;
}

static bool sgn_allowed_city_dead( const mtype_id &m )
{
    const std::string &id = m.str();
    // MonsterGenerator's dormant twins are pseudo_dormant_<id>; dda's own dormant zombie is
    // mon_pseudo_dormant_zombie
    std::string base = id.rfind( "pseudo_dormant_", 0 ) == 0 ? id.substr( 15 ) : id;
    if( base == "mon_pseudo_dormant_zombie" ) {
        base = "mon_zombie";
    }
    return base.rfind( "sgn_", 0 ) == 0 || sgn_kept_dda_zombies.count( base ) > 0 ||
           sgn_from_cocoon( m );
}

// E2: GROUP_ZOMBIE and GROUP_ZOMBIE_HORDE are overridden ("override": true), not extended.  The
// horde group is hardcoded in overmap.cpp for street hordes, so it has to be overridden as well.
// Breaks if: either override is turned back into an extend or deleted (dda's soldiers, SWAT, US
// cops and ferals return), or a dda zombie is added without being judged here first.
TEST_CASE( "saigon_zombie_groups_are_saigon", "[saigon][monster]" )
{
    if( !sgn_mon_zombie_xe_om.is_valid() ) {
        WARN( "saigon_2000s is not loaded; skipping" );
        return;
    }
    for( const char *grp : {
             "GROUP_ZOMBIE", "GROUP_ZOMBIE_HORDE"
         } ) {
        CAPTURE( grp );
        const mongroup_id gid( grp );
        REQUIRE( MonsterGroupManager::isValidMonsterGroup( gid ) );
        const std::vector<mtype_id> members = MonsterGroupManager::GetMonstersFromGroup( gid, true );
        std::string strangers;
        for( const mtype_id &m : members ) {
            if( !sgn_allowed_city_dead( m ) ) {
                strangers += m.str() + " ";
            }
        }
        CAPTURE( strangers );
        CHECK( strangers.empty() );
        // and it really is the Saigon mix, not an empty override that falls back on its default
        CHECK( std::count( members.begin(), members.end(), sgn_mon_zombie_xe_om ) > 0 );
        CHECK( std::count( members.begin(), members.end(), mtype_id( "sgn_mon_zombie_cong_an" ) ) > 0 );
        CHECK( sgn_allowed_city_dead( gid.obj().defaultMonster ) );
    }
}

// a firearm in the policy's sense (item::is_firearm): a GUN item that is not a slingshot or a
// crossbow (PRIMITIVE_RANGED_WEAPON)
static bool sgn_is_firearm( const itype *t )
{
    return t != nullptr && t->gun && !t->has_flag( flag_PRIMITIVE_RANGED_WEAPON );
}

// E2: no monster reachable from the city groups drops a firearm.  "Reachable" follows what the
// game does to a monster after it spawns: dormant twins wake into their zombie, zombies evolve
// (upgrade_into, upgrade_group), breed (baby_monster, baby_monster_group), burn and zombify.
// For each one, death_drops is expanded exhaustively, so a 1% gun is caught as surely as a 100%
// one.  This is the C++ twin of audit_us_content.py's monster pass (ledger: 118 reachable, 0
// firearm drops).
// Breaks if: a Saigon zombie's drops gain a gun, a zombie in the groups evolves into one that
// drops a gun (dda's soldier and cop lines did), or the override is lost (the count jumps and the
// soldiers' drops fail).  The lower bound on the count catches the walk silently breaking.
TEST_CASE( "saigon_city_dead_drop_no_firearms", "[saigon][monster]" )
{
    if( !sgn_mon_zombie_xe_om.is_valid() ) {
        WARN( "saigon_2000s is not loaded; skipping" );
        return;
    }
    std::set<mtype_id> reach;
    std::set<mongroup_id> groups_seen;
    std::vector<mtype_id> todo;
    const auto add_group = [&]( const mongroup_id & grp ) {
        if( grp.is_null() || !MonsterGroupManager::isValidMonsterGroup( grp ) ||
            !groups_seen.insert( grp ).second ) {
            return;
        }
        for( const mtype_id &m : MonsterGroupManager::GetMonstersFromGroup( grp, true ) ) {
            todo.push_back( m );
        }
    };
    add_group( GROUP_ZOMBIE );
    add_group( GROUP_ZOMBIE_HORDE );
    while( !todo.empty() ) {
        const mtype_id m = todo.back();
        todo.pop_back();
        if( m.is_null() || !m.is_valid() || !reach.insert( m ).second ) {
            continue;
        }
        const mtype &t = m.obj();
        if( m.str().rfind( "pseudo_dormant_", 0 ) == 0 ) {
            todo.emplace_back( m.str().substr( 15 ) );
        }
        todo.push_back( t.upgrade_into );
        add_group( t.upgrade_group );
        todo.push_back( t.baby_type.baby_monster );
        add_group( t.baby_type.baby_monster_group );
        todo.push_back( t.burn_into );
        todo.push_back( t.zombify_into );
    }
    CAPTURE( reach.size() );
    CHECK( reach.size() >= 60 );
    std::string armed;
    int with_drops = 0;
    for( const mtype_id &m : reach ) {
        const item_group_id &drops = m->death_drops;
        if( drops.is_null() || !item_group::group_is_defined( drops ) ) {
            continue;
        }
        with_drops++;
        for( const itype *it : item_group::every_possible_item_from( drops ) ) {
            if( sgn_is_firearm( it ) ) {
                armed += m.str() + ":" + it->get_id().str() + " ";
            }
        }
    }
    CAPTURE( with_drops, armed );
    CHECK( armed.empty() );
    // the Saigon dead carry things (the ledger's drops); a walk that found no drops checked nothing
    CHECK( with_drops >= 10 );
}
