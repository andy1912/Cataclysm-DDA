# Critic review: d3_r3 (Climate, Environment and Vehicles), round 3 (FINAL)

Rubric: `doc/saigon/analysis/CRITIC_RUBRIC.md` (N=3, k=3). Base SHA `fe6a10c2b1`. HEAD `b9faa4a291`.

What I checked against:
- Every `src/` file the report cites is unchanged from base, apart from the C6 hunks in `src/game.cpp` and `src/main.cpp`. Citations were checked in the working tree.
- Committed B4a state:
  - `data/mods/saigon_2000s/region/weather.json` at `e1125663f1`, where `sgn_wet` is `(sgn_doy() >= 41) * (sgn_doy() < 253)` (`:35`);
  - `tests/saigon_weather_test.cpp` (`doy <= 252`, `:40`);
  - `data/mods/saigon_2000s/vehicles/vehicles.json`.
- The analyst's probe `scratchpad/ud4/mods/sgn_a3_flood/flood.json` was read in full. Its `check_mod.sh` result is `scratchpad/flood_check3.txt`, which says `OK: sgn_a3_flood`.
- My scripts are in `scratchpad/c3r3/`.
- No probe mod was needed: every question was settled by reading code. Nothing outside this file was modified.

## Verdict

**REJECT** (on one MAJOR defect, detailed under D1 below).

| Severity | Count |
|---|---|
| BLOCKER | 0 |
| MAJOR | 1 |
| MINOR | 9 |

- Citation failure rate: **4 / 448 ≈ 0.9 %**, under the 2 % bar.
- **r2's D1 and D2, and all 11 r2 MINORs, are fixed in the body**, not just claimed in the changelog. Each fix was re-derived; details below.
- The REJECT rests on one **new** MAJOR. The r2 critic missed it.
  - The only test guarding B4c's option-on path, `humid_sweat_efficiency`, asserts a threshold that the option-**off** path already exceeds.
  - It also turns the option on through `override_option`, which does not refresh the option cache that the report itself prescribes.
  - So the test passes green on a B4c that never runs. This matters because the report's own RR4 says this test is the *only* guard.
- Because this is the final round, the fix is written into the TDD disposition at the end as a binding condition. It is a two-line test change, not a design change.

## Summary: verification of the r2 fixes

### D1 (MAJOR, r2): flood-off stranded tiles. **FIXED.**

**The lazy drain window (§4.3.3) is mechanically sound.** I traced it against the EOC queue.
- `process_eocs` requeues a RECURRING EOC when `activate()` is true. When it is false, the EOC sleeps only if `check_deactivate` is also true (`src/effect_on_condition.cpp:285-296`).
- `process_reactivation` wakes sleepers on `!check_deactivate` (`:320-336`). It is called for globals only on a weather-type change (`src/weather.cpp:1072-1073`; the only global caller, by grep).
- Walking through the cases:

| Phase | Flood-off `condition` | `deactivate_condition` | Result |
|---|---|---|---|
| Before any flood | false (`sgn_flooded` unset → 0) | true | sleeps |
| Storm floods, then rain stops | n/a | false (`sgn_flooded = 1`) | the type change wakes it |
| 0–3 h after the last heavy rain | false | false | requeued every 30 min, no effect |
| 3–48 h | true | n/a | drains around the avatar every 30 min |
| ≥ 48 h | true | n/a | the inline EOC sets `sgn_flooded = 0`; the next firing fails and sleeps |

**Every piece of the JSON resolves:**
- `time('3 h')` parses through `_read_from_string<time_duration>` (`src/math_parser_diag.cpp:1329-1345`).
- `time('now')` is double turns, and global vars hold `diag_value` (`src/global_vars.h:12`), so there is no precision loss.
- Inline `run_eocs` objects go through `effect_on_conditions::load_inline_eoc` (`src/effect_on_condition.cpp:132`). Their `condition` is honoured by `activate()` (`:370-372`).
- `z_override` sets z = `z_adjust` (`src/npctalk.cpp:4599-4602`).
- The probe JSON matches the report verbatim.

**The `F-drain` loader revert is feasible.**
- `map::actualize` (`src/map.cpp:9822`) runs per loaded submap and walks all 144 tiles (`:9846-9884`).
- `time_since_last_actualize` (`:9839`) is the time **away from the bubble**, because `map::saven` stamps `last_touched = calendar::turn` on unload (`:9237`).
- `ter_t::transforms_into` exists, is loaded (`src/mapdata.cpp:1380`) and is validated in `check` (`:1556-1557`, `:1588-1589`).
- The same loop already does exactly this for harvested plants: `restock_fruits` → `ter_set( p, ter.transforms_into )` (`src/map.cpp:9594-9606`). That is a precedent the report could have cited.
- Every other consumer of `transforms_into` is flag-gated (`HARVESTED`, `GRAZABLE`, `BROWSABLE`, or a harvest action), so declaring it on `t_sgn_hem_flooded` has no side effects.
- **The flag does not need registering.** `map_data_common_t::set_flag( std::string )` accepts any string (`src/mapdata.cpp:1022-1031`), and there is no terrain-flag registry.
  - **However**, a string flag is a `std::set<std::string>` lookup (`src/mapdata.h:623-625`) on every tile of every loaded submap.
  - It should be added to the `ter_furn_flag` enum (`src/mapdata.h:289-396`) so the test is a bitset read (D-m2 below).

**The residual leak is stated, and test case 2 covers the moving avatar.** RR3's wording is wrong (D-m3).

### D2 (MAJOR, r2): B4b acceptance. **FIXED.**

- Noise semantics under curves are given per quantity: flat, with no `s` factor (§2.5 step 4 table).
- P keeps the dda formula, so the F5 `cloudy` coupling is unchanged by construction. Optional anchors are given and tied to step 8.
- Step 8 re-tunes the B4a thresholds, with the bands as the acceptance.
- The bands are two-sided: wet 0.12–0.35 and dry 0.002–0.03, plus two intensity-mix bands.
- Check: with the proposed `humidity_noise` start of 8 and dry anchors ≤ 76 %, H stays ≤ 84. So the committed dry arm (H ≥ 99, `weather.json:58`) gives a dry share of exactly 0, which fails the new 0.002 floor. This is the degenerate case r2 asked the bands to catch, and step 8 is forced to re-tune it.
- Remaining gaps are minor (D-m6).

### r2 MINORs

| r2 ID | Status | Evidence |
|---|---|---|
| D-m1 F3 | FIXED in code: `weather.json:35` `< 253`, test `:40` `<= 252` | The report still calls it "uncommitted"; it was committed in `e1125663f1` before the report commit (D-m1 below) |
| D-m2 Scarlet | Documented; the decision is acceptable | The stated reason for not black-listing is false (D-m4 below) |
| D-m3 water months | FIXED | Re-derived from `src/weather_gen.cpp:309-327`: 15 Nov 1.0–3.2, 21 Dec 3.1–5.3, 1 Jan 4.4–6.6, 5 Feb 10.4–12.6 °C. All match. The "±2 °F daily term" wording is wrong: the code is `2 + 2·sin` = 0…+4 °F (FAIL row 2). The numbers already use 0…+4 |
| D-m4 night row | FIXED | 38.5 / 38.5, with the precondition `temp_conv ≥ 40` or wet stated (`src/character_body.cpp:196-203`) |
| D-m5 B4c gate | FIXED | **Verified:** `tests/test_main.cpp:250-258` `sectionStarting` calls `rng_set_engine_seed( m_config->rngSeed() )`, so `--rng-seed` pins the game RNG per section |
| D-m6 cache | FIXED as specified (default 1.0, not serialised, reset on `:420-426`, `drying_rate` `tests/limb_test.cpp:220,243`) | The "cached option" design breaks the test (D1 below) |
| D-m7 funnel | FIXED | Analytic: downspout area π·1.2² m² × 3 mm/h = 13.57 L/h = 54.3 charges/h; very light 9.05 → 36 in 4 h. Small numeric slip (D-m7 below) |
| D-m8 ba gác | FIXED | Script-recomputed **738.53 kg, COM (−0.348, 0.000)**. 6 `cargo_space` and 7 `frame`. `cargo_rack` 85,330 g (`data/json/items/vehicle/cargo.json:74`). The y = −1 row is (0,−1),(−1,−1). At L = 800: COM = (−0.43, −0.52) → (0, −1); gaps 0.46 / 2.03 / 3.14, wrap 3.60 > π. Confirmed |
| D-m9 probe | FIXED | dda-only everywhere. The probe's own `sgn_wet` still has the superseded `<= 252`, which only matters for probe runs |
| D-m10 dormant | FIXED | The pseudo-dormant mtype has speed 1 and special-attack cooldown 1, initialised `rng( 0, cooldown )` (`src/monster.cpp:271-272`; `src/monstergenerator.cpp:546,562`). So conversion takes about 1–2 turns, and a 10-turn window is adequate |
| D-m11 sound | FIXED | `data/json/weather_type.json:76,99,122,147,170` give 1/4/8/8/8. `light_drizzle` has none (0) |

## Citation verification table

**Method.**
- `scratchpad/c3r3/cites.py` (the r2 checker, retargeted to `d3_r3.md`) parsed every `path:line[-line][,…]`, every `weather.json:`/`zombies.json:` alias, and every bare `:line`.
- It checked that each file exists and the range fits, then looked within ±5 lines for a backticked symbol from the same report line.
- Every non-OK row was opened by hand. Every new or changed r3 citation was also opened by hand, whatever its auto result:
  - `src/effect_on_condition.cpp:132,285-296,320-336,344-349,370-372`
  - `src/weather.cpp:1072-1073`
  - `src/npctalk.cpp:4599-4602,4674-4699,4688-4699`
  - `src/map.cpp:2516-2519,5439-5451,9822,9839,9846-9866`
  - `src/math_parser_diag.cpp:1310-1327,1336-1337,1374-1375,1823`
  - `tests/test_main.cpp:252-257`
  - `src/character_body.cpp:184,196-203,420-426`
  - `tests/limb_test.cpp:190,220,243`
  - `src/worldfactory.cpp:2059-2092,2091`
  - `data/json/weather_type.json:106,692-735`
  - the Scarlet Storm EOC file `:3-27`
  - `src/weather_gen.cpp:301-330,373-377`
  - `src/monstergenerator.cpp:52,492-578`
  - `data/json/items/vehicle/cargo.json:74`
  - `src/vehicle.h:1685`
  - `src/vehicle.cpp:4887-4890`
  - `src/do_turn.cpp` (all 15 lines)

| Class | Count | Result |
|---|---|---|
| References parsed | 448 | |
| Automatic OK (symbol within ±5) | 383 | OK |
| NOSYM, reviewed by hand | 58 | All OK. Most are file-only refs, or bare refs resolved to the wrong file by the script and OK on the right one. Examples: `weather.json:49-59/66-78/84-96/99-116`; `:146`, `:151-152` → `src/weather_gen.cpp`; traps `:59/:73/:881/:895/:958`; `:62-83` → `bikes.json`; `:474` → `src/weather.cpp` |
| RANGE (script mis-resolution) | 6 | OK on the right file: `:1056`, `:1067-1074`, `:1076`, `:1099` → `src/weather.cpp`; `:877-879` → `src/calendar.cpp`; `:324` → `src/weather_gen.cpp` (but see FAIL 2) |
| RANGE (genuine) | 1 | FAIL 1 |
| NOFILE | 0 | |
| **FAIL total** | **4** | 0.9 % |

FAIL rows:

| # | Report location | Citation | Claimed | Actual |
|---|---|---|---|---|
| 1 | §2.4(c) line 291 | `data/json/weather_type.json:692-735` | `scarlet_storm_5` | The file has 725 lines. `scarlet_storm_5` is `:692-724` |
| 2 | §2.5.5 line 379 | `src/weather_gen.cpp:324` | "the ±2 °F daily term" | `2.0 + 2.0 * std::sin(…)` is 0 to +4 °F. The tabulated ranges already use 0…+4, so only the wording is wrong |
| 3 | §2.4(c) line 295, RR5 | `NPC_Pat_POIs.json` named as referencing the Scarlet weather ids; black-listing "risks breaking those conditions" | NPC_Pat only contains the dialogue topic `TALK_ROBOFAC_MERC_PAT_POI_scarlet_storm_1` (`:508,529`), not a weather id. `is_weather` is `weather_id == weather_type_id( str )` (`src/condition.cpp:1699-1705`), and `weather_black_list` only filters `sorted_weather` (`src/weather_gen.cpp:368-381`). Black-listed types stay loaded, so those conditions just evaluate false; nothing breaks |
| 4 | §2.4(b) lines 272-278; Recs B4a-1; changelog D-m1 | `weather.json:34-35`, "LANDED in the working tree, uncommitted … commit it with the next B4a change" | The change is committed in `e1125663f1` ("B4a wet season ends Nov 30"), an ancestor of the report commit `b9faa4a291`. `git status` shows `weather.json` clean |

## Defects

### MAJOR

**D1 (R5): `humid_sweat_efficiency`, the sole guard for B4c's option-on path, cannot fail when B4c is off or broken.**

- **Claims** (§3.3, "New test", steps 1, 4, 5):
  - step 1: `override_option ovr( "HUMID_SWEAT_MODEL", "true" )`;
  - step 4: "Assert `temp_cur(torso)` at RH 90 minus at RH 50 is ≥ 1.0 °C. [CALC] … 42.2 vs 38.6 (difference 3.6)";
  - step 5: "With the option off, assert the difference equals the AT-only difference (… 2.4 °C …) within 0.2 °C".
- The §3.3 Gate adds: "The option-on behaviour is guarded only by the new `humid_sweat_efficiency`". RR4 repeats this.

**Evidence: the threshold does not discriminate.**
- The report's own numbers give a RH 90 − RH 50 difference of **2.4 °C with the option off** (39.2 − 36.8, §3.1 and §3.3 tables) and 3.6 °C with it on.
- The step-4 bound of ≥ 1.0 is met by both, so a B4c whose multiply is missing, or whose `evap_eff` is always 1.0, passes step 4.

**Evidence: the option is never turned on in the test.**
- The report prescribes reading `HUMID_SWEAT_MODEL` into "a static cached by `options_manager::update_options_cache`".
- `override_option` only calls `cOpt::setValue` (`tests/options_helpers.cpp:10-21`). `update_options_cache` is called only from `src/options.cpp:4194,4212` and `src/worldfactory.cpp:2091`, never by `override_option`.
- So step 1 leaves the cached flag false, and the test runs the option-**off** path while believing it is on.
- The existing precedent sets the cached global by hand next to the override: `override_option opt( "CIRCLEDIST", "true" ); trigdist = true;` (`tests/monster_test.cpp:368-369`, `:378-379`).
- Together: the test is green on a B4c that never executes. The report says this is the only guard for the option-on path, because the hidden `[.bodytemp]` tests are red in vanilla.

**Required fix:**
1. Make the cached flag refreshable from tests. Either:
   - expose it (e.g. `extern bool humid_sweat_model;`, set beside the override as `trigdist` is), or
   - call `options_manager::update_options_cache()` after constructing and after destroying the override (a small RAII helper).
2. Replace step 4 with a discriminating assertion at a fixed RH: at RH 90, `temp_cur(torso)` with the option on minus with it off ≥ 2.0 °C. [CALC] gives 42.2 − 39.2 = 3.0.
   - Keep the RH-difference check only as a two-sided band: on 3.6 ± 0.4, off 2.4 ± 0.2.
3. Add one assertion that `sweat_evap_eff` equals 1.0f exactly with the option off, which proves the off path is a no-op.

### MINOR

**D-m1 (R2): F3 status is stale** (FAIL row 4).
- §2.4(b), the Recs and the changelog say F3 is "LANDED in the working tree, uncommitted" and should be committed later. It is committed in `e1125663f1`.
- The values cited (`weather.json:35`, test `:40`) are correct.
- Fix: say "committed in `e1125663f1`".

**D-m2 (R3, R5): the `F-drain` flag must be an enum flag, and its test cannot unload the submap.**
- **Flag cost.** A string flag tested with `has_flag( std::string )` is a `std::set<std::string>::count` (`src/mapdata.h:623-625`), done for every tile of every loaded submap inside `map::actualize`. A full bubble load is 121 × 21 submaps.
  - Fix: add `TFLAG_DRAINS_WHEN_DRY` to `ter_furn_flag` (`src/mapdata.h:289-396`) and to `enum_to_string<ter_furn_flag>` (`src/mapdata.cpp:194+`), so the test is a bitset read.
- **Test distance.** The F-drain test says "unload it (move > 2 submaps away)". The bubble is `MAPSIZE` 11 (`src/map_scale_constants.h:11-12`), so a submap leaves the bubble only when it is more than `HALF_MAPSIZE` = 5 submaps (> 60 tiles) from the avatar's submap. At 2–5 submaps it stays loaded, `map::saven` never stamps it, and the test would pass vacuously or fail for the wrong reason.
  - Fix: teleport at least 7 submaps (or ≥ 4 OMT) away, as case 2 already does with 100 tiles.
- **Readability.** State that `time_since_last_actualize` measures time out of the bubble (because of `map::saven`, `src/map.cpp:9237`), not time since the flood. A tile flooded, then unloaded 2 h into a storm and reloaded 1.5 h after it ends, drains "early". That is acceptable, but say so.
- **Precedent.** Cite `map::restock_fruits` (`src/map.cpp:9594-9606`) as the in-loop `ter_set( p, ter.transforms_into )` precedent.

**D-m3 (R2, final-round rule): RR3's mitigation sentence is false.**
- RR3: "If it is not shipped, the next storm's drain window clears them".
- §4.3.3 says the opposite, correctly: drain windows only transform within 60 tiles of the avatar (`src/npctalk.cpp:4674-4699`, `src/map.cpp:5446-5450`). A disc stays flooded "until a later drain window passes near it", and late-season discs persist through the dry season.
- Fix: "the next drain window clears them only if the avatar comes within 60 tiles during it; otherwise they persist, up to the whole dry season".

**D-m4 (R2/R7): the Scarlet Storm rationale is false** (FAIL row 3).
- Black-listing does not break `is_weather` users; they simply never see the type.
- The decision to document rather than black-list is still an acceptable canon call, with RR5's B9 trigger.
- Fix:
  - replace the "risks breaking … UNVERIFIED" rationale with the verified one ("black-listing is safe: `is_weather` compares ids, and the types stay loaded");
  - drop NPC_Pat from the list;
  - state that the reason to keep the storm is canon, not technical risk.
- Also note that `scarlet_storm_4/5` carry `temperature_modifier: -20` (`data/json/weather_type.json:651,704`). That is a −20 K local swing inside a "no winter" city, which is relevant to B9's canon decision.

**D-m5 (R2): the cold-flood-water timing is misplaced.**
- §4.3.3 "Limits" says B4b item 5 is needed "to stop flood water feeling cold in December". Floods can only start while `sgn_wet()` (to 30 Nov), and drain windows run to ≈2 Dec.
- dda water [CALC from `src/weather_gen.cpp:321-324`]:
  - 1 Sep ≈ 9.4–11.6 °C;
  - 1 Oct ≈ 4.4–6.6 °C;
  - 15 Nov 1.0–3.2 °C.
- So the cold-wading collision is **Sep–Nov floods**, not December.
- RR6 mitigates only "the scenario start (21 Dec)". The scenario starts dry, so the first flood a player sees is ~1 May (water ≈ 23 °C), and the cold floods come 9–11 months in.
- Fix: correct the month in "Limits" and RR6. Either gate shipping the flood toggle (B4a follow-up 7) behind B4b item 5, or state that pre-B4b floods in Sep–Nov are 1–12 °C water.

**D-m6 (R5): B4b test gaps.**
- (a) `monthly_climate_curve` asserts only T. Add an H assertion: monthly mean H within ±2 % of the `monthly_humidity` anchors, and the H range bounded by `humidity_noise`. Otherwise `monthly_humidity` is validated only indirectly through the rain bands.
- (b) The "Band (now)" dry ceiling of 0.03 loosens the committed `CHECK( dry_share <= 0.02 )` (`tests/saigon_weather_test.cpp:111`). Meanwhile Recs B4a-4 (F2) still gates on `dry_share <= 0.02`. Pick one; 0.02 is consistent with the measured 0.014.

**D-m7 (R5): funnel test numerics and spec.**
- The heavy-class Poisson σ per seed is 1/√217 = 6.8 %, not "≤ 5 %". It is 3.9 % on the 3-seed mean, so the conclusion holds.
- The live part needs a funnel container that holds ≥ 217 charges (≥ 55 L, e.g. a 200 L drum). Otherwise `add_rain_to_container` saturates, and the heavy class under-counts.
- The analytic part asserts the back-fill "before `roll_remainder`". Today that value is computed inline in `retroactively_fill_from_funnel` (`src/weather.cpp:246`). Name the helper the B4b refactor will expose (e.g. `funnel_expected_charges( depth_mm, const trap & )`) so the test has something to call.

**D-m8 (R5): `saigon_flood_toggle` harness preconditions are unstated.**
- Case 1 must set `calendar::turn` into the wet season (turn-day 41–252). Otherwise flood-on's `sgn_wet()` gate makes every case vacuous.
- The global RECURRING EOCs must be queued in the test (`effect_on_conditions::load_new_character`, or an explicit queue).
- `get_weather().update_weather()` must run after each forced weather change. Sleeping EOCs wake only through `process_reactivate` at `src/weather.cpp:1072-1073`.
- "Both EOCs inactive after 48 h" must be "after 48 h 30 min". Flood-off clears the flag on the ≥ 48 h firing and goes to sleep on the next one, 30 min later.

**D-m9 (R5): the option cache is described inconsistently.**
- §3.3 says to read the option "once per turn into a static cached by `options_manager::update_options_cache`". Those are two different mechanisms; the second is refreshed on options load, not per turn.
- Pick the `update_options_cache` static (as `trigdist`) and document its test-side refresh (D1).

## Missed topics (spot-check)

1. **Option-cache test plumbing.** Promoted to D1.
2. **The Scarlet Storm's −20 K `temperature_modifier`** (`data/json/weather_type.json:651,704`). It is a climate effect the report does not mention while it argues for keeping the storm. Folded into D-m4.
3. **Phase transitions inherited by `t_sgn_hem_flooded`.** `copy-from t_water_murky` brings `phase_targets` (ice) and `phase_temps` [−15, −10] (`data/json/furniture_and_terrain/terrain-liquids.json:91-93`). The freeze target would not round-trip back to `t_sgn_hem_flooded`.
   - Unreachable today: the minimum is 5.4 °C, and even under a Scarlet Storm it is about 5 °C.
   - Still, delete `phase_targets` in the flood terrain so a future cold mod or debug weather cannot strand a flooded tile as ice. Informational, not a defect.

## Residual risks RR1–RR10: final-round judgement

| ID | Judgement | Note |
|---|---|---|
| RR1 | **Accept** | Honest; the mitigation (B4b with 18/40 bounds) is concrete and verified feasible |
| RR2 | **Accept** | Honest downgrade; bands as acceptance, thresholds as tuning |
| RR3 | **Accept only with corrected wording** | The "next storm's drain window clears them" sentence is false (D-m3). The F-drain mitigation itself is verified feasible (D-m2 adjustments) |
| RR4 | **Accept only with D1 fixed** | The "one guard" is currently vacuous. With D1's fix it is a real guard |
| RR5 | **Accept only with corrected rationale** | Black-listing is technically safe (D-m4). Keeping the storm is a canon decision for B9, so state it that way |
| RR6 | **Accept only with corrected scope** | The cold-water collision is Sep–Nov floods, not just the 21 Dec start (D-m5) |
| RR7 | **Accept** | Honest R4 labels, P2-4/P2-6 seams with tests |
| RR8 | **Accept** | All timings are UNVERIFIED with named benchmarks. B5b's 10-turn window matches the speed-1, cooldown-0/1 conversion |
| RR9 | **Accept** | The concrete check (load, save, remove the mod, reload) is stated. `load_external_option` does write the live option (`src/worldfactory.cpp:2059-2092`) |
| RR10 | **Accept** | 738.53 kg re-computed |

No RR is a hidden blocker. Four need their text corrected because they currently assert something false or incomplete.

## Required changes (binding conditions carried into the TDD, since there is no r4)

1. **D1.** Make `humid_sweat_efficiency` discriminating and actually enable the option:
   - refresh the cached flag beside `override_option` (the `trigdist` pattern, `tests/monster_test.cpp:368-369`) or call `update_options_cache()`;
   - assert option-on minus option-off at RH 90 ≥ 2.0 °C;
   - assert `sweat_evap_eff == 1.0f` with the option off.
2. **D-m1.** Record F3 as committed (`e1125663f1`).
3. **D-m2.**
   - Add `DRAINS_WHEN_DRY` as a `ter_furn_flag` enum value.
   - Change the F-drain test to move the avatar ≥ 7 submaps away.
   - Document that the "away time" comes from `saven`.
4. **D-m3.** Correct RR3's mitigation sentence.
5. **D-m4.** Correct the Scarlet rationale: black-listing is safe; drop NPC_Pat; keeping the storm is a canon call. Mention its −20 K modifier.
6. **D-m5.** Change "cold in December" to Sep–Nov flood water at 1–12 °C before B4b. Either gate flood-toggle shipping on B4b item 5 or state the collision in RR6.
7. **D-m6.**
   - Add an H-curve assertion to `monthly_climate_curve`.
   - Reconcile the dry ceiling (keep 0.02).
8. **D-m7.**
   - σ per seed for heavy rain is 6.8 %.
   - The live test needs a ≥ 55 L container.
   - Name the pre-roll back-fill helper.
9. **D-m8.** In `saigon_flood_toggle`, state:
   - the wet-season turn;
   - the EOC queueing;
   - `update_weather` after each forced change;
   - "48 h 30 min".
10. **D-m9.** One option-cache mechanism.
11. **FAIL rows 1 and 2.** `weather_type.json:692-724`; "0…+4 °F daily term".

## Final disposition for TDD

**Disposition:**
- The design content of d3_r3 is **accepted as the A3 input to the TDD**, subject to the binding conditions above.
- D1 is a test-specification fix inside B4c and does not change any seam. B4c may not be marked done until its fixed `humid_sweat_efficiency` is green with the option on and off.
- The risk register to carry forward:

| Entry | Risk | Owner / trigger | Carry-forward condition |
|---|---|---|---|
| K1 / RR1 | Pass-1 climate swings 5.4–46.4 °C with a sawtooth | Main session; **B4b next** | `saigon_monsoon_climate` min ≥ 18, max ≤ 40 in the B4b commit; no heat or thirst tuning before |
| K2 | The monsoon clock assumes `SEASON_LENGTH` 91 | All mod work | The mod never sets it; B4b falls back to `year_fraction` |
| K3 | Weather conditions read `calendar::turn` (forecast and back-fill) | P2-2 | `_weather_doy` context |
| K4 | Overriding dda `weather_type`s or `hot` conflicts with other mods | B4a/B9 | `conflicts` with TropiCataclysm and desert_region |
| K5 | B4c-on: wet-season `hot` 1 in shade, `hot` 2 in sun | B4c | Option-gated; tune after B4b |
| K6 | 3 mm/h cap; very light rain collects 0 live; back-fill over-credit ∞/4×/2.67× | B4b / P2-2 | `funnel_live_matches_backfill` (with D-m7 fixes) |
| K7 | Ba gác one-sided stall at ≥ 738 kg | B6 | `ba_gac_one_sided_load` test, keep as a mechanic |
| K8 / RR7 | No two-wheeler physics; xích lô and ghe are reskins | P2-4, P2-6 | Honest labels; P2 tests |
| K9 | Ghe beach when turning in 3-tile canals | A2 | Turning basins |
| K10 | Monster blow-up from implicit `monster_density`; horde scalar adds awake zombies | A2/B9 | Explicit `density`; scalar 80; B5c |
| K11 / RR3 | Flood discs persist outside the avatar's drain windows | B4a follow-up 7 + `F-drain` | Lazy window as specified; **F-drain with an enum flag and a ≥ 7-submap test (D-m2)**; RR3 wording corrected (D-m3) |
| K12 / RR6 | New England water temperature; **Sep–Nov flood water 1–12 °C** | B4b item 5 | `water_temperature_curve`; gate the flood toggle on it or document it (D-m5) |
| K13 / RR4 | Hidden `[.bodytemp]` tests red in vanilla; B4c-on has one guard | B4c | Seed-pinned diff (verified `tests/test_main.cpp:250-258`) **plus the D1-fixed `humid_sweat_efficiency`** |
| K14 / RR8 | All timing magnitudes unmeasured (bodytemp, vehicles, dormant first-load spike, flood transforms) | B5a–d, B6 | Before the B9 content lock |
| RR2 | Post-B4b threshold re-tune; intensity bands unmeasured | B4b | Lock bands from the first `CAPTURE` run; add an H-curve assertion (D-m6) |
| RR5 | Scarlet Storm rains in the dry season (and −20 K) | B9 canon decision | Black-listing is verified safe; if cut, black-list `scarlet_storm_1..5` |
| RR9 | `HUMID_SWEAT_MODEL` persistence in world options | B4c | Load, save, remove the mod, reload check |
| RR10 | Ba gác ≈ 2.5× real mass | B6 follow-up | Lighter bed parts; re-run `vehicle_efficiency` and `ba_gac_one_sided_load` |
