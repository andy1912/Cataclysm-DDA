# Critic verdict: D4 (JSON Ecosystem & Modding), round 2

- **Audited report:** `doc/saigon/analysis/d4_r2.md` (532 lines).
- **Rubric:** `doc/saigon/analysis/CRITIC_RUBRIC.md` (N=4, k=2).
- **Code under audit:** base SHA `fe6a10c2b1`.
  - Every citation was resolved with `git show fe6a10c2b1:<path>`. This matters for `src/game.cpp` and `src/main.cpp`, whose lines shifted in the committed C6 fix (`2efb03fe98`).
  - All other cited files are identical to base.
- **Runtime checks:** the post-C6 curses binary `./cataclysm` (built 2026-09-30 07:53), run with throwaway mods under a scratchpad `--userdir`. Nothing was written to the repo.

## Verdict

**REJECT.** There are 0 BLOCKER, 1 MAJOR and 5 MINOR defects. The citation failure rate is 0.0% (0 of 545 line refs).

All 13 round-1 defects, F1–F3 and all 12 required changes are fixed in substance, not just in the changelog. One MAJOR defect remains, and it rules out a PASS:
- The report's C6 seam and validation are **incomplete**. It missed a second curses-only `--check-mods` bug: `options_manager::init()` runs twice.
- That bug sits inside the very range the report cites (`src/main.cpp:771-780`).
- With only the report's seam, every `--check-mods` run exits 1 with ~106k option errors. The coordinator reproduced this and fixed it in `2efb03fe98`.

## Summary

### Round-1 follow-through (verified against code, not the changelog)

| r1 item | Status | Evidence checked |
|---|---|---|
| D1 C1 not required | FIXED | §0.5, §2.2 routes (a)–(e), §4.3 C1 "optional", §8.2 step 7, R1/R10. Road mapgen weights re-derived: 5 dda `mapgen` objects covering 6 `om_terrain`s, all `global_val vanilla_road_weight` (`data/json/mapgen/road.json:5,162,257,531,744`). No other dda mapgen targets a `road_*` om_terrain. Weighted-pick mechanics (`src/mapgen.cpp:508-523,536-545`) and nested `weighted_int_list` (`src/mapgen.h:595-607`, `src/mapgen.cpp:831-845`) confirmed. hunvre precedent: 24 `mapgen` objects plus the `game_begin` EOC. `game_begin` is sent after `opening_screen()` (`src/main.cpp:877-882` at base). |
| D2 MIGRATION | FIXED | §2.1 row, §2.3 decision table, R14, §7 cost row. The **overwrite correction to r1 is right.** `add_migration` overwrites the first non-`from_variant` entry (`src/item_factory.cpp:4661-4667`), so the "Multiple non-variant migrations" debugmsg at `:1774` is unreachable for JSON-only migrations. **Runtime-confirmed:** a mod migrating dda's already-migrated `reloaded_338lapua_api` to `338lapua_fmjbt` gave exit 0 with 0 ERROR lines. |
| D3 missing B6/B8 schemas | FIXED | §5 rows 27–31 and §1.3 rows. See "New §5 rows" below. |
| D4 `conflicts` | FIXED | `src/worldfactory.cpp:195-203` (inside the `bool show_prompt` overload at `:177`). The new claim that the programmatic overloads `:158`/`:166` skip the check is correct. |
| D5 C1 gating/cost | FIXED | Opt-in keys only. The default path stays `add`. The dda duplicates reproduce exactly: `parkinglot`, `oa_vg_wreck`, `pump_station_vehicles`. The O(n²) load cost is stated. |
| D6 whitelist scope | FIXED | The batch filter (`src/overmap.cpp:281-289`) and `map_extra::is_valid_for` (`src/map_extras.cpp:1314-1319`) are scoped correctly. Bypasses are listed (`src/mission_util.cpp:195-203`, `src/overmap.cpp:2024-2030`, `src/game.cpp:995-1016`, `src/overmap_highway.cpp:232-237`, `src/start_location.cpp:590-595`, `src/timed_event.cpp:312-317`). R15 is added. The 154 `"om_special"` refs in `data/json` reproduce. |
| D7 hardcoded ids | FIXED | Reproduced on the base tree: 4,870 decls / 2,535 unique; `ammotype` 55 decls / 36 unique; `morale_type` 84; `zone_type_id` 85; `ammo_effect_str_id` 83; 66 multi-line; 609 inline literals (~600), 44 in headers (~40); `bodypart_id(` 414; `mon_flag_id(` 136; both are `int_id` (`src/type_id.h:39,188`). The per-type unique counts in the table all match. |
| D8 mandatory keys | FIXED | Scenario `name/description/start_name/points/allowed_locs` (`src/scenario.cpp:63-100`) and profession `items` optional are correct. The `subtypes` rule is **runtime-confirmed**: a copy-from patch of `cookbook_daintydishes` setting `max_level` without `subtypes` gave exit 1 with "Unread data … `max_level`". The supporting figures are wrong, though (D5 below). |
| D9 SEASON_LENGTH | FIXED | `src/game_io.cpp:452-453` runs in the save-load path after the world's mods are loaded. `src/scenario.cpp:124,137-157` bakes in the season length. The rule "never set it in the mod" is stated. |
| D10 checkable facts | FIXED | The TC `conflicts` list matches all 11 other `total_conversion` ids plus `tropicata`/`desertpack`/`ruralbiome`. The `polib` prerequisite is stated. `-r` is opened in append mode (`lang/extract_json_strings.py:93`). The year comes from `src/calendar.cpp:836`. `backrooms` and the aftershock deps are correct. |
| D11 speculation | FIXED | Both claims are now marked UNVERIFIED. |
| D12 UB precondition | FIXED | `src/item_factory.cpp:1671`. |
| D13 / F3 `UPS` | FIXED | `src/visitable.cpp:52`, `src/character.cpp:229`, `src/requirements.cpp:47`. |
| F1, F2 | FIXED | See D8 and D4. |

### High-scrutiny claims

- **JSON-only traffic routes.** Correct in mechanism.
  - Route (a) displaces dda road mapgen from turn 0.
  - Route (b)'s precedent is real, and the timing caveat is right.
  - Route (c) works, but coverage is under-specified (D4).
  - The route (d) totals reproduce exactly: `city_vehicles` 122/26,219; `city_pileup` 75/20,490; `police_pileup` 5/806; `highway` 82/20,479; `parkinglot` 101/19,232; `crashed_helicopters` 15/16,884; `suburban_home` 80/12,670.
- **Auto-created singleton vehicle groups.** Correct: `vgroups[vgroup_id( id.str() )].add_vehicle( id, 100 )` at `src/veh_type.cpp:1342`. `jmapgen_vehicle` reads `"vehicle"` as `mapgen_value<vgroup_id>` (`src/mapgen.cpp:2714,2721`), so direct prototype placements go through it. dda has no group/prototype id collisions (66 groups, 256 prototypes). The report does not state the namespace hazard this creates for Saigon ids (Missed topics).
- **C1 gating.** Correct and sufficient.
- **The new §5 rows 27–31.** All verified.
  - `vehicle_part`: there is no top-level `mandatory` in `vpart_info::load`. Only `workbench`/`transform_terrain` sub-objects have one. `check()` requires the item (`src/veh_type.cpp:873-875`), and copy-from rewrites `looks_like` (`:224-246`).
  - `vehicle_placement`: `src/vehicle_group.cpp:105-113`.
  - Nested `mapgen`: weight is `int` with default 1000 (`src/mapgen.cpp:834`).
  - `terrain`: `name`/`description` are mandatory (`src/mapdata.cpp:1202-1203`), and `color`/`bgcolor` is required unless copy-from (`:793-794`).
  - `furniture`: `move_cost_mod`/`required_str` (`:1618-1619`).
- **Mission leak.** Correct. `overmap_buffer.place_special` is called without the feature-flag filter.
- **C6 hang analysis.** Correct as far as it goes.
  - `initialize_interface` skips `catacurses::init_interface()` in test mode (base `src/main.cpp:764-776`).
  - `catacurses::getmaxy/getmaxx` return **0** for a null window (base `src/ncurses_def.cpp:105-118`).
  - `ensure_term_size` (base `:578-611`) spins at `:585`: `getch()` returns immediately and the size never changes.
  - **It missed the double options init (D1).**
- **B10 decision rule.** Sound, and runtime-backed for the overwrite case. It leaves two checkable hazards UNVERIFIED or unstated (D3).

## Citation verification

Method: a script extracted every `path:line[-line][,line…]` and every backticked `:NNN` shorthand, binding each shorthand to the last path on the same report line. Each range was resolved against `git show fe6a10c2b1:<path>` and range-checked. The script dumped ±2 lines of every unique (path, range) pair (3,955 lines), and I read all of them against the report's claim.

The extractor mis-bound one reference, `tools/format/CMakeLists.txt:3-8`, to the root `CMakeLists.txt`. I checked it by hand, and it is correct (target `json_formatter`).

| Metric | Count |
|---|---|
| Citation strings extracted | 453 |
| Individual line refs | 545 |
| Unique (path, range) pairs read | 432 |
| Out of range / nonexistent path | 0 |
| Symbol or claim not at cited line (±5) | 0 |
| **FAIL** | **0 (0.0%)** |
| Backticked identifiers grepped | 576. 561 found. The 15 not found are directory names (`No_Hope`, `mapgen_pallete`, `mod_settings`, `setting_blacklists`, `migration_and_obsoletion`, `mapgen_eocs`), proposal/scratch tokens (`SAIGON`, `sgn_*`), `ModuleNotFoundError`, `ducpa` and the SHA. None is a claimed code symbol. |

FAIL rows: none.

**SCRIPT-VERIFIED figures re-run.** These all match: `MIGRATION` 855; ITEM 10,440; mapgen 7,072; recipe 5,603; item_group 5,528; MONSTER 1,221; om_special 154; the vehicle-group totals; the duplicate entries. **Two do not match** (D5).

## Defects

### D1 (MAJOR, R2/R5): C6 seam and validation are incomplete; the double `options_manager::init()` was missed

- **Claim:** §4.3 C6 says to skip `ensure_term_size()` when `test_mode`, then "**Validate:** the same command exits within load time." §8.2 step 0 says "C6 (tiny C++) … Otherwise `--check-mods` is unusable", which implies C6 alone makes it usable.
- **Evidence:**
  - In a non-TILES build, `initialize_interface` runs `get_options().init(); get_options().load();` unconditionally (base `src/main.cpp:759-762`, `#if !defined(TILES)`).
  - In test mode with `cli.check_mods` it runs them **again** (base `src/main.cpp:777-780`). That line is inside the report's own citation `src/main.cpp:771-780`.
  - The coordinator reproduced the result with the hang removed: `--check-mods` exits 1 with about 106k option errors. Fixed in `2efb03fe98` (`src/main.cpp` +4 lines).
  - So the report's seam would have turned a hang into a false FAIL for every mod. The stated validation ("exits within load time") would pass, while the exit code, which is the gate §8.2 step 1 relies on, would be wrong.
- **Required fix:**
  - Extend C6 with the second hunk: in `initialize_interface`, skip the `cli.check_mods` re-init when `!defined(TILES)`, or guard `options_manager::init` against re-entry.
  - Change the validation to "a minimal valid mod gives exit 0 and 0 ERROR lines in `config/debug.log`". Measured post-fix: `crit_ok` took 93 s, returned rc 0 and logged 0 ERROR lines.
  - Update R16 and the changelog. Mark C6 as landed (`2efb03fe98`).

### D2 (MINOR, R2): C2 and R2 "exits 0 on a hard JSON error" is contradicted at runtime

- **Claim:** §0.5 says "C2 fixes the exit-0-on-JSON-error gap". §6.2 gotcha 2 says "A hard JSON error exits 0". §9 R2 says "`--check-mods` exits 0 on a fatal JSON error". The C2 seam is "set a failure flag … return false". The runtime result was correctly marked UNVERIFIED.
- **Evidence (runtime, post-C6 binary):**
  - `crit_syntax` (truncated JSON) exited with **rc 134**, and `crit_badtype` (`"type":"COMESTIBLE"`) also exited with **rc 134**. Both printed `Error loading data`, then `libc++abi: terminate_handler unexpectedly threw an exception`.
  - `config/debug.log` has 2,239 ERROR lines. The backtrace is `main` → `exit` → `__cxa_finalize` → `generic_factory<mtype>::~generic_factory` → deferred `std::pair<JsonObject,std::string>` destructor → `JsonObject::report_unvisited` → `error_skipped_members` (`src/flexbuffer_json.cpp:332`). The first message is on dda's `data/json/monsters/LIXA_monsters.json` `copy-from`.
  - Mechanism: the exception at `src/game_io.cpp:200-202` skips `finalize_loaded_data()`, so dda's deferred copy-from objects are never consumed. Their `JsonObject`s are destroyed at static teardown and flood debugmsg, and the process aborts.
  - Consequences:
    - The exit code is non-zero, but only through a crash.
    - The C2 seam as written (`return false`) would still abort after `exit(1)`.
    - `tools/saigon/check_mod.sh`'s header comment repeats the incorrect "exit 0" premise.
- **Required fix:**
  - Restate R2 and C2 with the measured behaviour: "rc 134 via static-destruction abort; ~2.2k spurious ERRORs mask the real one".
  - Change the C2 seam to (1) record failure and return false, **and** (2) discard deferred data on the error path, for example `DynamicDataLoader::get_instance().unload_data()` in the catch, so teardown is clean. Leave the exact call UNVERIFIED until tested.
  - Validate with the two scratch mods: expect rc 1, one `Error loading data`, and no abort.

### D3 (MINOR, R6/R7): MIGRATION hazards that could have been verified are left UNVERIFIED or unstated

1. "Harvest drops and profession starting items are candidates to audit (UNVERIFIED)" is checkable by grep. `migrate_id` has no caller in `src/profession.cpp`, `src/harvest.cpp` or `src/activity_handlers.cpp`. The full caller list is `src/map.cpp:5829`, `src/mapgen.cpp:2362,2495,2865`, `src/mattack_actors.cpp:1455,1459`, `src/savegame_json.cpp:345,3379` and `src/veh_type.cpp:600,1578-1579`. So those paths **do** build the un-migrated id. State it as fact.
2. Migration is **single-hop**. `migrate_id` returns `parent->replace` with no loop (`src/item_factory.cpp:4720-4735`), and the group rewrite is one `replacements.find` (`src/item_group.cpp:397-401`). If dda migrates A→B and the mod migrates B→C, saved or mapgen A becomes B, not C.
3. Migrating a gun id hides its turret part: `NO_INSTALL_HIDDEN` if `item_id != migrate_id( item_id )` (`src/veh_type.cpp:599-603`).
- **Required fix:** add items 1–3 to §2.3 and R14.

### D4 (MINOR, R5): Route (c) coverage is under-specified; bridges are not covered by route (a)

- **Claim:** §5.1 says "one object per dda road om_terrain / nested id", and gives a single `24x24_road_straight_vehicles` example.
- **Evidence:** the dda vehicle entry points referenced from `road.json` and `bridges.json` are 8 top-level nested ids:
  - `24x24_road_end_vehicles` (×2 refs), `24x24_road_straight_vehicles`, `24x24_road_curved_vehicles` (×2), `24x24_road_curved_layby_vehicles`, `24x24_road_tee_vehicles`, `24x24_road_four_way_crossroad_vehicles`;
  - and, from `data/json/mapgen/bridges.json`, `24x24_bridge_road_vehicles` and `24x24_bridgehead_ground_vehicles`.

  Bridge OMTs are not `road_*` om_terrains, so route (a) alone leaves dda bridge traffic in place. Each top-level id has exactly one dda definition at weight 1000, so the "~0.1% residual" figure holds per id. Also, "six dda road mapgens" should read "5 mapgen objects / 6 om_terrains".
- **Required fix:** list the 8 (route c) and 6 (route a) ids explicitly in §2.2 and §5.1, and state that bridges need (c).

### D5 (MINOR, R2): Two figures reused from r1 do not reproduce

- §5 row 5 says "the critic counted 325 dda professions/hobbies without it". In fact `data/json` has **342** `profession` objects, of which **125** lack `items` (123 of those are hobbies). Across all of `data/` the figure is 353 of 747.
- §5 row 9 says "dda restates `subtypes` in 4,151 of 4,987 ITEM copy-froms [SCRIPT-VERIFIED]". A re-run over `data/json` gives **4,208 of 5,054**, or 4,183 of 5,029 excluding `obsolet*` paths. It is tagged SCRIPT-VERIFIED but was not re-run.
- The conclusions are unchanged.
- **Required fix:** re-run both counts and replace them, or drop the numbers.

### D6 (MINOR, R2): `map_extra_id` location list incomplete

The §3.1 row cites `src/map_extras.cpp` and `src/timed_event.cpp`. `static const map_extra_id` declarations also exist in `src/overmap.cpp` and `src/overmapbuffer.cpp`. **Required fix:** add them.

No R3 violations. Every proposal is load-time or tooling. The per-OMT cost of var weights (`src/mapgen.cpp:508-517`) is addressed, and constant weights add none. No R4 violations: reskins are explicitly flagged text-only.

## Missed topics

1. **Double `options_manager::init()` in non-TILES `--check-mods`** (base `src/main.cpp:759-762` + `:777-780`). This is D1, found and fixed by the coordinator. The report's C6 covered only the `ensure_term_size` hang.
2. **Static-destruction abort after a caught load error** (deferred dda copy-from `JsonObject`s, `src/flexbuffer_json.cpp:252,332`). This is D2, and it determines what C2 must actually do.
3. **Shared vehicle-group/prototype namespace.** Every `vehicle` id silently creates a `vehicle_group` of the same id (`src/veh_type.cpp:1342`), and `vehicle_group` loads append (`src/vehicle_group.cpp:80-87`). A Saigon `vehicle_group` named like any Saigon or dda prototype would therefore merge with that singleton. A same-id prototype override (route e) adds a second weight-100 entry, which is harmless. The authoring rule needs one line in R8.
4. MIGRATION single-hop and turret hiding (D3).
5. Aside (not scored): the committed C6 comment in `src/game.cpp` says `getmaxy/getmaxx` "return -1". The `catacurses` wrappers return **0** for a null window (base `src/ncurses_def.cpp:105-118`). The fix is correct either way.

## Runtime checks performed (scratchpad `--userdir`, post-C6 `./cataclysm`)

| Mod | Content | rc | debug.log ERROR | Result |
|---|---|---|---|---|
| `crit_ok` | one valid snippet | 0 | 0 | C6 fix works (93 s) |
| `crit_syntax` | truncated JSON | **134** | 2,239 | D2 |
| `crit_badtype` | `"type":"COMESTIBLE"` | **134** | 2,239 | D2 |
| `crit_sub` | book copy-from sets `max_level`, no `subtypes` | 1 | 2 | Confirms the §5 row 9 rule |
| `crit_mig` | re-migrate dda's `reloaded_338lapua_api` → `338lapua_fmjbt` | 0 | 0 | Confirms the overwrite correction (`src/item_factory.cpp:4661-4667`) |

## Required changes for next revision

1. [ ] **(D1, MAJOR)** Add the double-options-init hunk to C6 (base `src/main.cpp:759-762,777-780`). Change the C6 validation to "exit 0 **and** 0 ERROR lines in `debug.log`". Mark C6 landed in `2efb03fe98`. Update R16, §6.2 gotcha 1 and §8.2 step 0.
2. [ ] **(D2)** Replace "exits 0" in §0.5, §6.2 gotcha 2 and R2 with the measured rc 134 static-teardown abort. Redesign the C2 seam to return false and discard deferred data on the error path. Validate on the two scratch mods (expect rc 1 and no abort).
3. [ ] **(D3)** State as verified that profession/harvest/butchery item construction is not migrated. Add single-hop migration and turret-part hiding to §2.3 and R14.
4. [ ] **(D4)** List the 6 road om_terrains for route (a) and the 8 nested vehicle entry ids for route (c), including the 2 bridge ids. Correct "six dda road mapgens" to 5 objects / 6 om_terrains.
5. [ ] **(D5)** Re-run and correct the profession-without-`items` count (125/342) and the ITEM copy-from `subtypes` count (4,208/5,054).
6. [ ] **(D6)** Add `src/overmap.cpp` and `src/overmapbuffer.cpp` to the `map_extra_id` row.
7. [ ] **(Missed 3)** Add the vehicle-group/prototype shared-namespace rule to R8 and §8.1 (`vehicles/`).
