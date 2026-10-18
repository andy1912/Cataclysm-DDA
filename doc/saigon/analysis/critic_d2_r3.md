# Critic verdict: D2 r3 (Mapgen & Worldgen), final round

- Critic: A2.4 (adversarial Codebase & Systems Critic), rubric `doc/saigon/analysis/CRITIC_RUBRIC.md`, N=2, k=3.
- Audited: `doc/saigon/analysis/d2_r3.md` (1,250 lines), in full. I also checked every r2 defect (D1–D10 in `critic_d2_r2.md`) against the r3 text and the code, and judged the residual-risk table RR1–RR9 (§9b).
- Repo: `/Users/ducpa/code/cdda-saigon`, HEAD `5307ba312d`. `git diff --stat fe6a10c2b1 -- src tests data/json` shows only `src/game.cpp` and `src/main.cpp` changed (the C6 test-mode fix). Every other citation was checked against base-SHA code.
- Empirical probe: I ran `tools/saigon/check_mod.sh` against a throw-away probe mod. The mod and its userdir lived in my scratchpad (`SAIGON_USERDIR`), so nothing was written into the repo. Results are in §"Empirical probe".

## Verdict

**PASS**

- Defects: 0 BLOCKER, 0 MAJOR, **9 MINOR**.
- Citation failure rate: **0 / 633 = 0.0 %**.

**r2's MAJOR (D1) is really fixed.**
- Roof-walk continuity now comes from role oter types inside one multi-OMT `city_building`, not from a neighbour test.
- The cross-building guarantee is honestly downgraded, and a concrete C++ seam (C1) is proposed to restore it.
- The hẻm port rule no longer relies on rotation-blind row matching.

All ten r2 defects were addressed in substance. The remaining MINOR findings are:
- design-geometry slips in the new lot and z3 template: stairs, cap ordering, the last lot, party walls and tank fill;
- test-specification gaps;
- one canon conflict created by the D2 fix;
- a stale sentence.

None of them invalidates a headline guarantee *and* evades the report's own tests. This is the final round, so every open MINOR goes to the TDD risk register (see the last section).

## Summary

### Were the r2 defects actually fixed?

| r2 item | Status | Evidence |
|---|---|---|
| **D1 (MAJOR)** rotation-blind PREFIX caps, planks and ports | **FIXED** | **Relative rotation is fixed by construction.** Role types `sg_nh_{solo,endw,mid,ende,pairf,pairb}` sit inside multi-OMT `city_building`s. Special placement rotates both the points (`src/overmap.cpp:3012` → `om_direction::rotate`, `src/overmap.cpp:2815-2832`) and each oter (`src/overmap_special_fixed.cpp:269`), so the relative rotation of cells inside one building is fixed at authoring time.<br>**Caps and planks.** Caps are unconditional per role, and planks exist only inside `pair_1x2`.<br>**Honest downgrade.** Cross-building links are downgraded (§4.a.2 item 5, RR1). §7.2, the Risks row (l. 1200) and l. 540 are corrected.<br>**Hẻm ports** no longer list rows (l. 619-621).<br>**Test.** A perpendicular-corner test case is added (l. 585-588).<br>**New slips in the implementation of R-ROOF:** D2, D3, D6a below. |
| D2 motorcycle 4 tiles | **FIXED** | The group is now `scooter` 80 / `bicycle` 20. Both are x ∈ [−1, 1] (`data/json/vehicles/bikes.json:3-12`, `:193-203`), and the child prototypes add no parts outside that range (`:13-21`, `:212-221`).<br>The "rotation 180" remedy is withdrawn, and the probe confirms the OOB debugmsg.<br>The static footprint test over `all_possible_results` is implementable: `VehicleGroup::all_possible_results()` is public (`src/vehicle_group.h:45`), and so is `vehicle_prototype::part_def::pos` (`src/veh_type.h:525-526`).<br>Side effect: a canon conflict (D8). |
| D3 status-0 rationale | **FIXED** | `status: 0` = `UNDAMAGED` (`src/enums.h:77-83`). Full HP is set (`src/vehicle.cpp:517-519`), and `destroyEngine` is only in the `else` branch (`src/vehicle.cpp:520-547`). The option pin is at `src/vehicle.cpp:358`, and `override_option` is at `tests/options_helpers.h:10-16`. |
| D4 test specs | **FIXED, one new gap each** | (a) The endpoints (1, 17) → (70, 17) are correct under the lot template. (b) Doors are traversed via `ter.open` (`src/mapdata.cpp:1378`), but windows also define `open` (D6b). (c) `clear_vehicles()` and `clear_map_without_vision()` are re-run per seed (`src/map_helpers.h:17`, `:21`). |
| D5 B3 not compilable | **FIXED** | Every named member is public:<br>- the dirty setters `src/map.h:482-496` (public section from `src/map.h:455`);<br>- `vehmove` `src/map.h:889` (public from `:859`);<br>- `build_map_cache` `src/map.h:1833` (public from `:1800`);<br>- `mapbuffer::lookup_submap` `src/mapbuffer.h:62` (public `:20`);<br>- `submap::is_uniform` `src/submap.h:293` (public `:76`);<br>- `maptile_soa` is a struct (`src/submap.h:62`).<br>The setters also dirty the lightmap (`set_lightmap_cache_dirty_below`, `src/map.cpp:391-447`), so `generate_lightmap` (gated on `lightmap_dirty`, `src/lightmap.cpp:503-508`) really re-runs `build_sunlight_cache` (`src/lightmap.cpp:546`) inside the timed call. The replacement computation of the max populated z mirrors `calc_max_populated_zlev` (`src/map.cpp:11914-11947`). "3×3" is corrected at l. 56 and l. 1177. |
| D6 nest pre-pass | **FIXED** | §6.2 l. 920-925 matches `src/mapgen.cpp:6259` (runs regardless of `verify`), the recursion at `src/mapgen.cpp:3941-3961`, which evaluates conditions via `get_entries` (`src/mapgen.cpp:3834-3842`), and the RNG draws at `src/mapgen.cpp:6444-6447`. The arithmetic of the nest estimate checks out (12–18 × 1,152 ≈ 14–21k per level). |
| D7 main row faces no road | **FIXED** | 6×7 special with an internal ST row at y = 0. Every SH cell's arrow points at an owned ST cell. I checked this for all 11 SH cells, including the `_east`/`_west` endw/ende placement under `om_direction::rotate`. |
| D8 hẻm exits and rear strips | **FIXED** | HEM (0–1, 2–3) exits south via KENH, HEM (5, 2–3) exits via KENH, and HEM (0–1, 6) exits via STILT (PREFIX `sg_kenh` matches `sg_kenh_stilt_*` at the `_` boundary, `src/overmap_terrain.cpp:310-331`). Rear strips are open at x = 0 and x = 23. A district BFS test is added, though it is not implementable as literally written (D6c). |
| D9 tanks empty | **FIXED in mechanism, numbers wrong** | The `liquids` palette mapping on `f_standing_tank` loads cleanly (probe). The liquid is added after the furniture: `liquids` pieces run in the `default_` phase, after `furniture` (`src/mapgen.h:89-99`). `add_item_or_charges` accepts liquids on `NOITEM` + `LIQUIDCONT` tiles (`src/map.cpp:5887-5960`). But the stated fill level is false (D5). |
| D10 lot geometry | **FIXED as asked, new slips** | Stair off the divider: yes. Party wall at lx = 0: yes. h3 `t_stairs_down` INDOORS noted: yes (`data/json/furniture_and_terrain/terrain-zlevel-transitions.json:118-128`). But the stair column spec puts up and down stairs on the same tile (D1), and the template collides with the end cap in the last lot (D3). |

### Designs I tried to break (the caller's list)

| Design | Result | Evidence |
|---|---|---|
| Fixed-role 1–3-OMT rows with capped ends | **Sound in principle.** Three implementation slips: cap **ordering** (D2), last-lot collisions (D3), and placement asymmetry in the city grower (D7). | Stable phase sort, then declaration order: `src/mapgen.cpp:4968`, `:6403-6432`. `place_building` and the local +x direction: `src/overmap_city.cpp:281-303`, `src/overmap.cpp:2815-2832`. |
| Back-to-back pair | **Sound.** The 180° authoring makes x ↦ 23 − x map {11, 12} onto itself. RR3 (back frontage facing field in 3–5-deep blocks) is honest. | `data/json/overmap/multitile_city_buildings.json:5201-5215` is the precedent for multi-cell footprints. |
| C1 rotation-aware neighbour check, "~20 lines" | **Feasible.** About 20–35 lines of core C++, plus doc and unit test.<br>The allowed-neighbour set is `std::unordered_map<direction, cata::flat_set<std::pair<std::string, ot_match_type>>>` (`src/mapgen.cpp:3572`). A struct with `operator<`, one optional int in the parser (`:3579-3587`) and one extra conjunct in `test` (`:3614-3616`) suffice. `mapgendata::terrain_type()` (`src/mapgendata.h:186`), `neighbor_at` (`src/mapgendata.h:244-245`) and `oter_t::get_rotation` (`src/overmap_terrain.cpp:851-863`) all exist. It reads state only, so there is no save or determinism impact.<br>The probe confirms that today's loader **rejects** `relative_rotation` ("Invalid or misplaced field name"), so C1 is genuinely required and pass-1 JSON must not use the key before it lands.<br>Unspecified semantics: see D9. | `src/mapgen.cpp:3569-3621`, `src/mapgendata.cpp:80-84` |
| Hẻm port rule (alleys, roads, canals) | **Sound.**<br>`road` TYPE matches vanilla road oters. `sg_kenh` PREFIX covers `ew`, `causeway` and `stilt`.<br>Rotation argument for canals: a KENH cell met side-on presents its embankment, and met end-on presents wadeable `t_water_murky` (move_cost 5).<br>The C1 derivation `relative_rotation = d` is correct. I re-derived it: rotation r maps local direction d → d + r (`src/overmap.cpp:2824-2829`), and a row's rear faces r_row + 2.<br>Nit: the district's `sg_street_*` is not in the list. That is harmless in §7.2, where no HEM touches an ST cell, but it matters for future districts. | `src/mapgen.cpp:3604-3621`; `data/json/furniture_and_terrain/terrain-liquids.json:79-86` |
| Parking group without motorcycle; footprint test | **Sound.** Probe: scooter and bicycle at x = 1 and x = 21 with rotation 0 raise no OOB. The static test catches future 4-tile prototypes. **Canon conflict:** D8. | `src/mapgen.cpp:2772-2825` |
| Rooftop BFS (1, 17) → (70, 17) | **Correct.** Both are walk tiles (lot 0 lx = 1, and A2 lot 5 lx = 2) next to the caps at x = 0 and x = 71. Row 17 is continuous, because the lx = 0 dividers are open on rows 17–18 and h3 tanks sit on row 18. | §4.a.1 lot template |
| Doors-openable traversal | **Partly.** `ter.open` is also defined for windows (e.g. `t_window_domestic` → `t_window_open`, `t_window_no_curtains`). There are 52 non-DOOR terrains with `open`, so the BFS can "reach" a plot through a window (D6b). | `src/mapdata.cpp:1378`; `data/json/furniture_and_terrain/*.json` |
| B3 public API only | **Correct.** See D5 in the table above. |  |
| Recursive vehicle-collision pre-pass | **Correct and adequately costed.** It honours `check_z`, because `correct_z_level` is part of `get_entries`. | `src/mapgen.cpp:3834-3842`, `:3941-3961`, `:6436-6452` |
| 6×7 district with street row | **Correct topology.**<br>I checked all 42 cells, the roof groups R1–R5 and their cap placement under `_east`/`_west`, HEM → ST routes and counts (42 cells, 476 submaps, ≤ 71 vehicles).<br>`land` excludes roads (`data/json/overmap/special_locations.json`), so the special cannot overwrite city streets.<br>The district BFS test cannot run in one bubble (D6c). |  |
| Tank filling | **Mechanism OK. Stated fill level false** (D5). |  |
| Stair geometry | **Self-contradictory** (D1). |  |
| Party walls | **Underspecified at z ≥ 3 for mixed heights** (D4). |  |
| Canon (`doc/saigon/CONTENT_BIBLE.md`) | **Mostly met:** 3–5 floors, shop gates on row 2, parked two-wheelers, hẻm 1–3 wide, murky canal with stilt houses and static boats, tanks with water, and rooftop connection within buildings plus via C1.<br>**Gaps:** "110cc underbones everywhere … a few 50cc scooters" (`CONTENT_BIBLE.md:9`) versus a scooter-dominated group (D8). The spawn and performance density budget that `CONTENT_BIBLE.md:119` explicitly asks of A2/A3 is absent (missed topic 1). | `doc/saigon/CONTENT_BIBLE.md:9`, `:11`, `:29-32`, `:77-78`, `:119` |

### Empirical probe (scratch mod, `tools/saigon/check_mod.sh`, userdir outside the repo)

| Probe | Result |
|---|---|
| `vehicle_group` scooter 80 / bicycle 20; `place_vehicles` at (1, 0) and (21, 0), rotation 0, status 0 | No error. |
| `motorcycle` at (21, 0), rotation 0 | No OOB (max x = 23). This confirms r2's point that the checker cannot see prop overlap. |
| `motorcycle` at (1, 0), rotation 180 | `src/mapgen.cpp:2820` debugmsg "extends too far west, reaching coordinate x = -1". This confirms r3's withdrawal reason. |
| Palette `liquids` `{ "O": { "liquid": "water", "amount": [40, 200] } }` on `f_standing_tank` in a nested chunk | Loads cleanly. |
| `neighbors` entry with `"relative_rotation": 0` | JSON error "Invalid or misplaced field name "relative_rotation"" (`src/flexbuffer_json.cpp:332` via `jmapgen_nested::jmapgen_nested`). C1 is required C++. |

## Citation verification table

**Method.**

1. A Python script extracted every `(src|tests|data|doc)/…:N[-M][,N[-M]]` token from `d2_r3.md` and expanded comma lists. It excluded the proposed `tests/saigon_*` files.
2. It checked existence and line bounds.
3. It flagged a citation when none of the backticked identifiers on the same report line occurs within ±5 lines of the cited range.
4. I printed the first cited lines of **all 168 flagged citations** and reviewed them by hand.
5. Separately, I opened by hand all **46 citation strings that are new in r3** (diff of the citation sets of r2 and r3).
6. I grepped the backticked identifiers across `src`, `tests`, `data` and `doc`.

| Metric | Count |
|---|---|
| `path:line` citations checked | 633 (the report's §10 says 630; the difference is tokenization) |
| File missing | 0 |
| Line out of range | 0 |
| Flagged by the proximity heuristic, then reviewed by hand | 168 (my heuristic is stricter than the analyst's 119). 168 OK. |
| New in r3, opened by hand | 46 unique strings. 46 OK. |
| **FAIL** (claim contradicts the cited code) | **0 (0.0 %)** |
| Backticked vanilla identifiers not found | 0 (see note) |

**FAIL rows:** none.

Notes that are not failures:
- l. 802 names `vgroup_id::all_possible_results`. The member is `VehicleGroup::all_possible_results()` (`src/vehicle_group.h:45`), reached as `vg_id->all_possible_results()` exactly as at `src/mapgen.cpp:2775`. This is a naming nit.
- l. 1221 (RR5) and l. 573 call the per-charge volume of water UNVERIFIED. It is readable in the data (`data/json/items/comestibles/drink.json`, `water_clean` "250 ml", "charges": 1, inherited by `water`). See D5.

## Defects

All are MINOR. Each lists the rule, the claim, the evidence and the required fix.

**D1: The stair column puts `t_stairs_up` and `t_stairs_down` on the same tile on every intermediate floor (R2, design contradiction).**
- *Claim* (§4.a.1 lot template, l. 462): "`t_stairs_up` at (2, 13) on z0..z(top−1); `t_stairs_down` at (2, 13) on z1..z(top)."
- *Evidence:*
  - On z1..z(top−1) one tile must carry both terrains, which is impossible. Only single-tile hybrids such as `t_ladder_up_down` have both `GOES_UP` and `GOES_DOWN` (`data/json/furniture_and_terrain/terrain-zlevel-transitions.json`).
  - Whichever write comes last wins, so either nothing on z1..z(top−1) leads down, or nothing leads up.
  - When the tile directly above or below is not a matching stair, `game::find_stairs` falls back to the **nearest** matching stair anywhere in the same 24×24 OMT (`src/game.cpp:9956-9996`). With 6 lots per OMT, a broken or missing stair can silently land the player in a *neighbouring lot*, through the party wall.
- Test case 4 (3D BFS) would catch the contradiction, so it cannot ship unnoticed. It is still wrong as specified.
- *Fix:* per floor, place `t_stairs_up` at (2, 13) and `t_stairs_down` at (1, 13). Omit the down tile on z0 and the up tile on the top floor. This relies on the in-OMT nearest-stair fallback resolving within 1 tile, which beats the 4-tile distance to the next lot. Alternatively, alternate the column per floor. Test case 4 must also assert that each vertical move lands in the **same lot** (lot index = x / 4).

**D2: The "unconditional" end caps can be overwritten by the lot nests; the application order is unspecified (R5).**
- *Claim* (l. 546-551): the z3 mapgen of each role "places `t_concrete_wall` … on rows 16–19", so "no walk tile can ever border a building's outside without a wall".
- *Evidence:*
  - Lot 0's chunk writes lx = 0 on rows 16–19 (railing on rows 16 and 19, walk on 17–18), and lot 5's chunk writes lx = 3. Those are exactly the cap tiles at x = 0 and x = 23.
  - Mapgen pieces run in phase order `terrain < furniture < default_ < nested_mapgen` (`src/mapgen.h:89-99`), then in declaration order within a phase (a stable sort, `src/mapgen.cpp:4968`; applied at `:6403-6432`).
  - A cap authored the natural way (in `rows`/`terrain` or `place_terrain`) is therefore **overwritten** by the lot nests. Only a cap that is itself a `place_nested` entry declared *after* the six lot entries survives.
- *Fix:* state that caps are nested chunks declared after the lot placements. Alternatively, make the lot chunks leave lx = 0 of lot 0 and lx = 3 of lot 5 as `" "` no-ops in end roles; that needs role-specific lot chunks. Add to test case 3 an explicit assertion that (0, 16..19) and (23, 16..19) are `t_concrete_wall` in end roles.

**D3: The last lot collides with the end cap at x = 23 (R2).**
- *Claim* (l. 464): the ende/solo/pair cap "supplies the outer wall at x = 23 on rows 2–19, which leaves that lot 2 interior tiles wide".
- *Evidence:* the six lots share one set of lot chunks. There is no mechanism to make lot 5 two tiles wide. Lot 5's lx = 3 is x = 23, and three things land on the cap column:
  - the shutter spans lx = 1..3 on row 2 (l. 465), so it reaches (23, 2);
  - the h3 tank is at (3, 18) (l. 571), so it lands at (23, 18), on the cap;
  - the h4/h5 tank at (3, 3) lands at (23, 3).
- Depending on the write order (D2), the result is either furniture or liquid on a wall tile, or a hole in the outer wall.
- *Fix:* move the per-lot fixtures that are not walls to lx ≤ 2 (tank at (2, 18) or (1, 18); the shutter can stay at lx = 1..3 only if the cap starts at row 3). Alternatively, give end roles a dedicated lot-5 chunk.

**D4: Party-wall ownership above z2 is undefined for mixed lot heights (R5).**
- *Claim* (l. 460): at z3, lx = 0 is "setback wall, or deck edge `t_railing` on h3". Each lot chunk writes only its own columns.
- *Evidence:*
  - Lot k's lx = 0 is also lot k−1's east wall. If lot k is h3 (railing at lx = 0) and lot k−1 is h4/h5, lot k−1's `t_thconc_floor` (INDOORS) setback room gets a **railing** as its east wall.
  - At z4 (h5 room) the east wall is written by nobody.
  - The `omt_stack` params are independent per lot (l. 492-500), so no chunk knows its neighbour's height.
  - The same gap leaves the h4/h5 upper deck edges over an h3 neighbour unspecified. A walk-off there is warned by the vanilla "ledge" prompt (`src/game.cpp:7557-7562`), so it is not a silent fall. It is still outside every stated guarantee.
- *Fix:* at every level where a lot has a setback room, the lot writes its **own** east wall at lx = 3 (room interior lx = 1..2), and lx = 0 stays the west wall. Alternatively, choose lot heights with a single `omt_stack` parameter per cell (height-banded roles, already the "cost option" at l. 592), which removes mixed heights inside a cell.

**D5: The rooftop tank fill level is asserted, and it is false (R2/R7).**
- *Claim* (l. 573, RR5 l. 1221): `amount` [40, 200] charges; "Tanks start 10–60 % full"; the volume per charge is UNVERIFIED.
- *Evidence:*
  - `water` copies from `water_clean`, which is "volume": "250 ml", "charges": 1 (`data/json/items/comestibles/drink.json`).
  - `jmapgen_liquid_item` sets `charges = amount.get()` (`src/mapgen.cpp:2364-2368`).
  - 40–200 charges = 10–50 L of the 300 L `keg_capacity` (`data/json/furniture_and_terrain/furniture-storage.json:1327`), which is **3.3–16.7 %**.
- *Fix:* use `amount` [120, 720] for 10–60 % (30–180 L). Remove the UNVERIFIED tag and cite the item.

**D6: Test-specification gaps (R5).**
- **(a) Test case 3's invariant is unsatisfiable as written.**
  - "For every walkable z3 tile, each orthogonal neighbour must be walkable or be `t_concrete_wall`/`t_railing`/`t_bridge`."
  - `t_railing` is itself walkable (move_cost 3, `data/json/furniture_and_terrain/terrain-fences-gates.json:1184-1191`), and the row-19 railing borders open air at row 20. Case 1's BFS also counts it as walkable (move_cost > 0).
  - The h3 deck's front edge (row 2, bordering open air at row 1) has no specified treatment.
  - *Fix:* define "walk surface" = {`t_concrete_roof`, `t_bridge`, stair tiles}. Treat `t_railing`/`t_concrete_wall` as edges. Specify an h3 front parapet or railing at row 2.
- **(b) Doors-openable BFS also opens windows.** 52 terrains that are not `DOOR` define `open`. *Fix:* traverse `open` only when the terrain has the `DOOR` flag and the `open` target is passable.
- **(c) The district BFS cannot run in the bubble.**
  - 6×7 OMT is 144×168 tiles, but the bubble is `MAPSIZE` 11 submaps, 132×132 (`src/map_scale_constants.h:11`).
  - *Fix:* run the BFS over `MAPBUFFER.lookup_submap( tripoint_abs_sm )` + `submap::get_ter` across all cells of the special, or run it per 4×4-OMT window with overlap.

**D7: Stale performance claim, and unanalysed placement effects of multi-OMT rows (R2/R3-lite).**
- *Claim* (l. 883): "Saigon's 1×1 row buildings do not add placement work beyond vanilla's". RR1 (l. 1217): "weight `sg_nhaong_row_3` highest so most frontage is inside 3-OMT walks".
- *Evidence:*
  - r3's rows are 1×1, 1×2, 1×3 and 2×1.
  - `place_building` rotates by `opposite(dir)` (`src/overmap_city.cpp:284-285`). With `om_direction::rotate` (`src/overmap.cpp:2815-2832`), local +x runs **backward** along the street for left-side buildings and **forward** for right-side ones.
  - **Left side:** a 1×3 row fits only if the two previous left frontage cells are still free (each is built with 75 % probability). Left frontage therefore gets mostly `row_1`/pair after up to 10 retries (`src/overmap_city.cpp:289-303`). The "most frontage in 3-OMT walks" mitigation holds for roughly half the frontage at best.
  - **Right side:** rows claim future frontage. They can **suppress right-hand side streets**, because side streets are laid out when the grower reaches their step (`src/overmap_city.cpp:413-430`), after earlier buildings. `lay_out_street` stops on non-road terrain, and "Don't bother" applies at ≤ 1 node (`src/overmap_city.cpp:396-398`).
  - Vanilla `strip_mall` (5 OMT, shops weight 750, `data/json/region_settings/region_settings/regional_map_settings.json:824`) has the same effect, so it is not new *in kind*. Making row_3 the dominant pick makes it systematic.
- *Fix:* correct l. 883. Have B1 also report the fraction of SH cells with a road on local north, the side-street count per city against vanilla, and the per-side distribution of row lengths. Restate the RR1 sub-mitigation as UNVERIFIED.

**D8: Canon conflict created by the D2 fix: the frontage is scooter-dominated, not underbone-dominated (R4-lite/canon).**
- *Evidence:*
  - `CONTENT_BIBLE.md:9` says "110cc underbones, Chinese copies, and a few 50cc scooters".
  - `CONTENT_BIBLE.md:77` bases the underbone on the **existing motorcycle prototype**, which is 4 tiles (`data/json/vehicles/bikes.json:63-76`).
  - `sg_parked_twowheelers` is scooter 80 / bicycle 20. The r3 footprint test would reject a motorcycle-derived underbone.
- *Fix:* state a cross-domain constraint for B6 and A3: the Saigon underbone prototype must be authored with parts x ∈ [−1, 1], y = 0 (3 tiles, like `scooter_abstract`), and then dominate `sg_parked_twowheelers`. Until then, the scooter weight is a placeholder.

**D9: C1 semantics are incomplete, and the ID clashes with d4 (R5-lite).**
- *Evidence:*
  - `oter_t::get_rotation` returns 0 for non-rotatable oters and a line-derived value for linear ones (`src/overmap_terrain.cpp:851-863`). So `relative_rotation: 0` also matches any non-rotatable neighbour, and road neighbours get a meaningless value.
  - Self-rotation under `IGNORE_ROTATION_FOR_ADJACENCY` (`src/mapgendata.cpp:80-81`) is not specified.
  - Above and below directions are not specified either.
  - `doc/saigon/PROGRESS.md:85` already renames this seam **M-C1**, because d4 uses C1 for something else.
- *Fix:* specify that the predicate is evaluated only when the neighbour `is_rotatable()` and not linear (otherwise false), that self-rotation is taken raw, that it is horizontal directions only, and that the seam ID is M-C1. Count the doc (`doc/JSON/MAPGEN.md`) and unit test in the size estimate.

## Residual risks RR1–RR9: final-round judgement

| RR | Judgement | Reason |
|---|---|---|
| RR1 cross-building roofs | **Acceptable** (honest downgrade and a concrete seam) | The probe confirms that C1/M-C1 is required and the only route. The sub-mitigation "weight row_3 highest" is overstated (D7). |
| RR2 district roof groups not joined | **Acceptable** | Guarded against drops by the district test. It depends on D2 and D6a being fixed. |
| RR3 pair back cell faces field | **Acceptable** | It follows from `src/overmap_special.cpp:316-318`, and B1 measures it. |
| RR4 collapse next to the plank | **Acceptable** | `t_bridge` has no `bash`. The support counting at `src/map.cpp:4172-4185` is honestly UNVERIFIED, with a test step and a fallback. |
| RR5 tanks | **Not acceptable as written** | It asserts "10–60 % full", which is false with the specified amounts (D5). After the D5 fix it is acceptable, and rain refill belongs to A3. |
| RR6 boats, floods, bridges | **Acceptable** | Deferred with owners. Static canoes are placed away from both collision branches. |
| RR7 performance unverified | **Acceptable** | Budgets and benchmarks exist, and B3 is now implementable. |
| RR8 pre-pass RNG | **Acceptable, accurate** | `src/mapgen.cpp:6444-6447` |
| RR9 mutable special as `city_building` | **Acceptable** | Not used by the design. |

**Missing from §9b**, and to be added in the TDD:
- D1 (stairs);
- D2/D3/D4 (z3 template integrity);
- D8 (the underbone footprint constraint);
- the zombie-density budget (missed topic 1).

## Missed topics (spot-check)

1. **Monster spawn density and its per-turn budget.**
   - `CONTENT_BIBLE.md:119` says "much higher human-zombie density per OMT than in dda cities. This needs a spawn and performance budget from A2/A3."
   - d2_r3 has no design for any of these: `place_monsters`/`mondensity` on the Saigon oters, `place_mongroups` (only listed at l. 176), static spawns (`src/mapgen.cpp:283-379`), or a monster count per bubble next to the ≤ 150-vehicle budget.
   - Monster movement is a `do_turn` hot path. Either A2 or A3 must own this. It is not in the A2 brief (`doc/saigon/PLAN.md:42`), so it is not an R6 defect, but it must be registered.
2. **Iron accordion gates (cửa sắt kéo).** Canon's "loud, slow entries" (`CONTENT_BIBLE.md:11`, `:29`) is reduced to a stand-in `t_door_metal_c` in the test. No terrain is chosen (lock, bash and pry semantics). This belongs to B8b, and it should be noted.
3. **Upper-deck edges.** The z4/z5 decks of h4/h5 lots over h3 neighbours are outside every guarantee. The vanilla "ledge" warning (`src/game.cpp:7557-7562`) mitigates this (D4).

## Required changes (no further round; for the TDD author and Part B)

1. [ ] D1: replace the single stair column with a per-floor up/down pair, and assert same-lot landing in test case 4.
2. [ ] D2: specify caps as nested chunks declared after the six lot placements, and assert the cap tiles in test case 3.
3. [ ] D3: move lot fixtures off lx = 3, or add an end-role lot-5 chunk.
4. [ ] D4: each setback storey writes its own east wall (interior lx = 1..2), or use height-banded roles.
5. [ ] D5: `amount` [120, 720]; cite `water_clean` 250 ml; correct RR5.
6. [ ] D6: redefine the walk surface in test case 3 and specify the h3 front edge; door traversal only for the `DOOR` flag; run the district BFS over MAPBUFFER submaps.
7. [ ] D7: correct l. 883, extend B1 metrics, and mark the RR1 weighting as UNVERIFIED.
8. [ ] D8: record the B6 constraint that the underbone must be 3 tiles (x ∈ [−1, 1]) to join `sg_parked_twowheelers`.
9. [ ] D9: complete the M-C1 semantics (rotatable, non-linear, horizontal only) and rename it to M-C1.
10. [ ] Missed 1: assign ownership (A2 or A3) of the zombie-density spawn and per-turn budget.

## Final disposition for TDD

The rubric verdict is **PASS**, so d2_r3 is accepted as the domain-2 chapter source. Because this is the last round, the following findings **must** be entered in the TDD risk register (`doc/saigon/TDD.md`, A6.3), each with the owner and validation shown.

| Register ID | Source | Risk | Owner | Validation |
|---|---|---|---|---|
| TR-D2-01 | RR1 + D7 | Roofs do not connect across separate row buildings in JSON-only mode. Multi-OMT rows have left/right placement asymmetry and may suppress side streets. | A2 / B8g; M-C1 in the pass-1 fork | M-C1 unit test; `saigon_rooftop_walkability` case 3 with M-C1; B1 frontage-to-road and side-street metrics |
| TR-D2-02 | D9 | M-C1 predicate semantics (non-rotatable or linear neighbours, `IGNORE_ROTATION_FOR_ADJACENCY`, vertical directions) and the ID clash with d4 C1 | fork C++ | P1-C1 fixture test with a rotatable, a non-rotatable and a road neighbour |
| TR-D2-03 | D1 | The stair column spec is self-contradictory; a wrong stair silently teleports the player to a neighbouring lot via `game::find_stairs` | B8b | Test case 4 with same-lot landing assertion |
| TR-D2-04 | D2 + D3 + D4 + D6a | z3 template integrity: cap write order, last-lot collisions, mixed-height party walls, h3 front edge | B8b | Test cases 1 and 3 with the corrected walk-surface definition and explicit cap-tile assertions |
| TR-D2-05 | D5 / RR5 | Tank fill amounts; no rain refill | B8b (amount); A3 (rain) | Test case 5 checks charges within [120, 720] |
| TR-D2-06 | D6b + D6c | Reachability tests can pass through windows, and the district BFS exceeds the bubble | B8c / B8g | Door-only traversal; MAPBUFFER-level BFS |
| TR-D2-07 | D8 | Canon underbone versus the 3-tile parking slot | B6a / A3 with A2 | `saigon_frontage_parking_safe` static footprint test over the final group |
| TR-D2-08 | Missed 1 | No zombie-density spawn or per-turn budget, although canon requires one | A2 / A3 (assign) | Benchmark B3 extended with monster count and `monmove` time against vanilla downtown |
| TR-D2-09 | RR2 | District roof groups not joined | B8g (playtest) | District test (no drops) |
| TR-D2-10 | RR3 | `pair_1x2` back frontage faces field in 3–5-deep blocks | B8g; P2.6 | B1 rate |
| TR-D2-11 | RR4 | Collapse next to the plank is UNVERIFIED | B8b | Bash step in test case 5 |
| TR-D2-12 | RR6 | No boat routes, floods or z1 canal bridges | A3; P2.3 | As in §8 |
| TR-D2-13 | RR7 | All performance magnitudes are UNVERIFIED | A6 / S0 build | B0–B3 against vanilla downtown |
| TR-D2-14 | RR8 | Mapgen dressing depends on generation order (vanilla behaviour) | A2 | Topology-only determinism test (P2.7) |
| TR-D2-15 | RR9 | Mutable special as `city_building` is untested | A2 | Not used; test before any use |
| TR-D2-16 | §9 B1–B4, B8 | Vanilla worldgen bugs: `city_spacing`/`city_size` clobber, duplicate predefined cities, the pick-loop hang, the partial `connections` reset, and pregen migration/run overflow | fork (P2.0) | `[overmap]` tests plus the new unit tests listed in §8 P2.0 |

Items that need **no** register entry: r2 D1–D10 as fixed above, apart from the residual slips listed; B7 (dead code, harmless); and the doc-drift row (B5), which is a tuning note only.
