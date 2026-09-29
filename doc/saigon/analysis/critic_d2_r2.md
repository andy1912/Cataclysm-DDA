# Critic verdict: D2 r2 (Mapgen & Worldgen)

- Critic: A2.4 (adversarial Codebase & Systems Critic), rubric `doc/saigon/analysis/CRITIC_RUBRIC.md`, N=2, k=2
- Audited: `doc/saigon/analysis/d2_r2.md` (1,078 lines), plus a check that every r1 item in `critic_d2_r1.md` (D1–D16, F1–F13) is actually fixed
- Repo: `/Users/ducpa/code/cdda-saigon`, HEAD `b23233c298`. The commits after `fe6a10c2b1` touch only `doc/saigon/`, so every citation was checked against base-SHA code.

## Verdict

**REJECT**

- Defects: 0 BLOCKER, **1 MAJOR**, 9 MINOR.
- Citation failure rate: 3 / 580 = **0.5 %**, well under the 2 % limit.

The rejection comes from one design error in the new rooftop network (D1). The report says that where rows of different rotation meet, a parapet cap closes the roof walk and no plank link is built. The code cannot do that.

- A `PREFIX` neighbour match ignores rotation (`src/overmap_terrain.cpp:310-331`).
- `mapgendata` rotates only the neighbour *position*, not the neighbour id (`src/mapgendata.cpp:80-84`).

As a result, perpendicular rows leave the walk uncapped over open air, and the report's own start district generates two planks that the report says will not exist.

Everything else is a MINOR fix. The r1 rework is otherwise real and mostly correct.

## Summary

### Were the r1 items actually fixed?

| r1 item | Status | Evidence in r2 |
|---|---|---|
| D1 (MAJOR) bike slots wreck the shop front | **FIXED, with new slips** | The design and the destroy/smash documentation are correct. Bikes are curb-parallel on row 0, and rows 1–2 are never reached, which matches `src/mapgen.cpp:7065-7085`. The count is ≤ 6 per OMT, and a test was added. New problems: the motorcycle is 4 tiles long, not 3 (D2), the claim that status 0 is flaky is wrong (D3), and the test loop accumulates vehicles across seeds (D4). |
| D2 (MAJOR) rooftops don't connect | **PARTLY FIXED** | Added: shared z3 walk, stair and ladder steps, `t_concrete_roof`/`t_thconc_floor` `roof` and INDOORS semantics (all correct against the JSON), a plank link, and a BFS test. The corner and rotation-mismatch handling is wrong (D1 below). The tank provides no water (D9). |
| F1–F5 bare shorthand | FIXED | A scripted check finds 0 bare `:NNN` tokens. |
| F6 desert range | FIXED | The file has 630 lines, and the citation is now `:598-630`. |
| F7/D6 MA cities | FIXED | `json.load` counts 351. |
| F8/D8 B1 "silent" | FIXED | The report now says a debugmsg fires. ("Silently" at l. 82 refers to B4, which really is silent.) |
| F9/D7 side-street spacing | FIXED | `block_width + 1`. |
| F10/D10 B7 | FIXED | Now described as dead code. `src/mapgen.cpp:383`, `:410`, `src/map.cpp:9384-9392` confirm it. |
| F11 `generate_sub` reads | FIXED | Three reads, `src/overmap.cpp:1080-1083`. |
| F12/F13/D4 pregen z | FIXED | The phrase "z = 0 only" is gone everywhere except the changelog. |
| D3 hẻm connectivity and rotation | FIXED | The ports at 11–12 are invariant under rotation. One `omt` parameter drives the `switch` (syntax matches `src/mapgen.cpp:1535-1571`, `:1648-1657`). A single closed arm cannot disconnect a quadrant. The PREFIX-on-rows port rule inherits D1's rotation blindness (see D1). |
| D5 pregen loader bugs | FIXED | Three bugs are listed and confirmed at `src/savegame.cpp:924-936`. |
| D9 per-column overhead | FIXED | §6.2 matches `src/mapgen.cpp:187-283`. |
| D11 river branches | FIXED | `src/overmap_water.cpp:55-57`, `:212-213`, `:555`. |
| D12 unverified magnitudes | FIXED | Every §6 figure is tagged UNVERIFIED and tied to B1–B3. B3 as written cannot compile (D5). |
| D13 `do_vehicle_caching` | FIXED | `src/map.cpp:10819-10821`. |
| D14 canal water model | FIXED | `t_water_murky` is SHALLOW_WATER, SWIMMABLE and FISHABLE, and has no `DEEP_WATER` (`terrain-liquids.json:79-86`). Boats and floods are explicitly deferred. |
| D15 golden snapshot | FIXED | Nit: `closest_points_first( origin, 0, 1 )` returns a **3×3** cluster (9 overmaps), not the 2×2 that the test comment and r2's changelog say. |
| D16 hẻm RNG scope | FIXED | §5.2 narrowed. |

### New designs I tried to break

| Claim | Result | Evidence |
|---|---|---|
| Curb-parallel slot at `rotation: 0` occupies (m−1..m+1, 0) | TRUE for `scooter` and `bicycle`, **FALSE for `motorcycle`** | The checker places part x along the facing ray (`src/mapgen.cpp:2778-2783`). `scooter_abstract` `o>o` and `bicycle_abstract` `o#o` span x ∈ {−1, 0, 1}, but `motorcycle_abstract` `o#>o` spans x ∈ {−1, 0, 1, **2**} (`data/json/vehicles/bikes.json`). See D2. |
| Row-2 shutter is never reached | TRUE | All parts are on y = 0. The impassable branch is `src/mapgen.cpp:7065-7085`. Vehicles (phase `default_`) are placed before nested props (phase `nested_mapgen`) (`src/mapgen.h:89-99`). |
| `manual_mapgen` / `manual_nested_mapgen` / `prep` exist | TRUE | `tests/mapgen_helpers.h:11-24`, `tests/mapgen_helpers.cpp:17-41`. `clear_map_without_vision` is at `src/map_helpers.h:17`. `clear_avatar` is at `tests/player_helpers.h:20`. `rng_set_engine_seed` and `smallmap::generate` follow `tests/mapgen_post_process_test.cpp:175-179`. `--mods` is at `tests/test_main.cpp:368-370`. `vehicle_part::damage` is at `src/vehicle.h:473`. `veh_spawn_status::PRISTINE` is at `src/enums.h:77-83`. |
| `status: 0` makes the damage assertion flaky | **FALSE** | UNDAMAGED sets full HP and never enters the branch that applies `destroyEngine` (`src/vehicle.cpp:386-388`, `:517-547`). See D3. |
| `t_concrete_roof`: move_cost 2, FLAT, ROAD, no INDOORS | TRUE | `data/json/furniture_and_terrain/terrain-roofs.json:286-294` |
| `t_thconc_floor`: INDOORS + `"roof": "t_concrete_roof"` | TRUE | `terrain-floors-indoor.json:4-11` |
| `t_bridge`: "walkway", move_cost 2, FLAT | TRUE | `terrain-bridges-docks.json:4-11`. It also has `SWIM_UNDER`, connect group `WATER`, and no bash entry, so it cannot be bashed. |
| `t_railing` is passable | TRUE | move_cost 3, `THIN_OBSTACLE`, `CLIMBABLE` |
| Outside cache comes from INDOORS; `roof` key is used by `get_roof`/bash/construction | TRUE | `src/map.cpp:10549-10551`, `src/mapdata.cpp:1382`, `src/map.cpp:4442-4462`, `:4760`, `src/construction.cpp:2218-2223` |
| Plank halves meet under a 180° rotation | TRUE for real back-to-back rows | x ↦ 23 − x maps {11, 12} onto {12, 11}, and together the halves span the 8-tile rear hẻm. |
| "Where rotations differ, the parapet cap applies and no link is built" | **FALSE** | See D1. |
| Hẻm spine is rotation-symmetric; at most one arm is closed | TRUE | The logic holds. The load-time `switch` completeness check is at `src/mapgen.cpp:1566-1571`. |
| `neighbors` accepts an `om_terrain` + `om_terrain_match_type` list with OR semantics | TRUE | `src/mapgen.cpp:3569-3620`. `PREFIX` requires a `_` boundary (`src/overmap_terrain.cpp:310-331`). |
| Canal: `t_water_murky`, z0 only, causeway | TRUE as a design | Note that the 6–8-tile murky strip is wadeable (move_cost 5). It is not a barrier, so the causeway is cosmetic in pass 1. Acceptable because the report calls it a simplification. |
| Lot chunk 24×24 placed at x = 20 | OK *if* it writes only columns 0–3 | The load-time nest OOB check in `jmapgen_nested::check` (`src/mapgen.cpp:3880-3928`) computes the maximum from `all_placement_coords`. The report states the columns 0–3 constraint. |
| Benchmarks B1–B3 are implementable as tests | **PARTLY FALSE** | `map::build_sunlight_cache` is `protected` (`src/map.h:2044`, `:2069`) and `map::calc_max_populated_zlev` is `private` (`src/map.h:2177-2182`). See D5. |
| Setting canon | Mostly consistent | The report satisfies canon on 3–5 floors, iron gates, parked motorbikes, connected rooftops (except at corners, D1), 1–3-tile hẻm, and murky water that is unsafe until boiled. Two gaps remain: "Rooftop tanks provide water" is not met (D9), and the "small boats" part of the canal row is not placed even as static props (missed topic 5). |

## Citation verification table

**Method.**

1. A script (Python) extracted every `(src|tests|data|doc)/…:(N[-M])(,N[-M])*` token and expanded comma lists. The proposed `tests/saigon_*` files were excluded.
2. It checked that each file exists and each line range is in bounds.
3. A row was flagged when none of the backticked identifiers on the same report line appears within ±5 of the cited range.
4. I printed and reviewed by hand all 159 flagged rows, plus every citation in the new §4.a.2, §4.b, §4.f, §6.3, §6.4 and §8 text.
5. Separately, I grepped every backticked identifier across `src`, `tests`, `data` and `doc/JSON`. The only misses are proposed names (`closed_arm`, `place_canals`, `sg_*`), file stems and the SHA.

| Metric | Count |
|---|---|
| `path:line` citations checked | 580 (the report's own §10 counts 577; the difference is in how comma lists are tokenized) |
| File missing | 0 |
| Line out of range | 0 |
| Flagged by the proximity heuristic, then reviewed by hand | 159, of which 156 are OK |
| **FAIL** (claim contradicts the cited code) | **3 (0.5 %)** |
| Backticked existing symbols not found | 0 |

**FAIL rows**

| # | Report line | Citation | Problem |
|---|---|---|---|
| F1 | 1052 | `src/mapgendata.cpp:80-84` as the basis for the mitigation "Parapet caps (no drops)" | The cited code rotates only the neighbour position; the neighbour id keeps its absolute suffix. A `PREFIX` match (`src/overmap_terrain.cpp:310-331`) therefore cannot detect a rotation mismatch, so the cap is not placed there. Same false claim, uncited, at l. 540 and l. 988–989. |
| F2 | 742 | `src/vehicle.cpp:423` "With `status: 0`, `destroyEngine` can still roll … so the assertion would be flaky" | `destroyEngine` is rolled, but under UNDAMAGED the damage branch that applies it is skipped (`src/vehicle.cpp:386-388`, `:517-521` versus `:538-547`). The assertion is not flaky with status 0. |
| F3 | 905 | `src/lightmap.cpp:366` `build_sunlight_cache` and `calc_max_populated_zlev()` as things "timed/recorded" from `tests/saigon_perf_test.cpp` | Both are non-public (`src/map.h:2044-2069` protected; `src/map.h:2177-2182` private), so the test as specified will not compile. |

## Defects

### MAJOR

**D1: The rooftop network's corner and rotation guarantee is false. PREFIX neighbour matching is rotation-blind (R2).**

*Claims:*
- §4.a.2 item 5 (l. 540): "Where neighbouring rows have different rotations, the parapet cap applies and no link is built."
- §7.2 (l. 988–989): the (2,0)/(2,1) corner "is a parapet dead-end", and "no cross-hẻm plank is generated inside this special."
- Risks (l. 1052): "Parapet caps (no drops)."

*Code:*
- The cap (item 3) and the plank (item 4) are both conditioned on `{ "om_terrain": "sg_nhaong_row", "om_terrain_match_type": "PREFIX" }`.
- `is_ot_prefix` compares the id string up to a `_` boundary (`src/overmap_terrain.cpp:310-331`), so `sg_nhaong_row_z3_east` matches exactly like `sg_nhaong_row_z3_north`.
- `mapgendata` rotates only the lookup position, `overmap_buffer.ter( over + displace( dir ).rotate( rotation ) )`, and never the neighbour id (`src/mapgendata.cpp:80-84`). Joins are rotated (`:116-119`), but neighbours are not.
- A single rotatable mapgen therefore cannot tell "same rotation as me" apart from "perpendicular".

*Consequences:*
1. **Walk-off drops.** For §7.2 cell (2,1) `SH→`, the local west neighbour is (2,0) `SH↑`. It matches PREFIX, so no cap is placed.
   - (2,1)'s walk (local rows 16–19, local x = 0) sits at global (4..7, 0) of that OMT.
   - That abuts (2,0)'s global row 23, which is the rear strip and open air at z3.
   - The same happens at (4,1)/(4,0), and at every block corner in the procedural city.
2. **Planks the report says do not exist.** (2,0) and (4,0) have SH south neighbours ((2,1) `SH→` and (4,1) `SH←`), so each places `sg_roof_plank_s`. The other half is never built. The plank ends against the perpendicular row's side, which is a setback-room wall or an uncapped deck.
3. **Hẻm ports.** The hẻm port rule (§4.b) has the same blind spot. A row that is side-on to a hẻm opens a port into its party wall, not its rear strip.
4. **The test cannot catch any of this.** `saigon_rooftop_walkability` uses 3 same-street rows, 3 back-to-back rows and a *road* negative case. It has no perpendicular-row configuration.

*Fix* (any one of these makes the claim true):
- (a) Make row continuity **type-based, not rotation-based**. Ship rows as multi-OMT `city_building`s (1×2 or 1×3 along +x, plus an optional back-to-back 2×N) whose cells have distinct oter *types* per role, so a `TYPE`/`PREFIX` match implies a known relative rotation. Place caps **unconditionally** at the building's outer ends.
- (b) Inside `sg_district_q1_start`, give each rotation role its own oter type (for example `sg_nhaong_row_face_n`, `_face_e`) and match on those.
- (c) Downgrade the claim: say that the walk and plank are guaranteed only within one building footprint, and that corners may drop.

In every case:
- Correct l. 540, §7.2 l. 985–989 and Risks l. 1052.
- Fix the hẻm port rule to open only toward a row's rear.
- Add a walkability test case with a perpendicular corner (an L of `_north` and `_east` rows) that asserts no walk tile borders `t_open_air` at z3 without a wall or railing in between.

### MINOR

**D2: The motorcycle breaks the 3-tile slot invariant, and the suggested remedy goes out of bounds (R2).**

- `motorcycle` (15 % of `sg_parked_twowheelers`) is `o#>o` with parts at x = −1..2 (`data/json/vehicles/bikes.json`, `motorcycle_abstract`). At mount (m, 0) with rotation 0 it covers m−1..m+2, which is exactly the gap-prop tile (3, 0), (7, 0), and so on.
- Vehicles are placed in phase `default_`, before the nested props (phase `nested_mapgen`, `src/mapgen.h:89-99`). The prop furniture is therefore written under the bike's fourth part. It is not smashed, but it is an obstacle under a vehicle.
- The report's validation ("check with the load-time OOB checker") cannot detect this: the maximum x is 21 + 2 = 23, which is in bounds.
- The remedy "use rotation 180" is wrong. At mount (1, 0), the part at x = +2 maps to 1 − 2 = −1, which is out of bounds, and `src/mapgen.cpp:2792-2825` will debugmsg.
- *Fix:* do one of the following:
  - drop `motorcycle` from the group;
  - give 4-long vehicles dedicated slots whose following gap tile has no prop;
  - mount them at (m, 0) with rotation 0 only where m + 2 is not a prop tile.
  - In addition, the parking test's PRISTINE variant must include every prototype in the real group, and must assert that no furniture lies under any vehicle part.

**D3: The "status 0 is flaky" rationale is wrong (R2).** See F2. Under `UNDAMAGED`, parts get full HP and `destroyEngine` is never applied (`src/vehicle.cpp:517-547`). `PRISTINE` is harmless but unnecessary. *Fix:* correct the text. The only real non-determinism source is the world option `OVERRIDE_VEHICLE_INIT_STATE` (`src/vehicle.cpp:357-362`); the test should pin it.

**D4: The test specifications contradict the design (R5).**

- **(a) Rooftop test.** The BFS goes from (0, 17) to (71, 17). With non-row outer neighbours, both of those tiles are the parapet cap (`t_concrete_wall`, move_cost 0), as the report's own negative case 4 asserts for x = 71. The positive assertion can never pass. Use (1, 17) → (70, 17).
- **(b) Hẻm test.** It does a BFS "over passable z0 tiles" to reach `t_door_c`, but `t_door_c` has move_cost 0 (`terrain-doors.json`). Doors must be traversed through the `DOOR`/`OPENCLOSE` flag, or reached by adjacency.
- **(c) Parking test.** It runs 200 seeds on one OMT without clearing between them. Bikes from earlier seeds will merge with new ones (`src/mapgen.cpp:6966-7060`), and `get_vehicles().size() <= 6` fails. Clear the vehicles and re-run `prep` per seed.

**D5: Benchmark B3 calls non-public members (R5).** See F3. *Fix:* do one of the following:
- add a test-only accessor or friend declaration, which is a C++ seam and must be listed as one;
- time `map::build_map_cache( z, false )` as a whole (it is public, `src/map.h:1833`, and includes lighting);
- read `max_populated_zlev` through a new public getter.

Also fix "2×2 cluster" in the D15 changelog. The cluster is 3×3.

**D6: Nest-cost accounting misses the recursive `has_vehicle_collision` pre-pass (R3 coverage).**

- Every `apply_mapgen_in_phases` call, which includes every `nest()`, begins with `objects.has_vehicle_collision( md, offset )` whether or not `verify` is set (`src/mapgen.cpp:6259`).
- That pass recurses through *every selected entry list* of every `place_nested` (`src/mapgen.cpp:3941-3961`). It evaluates each entry's param or switch, and runs `veh_at` for each object (`src/mapgen.cpp:1883-1893`, `:6436-6452`).
- With lot → sub-chunk nesting, each subtree is walked once per ancestor.
- §6.2 also undercounts z0 nests: `sg_frontage_row` adds up to 6 prop nests (about 4 non-null), not "~2".
- The figures are already UNVERIFIED, so this is MINOR. *Fix:* add the pre-pass to §6.2 and have B2 report nests per column.

**D7: The §7.2 main row does not actually face a road (R2).**

- The `SH↑` cells at y = 0 are drawn as facing a "main road (connection at [3,-1])".
- A fixed-special connection only builds a road *starting* at (3, −1) toward the city target (`src/overmap_special_fixed.cpp:305-319`).
- The cells (0..2, −1) and (4..5, −1) keep whatever terrain they had. Five shop fronts and their frontage bikes will usually face fields.
- *Fix:* do one of the following:
  - put a street row inside the special (make it 6×7, with `sg_street_*` at y = 0);
  - give the y = −1 cells `"locations": [ "road" ]`-style constraints and accept the lower placement rate.

**D8: The §7.2 hẻm layout is inconsistent with §4.b (R2 minor).**

- "HEM exit S" at (1, 2) faces `KENH`, which is not in the port `neighbors` list, so that port is capped.
- The hẻm cells reach the streets only through nhà ống rear strips. Whether a rear strip is open at its OMT ends is not specified.
- *Fix:* add `sg_kenh` to the port rule, or relabel the cell. Specify that rear strips are open at x = 0 and x = 23. Add a district-level BFS from every HEM cell to an ST cell.

**D9: Canon "Rooftop tanks provide water" is not met (R6-lite, `doc/saigon/CONTENT_BIBLE.md:29`).**

- `f_standing_tank` is a keg-style `LIQUIDCONT` (`furniture-storage.json:1316-1326`), and it is placed empty. No `place_liquids` is specified and no rain collection is designed.
- It appears only on h4 and h5 lots (3 : 1 against the altar), never on h3 lots.
- *Fix:* specify `place_liquids` with water, a fill-level range, and presence on every lot type (or state the rate). Alternatively, use a rain-collecting furniture and cite its flag.

**D10: Lot geometry is underspecified, and one tile contradicts the roof rule (R5 minor).**

- The stair column at lot-local (3, 14) is on the divider column x = 3 that the roof walk uses for `t_railing`.
- Party-wall placement between 4-tile lots is never defined (is x = 3 a wall?).
- The h3 deck's `t_stairs_down` carries `INDOORS` (`terrain-zlevel-transitions.json`). That contradicts "roof decks must not carry INDOORS", though it is harmless as a single sheltered tile.
- *Fix:* define the lot template (the wall columns, the interior width, and a stair column that is not in a wall), and note the stair-tile exception.

## Missed topics (spot-check)

1. **Rotation-blind neighbour ids** (`src/mapgendata.cpp:80-84` versus joins at `:116-119`; `src/overmap_terrain.cpp:292-331`). This underlies D1 and the hẻm port rule.
2. **Per-nest `has_vehicle_collision` pre-pass** (`src/mapgen.cpp:6259`, `:3941-3961`). See D6.
3. **The motorcycle footprint** was readable in `bikes.json` and was left UNVERIFIED instead of checked. See D2.
4. **Riot-damage scope** (checked, and no defect): `generic_city_building_roof` deletes `riot_damage` (`data/json/overmap/overmap_terrain/overmap_terrain.json:55-60`). Only the z0 oter is post-processed, so the z3 walk is not bashed at generation. It would still help to state this, because z0 `bash_damage` (intensity ≤ 60, `data/json/post_process_generators.json:7`) can hit shutters and parked bikes.
5. **Canon "small boats"** (`CONTENT_BIBLE.md:32`) can be met in pass 1 as static vehicles. `add_vehicle_to_map` rejects only `DEEP_WATER` for non-floaters (`src/mapgen.cpp:6953`), so a xuồng can sit on `t_water_murky`. Boat *routes* are rightly deferred, but boat presence is not.

## Required changes for next revision

1. [ ] **D1 (MAJOR):** Make roof-walk continuity and plank links rotation-correct: use type or role-based matching through multi-OMT row buildings or per-role oter types, with unconditional caps at building ends. Otherwise, explicitly downgrade the guarantee. Correct §4.a.2 item 5, §7.2 (l. 985–989) and Risks l. 1052. Apply the same fix to the hẻm port rule, so ports open only toward a row's rear. Add a perpendicular-corner case to `saigon_rooftop_walkability`.
2. [ ] **D2:** Resolve the 4-tile `motorcycle` (drop it, or give it dedicated prop-free slots). Remove the "rotation 180" remedy. The parking test must cover every prototype in the group and assert that no furniture lies under a vehicle part.
3. [ ] **D3:** Correct the status-0 rationale. Pin `OVERRIDE_VEHICLE_INIT_STATE` in the test.
4. [ ] **D4:** Fix the test specs: rooftop BFS endpoints (1, 17) → (70, 17); hẻm BFS traverses doors; the parking test clears vehicles and re-preps per seed.
5. [ ] **D5:** Make B3 implementable: time public `build_map_cache( z, false )`, or list a test accessor as an explicit C++ seam. Change "2×2 cluster" to 3×3.
6. [ ] **D6:** Add the recursive `has_vehicle_collision` pre-pass and the frontage prop nests to §6.2. Have B2 report nests per column.
7. [ ] **D7:** Give the §7.2 main row a guaranteed street, either inside the special or through location constraints.
8. [ ] **D8:** Make "HEM exit S" consistent with the port rule. Specify that rear strips are open at the OMT ends. Add a district-level HEM → ST reachability check.
9. [ ] **D9:** Fill rooftop tanks with water (`place_liquids`) or use a rain-collecting fixture. State the rate per lot type.
10. [ ] **D10:** Define the lot template (walls, stair column off the divider), and note the `t_stairs_down` INDOORS exception on h3 decks.
