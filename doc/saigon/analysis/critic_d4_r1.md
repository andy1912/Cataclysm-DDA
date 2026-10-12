# Critic verdict: D4 (JSON Ecosystem & Modding), round 1

Audited report: `doc/saigon/analysis/d4_r1.md` (593 lines). Clone `/Users/ducpa/code/cdda-saigon`, HEAD `73388627e9`.
`git diff fe6a10c2b1 HEAD -- src data tools lang tests` is empty, so the code under audit is the base SHA.
Rubric: `doc/saigon/analysis/CRITIC_RUBRIC.md` (N=4, k=1).

## Verdict

**REJECT.** There are 0 BLOCKER, 3 MAJOR and 10 MINOR defects. The citation failure rate is 0.7% (3 of 422 line refs), which is under the 2% bar, but the MAJOR defects rule out a PASS.

## Summary

Citation discipline is strong. I extracted all 306 `path:line` citation strings (422 line refs, including the `:NNN` shorthand), dumped each cited line with a script, and read them. I also grepped all 269 backticked identifiers. Almost everything lands on the named symbol. I tried hard to falsify the high-impact claims, and they hold:

- `vehicle_group` is append-only (`src/vehicle_group.cpp:80-87` → `vehicle_group.h:37-38` `vehicles.add`).
- `--check-mods` exits 0 on a hard `JsonError` (`src/game_io.cpp:200-202,210`; `src/init.cpp:547-548` rethrows as `runtime_error`; no `DebugLog(D_ERROR)` on that path). Unvisited-member errors *do* go through `debugmsg` (`src/flexbuffer_json.cpp:331-333`), as the report says.
- `ITEM` + `subtypes` is correct (`src/init.cpp:367`, `src/item_factory.cpp:3115-3189`). No `COMESTIBLE`/`BOOK`/`TOOL`/`ARMOR`/`GENERIC` loader is registered.
- The region feature-flag whitelist filters the special batch (`src/overmap.cpp:281-289`) and `map_extra::is_valid_for` (`src/map_extras.cpp:1314-1319`).
- Erasing from a `std::set` inside a range-for is UB (`src/item_factory.cpp:1670-1674`).
- `npc` is first-wins via `std::map::emplace` (`src/npc.cpp:540`).
- The scenario `eoc` is queued by `load_new_character` at `src/game.cpp:1072` (`Character::queue_effects`, `src/character.cpp:452-460`, at `turn_zero`).
- `LATITUDE`/`LONGITUDE` are applied after `load_world_modfiles` (`src/game.cpp:700,715`).
- `SEASON_LENGTH` is applied before it (`src/game.cpp:695-697`).
- The hardcoded-id grep reproduces exactly: 4,724 declarations, 2,426 unique.
- The data volume counts reproduce, and the special budget of ≈13 reproduces.

Where the report fails is judgement and completeness, not citation hygiene:

1. **Its one "required" C++ seam (C1) is not required.** At least three JSON-only routes exist, and there is an in-repo precedent for one of them.
2. It **omits the item `MIGRATION` mechanism**, which is the most powerful JSON tool for replacing US items with Saigon items globally.
3. Its schema section **skips two of the four types the plan assigns to B6** (`vehicle_part`, `vehicle_placement`), and it has several wrong "mandatory" markings.

## Citation verification

| Metric | Count |
|---|---|
| Unique `path:line` citation strings checked (script + manual read) | 306 (288 explicit + 18 shorthand groups) |
| Individual line refs checked | 422 |
| Backticked identifiers grepped (outside `doc/saigon`) | 269; 266 found, 3 are proposal/meta tokens (`SAIGON`, `fe6a10c2b1`, `path:line`) |
| Abbreviated paths (`.../dimension_settings.json`, `desert_region/.../desert_regional_map_settings.json`, bare `game_io.cpp`, `npc.cpp`, `newcharacter.cpp`, `vehicle_group.cpp`, `generic_factory.h`) | all resolve; the lines match |
| OK | 419 |
| **FAIL** | **3 (0.7%)** |

FAIL rows:

| # | Citation | Claim | Actual |
|---|---|---|---|
| F1 | `src/profession.cpp:314-339` | "`items` is read unconditionally for new objects", and it is listed as **M** | It is read unconditionally, but `JsonObject::get_object` returns an empty object when the member is missing (`src/flexbuffer_json-inl.h:880-887`). 325 dda professions/hobbies have no `items` (for example `data/json/hobbies.json` `boating_license`). It is not mandatory. |
| F2 | `src/mod_manager_ui.cpp:104-108` | "`conflicts` is enforced **only here, in the UI**" | It is also enforced in `worldfactory::make_new_world` (`src/worldfactory.cpp:195-203`, "Unable to create new world: %s conflicts with %s") and at `src/worldfactory.cpp:857`. |
| F3 | `src/iuse.cpp:260-312`, `src/vehicle.cpp:120-127`, `src/mapgen.cpp:118-123` | Examples include `UPS` | `UPS` is in none of the three ranges. It is at `src/visitable.cpp:52`, `src/character.cpp:229` and `src/requirements.cpp:47`. |

## Defects

### D1 (MAJOR, R2/R7): C1 `vehicle_group` override is labelled "required", but JSON-only routes exist

- **Claim:** §0.5 says "one required seam … (C1) … required for de-Americanized traffic". §2 says "Vehicles in dda groups: **None in JSON**". R10 says the road weight EOC route is "Prefer not to rely on it; roads stay dda".
- **Evidence:**
  - dda road vehicles come only from nested chunks that `data/json/mapgen/road.json` pulls in (`24x24_road_*_vehicles` in `data/json/mapgen/nested/road_vehicles_nested.json:4,44,53,72,112`). The road mapgen weight is `{ "global_val": "vanilla_road_weight", "default": 1000 }` (`data/json/mapgen/road.json:5,162,257`).
  - (a) Mapgen is additive and weighted (`src/mapgen.cpp:798,822-829`). A Saigon road mapgen for the same `om_terrain` at weight 1,000,000 displaces dda roads at 99.9% **from turn 0**, with no `game_begin` timing issue.
  - (b) The EOC route has an in-repo total-conversion precedent: `data/mods/hunvre/json/mapgen/infrastructure/road.json:2-8` (own road mapgen + `vanilla_road_weight = 0`). dda even ships the override hooks "purely for mods to override" (`data/json/effects_on_condition/mapgen_eocs/vanilla_map_weight_eocs.json:3`).
  - (c) Nested mapgen is also additive (`src/mapgen.cpp:831-836` `nested_mapgens[id_base].add`). The mod can add same-id `24x24_road_*_vehicles` chunks with dominant weight.
  - (d) Appending to dda groups dilutes them. For example `city_vehicles` totals 26,219 (122 entries), so appending Saigon prototypes at weight 2,600,000 gives about 99% Saigon traffic.
- **Required fix:**
  - Downgrade C1 to "nice-to-have / upstreamable".
  - Document routes (a)–(d) with the precedents.
  - State the residual cases that really need C++: C++-hardcoded `vgroup_id` `parkinglot` (`src/vehicle_group.cpp:21,247`) and `crashed_helicopters` (`src/map_extras.cpp:345`), plus exact removal.
  - Re-rank §4.3 and §8.2 step 7.

### D2 (MAJOR, R6): Brief Q2 ("all mechanisms to suppress US content") misses item `MIGRATION`

- **Evidence:**
  - `add( "MIGRATION", … load_migration )` is at `src/init.cpp:370-371`.
  - At finalize, `Item_factory::finalize_item_blacklist` batch-replaces migrated ids in **every item group** (`src/item_factory.cpp:1722-1752`), **every requirement** (`:1754-1757`) and every vehicle item spawn (`:1810-1850`).
  - At spawn time it replaces them in `map::spawn_item` (`src/map.cpp:5829`) and mapgen (`src/mapgen.cpp:2362,2495,2865`).
  - Nothing forbids migrating an id that still exists. `check_consistency` only validates the target (`src/item_factory.cpp:3023-3033`).
  - dda uses it 855 times. Mod precedent: `data/mods/Magiclysm/migration_and_obsoletion/migration.json`.
  - This is the only JSON mechanism that swaps an American item for a Saigon equivalent everywhere, including in recipes, without the requirement-stripping side effect of `ITEM_BLACKLIST` (§3.2).
- **Required fix:**
  - Add `MIGRATION` to the §2 table with semantics, caveats and an example:
    - it also rewrites requirements, so never migrate hardcoded §3.1 ids;
    - "Multiple non-variant migrations" errors if dda already migrates that id (`src/item_factory.cpp:1774`);
    - it also converts existing saves.
  - Compare it with blacklist and same-id reskin in a decision table for B10.

### D3 (MAJOR, R6): The schema section omits B6 types the plan names, and has no loader semantics for them

- **Evidence:** `PLAN.md` B6 lists `vehicle`, `vehicle_part` (copy-from), `vehicle_group` and `vehicle_placement` as the main types. The report gives no schema, loader citation or example for `vehicle_part`, although it is registered at `src/init.cpp:352` and is a `generic_factory<vpart_info>` at `src/veh_type.cpp:58`. `vehicle_placement` appears only in the §1.3 collision row and has no §5 entry. B8 also relies on `terrain`/`furniture` (`src/init.cpp:313-314`), `nested_mapgen` (additive, `src/mapgen.cpp:831-836`) and `update_mapgen`, and none of them is covered. The plan's gate says Part A must "confirm or correct the JSON keys that Part B assumes".
- **Required fix:**
  - Add §5 rows for `vehicle_part` (copy-from semantics, mandatory keys, an example of a hull/engine part), `vehicle_placement`, `nested_mapgen`, `terrain` and `furniture`.
  - Add their collision semantics to §1.3.

### D4 (MINOR, R2): `conflicts` enforcement is misdescribed

This is F2. Fix §1.1 and R4 so they cite `src/worldfactory.cpp:195-203`. World creation is blocked; `conflicts` is not merely a UI hint.

### D5 (MINOR, R2/R3): C1's "behaviour-neutral for dda" is false and its cost is unaddressed

- **Evidence:** dda groups contain five duplicate ids: `parkinglot` has `motorcycle_3wheel` ×2 and `motorcycle_3wheel_super` ×2; `oa_vg_wreck` has `car_mini` ×2 and `semi_truck` ×2; `pump_station_vehicles` has `suv_electric` ×2. `add_or_replace` would collapse the summed weights into one weight, which changes the dda distributions. The analyst left this "UNVERIFIED" although a 10-line script settles it. `add_or_replace` also scans linearly per insert (`src/weighted_list.h:86-100`). That is O(n²) per group at load time; trivial at n≈122, but not stated.
- **Required fix:** use `add_or_replace` only when `"override": true` or a new opt-in key is present, or dedupe the dda data. State the load-time cost.

### D6 (MINOR, R2): The reach of the feature-flag whitelist is overstated

- **Claim:** "filters every overmap special **and every map extra**".
- **Evidence:** extras are filtered only on the region-random path (`map_extra_collection::filtered_by`, `src/regional_settings.cpp:854-867`). Scenario/start extras (`src/start_location.cpp:593`), timed events (`src/timed_event.cpp:315`) and debug bypass it. Several special-placement paths also bypass the whitelist:
  - mission targets (`src/mission_util.cpp:200`), so dda NPC missions can still place US specials;
  - forest trailheads (`src/overmap.cpp:2027-2029`);
  - forced placements (`src/game.cpp:995-1016`, `src/overmap_highway.cpp:232-237`).
- **Required fix:** scope the claim precisely and add the mission-target leak to the risk table.

### D7 (MINOR, R2): The hardcoded-id method has holes

- **Evidence:**
  - The stated regex `[a-z_]+(_id|_str_id|flag|ammotype)` cannot match `static const ammotype` (it needs a prefix char), so the 36 `ammotype` ids in the table are **not** part of the 2,426.
  - "A grep for inline literals … returns 0" is false. There are about 15 in headers, for example `src/map.h:984,1174,1177,2713,2740` and `src/profession.h:62-64`.
  - The table omits hardcoded ids that matter to this TC: `vgroup_id` `parkinglot`/`crashed_helicopters`, 14 `map_extra_id`, `profession_id` `unemployed`, and `faction_id` `your_followers`/`no_faction`.
- **Required fix:** correct the count and the method statement, and add the missing rows (especially `vgroup_id`, which feeds D1).

### D8 (MINOR, R2): Wrong "mandatory" keys in §5

- **Evidence:**
  - Profession `items` is not mandatory (F1).
  - Scenario `start_name` is effectively mandatory: `jo.get_string("start_name")` with no fallback (`src/scenario.cpp:78-81`). `allowed_locs` throws if empty (`src/scenario.cpp:98-99`). Both are listed under "Use:".
  - For `ITEM` same-id or copy-from patches, `subtypes` must be restated or the slot fields are never deserialized and raise unvisited-member errors (`src/item_factory.cpp:3176` reads `subtypes` into a local vector). dda restates it in 4,151 of 4,987 copy-from items. §8.3's book patch idiom needs this warning.
- **Required fix:** correct these rows and add the `subtypes` rule to §5 and §8.3.

### D9 (MINOR, R6): The `SEASON_LENGTH` analysis is incomplete

- **Evidence:** on a save load the options are re-read **after** mods load (`src/game_io.cpp:452-453`). A non-stub mod `SEASON_LENGTH` would therefore give a new game one calendar and the reloaded game another. Scenario JSON also bakes `SEASON_LENGTH` into its start times at load (`src/scenario.cpp:124,137-157`), which is why `#81904` exists.
- **Required fix:** state "never set SEASON_LENGTH/ETERNAL_SEASON in the mod; document the world-creation option instead", with these citations.

### D10 (MINOR, R7): Checkable facts left UNVERIFIED or wrong

- The Backrooms mod id is `backrooms`, not `Backrooms` (`data/mods/Backrooms/modinfo.json`).
- §3.2 says aftershock/hunvre/Megacity/MA "all declare `\"dependencies\": [\"dda\"]`". aftershock declares `["dda","no_npc_food"]`.
- The §6.3 dry run fails on this machine: `polib` is not installed (`ModuleNotFoundError`). The prerequisite is not mentioned.
- The extractor **appends output into the `-r` file** (`lang/extract_json_strings.py:92-95`), so running it against `lang/po/base.pot` mutates that file. This is undocumented.
- "Year 2004 … UNVERIFIED" is readable: the year is `years_since_cataclysm + 1` (`src/calendar.cpp:836`).
- The conflicts list omits `skyisland`, `Isolation_Protocol` and `defense_mode`.
- **Required fix:** verify these, fix the template, and add the tooling prerequisites.

### D11 (MINOR, R7): Speculation presented as fact

- "Even `aftershock_exoplanet` gets this wrong" asserts intent. Appending atomic cars may be deliberate.
- "This is the dominant fixed cost of depending on dda" (mapgen setup, §7) is unmeasured.
- **Required fix:** mark both UNVERIFIED, or measure with C5.

### D12 (MINOR, R2): The whitelist-mode UB precondition is overstated

- **Claim:** whitelist mode "hits the UB at `:1670-1674`".
- **Evidence:** the erase only runs when an id is on **both** a whitelist and a blacklist (`src/item_factory.cpp:1671`).
- **Required fix:** state the precondition. The advice to use blacklist mode only still stands, for performance reasons.

### D13 (MINOR, R2): F3 citation imprecision (`UPS`)

Cite a file that actually declares it.

## Missed topics (spot-checks)

1. **Item `MIGRATION`** as global replacement (D2). Grep: `add( "MIGRATION"` at `src/init.cpp:370`; `migrate_id` at `src/map.cpp:5829` and `src/mapgen.cpp:2362`.
2. **Road displacement by mapgen weight and the `vanilla_*_weight` hooks** (D1): `data/mods/hunvre/json/mapgen/infrastructure/road.json`, `data/json/effects_on_condition/mapgen_eocs/vanilla_map_weight_eocs.json`, `nested_mapgens[...].add`.
3. **`vehicle_part`, `nested_mapgen`, `terrain`/`furniture` schemas** (D3).
4. **Special-placement paths that bypass the region whitelist** (D6): `src/mission_util.cpp:200`, `src/overmap.cpp:2029`.
5. **The world-option re-read on save load** (D9): `src/game_io.cpp:452`.

No R3 violation on a runtime hot path. All proposals are load-time or tooling, and the report correctly notes the `monster_is_blacklisted` cost on the spawn path. No R4 violation: the report does not claim any Vietnamese mechanic, and §8.3 explicitly flags reskins as non-mechanical. No R5 violation: C1–C3 each name a seam, ordered steps and a validation.

## Required changes for next revision

1. [ ] Rewrite C1 as optional. Document JSON routes (a) high-weight Saigon road mapgen, (b) the hunvre `vanilla_road_weight` precedent, (c) same-id high-weight `nested_mapgen` vehicle chunks, and (d) group dilution, with citations. Identify what still truly needs C++ (`parkinglot`, `crashed_helicopters`, exact removal). Update §0, §4.3, §8.2 step 7 and R1/R10.
2. [ ] Add item `MIGRATION` to §2, with semantics (`src/item_factory.cpp:1722-1757,1810-1850`, `src/map.cpp:5829`), hazards (hardcoded ids, pre-existing dda migrations, save conversion) and a blacklist vs migration vs reskin decision rule for B10.
3. [ ] Add §5 schema rows (M keys, loader line, in-repo example) and §1.3 collision rows for `vehicle_part`, `vehicle_placement`, `nested_mapgen`, `terrain` and `furniture`.
4. [ ] Fix the §5 mandatory markings: profession `items` optional, scenario `start_name` and `allowed_locs` mandatory, and `ITEM` copy-from must restate `subtypes` (also in §8.3).
5. [ ] Fix the `conflicts` claim (`src/worldfactory.cpp:195-203`) and the conflict-id template (`backrooms`, plus the other TCs).
6. [ ] C1: gate `add_or_replace` behind the opt-in key (dda has 5 duplicate entries), and state the load-time cost.
7. [ ] Scope the whitelist claim (region-random extras only; mission/trailhead/forced specials bypass it) and add the mission-target leak to §9.
8. [ ] Correct the §3.1 method: the `ammotype` regex hole, the non-zero inline literals, and the missing `vgroup_id`/`map_extra_id`/`profession_id`/`faction_id` rows.
9. [ ] Extend R9 with `src/game_io.cpp:452-453` and `src/scenario.cpp:124,137-157`, and state "never set SEASON_LENGTH in the mod".
10. [ ] Tooling: add the `polib` prerequisite, and warn that `-r` is appended to.
11. [ ] Replace the verifiable-but-UNVERIFIED items (calendar year, dda duplicate check, mod ids) with verified statements. Mark "gets this wrong" and "dominant fixed cost" as UNVERIFIED.
12. [ ] Fix F3 (`UPS` citation) and state the UB precondition in C4/R6.
