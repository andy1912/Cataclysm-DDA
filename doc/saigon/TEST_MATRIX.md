# Saigon 2000s: test matrix

Unit F1-C (2026-10-18). One row per content area or mechanic of the mod, with the gate that
covers it and the gap that is left. "Python gate" means a script that `tools/saigon/check_mod.sh`
runs. "C++" means a case in `tests/saigon_*_test.cpp`, run with
`tests/cata_test --mods=dda,saigon_2000s "[saigon]"`. Every row also relies on the engine's own
load-time checks under `--check-mods` (ids resolve, mapgen exists for every overmap terrain,
recipes and item groups name real items), which `check_mod.sh` turns into failures.

The gates:

| Gate | What it checks |
|---|---|
| `check_mod.sh` (`--check-mods`) | The mod loads with no error or warning in debug.log. |
| `art/validate_tileset.py` | Mod tilesets: sheet paths, indices, sprite geometry. |
| `audit_us_content.py` | No American item, animal or mission is reachable from Saigon loot or people. Firearms only through `POLICE_ARMY_GUN_GROUPS` and the guard class. |
| `check_refs.py` | Every item and item_group reference resolves. Every building places someone (N6). Food vitamins exist. |
| `check_strings.sh` | Every translatable string extracts (T1). |
| `check_separation.sh` | Fork changes stay in the mod, tools, docs, tests and the listed engine files (S1). |
| `realmap/check_realmap.py` | Real-map bridges are straight and ramped, every hẻm network has a way in, no dda parks or warehouses. |

Status: **covered**, **partial** (some of it is covered, the gap is named), **in progress
(F1-E/W/V)** (another F1 test unit owns it), **gap** (nothing covers it).

| Area | Covered by | Gap | Final |
|---|---|---|---|
| Scenarios (2004 Vietmap, 2009 real map) | C++ `saigon_scenarios_and_starts` (F1-C): not blacklisted, intro EOC valid, the start counts (3 and 6), only Saigon professions. `saigon_new_game_realmap_2009`: the 2009 New-game path. | 2004 New-game path through `start_game` is not run (its starts are placed by `saigon_new_game_start_locations`). | covered |
| Start locations | `saigon_new_game_start_locations` (3 Vietmap starts placed, roofed, passable). `saigon_new_game_realmap_2009` (all 6 on the real map). `saigon_scenarios_and_starts` (F1-C): every allowed start is `sgn_` and its terrains exist. | none | covered |
| Professions and kits | `saigon_profession_kits` (F1-C): every profession either scenario permits, both genders, spawns valid items, no firearm, at least one `sgn_` item, a Saigon starting vehicle. The whitelisted hobbies hand out no firearm. `saigon_random_npcs`: random NPCs get Saigon professions. `audit_us_content.py` does not read profession kits. | Kits still use dda items (D3 B3-1, F2). This is content work, not a test gap. | covered |
| Climate: monthly curves, monsoon | `saigon_monsoon_climate`, `saigon_water_is_warm`, `monthly_climate_curve` | B4c heat index is not built. | covered |
| Weather types, flood (triều cường) | `saigon_flood_season` (wet-season rain floods, dry does not, drain). | The drain runs only around the player (D3 B4-1, F2). | covered |
| Items: street food, dishes, fruit, drinks, ice | `saigon_items_spawn_and_food_is_sane` (F1-C): every mod item spawns, nutrition is non-negative, cooked meat/egg/milk dishes spoil within 7 days. Food content itself: `saigon_food_test.cpp`. | Content-specific food behaviour is owned by V. | in progress (F1-V) + generic covered |
| Items: gear, clothing, household, kitchen, work | `saigon_items_spawn_and_food_is_sane` (F1-C): spawns, has a name and a description. `audit_us_content.py`. | No behavioural test (nón lá sun protection, mosquito net). The net is inert (D3). | partial |
| Items: currency, gold, wallet | `saigon_profession_kits` (every kit has `sgn_wallet`). `saigon_item_groups_spawn`. `audit_us_content.py` (US dollars only for tourists). | Gold prices (D3 B5-2, F2). | partial |
| Items: media, festival, culture (V3) | `saigon_items_spawn_and_food_is_sane` (spawns, snippet category exists). Content: `saigon_lore_test.cpp`. | | in progress (F1-V) + generic covered |
| Item groups (loot) | `saigon_item_groups_spawn` (F1-C): every `sgn_` group can reach an item and rolls without error. `check_refs.py`, `audit_us_content.py`. | Placement density per building is untested. | covered |
| Recipes | `saigon_recipes_learnable_and_makeable` (F1-C): every mod recipe makes a valid result, is not blacklisted, can be learned (skill, book or profession), and every component and tool slot has an alternative the world holds (an item group, a recipe result or a harvest). | Qualities (COOK, CUT...) are not traced to a findable tool. | covered |
| Books, book_learn | `saigon_books_teach_and_can_be_found` (F1-C): each mod book's recipes exist and point back to the book. Every teaching or skill book is findable. The cooking book teaches 10 or more recipes. | | covered |
| Vehicles: motorbikes, xích lô, ba gác, boats, parts | `saigon_traffic_is_mostly_two_wheelers`, `saigon_road_traffic_is_saigon` (groups and road chunks). Content: `saigon_vehicles_test.cpp`. | Drag and efficiency tuning; boats in canals. | in progress (F1-V) |
| Mapgen: nhà ống row | `saigon_nha_ong_row_structure`, `saigon_buildings_have_roofs`, `saigon_monster_budget_per_omt` | | covered |
| Mapgen: hẻm block | `saigon_hem_connectivity`, roofs, monster budget | Multi-OMT hẻm labyrinth not built. | covered |
| Mapgen: chợ | `saigon_cho_market_structure`, roofs, monster budget | The chợ stench (F2). | covered |
| Mapgen: chùa, chung cư | `saigon_chungcu_and_chua_structure`, roofs | | covered |
| Mapgen: kênh | `saigon_kenh_structure` | | covered |
| Mapgen: church, ward office, school (B8h) | `saigon_landmarks_structure` | | covered |
| Mapgen: landmarks L1-L4, real-map landmarks | `saigon_district1_landmarks` (footprints), `saigon_zoo_animals`, `saigon_realmap_2009_loads` | | covered |
| Mapgen: shophouse businesses (P1/P2, `sgn_pl_*`) and everyday places (V2, `sgn_vp_*`) | `saigon_places_enterable_and_roofed` (F1-C): every ground piece and its floors generate, can be entered from the tile edge, and have a roof over every indoor tile. `saigon_place_spawns_people` (the ward police post). | | covered |
| Mapgen: police and army sites (W3) | `audit_us_content.py` (guns only in their loot). Content: `saigon_weapons_test.cpp`. | | in progress (F1-W) |
| Mapgen: people specials, encounters, map extras (E1/E2) | `check_refs.py` (staffed). Content: `saigon_people_test.cpp`, `saigon_encounters_test.cpp`. | | in progress (F1-E) |
| Mapgen: roads, street life, railway, ferry, airport | `saigon_road_traffic_is_saigon`, `saigon_realmap_2009_ferry`, `saigon_realmap_2009_routes`, `saigon_realmap_2009_walkable` | Structural tests for `duong_sat`, `san_bay`, `ben_pha` pieces (covered only as walkable real-map routes). | partial |
| Region, overmap (Vietmap) | `saigon_cities_use_shophouses` (city pools 100% Saigon, no dda buildings) | | covered |
| Real map 2009 | `saigon_realmap_*` (8 cases), `check_realmap.py`, `saigon_engine_realmap_edge_road_exits` (F1-C) | | covered |
| Wildlife, fish, zoo animals | `saigon_delta_wildlife`, `saigon_zoo_animals`, `audit_us_content.py` (fauna) | | covered |
| Zombies, hordes | `saigon_monster_budget_per_omt` (mapgen spawns). Content: `saigon_encounters_test.cpp`. | Zombie behaviour (X14) is not built. | in progress (F1-E) |
| NPCs, factions, missions, dialogue | `saigon_random_npcs`, `saigon_npc_mission_pools`, `saigon_place_spawns_people`, `saigon_only_the_guard_is_armed`, `saigon_staff_have_voices`, `audit_us_content.py` (people). Content: `saigon_people_test.cpp`. | | covered + in progress (F1-E) |
| Weapons, firearm policy | `audit_us_content.py` (firearms only via `POLICE_ARMY_GUN_GROUPS` and the guard), `saigon_only_the_guard_is_armed`, `saigon_profession_kits` (F1-C, no firearm in a kit). Content: `saigon_weapons_test.cpp`. | | covered + in progress (F1-W) |
| Lore delivery (snippets, loa phường, radio, altars, intro) | `saigon_item_groups_spawn` (F1-C): name and carrier snippet categories exist and are non-empty. Content and EOC snippet references: `saigon_lore_test.cpp`. | Scheduled broadcasts reach only the player's z-level (V3). | in progress (F1-V) |
| Names | `saigon_random_npcs` (about 97% Vietnamese) | | covered |
| Tiles, sprites | `art/validate_tileset.py` (in `check_mod.sh`), `tools/saigon/art_coverage.py` (manual) | No game test renders tiles. The tiles build is checked by hand. | partial |
| Strings, translation | `check_strings.sh` | T2 (vi .po) is deferred. | covered |
| Separation from dda | `check_separation.sh` | | covered |
| Performance | `saigon_turn_time`, `saigon_zzip_level` (both hidden, run by hand) | Not in the default suite by design. | partial |

## Engine patches (doc/saigon/ENGINE_PATCHES.md)

| Patch | Test | Final |
|---|---|---|
| `display_buffer_coords.h`, `sdltiles.cpp` (HiDPI mouse) | `saigon_mouse_click_maps_to_display_buffer` (the math; the SDL glue is tiles-only and checked by hand) | covered |
| `do_turn.cpp` (no gamemode) | `saigon_engine_do_turn_without_gamemode` (F1-C); `saigon_turn_time` (hidden) | covered |
| `game.cpp` 1, test-mode terminal size | `check_mod.sh` | covered |
| `game.cpp` 2, scenario map choice | `saigon_new_game_realmap_2009`, `saigon_realmap_2009_*` | covered |
| `game.cpp` 3, forced placement keeps occupancy | `saigon_engine_forced_placement_keeps_occupancy` (F1-C) | covered |
| `game.cpp` 4 / `game.h`, `start_new_game_for_tests` | `saigon_new_game_realmap_2009` | covered |
| `main.cpp` (options init only in tiles) | `check_mod.sh` | covered |
| `map.cpp` 1 / `map.h`, vehicle-cache resync | `saigon_engine_resync_vehicle_lists` (F1-C), `saigon_new_game_realmap_2009` | covered |
| `map.cpp` 2, format string | `saigon_new_game_realmap_2009` (no logged errors) | covered (indirect) |
| `map_helpers.cpp`, `clear_overmaps` clears creatures | `saigon_engine_clear_overmaps_drops_creatures` (F1-C) | covered |
| `overmap.cpp` / `overmap.h`, pregenerated path and final | `saigon_realmap_loads_every_layer`, `saigon_realmap_reads_dda_single_layer_maps`, `saigon_realmap_2009_loads` | covered |
| `overmap_worldgen.cpp`, outside region | `saigon_realmap_2009_countryside` | covered |
| `savegame.cpp`, multi-layer, cities | `saigon_realmap_loads_every_layer`, `saigon_realmap_2009_loads` | covered |
| `savegame.cpp`, edge road exits | `saigon_engine_realmap_edge_road_exits` (F1-C) | covered |
| `scenario.cpp` / `scenario.h` | `saigon_new_game_realmap_2009` | covered |
| `weather_gen.cpp` / `.h`, monthly curves | `monthly_climate_curve` and the climate cases; `saigon_engine_monthly_curve_needs_12_values` (F1-C, rejects a curve without exactly 12 values) | covered |
| `zzip.cpp`, level 3 | `saigon_zzip_level` (hidden, needs a world archive) | partial |

## Running the F1-C cases
`tests/cata_test --mods=dda,saigon_2000s "[saigon_content],[saigon_engine]"` runs 13 cases. The
cases take about 60 s in all; data loading adds the rest of the 3.5-minute wall time. They pass
with seeds 7 and 1021. The world-touching engine cases and the places case stand on the real
map's overmap (0, 0), which loads in about a second. A generated Vietmap overmap takes about
100 s. These cases do not regenerate the world when they finish.

## Gaps left
- **Tiles:** no automated render check (tiles build only).
- **Compression level:** `zzip.cpp` level 3 is tested only by the hidden `saigon_zzip_level`.
- **Rail, airport and ferry pieces:** no structure test of their own.
- **Gear behaviour:** the nón lá, mosquito net and rain gear (X2) are not tested.
- **Gold prices:** not tested (F2).
- **Recipe qualities:** not traced to a findable tool.
- **Performance:** hidden by design.
