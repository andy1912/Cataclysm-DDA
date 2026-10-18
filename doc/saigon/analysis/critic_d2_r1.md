# Critic verdict: D2 r1 (Mapgen & Worldgen)

- Critic: A2.2 (adversarial Codebase & Systems Critic), rubric `doc/saigon/analysis/CRITIC_RUBRIC.md`, N=2, k=1
- Audited: `doc/saigon/analysis/d2_r1.md` (762 lines)
- Repo: `/Users/ducpa/code/cdda-saigon`, HEAD `73388627e9`. `git diff fe6a10c2b1 HEAD -- src data/json` is empty, so every citation was checked against base-SHA code.

## Verdict

**REJECT**

There are 0 BLOCKER, 2 MAJOR and 14 MINOR defects. The citation failure rate is 13 / 403 = 3.2 %, which is above the 2 % threshold. With the 5 ambiguous-shorthand rows excluded it is still 8 / 403 = 2.0 %, which is not under 2 %.

This is a strong report and it is close to passing. Every high-impact claim I tried to falsify held up against the code (see Summary). The rejection comes from two design errors in the pass-1 designs that Part B will copy directly, plus a set of small factual slips that together push the citation failure rate over the limit.

## Summary

### High-impact claims I tried to falsify (all CONFIRMED unless noted)

| Claim | Result | Evidence |
|---|---|---|
| Whole-column 21-z generation in one `map::generate` call | CONFIRMED | `src/mapgen.cpp:187-211` canvas over all z; `:226` loop `OVERMAP_HEIGHT → -OVERMAP_DEPTH`; `src/map.cpp:9294-9310` `loadn` generates the column if any of the 21 z × 4 submaps is missing. The report's "Only uniform levels are free" overstates it. See D9. |
| Overmap generation is synchronous, main thread, lazy | CONFIRMED | No `std::thread`/`std::async`/pool in `src/overmap*.cpp`, `src/mapgen*.cpp`, `src/map.cpp`, `src/lightmap.cpp`. `overmapbuffer::get` constructs and `populate()`s inline (`src/overmapbuffer.cpp:100-121`). `overmapbuffer::ter` → `get_om_global` → `get` (`:889-893`, `:384-391`). |
| 4 arms from the centre | CONFIRMED | `src/overmap_city.cpp:228-230` (`do … while( turn_right != start_dir )`). |
| Side-street spacing | PARTLY WRONG | The condition at `:413` is `c < croad - block_width`, so side streets come every **block_width + 1** OMT (3, or 4–6), and blocks are 2 or 3–5 OMT deep. §2.2's "side street every block_width" and §0's "side streets every 2 or 3–5 OMT" are off by one; §2.2's "blocks 2 or 3–5 OMT deep" is right. See D7. |
| B1: `city_spacing` check writes `city_size` | CONFIRMED | `src/regional_settings.cpp:809` `city_size = std::clamp( city_spacing, 0, 8 );`. It is not silent, though: a `debugmsg` fires at `:807-808`. See D8. |
| B2: predefined cities picked twice | CONFIRMED | `src/overmap_city.cpp:204` `random_entry( cities_to_place )` never removes an entry, and the loop at `:166` runs `num_cities_on_this_overmap_count` times. This hits MA hard (351 `city` objects, not 56, see D6). |
| B3: infinite pick loop | CONFIRMED | `src/overmap_city.cpp:268-277`: `do { pick } while( existing_unique \|\| !city_size.contains( town_size ) )` has no exit. |
| B4: partial `connections` nulls the other ids | CONFIRMED | `region_settings_overmap_connection::was_loaded` is declared `false` (`src/regional_settings.h:341`) and never set. `deserialize` passes it to `optional` (`src/regional_settings.cpp:465-472`), which resets unread members when `!was_loaded` (`src/generic_factory.h:958-960`). |
| River veto in `lay_out_street` | CONFIRMED | `src/overmap_city.cpp:318-319` (`is_river() … return false`), with the TODO at `:317`. |
| `OVERMAP_PREGENERATED_PATH` is z = 0 only | WRONG AS WORDED | `src/savegame.cpp:894-903` reads only the **first** object, but it honours that object's `"z"` (`jo.read( "z", z )`, used at `layer[z + OVERMAP_DEPTH]`). The accurate statement is "one z-level per file, selected by `z`". §3.2 says this correctly; §0, §7.1 and Risks say "z = 0 only". See D4. |
| Overlapping vehicles merge into wrecks | CONFIRMED but INCOMPLETE | `src/map.h:1857` `merge_wrecks = true`; `src/mapgen.cpp:6966-7060` merge; 200-part cap at `:6971-6975`. The report missed the **impassable-terrain branch** (`:7065-7078`): `destroy( p, true )` removes the wall, then the vehicle is smashed. That is exactly what breaks its own parking design (D1). |
| Every placed nested chunk rescans the full level | CONFIRMED | `nest()` → `apply_mapgen_in_phases` (`src/mapgen.cpp:6380-6392`) → `resolve_regional_terrain_and_furniture( md, offset.z() )` at `:6289` → `points_on_zlevel` over the whole smallmap with 2 flag tests per tile (`src/mapgen_functions.cpp:2238-2259`). |
| Sunlight cache starts at max populated z + 1 | CONFIRMED | `src/lightmap.cpp:371-372`; `calc_max_populated_zlev` returns the highest non-uniform submap level in the bubble (`src/map.cpp:11914-11947`). The quoted *cost* ignores the `fully_outside` fast-fill (`src/lightmap.cpp:408-413`) and the fact that vanilla already has multi-storey city buildings. The magnitude is unverified but presented as fact (D12). |
| `rebuild_vehicle_level_caches()` per spawned vehicle | CONFIRMED | `src/mapgen.cpp:6917` → `src/map.cpp:596-609` (all 21 z). |
| `omt_stack` parameters keep lot heights consistent | CONFIRMED | `src/mapgen.cpp:1848-1858`; stored in `omt_stack_arguments_map` (`src/overmap.cpp:759-787`) and serialized (`src/savegame.cpp:483-486`). Desert precedent `data/mods/desert_region/mapgen/earth.json:295-331` matches the proposed pattern exactly. |

### Is the pass-1 district structural or a reskin? (R4)

It is structural, not a reskin.

- **nhà ống:** 6 independent 4-tile parcels per OMT, with per-parcel vertical height carried by `omt_stack` parameters. This changes the parcel grain and the vertical structure.
- **hẻm:** a Wang-tile port labyrinth plus mutable-special `joins` changes circulation topology.
- **chợ:** a 2D `om_terrain` stall grid.

These are real changes to generation structure.

- The canal is the weakest part. In pass 1 it is a dead-ended 6-OMT set-piece strip. PLAN B8 scopes it as a "canal (kênh) segment", so this is acceptable, but see D14.
- The nhà ống height randomisation conflicts with the setting canon (D2).

### Do the JSON skeletons use keys that exist in the loaders?

Yes. I verified every key:

- `city_building` / `overmap_special`: `subtype`, `locations`, `overmaps.point/overmap`, `city_sizes` (and `[2,-1]` → `max = INT_MAX` through `src/common_types.h:39-50`), `occurrences`, `city_distance`, `priority`, `flags`, `rotate`, `connections.point/terrain/connection/from`. Loaders: `src/overmap_special.cpp:150-158`, `:170-177`, `:286-352`.
- mapgen: `fill_ter`, `palettes`, `place_nested.chunks/else_chunks/neighbors/joins/flags/flags_any/check_z` (`src/mapgen.cpp:3792-3804`), `{ "param", "fallback" }` chunks, `nested_mapgen_id`, square `mapgensize` (`:4554-4561`).
- parameters: `type`/`scope`/`default.distribution` (`:1760-1765`).
- neighbours: `om_terrain_match_type: PREFIX` (`src/enums.h:149-157`).
- `start_location.terrain` (`src/start_location.cpp:137`).
- `region_settings` keys (`src/regional_settings.cpp:610-642`) and `region_settings_city` keys (`:572-585`).

I also confirmed that multi-z special entries at z ≠ 0 pass placement on default terrain (`src/overmap.cpp:3029-3031`).

The only names that do not exist are the proposed new ids, which are correctly presented as new.

## Citation verification table

**Method.**

1. A script extracted every `path:line[-line][,line…]` token.
2. It resolved bare `` `:NNN` `` shorthand to the most recent path on the same or a preceding line (the report's own convention).
3. It checked file existence and line range.
4. It printed the cited lines, and flagged a row when none of the backticked symbols on that report line appeared within ±5 lines.
5. Every flagged row, and every high-impact row, was then checked by hand.
6. Separately, all 317 unique backticked identifiers were grepped across `src`, `data`, `tests` and `doc/JSON`. The only misses are the proposed new names (`sg_*`, `saigon_*`, `build_city_organic`, `density_rings`, `region_settings_canal`, and so on).

| Metric | Count |
|---|---|
| `path:line` citations checked | 403 (261 explicit, 142 shorthand) across 54 files |
| OK | 390 |
| FAIL | 13 (3.2 %) |
| — of which ambiguous shorthand (resolves to the wrong file under the report's own convention) | 5 |
| — of which the file or line is out of range | 1 |
| — of which the claim contradicts the cited code | 7 |
| Backticked existing symbols not found | 0 |

**FAIL rows**

| # | Report line | Citation (as resolved) | Problem |
|---|---|---|---|
| F1 | 266 | `src/regional_settings.h:801-805` (bare `:801-805` after `.h:52-103`) | The header has 585 lines. The intended target is `src/regional_settings.cpp:801-805`. Ambiguous shorthand. |
| F2 | 368 | `doc/JSON/MAPGEN.md:1648-1657` (bare after `MAPGEN.md:1197-1247`) | These are blank doc lines. The intended target is `src/mapgen.cpp:1648-1657` (`init_object`). Ambiguous shorthand. |
| F3 | 539 | `src/simple_pathfinding.h:2559` (bare after `simple_pathfinding.h:76`) | The file has 141 lines. The intended target is `src/overmap.cpp:2559`. Ambiguous shorthand. |
| F4 | 539 | `src/simple_pathfinding.h:2658-2729` | Same problem as F3; the intended target is `src/overmap.cpp`. |
| F5 | 539 | `src/simple_pathfinding.h:2719` | Same problem as F3; the intended target is `src/overmap.cpp`. |
| F6 | 329 | `data/mods/desert_region/.../desert_regional_map_settings.json:598-632` | The file has 630 lines, so the range runs past EOF (content matches at 598-630). |
| F7 | 336 | `data/mods/MA/cities.json` "56 `city` objects" | The file holds **351** `city` objects (`json.load` count). |
| F8 | 286 / 750 | `src/regional_settings.cpp:806-810` "silently" | `debugmsg( … city_spacing(%d) is outside the bounds … )` at `:807`. It is not silent. |
| F9 | 212 (§2.2 code comment) | `src/overmap_city.cpp:413` "side street every block_width" | The code gives every `block_width + 1` (see the Summary table). |
| F10 | 292 | `src/mapgen.cpp:383-389` (B7 "loops over 2×2 tiles") | The loop never runs. After the z loop, `set_abs_sub` last set `abs_sub.z() = -OVERMAP_DEPTH` (`:227-228`, `src/map.cpp:10928-10932`), so `if( abs_sub.z() >= 0 )` at `:383` is false. `loadn` does the real per-tile phase change (`src/map.cpp:9386-9392`). |
| F11 | 571 | `src/overmap.cpp:1077-1116` "two `ter_unsafe` reads each" | There are three: `oter_id_here`, `oter_above`, `oter_ground` (`:1080-1083`). |
| F12 | 664 | `src/savegame.cpp:894-903` "z = 0 only" | The code reads `"z"` from the object. See D5. |
| F13 | 760 | `src/savegame.cpp:894-903` "Pregen maps are z0-only" | Same problem as F12. |

## Defects

### MAJOR

**D1: The motorbike-slot design wrecks the shop front it is parked against (R2 + R3).**

- *Claim* (§4.f, l. 518): "Use fixed, non-overlapping slots: one bike every 2 tiles along the frontage strip, perpendicular to the curb." In §4.a the frontage strip is rows 0–1 and the house starts at row 2, with a shutter across the front.
- *Code:*
  - `scooter` is 3 tiles long: parts at x = −1, 0, +1 (`data/json/vehicles/bikes.json:213-220`; `"blueprint": [ "o>o" ]` at `:227`).
  - Placed perpendicular in a 2-row strip, it overlaps either row 2 or row −1.
  - Row 2 is the closed shutter, which is impassable. There, `add_vehicle_to_map` runs `destroy( p, true )` and then `veh_to_add->smash()` (`src/mapgen.cpp:7065-7085`). The shop front is demolished and the bike becomes a wreck.
  - Row −1 is outside the 24×24 smallmap, so the placement is rejected or raises the out-of-bounds debugmsg (`:7002-7010`).
- It is also internally inconsistent. One bike every 2 tiles gives 12 real vehicles per OMT, while §4.f/§6.3 budget at most ~6–10.
- *Fix:*
  - Specify the slots as parallel to the curb (3 tiles along row 0 or 1), or make the strip ≥ 3 rows.
  - Document the impassable-collision branch next to the merge-wreck trap.
  - Reconcile the slot count with the ≤ 10 per OMT budget. For example: 4–6 real bikes plus prop furniture for the rest.
  - Validation: a `manual_mapgen` test (`tests/mapgen_helpers.h:18`) asserting that after generation the shop-front row still has its terrain and every spawned bike has no `smash` damage.

**D2: The nhà ống per-lot random heights break the canon rooftop-movement mechanic, and roofs are not designed (R6 / R4).**

- *Canon* (`doc/saigon/CONTENT_BIBLE.md:29`): "Rooftops connect for movement. Rooftop tanks provide water."
- *Claim* (§4.a): the six lots in a row each draw an independent height (h3/h4/h5) from `omt_stack` parameters, and h3 lots "place nothing at z = 4..5".
- Adjacent roofs therefore sit at different z with sheer drops. Nothing in the report provides roof-to-roof traversal:
  - no shared parapet or roof-deck level;
  - no ladders or stairs between terrace heights;
  - no roof terrain or the `roof` key on floor terrain (`src/mapdata.cpp:1382`) that upper floors need so rain and sunlight treat them as indoors.
- Across OMT borders (row to row, over a hẻm) nothing is considered either.
- The report calls the height variation its main "structural" gain, but it is what defeats the district's defining mechanic.
- *Fix:*
  - Define a rooftop-connectivity rule. For example: every row has a common "base roof" level (z = 3) that all lots reach, and taller lots add setback floors with a ladder or stair down to the shared roof. Or constrain adjacent lots through a shared `omt`/`omt_stack` parameter so height differences are ≤ 1 and each step has a ladder chunk.
  - Specify roof and floor terrain ids with `roof`.
  - Say how roofs connect across a narrow hẻm (plank or bridge chunk at the shared height, conditioned on `neighbors`).
  - Validation: a mapgen test doing a BFS over walkable tiles at z ≥ 3 across a row of 6 lots, plus a 2-OMT row pair.

### MINOR

**D3: The Wang-tile hẻm does not guarantee connectivity or rotation consistency (R5).**

- §4.b picks four quadrants independently, and each has its own open or closed internal ports. Two adjacent quadrants can disagree (A open east, B closed west). A quadrant can end up with no open path to any OMT-edge port, which leaves plots unreachable.
- Neighbours are rotated into the local frame (`src/mapgendata.cpp:80-84`). Port coordinates must therefore be rotation-symmetric, or hẻm oters must be non-rotatable. The report says neither.
- *Fix:*
  - Drive each internal port with one `omt`-scoped parameter read by both quadrant chunks (`switch` chunks), and require at least one open port per quadrant.
  - Centre the edge ports (x = 11–12) or set `rotate: false`.
  - Validation: a BFS test over 100 seeds.

**D4: The `OVERMAP_PREGENERATED_PATH` limitation is misstated (R2).** See F12 and F13. Replace "z = 0 only" with "one z-level per file, chosen by the object's `z`; only the first array element is read". This also sharpens P2.8.

**D5: The pregen loader has bugs the report missed (spot-check).**

- In `src/savegame.cpp:924-927`, obsolete-id migrations are keyed at `tripoint_om_omt( p, j, z - OVERMAP_DEPTH )` (that is, z = −10 for a z0 file), while the terrain is written to `layer[z + OVERMAP_DEPTH]`.
- In the same branch `tmp_otid` is not updated, so the tile takes the previous run's terrain.
- `p < i + count` can run past `OMAPX` when a run wraps a row.
- These matter if the Option C OSM tool ever emits an obsolete id. *Fix:* add a Risks row and a P2.0 item.

**D6: Wrong MA city count (R2).** 351, not 56 (F7). *Fix:* correct it, and note that B2 affects MA directly.

**D7: Side-street spacing is off by one (R2).** See F9. *Fix:* correct §0 and §2.2 to "a side street every `block_width + 1` OMT".

**D8: B1 is not "silent" (R2).** See F8. *Fix:* "emits a debugmsg at load, then corrupts `city_size`; `city_spacing` itself is left unclamped".

**D9: "Only uniform levels are free" is overstated (R3 accuracy).**

- For every level, uniform or not, `map::generate` still does the following (`src/mapgen.cpp:248-253`, `:283-379`, `:392-406`):
  - allocates and saves 4 submaps;
  - runs the 7×7 `overmap_buffer.ter` density loop (49 lookups × 21 = 1,029 per column);
  - evaluates the map-extras collection, static spawns and post-process dispatch.
- *Fix:* state the fixed per-column overhead, and include it in the §6.4 `saigon_mapgen_cost` baseline.

**D10: B7 is mischaracterised (R2).** See F10. The block is dead code, not a 2×2 loop. *Fix:* restate it as "dead (`abs_sub.z()` is −10 after the z loop); harmless because `loadn` applies phase change per tile".

**D11: The river minimum-width claim ignores branches (R2).**

- `river_scale = 1 + max(1, river_scale)` (`src/overmap_water.cpp:555`) applies only to major rivers.
- Branches use `river_scale - river_branch_scale_decrease` (`:212-213`) and can be radius 1, about 3 OMT (72 m).
- The conclusion (no 10–30 m canals from the river generator) still holds. *Fix:* correct the numbers.

**D12: Unverified magnitudes are presented as fact (R7).**

- Examples:
  - "~450 vehicles … This is the #1 density risk" (l. 619);
  - "raises the ray-cast start to z = 6 for everything … budget (6 − player_z) extra levels × 132²" (l. 617);
  - "That is cheap" (l. 599, nest scans).
- None is marked UNVERIFIED, and the sunlight claim ignores the fast-fill path and vanilla's existing tall buildings.
- *Fix:* tag these UNVERIFIED and attach the §6.4 benchmark to each, with the vanilla downtown as the comparison.

**D13: Per-turn vehicle cache cost is missed (R3 coverage).**

- `map::build_map_cache` calls `do_vehicle_caching( z )` for every z, every time it runs. This walks every part of every vehicle (`src/map.cpp:10784-10800`, `:10820-10822`) and is not gated by a dirty flag.
- With dense parked bikes this is a second per-turn cost on top of `vehmove`. *Fix:* add it to §6.3 and to the "≤ 150 vehicles in bubble" rationale.

**D14: The canal design does not state its canon gaps or its water model (R4-lite / R5).**

- Canon (`CONTENT_BIBLE.md:32`) calls for "Boat routes … Wet-season floods".
- The pass-1 kênh is a 6-OMT strip that dead-ends at the special's edges, with no connection to the river. The report does not say which water terrain is used (deep or shallow, `DEEP_WATER`, whether boats can float) or whether a boat can use it.
- The bridge description "street deck at z0, water under deck" is ambiguous: vanilla bridges put the deck at z1 (`src/overmap.cpp:1146-1195`).
- PLAN B8 accepts a "segment", so this is MINOR.
- *Fix:*
  - Name the terrain ids and depth.
  - State that boat routes and flooding are out of pass 1 and map them to P2.3 or domain A3.
  - Optionally, place the district with a `river`-adjacent location so the kênh meets the river.

**D15: P2.1's validation cannot prove "bit-for-bit" (R5).**

- `overmap_generation_is_deterministic` (`tests/overmap_test.cpp:1043-1109`) compares runs of the *same* binary. It cannot detect drift between the pre-change and post-change `"grid"` paths.
- *Fix:* add a golden-snapshot test that hashes z0 across the 2×2 cluster for a fixed seed, recorded on the base SHA and asserted after P2.1.

**D16: The pass-2 hẻm RNG statement is self-contradictory (R2 minor).**

- §5.2 says the C++ hẻm mapgen "must not consume the global stream, so that visiting order does not change results". But §5.1 has it call JSON nested chunks, and all JSON mapgen draws from the global RNG.
- Only the maze and the edge-port hash need the local engine.
- *Fix:* narrow the claim to "the port and maze decisions use a local engine seeded by `hash(world_seed, omt)`; interior dressing may use the global RNG".

Also noted, not counted: the ambiguous shorthand in F1–F5. The convention "bare `:NNN` = the last-named file" breaks when a line names two files. Always repeat the path when it changes.

## Missed topics (spot-check)

1. **Vehicle vs. impassable-terrain collision at mapgen** (`src/mapgen.cpp:7065-7085`). See D1.
2. **`do_vehicle_caching` per turn** (`src/map.cpp:10784`, called from `build_map_cache` `:10820-10822`). See D13.
3. **Pregen loader bugs** (`src/savegame.cpp:924-927`). See D5.
4. **Rooftop and roof terrain** (the `roof` key, `src/mapdata.cpp:1382`) for multi-z nhà ống. See D2.
5. The fixed per-column overhead of uniform levels in `map::generate`. See D9.

## Required changes for next revision

1. [ ] **D1:** Redesign motorbike slots: parallel to the curb or a ≥ 3-row strip. Document the `destroy()` + `smash()` impassable branch (`src/mapgen.cpp:7065-7085`). Reconcile the slot count with the ≤ 10 real vehicles per OMT budget. Add a `manual_mapgen` test that the shop front survives and bikes are unsmashed.
2. [ ] **D2:** Add a rooftop-connectivity design for nhà ống rows that satisfies `CONTENT_BIBLE.md:29`: a shared base-roof level or bounded height steps with ladder chunks, a cross-hẻm roof link, and roof/floor terrain with `roof`. Add a BFS walkability test at z ≥ 3.
3. [ ] Fix every FAIL row F1–F13. Repeat the file path whenever it changes (no bare `:NNN` after a line that names two files). Correct MA to 351 cities, the side-street spacing to `block_width + 1`, B1 to "debugmsg, not silent", `generate_sub` to 3 reads, and pregen to "one z-level per file, chosen by `z`".
4. [ ] **D10:** Restate B7 as dead code (the `abs_sub.z()` = −10 reasoning).
5. [ ] **D3:** Make hẻm internal ports parameter-shared, and make edge ports rotation-symmetric or `rotate: false`. Add a connectivity test.
6. [ ] **D5:** Add the `unserialize_omap` migration-z and RLE-overflow bugs to §2.5, Risks and P2.0/P2.8.
7. [ ] **D9, D13:** Extend §6 with the fixed per-column overhead (uniform levels, 1,029 `ter` lookups) and the per-turn `do_vehicle_caching` cost.
8. [ ] **D11:** Correct the river-width minimum to account for branches.
9. [ ] **D12:** Mark the vehicle-count, sunlight and nest-scan magnitudes UNVERIFIED, each tied to a §6.4 benchmark against a vanilla downtown baseline.
10. [ ] **D14:** Name the kênh water terrain ids and depth, and state explicitly that boat routes and flooding are deferred to P2.3 or A3.
11. [ ] **D15:** Add a cross-build golden-snapshot test for P2.1 "grid" bit-identity.
12. [ ] **D16:** Narrow the hẻm RNG determinism claim to port and maze decisions.
