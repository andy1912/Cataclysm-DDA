# Critic review: d3_r2 (Climate, Environment and Vehicles), round 2

Rubric: `doc/saigon/analysis/CRITIC_RUBRIC.md` (N=3, k=2). Base SHA `fe6a10c2b1`. HEAD `b72fb48e8d`. Every source file cited by the report is unchanged from base, except for the C6 hunks in `src/game.cpp`/`src/main.cpp`. Citations were checked in the working tree. The uncommitted `data/mods/saigon_2000s/{furniture,mapgen,overmap}` work in progress was not loaded or relied on.

## Verdict

**REJECT.**

| Severity | Count |
|---|---|
| BLOCKER | 0 |
| MAJOR | 2 |
| MINOR | 11 |

- Citation failure rate: **4 / 419 ≈ 1.0 %**, under the 2 % bar. All four failures are claims that contradict the cited code; no path or line is wrong.
- The verdict is REJECT only because of the two MAJOR defects. Both are design defects in fixes the report itself presents as complete:
  - the redesigned flood EOC pair (D1);
  - the B4b acceptance (D2).

## Summary

r2 is a large improvement. **All 9 MAJOR and all 13 MINOR defects from r1 are addressed in the body, not just in the changelog.**

I re-derived or re-read each of these, and each holds:

**Weather and climate**
- The B4a validation now advances `calendar::turn` per sample (`tests/saigon_weather_test.cpp:48,54`).
- The pass-1 extremes are stated, and B4b now blocks B4c.
- F1 daily means: 19.0 / 35.8 / 25.0 °C.
- F2: the dry-season noise-free mean is 59.3 % (range 52–75 %) and the wet season averages 86.5 % [re-computed].
- F4: off-afternoon and dry-season events always escalate to heavy rain. Confirmed against the committed thresholds (`weather.json:57-58,75,93`).
- F5: the inherited `cloudy` prerequisite applies P < 1010 (`data/json/weather_type.json`, `required_weathers: ["cloudy"]`).
- The `required_weathers` chain with last-match-wins (`src/weather_gen.cpp:250-265`). `copy-from` keeps `required_weathers` (`src/weather_type.cpp:147`, `optional(…was_loaded…)`).

**Floods and EOCs**
- The flood EOCs now carry a `condition`, so they sleep (`src/effect_on_condition.cpp:283-296,370-372`; reactivation at `:316-336`).
- `z_override` sets z = `z_adjust` (`src/npctalk.cpp:4597-4605`).
- `f_transform_radius` loads a separate `map tm` when the area is out of bounds (`src/npctalk.cpp:4687-4697`).

**Funnels**
- `int` truncation at `src/weather.cpp:334,368`.
- Over-credit of ∞ / 4× / 2.67×: back-fill `rain_amount` is 1/4/8 per turn (`:170-179`), fed as a rate at `:246`.
- The vehicle funnel at `src/vehicle.cpp:8648` has the same flaw, and the report covers it.

**Monsters**
- `GROUP_ZOMBIE_HORDE` has 46 entries summing to weight 10,477, of which `GROUP_VANILLA_DORMANT` is 250 (2.4 %). `GROUP_ZOMBIE` sums to 10,977 [script].
- Horde gating (`src/overmap.cpp:3447-3455`).

**Heat**
- Heat levels with B4c on: shade 42.2 → `hot` 1 + `hot_speed` 1; sun 43.5 → `hot` 2 + `hot_speed` 1 (`src/character_body.cpp:716-743`, `src/weather.h:40-47`).
- `evap_eff` is 0.195 (night case: 0.407).
- `sheltered` is computed once at `src/character_body.cpp:439`, and `is_sheltered` calls `veh_at` (`src/game.cpp:4921-4928`).

**Vehicles**
- Ba gác: 30 parts. One-sided stall when L ≥ M0 (≈ 738 kg). `std::round(-0.5) = -1`.
- Ba gác wheel angles 0.46 / 2.03 / 3.14 rad, wrap gap 3.60 > π. `balanced_wheel_config` uses `max_angle_gap <= M_PI` (`src/vehicle.cpp:5213-5241`), so rear loading at exactly π passes.
- Lone rower: muscle fuel exists only if the driver's tile has a muscle engine (`src/vehicle.cpp:3913-3936`). Every enabled muscle engine adds its base `vpi.power` (`:1134`), and the strength bonus goes only to an occupied station (`:1147-1160`). A lone rower gets (900 + 720)·4/5 = 1,296 W against 900 W from the oars alone (`total_power`, `:4074-4102`). The finding is correct.
- R4 labels: underbone = stat variant; ba gác = structurally distinct; xích lô and ghe = reskins; xuồng = variant. Each is tied to a P2 seam. `PROTRUSION` is read only on the first part in a square (`src/vehicle.cpp:1284-1291`). These labels are honest and match the landed `vehicles.json`.

**Ice**
- `latent·m / (0.0076·V^(2/3)/ins · ΔT)` gives 4.06 h bare and 16.2 h in `sgn_thung_xop` (pocket `insulation` 4, `gear.json:102-124`) for 1 L, and 6.9 / 27.7 h for 5 L at 30 °C (`src/item.cpp:4224-4225`, `src/item_contents.cpp:2771`). Confirmed.

**Sound**
- `sound_attn` is subtracted at `src/sounds.cpp:451,478,577` and `src/character_health.cpp:3109`.

**Where it still fails:**
- (D1) The new flood-off EOC only drains the circle around wherever the avatar is when it fires. Tiles flooded anywhere else stay flooded for good.
- (D2) B4b replaces the humidity and pressure inputs that every committed B4a rain threshold was tuned against. Yet its "tightened" acceptance adds only temperature bounds and keeps a wet-share check that has no upper bound.

The minors include:
- an F3 fix that is itself off by one;
- an exception to the "season gate is ANDed" claim (the vanilla Scarlet Storm);
- wrong water-temperature months;
- a wrong night row in the heat table;
- a B4c gate that is not literally "byte-identical"-able;
- a statistically flaky funnel test.

## Citation verification table

Method: `scratchpad/cites.py` parsed every `path:line[-line][,…]`, the `weather.json:`/`zombies.json:` aliases, and each bare `:line`, resolved to the nearest preceding path. It checked that the file exists and the range fits, then looked for a backticked symbol from the report line within ±5 lines. Every non-OK row was opened by hand.

| Class | Count | Result |
|---|---|---|
| References parsed | 419 | |
| Automatic OK (symbol within ±5) | 357 | OK |
| NOSYM, reviewed by hand | 57 | All OK. Most are design names or files named only by path. Some bare refs resolved to the wrong file and are OK on the right one, e.g. `:49-59` → `weather.json`, `:324` → `src/weather_gen.cpp`, `:439` → `src/character_body.cpp`, `:62-83` → `bikes.json`, traps `:59/:73/:881/:895/:958` (ids confirmed) |
| RANGE (script mis-resolution) | 5 | All OK on the right file: `:1056`, `:1067-1074`, `:1076`, `:1099` → `src/weather.cpp`; `:877-879` → `src/calendar.cpp` |
| NOFILE | 0 | |
| **Claim contradicts the cited code (R2 FAIL)** | **4** | Listed below |

FAIL rows:

| # | Report location | Citation | Claimed | Actual |
|---|---|---|---|---|
| 1 | §0.2, §2.5.5, K12 | `src/weather_gen.cpp:301-330` | dda water is "1–5 °C in Dec–Feb" | `day` counts from 1 Jan (`src/calendar.h:582-585`). The water is 1.0–3.2 °C on 15 Nov (the minimum), 3.1–5.3 °C on 21 Dec, 4.4–6.6 °C on 1 Jan, **10.4–12.6 °C on 5 Feb** and 15.2–17.4 °C on 28 Feb |
| 2 | §2.4(b) F3, Recs B4a-1 | `weather.json:34-35`, `tests/saigon_weather_test.cpp:38-41` | Two extra wet days; fix with `<= 252` | One extra day, and the fix is wrong (D-m1) |
| 3 | §2.4(c) | `data/json/weather_type.json:42-160` | "No `drizzle`, `rain` or `thunder` can occur unless … `light_drizzle` matched first" | `rain` also accepts `scarlet_storm_1/2/3`, and `scarlet_storm_5` rains with no prerequisite (D-m2) |
| 4 | §3.3 table, night row | `src/character_body.cpp:716-743` | 36.9 (on) / 34.5 (off) | Sweat is forced only at `temp_conv >= BODYTEMP_HOT` (`:196-203`). At 38.5 °C the body dries and `temp_cur` → ≈ 38.5 °C in both cases (D-m4) |

## Defects

### MAJOR

**D1 (R2, R5): the redesigned flood-off EOC strands flooded tiles for good.**
- **Claim (§4.3.3):** "So while dry and unflooded both EOCs are inactive … So the street floods even while the player is on a rooftop."
- **Evidence:**
  - Both EOCs start with `u_location_variable` → `sgn_flood_center`, which is the avatar's position at the moment of firing (`src/npctalk.cpp:4597-4605`). They transform only `trig_dist <= 60` around it (`src/map.cpp:5446-5450`).
  - Flood-on re-fires every 10 min while it rains heavily, flooding a 121-tile disc around wherever the avatar is *now*. A player who walks or drives during a storm leaves a trail of flooded discs.
  - Flood-off fires ≥ 3 h later and drains only the disc around the avatar's *then-current* position. It then sets `sgn_flooded = 0` and sleeps until the next flood.
  - Every flooded tile outside that last disc stays `t_sgn_hem_flooded` (`SHALLOW_WATER`, move cost 5, murky-water source) with no path back. The same applies if the player simply walked 60+ tiles away during the 3 h wait.
  - The proposed `saigon_flood_toggle` test keeps the avatar static at z=2, so it cannot detect this.
  - The "Limits" list omits it, and the r1 D4 defect ("floods in dry weather") reappears in a different form.
- **Required fix:**
  - Make drain lazy and position-independent. Options:
    - Flood-off does not clear `sgn_flooded` on its first pass. It keeps running every 30 min while `time('now') - sgn_last_heavy_rain` is between 3 h and some cap (e.g. 48 h), so the player drains whatever area they are in.
    - Or: the flooded terrain itself carries the revert. For example, a mapgen-update / `transforms_into` rule applied when the submap is loaded, or at P2-3 a `map::loadn` hook.
  - State the residual leak (tiles never revisited stay flooded until the next flood-off near them).
  - Extend the test: flood at A, move the avatar 100 tiles, run flood-off, return to A, and assert A reverted (or assert the documented behaviour).

**D2 (R5, R6): the B4b acceptance does not protect the monsoon that B4b re-parameterises.**
- **Claim (§2.5, Recs):** "Tighten `saigon_monsoon_climate` to `min_temp_c >= 18` and `max_temp_c <= 40`, and keep the other bounds."
- **Evidence:**
  - Every committed rain threshold is tuned against the *current* H/P generator:
    - root: wet afternoon H ≥ 78, wet H ≥ 98, dry H ≥ 99;
    - 82 / 85 / 88 escalation;
    - `cloudy` P < 1010.
  - The current H generator has ±20–60 % noise (`src/weather_gen.cpp:195-199`) and P has ±15–45 hPa (`:202-205`).
  - B4b replaces these with `monthly_humidity` (wet-season anchors 79–85 %) and `humidity_noise`/`pressure_noise`. It does not say whether the `( -seasonality + 2 )` amplitude factor survives when a curve is set ("same pattern for H", §2.5.4).
  - The proposed anchors put the wet-season mean *above* the 78 % afternoon root threshold. With ±20 % noise (and no 60 % winter noise), the H ≥ 99 dry-season arm practically never fires.
  - So the wet share can rise toward "rain almost every cloudy wet afternoon", the dry share can collapse to ≈ 0, and the P < 1010 coupling (F5) moves with `monthly_pressure`, for which no anchors are given.
  - The kept bounds are `wet ≥ 0.05`, `dry ≤ 0.02`, `wet ≥ 4·dry` and `afternoon ≥ 0.5`. A wet share of 0.6 or a dry share of 0 passes every one of them.
  - The B4b plan has no re-tuning step for the B4a thresholds and no upper bound.
- **Required fix:**
  - Specify the noise semantics when a curve is set.
  - Give `monthly_pressure` anchors, or state that P keeps the dda formula.
  - Add an explicit B4b step: "re-tune the B4a thresholds against the new generator".
  - Add two-sided bands to the test, e.g. wet share 0.12–0.35, dry share 0.002–0.03, afternoon share ≥ 0.5, plus a per-intensity mix check (the fraction of wet-season rain hours that are `thunder`), so a degenerate monsoon fails.

### MINOR

- **D-m1 (R2): the F3 fix is off by one in the other direction.**
  - `time('now','unit':'days')` is fractional (`src/math_parser_diag.cpp:1336-1337`, `_time_in_unit`). So the committed `sgn_doy() <= 254` is wet on [41.0, 254.0]: May 1 to the end of **Dec 1** (doy 253). The over-run is one day, not two.
  - The proposed `<= 252` ends the wet season at 00:00 on 30 Nov and drops 30 Nov.
  - The correct JSON is `sgn_doy() < 253`. The test's integer `doy <= 252` (`tests/saigon_weather_test.cpp:40,58`) is then consistent.
  - Note that today the test already counts 23 h/yr of doy 254 as wet while the JSON counts them as dry.
- **D-m2 (R2): an exception to the season gate.**
  - Vanilla `EOC_START_SCARLET_STORM` (`game_start`, `data/json/effects_on_condition/nether_eocs/scarlet_storm_effect_on_condition.json:3-27`) sets `scarlet_storm_active`.
  - `rain` lists `scarlet_storm_1/2/3` in `required_weathers`, and `scarlet_storm_5` has `rains: true` and `precip: heavy` with no prerequisite. Both apply in `current_dimension: default`, which the Saigon region uses.
  - So heavy rain (and the §4.3 flood-on, while wet) can occur outside the chain as the storm crosses.
  - Fix: either black-list the Scarlet Storm types in `sgn_weather`'s `weather_black_list` (and check that the EOC tolerates this), or document the exception.
- **D-m3 (R2): water-temperature months are wrong** (FAIL row 1).
  - The January wading example "(3 − 19)/5" should use ≈ 4–9 °C.
  - The dda minimum is 15 Nov (Jan-day 318.5), not 5 Feb. `water_temperature_curve` should also sample 15 Nov (turn-day 238), where the dda value is ≈ 1 °C.
  - The defect still stands, at its worst in Nov–Dec, the scenario's opening weeks.
- **D-m4 (R2): the night row in the §3.3 table is wrong** (FAIL row 4).
  - Below 40 °C `temp_conv`, wetness is not forced (`src/character_body.cpp:196-203`), so there is no −4·`clothing_mult` term. The result is ≈ 38.5 °C with the option on and off.
  - The conclusion ("none") holds, but the row should be corrected. Also state the equilibrium formula's precondition (`temp_conv ≥ 40` or externally wet).
- **D-m5 (R5): the B4c gate "byte-identical" cannot be met literally.**
  - The captured output includes log timestamps, the version hash (which changes with the B4c commit), the benchmark timing and the test-world id (see the analyst's run log).
  - `update_body_wetness` uses `roll_remainder` (`src/character_body.cpp:184`), which is global-RNG dependent.
  - Fix: run with `--rng-seed <fixed>` and diff only the assertion expansions.
  - Note the cost: the r2 baseline run took 1,179 s.
  - Say plainly that the option-on behaviour is guarded only by `humid_sweat_efficiency`, because the hidden tests are already red.
- **D-m6 (R5, R3): the `sweat_evap_eff` cache is underspecified.**
  - It must default to 1.0 and not be serialised.
  - `drying_rate` calls `update_body_wetness` without `update_bodytemp` (`tests/limb_test.cpp:220,243`).
  - The early returns in `update_bodytemp` (`DEBUG_NOTEMP`, `CANNOT_CHANGE_TEMPERATURE`, `src/character_body.cpp:420-426`) would leave it stale. Reset it to 1.0 there.
  - Read `HUMID_SWEAT_MODEL` once per turn (or as a cached option reference), not with a `get_option<bool>` string lookup per character per turn.
- **D-m7 (R5): `funnel_live_matches_backfill` is statistically flaky as specified.**
  - A `tr_funnel` (r = 300 mm) collects ≈ 3.4 charges/h in heavy rain, 1.7 in light (after the fix) and 0.57 in very light.
  - With 5 seeds of one hour, the Poisson σ of the mean is ≈ 24 %, 34 % and 60 % of the expectation, so a ±25 % band fails often.
  - Use `tr_downspout_funnel` (≈ 54 charges/h heavy) over ≥ 4 h, or assert the analytic expectation (`funnel_turns_per_charge`) directly against the back-fill depth.
- **D-m8 (R2): ba gác geometry details.**
  - The bed is 6 `cargo_space` tiles and 7 `frame`s, not "7 frame + cargo_space tiles". `cargo_rack` is 85.33 kg each, which is the real source of the mass.
  - The y = −1 row has **2** cargo tiles, (0,−1) and (−1,−1), not three as test step 3 says.
  - The stall math is unaffected, because the load's x = −0.5 still rounds to 0 at L = M0.
- **D-m9 (internal contradiction):** §4.3.3 Validation says the probe `sgn_a3_flood` "depends on `saigon_2000s`". §3.4 says it was made dda-only. Pick one.
- **D-m10 (R7, missed cost): dormant zombies are not free on first load.**
  - `sgn_GROUP_ZOMBIE_DORMANT` members are `pseudo_dormant_*` mtypes. These are real monsters until their `pseudo_dormant_trap_setup_attk` special attack turns them into a corpse plus `tr_dormant_corpse` (`src/monstergenerator.cpp:492-578`).
  - Up to 1,200 of them therefore enter `monmove` on the first turns after a district loads. Each dormant corpse is then visited by `item::process_corpse` every item tick (`src/item.cpp:4452-4468`).
  - B5b must time the first ~5 turns after load as well as steady state.
- **D-m11 (R7): sound masking is overstated.**
  - "sounds are attenuated by 8" holds only for `thunder`, `lightning` and `rainstorm`. `rain` is 4, `drizzle` 1, and the very-light root `light_drizzle` 0.
  - `sound_attn` is applied globally, including indoors and underground (`src/sounds.cpp:451,478,577`).
  - So the stealth window applies to thunder afternoons and is weaker in ordinary rain.

## Missed topics (spot-check)

1. **Scarlet Storm interaction** with the season gate and the flood EOC (promoted to D-m2).
2. **First-load cost of pseudo-dormant monsters** (promoted to D-m10).
3. **Flood transform and items or vehicles.** `t_water_murky` is `LIQUID`, `SWIMMABLE` and `NO_SCENT` (`terrain-liquids.json:79-89`).
   - Parked `sgn_veh_underbone`s on flooded tiles stay wheeled, not watercraft (`src/vehicle.cpp:4887-4890`). They need traction on move-cost-5 terrain.
   - Items left on flooded tiles stay. That is acceptable, but the `saigon_flood_toggle` test should assert that items and parked bikes survive a flood/drain cycle.

## Required changes for next revision

1. **D1.** Redesign flood-off so the drain does not depend on the avatar's position at one instant (a lazy drain window, or a terrain/loader-side revert). Document the residual leak. Add a moving-avatar case to `saigon_flood_toggle`.
2. **D2.**
   - Define the H/P noise semantics under curves.
   - Give `monthly_pressure` anchors or keep dda P explicitly.
   - Add a B4b step to re-tune the B4a thresholds.
   - Make the `saigon_monsoon_climate` bounds two-sided (wet 0.12–0.35, dry 0.002–0.03), plus an intensity-mix check.
3. **D-m1.** The F3 fix is `sgn_doy() < 253` in JSON with the test's integer `doy <= 252`. Correct "two days" to "one day (1 Dec)".
4. **D-m2.** Black-list or document the Scarlet Storm path. Qualify the "ANDed" claim.
5. **D-m3.** Correct the water-temperature months in §0.2, §2.5.5 and K12, and fix the January example. Add a 15 Nov sample to `water_temperature_curve`.
6. **D-m4.** Fix the night row and state the precondition of the equilibrium formula.
7. **D-m5 and D-m6.**
   - Gate on `--rng-seed`-pinned assertion expansions, not raw output.
   - Specify the `sweat_evap_eff` default (1.0), its reset on early return, and that it is not serialised.
   - Cache the option read.
8. **D-m7.** Re-specify the funnel test (downspout, several hours, or an analytic assertion).
9. **D-m8 to D-m11.**
   - Ba gác tile counts and test step 3.
   - Probe-dependency contradiction.
   - First-load dormant cost in B5b.
   - Per-type `sound_attn` wording.
