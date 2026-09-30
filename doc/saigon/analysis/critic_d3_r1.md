# Critic review: d3_r1 (Climate, Environment and Vehicles), round 1

Rubric: `doc/saigon/analysis/CRITIC_RUBRIC.md` (N=3, k=1). Base SHA `fe6a10c2b1`.
`git diff --stat fe6a10c2b1 HEAD -- src tests data/json data/core` shows only `src/game.cpp` and `src/main.cpp` (C6 hunks). Every other cited source line is therefore identical at base and at HEAD, and every citation below was checked in the working tree.

## Verdict

**REJECT.**

| Severity | Count |
|---|---|
| BLOCKER | 0 |
| MAJOR | 9 |
| MINOR | 13 |

- Citation failure rate: 0 hard failures out of 259 explicit `path:line` references and about 100 bare `:line` references, so 0 % (< 2 %).
- The verdict is REJECT only because of the MAJOR defects. None of them is a citation error: each is a claim or design that the code contradicts, or a validation plan that cannot work as written.

## Summary

This report is unusually well cited, and most of its high-impact mechanical claims hold up under adversarial re-reading.

**Claims that survived falsification:**
- The weather tick and its cost:
  - `update_weather` is called every turn (`src/do_turn.cpp:604`).
  - It regenerates only when `calendar::turn >= nextweather` (`src/weather.cpp:1035`).
  - `nextweather = turn + rng(duration_min, duration_max)` (`:1056`), and both default to 5 min (`src/weather_type.cpp:129-130`). `grep -c duration_min data/json/weather_type.json` returns 0.
- The hard-coded constants `seasonality_magnitude_K = 12` (`src/weather_gen.cpp:38`) and `noise_magnitude_K = 6` (`:42`).
- The ±8.4 K ramp within spring and autumn (12·cos(±π/4) = ±8.49 K).
- A seasonal-mod jump of 10.8–11 K at each season boundary.
- TropiCataclysm's midwinter mean: 16 + 5 − 12 = 9 °C. The JSON is at `tropical_regional_map_settings.json:24-43`, and midwinter falls on turn-day 318.5, inside CDDA winter.
- The monsoon clock syntax:
  - `time_eval` returns fractional days since `turn_zero` (`src/math_parser_diag.cpp:1336-1337`).
  - `%` is evaluated with `std::fmod` (`src/math_parser_impl.h:281`).
  - Doy 41 is 1 May in CDDA's month table.
- The 3 mm/h rain cap (`src/weather.cpp:444-452`).
- The 8/3 ≈ 2.67× off-bubble funnel over-credit for **heavy** rain (`:170-179`, `:246`).
- The apparent-temperature formula at `src/weather.cpp:687-689`.
- The humidity-independent sweat term `-0.008_C_delta * clothing_mult` (`src/character_body.cpp:191`).
- The bodytemp equilibrium table. I re-derived 45.0 / 40.8 / 43.2 / 42.6 °C for `temp_conv` and `conv − 4·clothing_mult` for `temp_cur`.
- Balance means only "rounded centre of mass inside the wheel hull" (`src/vehicle.cpp:5213-5241`). No other stability code exists: `UNSTABLE_WHEEL`/`STABLE` are used only at `src/veh_type.cpp:897-903` and `src/vehicle.cpp:5100`.
- Boats in shallow `t_water_murky`:
  - The terrain flags are `SWIMMABLE` + `SHALLOW_WATER` and not `DEEP_WATER` (`terrain-liquids.json:79-89`).
  - `is_watercraft()` returns `in_water && wheelcache.empty()` (`src/vehicle.cpp:4887-4890`).
  - `thrust` skips the wheel check for such boats (`src/vehicle_move.cpp:473-475`).
- Parked vehicles cost the same per turn as moving ones, apart from `vehproceed` (`src/map.cpp:921-1001`, `:10784-10800`).
- City hordes are placed on `oter_type_road` only, at `size × SPAWN_CITY_HORDE_SCALAR × SPAWN_DENSITY` (`src/overmap.cpp:3459,3479`).
- `monmove()` has no cap (`src/do_turn.cpp:285-341`).

**Runtime evidence gathered by this critic:**
- **All of the report's JSON sketches load cleanly.** I wrote them into a throwaway mod `sgn_crit_probe` under a scratch `--userdir`:
  - the underbone, ba gác, xích lô;
  - the xuồng and ghe, built from the prose in §5.e;
  - `sgn_oars`, `sgn_longtail`;
  - the weather generator, the three `jmath_function`s and the `thunder` override;
  - the flood terrain, transforms and EOC from §4.3.

  `./cataclysm --userdir <scratch>/ud/ --check-mods sgn_crit_probe` returned rc 0 with no ERROR/WARNING lines in `config/debug.log`.
- **Negative control.** A mod with two `cargo_space` parts on one tile returned rc 1 and logged `src/vehicle.cpp:1682` / `src/veh_type.cpp:1548` ERRORs. So the pipeline really does catch bad parts.
- **Baseline tests.** `./tests/cata_test --user-dir=<scratch>/ut/ "[weather]"` reported **All tests passed (150 assertions in 7 test cases)** in 114 s. The 7th case is an uncommitted `tests/saigon_weather_test.cpp` from concurrent B4a work. It is skipped without the mod, and it is not part of the audited report.
- **Runtime check of the pass-1 climate.** I ran that uncommitted `saigon_monsoon_climate` test with `--mods=dda,saigon_2000s`. The working-tree mod uses the report's §2.4(a) generator values verbatim, and the test advances `calendar::turn` per sample. Across 3 seeds with hourly samples:
  - minimum temperature **5.4–6.4 °C**, maximum **45.4–46.4 °C**;
  - wet-season rain share 0.19–0.20, dry-season share 0.012–0.019;
  - afternoon share of wet-season rain **0.52–0.57**.

  These numbers bear directly on D1, D2 and D13 below.

**Where the report fails:**
1. Its B4a validation test cannot work as specified, because `collect_weather_data` never advances `calendar::turn`.
2. Its pass-1 temperature defect is understated by a wide margin.
3. The flood EOC as written never deactivates.
4. The funnel analysis misses an `int` truncation.
5. The monster budget rests on a false claim about `GROUP_ZOMBIE_HORDE`.
6. It misses the hard-coded New England water temperature.
7. The B4c validation plan omits the existing (hidden-tag) bodytemp tests.
8. The ba gác's "symmetric bed keeps the COM inside the triangle" claim fails under one-sided cargo load.

## Citation verification table

The explicit references were extracted mechanically. A script (`scratchpad/cites.py`) parsed every `path:line[-line][,:line…]`, checked that the file exists and the range fits, and then looked for the report line's backticked symbols within ±5 lines. Every NOTOK/NOSYM row was then opened by hand. Bare `:line` references were resolved against the preceding file and spot-checked (about 70 of 101).

| Class | Checked | OK | FAIL |
|---|---|---|---|
| Explicit `path:line` (after expanding ranges) | 259 | 259 | 0 |
| Automatic symbol-within-±5 hit | 190 | 190 | 0 |
| Manually re-checked (NOSYM or NOTOK because the report line's tokens were design names, not code) | 69 | 69 | 0 |
| Bare `:line` references, spot-checked | ~70 of 101 | all | 0 |
| **Total hard FAIL** | | | **0 (0 %)** |

**Loose but acceptable citations** (not counted as FAIL):
- `src/vehicle.cpp:1682` is the `debugmsg` that prints the `can_mount` failure. The quoted text "Part needs to be adjacent…" comes from `can_mount`, not from this line.
- `src/item_factory.cpp:3021` is the generic "warnings for type" `debugmsg`, not the "bigger on the inside" check itself.
- `src/weather_gen.cpp:378-381` is the right location, but the claim about it is wrong (see D-m6).

## Defects

### MAJOR

**D1 (R5, R2): the B4a validation test cannot measure a monsoon.**
- **Claim (§2.4e):** "New test `saigon_monsoon_weather_types` … reuses `collect_weather_data` (`tests/weather_test.cpp:74-111`)", with wet/dry shares and a ≥ 70 % afternoon share.
- **Evidence:**
  - `collect_weather_data` loops `for( time_point i = begin; i < end; i += 1_minutes )` and calls `wgen.get_weather_conditions( w )`. It never assigns `calendar::turn`.
  - `sgn_doy()` and `sgn_afternoon()` read `calendar::turn` (`src/math_parser_diag.cpp:1336-1337`, `:1374-1375`). The report itself says so in §2.4(d).
  - So across the simulated year every gate is **constant**: all wet or all dry, and all afternoon or none.
  - The concurrent implementation had to write its own loop with `calendar::turn = t` (`tests/saigon_weather_test.cpp`, uncommitted), which confirms the trap.
- **Required fix:**
  - Specify a collector that sets `calendar::turn = t` inside a `restore_on_out_of_scope`, as that test does.
  - State the targets that measurement supports. At runtime the afternoon share is 0.52–0.57, not ≥ 0.70 (see D-m13).

**D2 (R7, balance): the pass-1 temperature defect is understated, and one mitigation claim is false.**
- **Claim (§2.4a, K1):**
  - "Spring and autumn still ramp ±8.4 K. This is an accepted, documented pass-1 defect."
  - "carry heat gameplay through the `hot` effect … and sun exposure, which do not depend on the generator ramp."
- **Evidence:**
  - With the B4a mods, the daily mean runs 19.0 °C on 21 Mar and 35.8 °C on 20 Jun, drops to 25.0 °C on 21 Jun, and returns to 36.0 °C on 21 Sep.
  - Typical daily highs reach 41 °C and typical lows fall to 12 °C.
  - Runtime over 3 seeds: minimum 5.4–6.4 °C, maximum 45.4–46.4 °C.
  - `hot` is driven by `temp_conv`, and `temp_conv` includes `(T − ambient_norm)/5` plus AT (`src/character_body.cpp:557-568`). So the `hot` effect depends directly on the ramp.
  - With B4c switched on, a 36 °C humid late-June day sits at `hot` 3.
- **Required fix:**
  - State the real extremes.
  - Delete the "independent of the ramp" claim.
  - Make B4b a pass-1 prerequisite for any heat-balance work, or at least block B4c on it.

**D3 (R5): the monsoon weather-type design is internally inconsistent.**
- **Claim (§2.4c):** "In each `condition`, AND the dda humidity/pressure test with a seasonal gate, for example: `{"or":[{"and":[wet,afternoon,RH>=80]},{"and":[!wet,RH>=99]}]}`", applied to `light_drizzle`, `drizzle`, `rain`, `thunder` and `lightning`.
- **Evidence:**
  - The example *replaces* the dda test. It does not AND it.
  - If the same condition is used for all five types, the `required_weathers` chain (`light_drizzle`→`drizzle`→`rain`→`thunder`→`lightning`, with the last match winning at `src/weather_gen.cpp:250-263`) promotes **every** matching event to `lightning`. There would be no intensity gradation.
  - If the condition is literally ANDed with the dda test, it can only make rain *rarer* than vanilla, so a wet season cannot emerge.
  - The concurrent implementation fell back to escalating per-type humidity thresholds (78/82/85/88) plus the dda arms.
- **Required fix:** give per-type conditions with escalating thresholds, say which dda arms are kept, and redo the determinism note.

**D4 (R2, R3): the flood EOC never deactivates, and it floods in dry weather.**
- **Claim (§4.3.3):** a RECURRING EOC with `recurrence: "10 m"` and `deactivate_condition: precip < 3` "runs `u_transform_radius` … So the cost is **zero while it is dry**."
- **Evidence:**
  - A recurring EOC is deactivated only when `activate()` returns false **and** `check_deactivate` is true (`src/effect_on_condition.cpp:285-296`).
  - `activate()` returns true whenever there is no `condition` (`:370-372`). The design names no `condition`.
  - So as written the EOC transforms 14,641 tiles every 10 min forever, including in dry weather.
- **Required fix:**
  - Add `"condition": { "math": [ "weather('precipitation') >= 3" ] }`.
  - Give the flood-off EOC a global flag as its deactivate gate.
  - Use `target_var` pinned to z=0. `points_in_radius( loc, radi, 0 )` (`src/map.cpp:5446`) touches only the avatar's z, so a player on a rooftop never sees the street flood (see D-m7).

**D5 (R2): the funnel analysis misses an `int` truncation, so the fix is incomplete.**
- **Claim (§2.6, §4.1):** "live filling is 3 mm/h … one hour of heavy rain back-fills 8/3 ≈ 2.7× more". It proposes `w->rain_mm_per_hour.value_or( precip_mm_per_hour( w->precip ) )` at `src/weather.cpp:461`.
- **Evidence:**
  - `static void fill_funnels( int rain_depth_mm_per_hour, … )` (`src/weather.cpp:334`) and `static void fill_water_collectors( int mmPerHour )` (`:368`) take `int`.
  - `precip_mm_per_hour` returns 0.5/1.5/3, so the live rates become **0 / 1 / 3 mm/h**.
  - The retroactive over-credit is therefore 2.67× for heavy rain, **4×** for light rain, and **unbounded** for very light rain, where live filling is 0.
  - A float `rain_mm_per_hour` passed at `:461` would be truncated too.
- **Required fix:**
  - Change both signatures to `double`.
  - Add a test that live filling equals back-fill for every precip class. No funnel test exists today; `tests/` only names `tr_funnel` in `submap_load_test.cpp`.

**D6 (R2): the monster budget rests on a false claim about horde composition.**
- **Claim (§6.1, §6.2):**
  - "`GROUP_ZOMBIE_HORDE` is dominated by `GROUP_VANILLA_DORMANT` (weight 250)."
  - Budget row: "`SPAWN_CITY_HORDE_SCALAR` ≈ 120 … the dormant share comes from `GROUP_ZOMBIE_HORDE`."
- **Evidence:**
  - The weights in `data/json/monstergroups/zombies.json:94-…` sum to 10,477: `mon_zombie` 4,720, `mon_zombie_fat` 750, tough 750, child 750, and so on. Dormant is 250/10,477 ≈ **2.4 %**.
  - Raising the scalar adds almost entirely **active** horde entities. `horde_map::spawn_entity` puts non-DORMANT types into the idle or immobile maps (`src/horde_map.cpp:136-146`).
- **Required fix:**
  - Correct the claim.
  - Take the dormant density only from explicit mapgen groups (e.g. `sgn_GROUP_ZOMBIE_DORMANT`).
  - Re-derive the street tier: raising the scalar raises awake zombies.

**D7 (R6, missed): the water temperature is hard-coded New England.**
- **Evidence:**
  - `weather_generator::get_water_temperature()` (`src/weather_gen.cpp:301-330`) is `54.5 + 20.7·sin(…)` °F. It ignores all JSON and gives about **1–5 °C in Dec–Feb** (Saigon's dry season, when the scenario starts) and at most 24 °C.
  - `Character::update_bodytemp` replaces the air temperature with it for the lower limbs on `SHALLOW_WATER` and the whole body on `DEEP_WATER` (`src/character_body.cpp:486-487`, `:557-560`).
- **Impact:**
  - Wading through the §4.3 flooded hẻm tiles (`SHALLOW_WATER`) or swimming a canal chills the character in a city whose canon (Bible §9) is "no winter and never frost".
  - The Cần Giờ fisherman profession (swimming 3) makes this reachable on day 1.
- **Required fix:** add this as a B4b item, e.g. an optional `water_temperature` monthly curve or an offset from the air curve. Add a test at doy 318.

**D8 (R5): the B4c validation omits the existing tests that guard the seam.**
- **Claim (§3.3):** a new `tests/bodytemp_humidity_test.cpp`, plus "with the option off … proves the gate works."
- **Evidence:**
  - The existing regression gates for exactly this code are:
    - `sweating` (`tests/player_test.cpp:186`, tagged `[char][suffer][.bodytemp]`), which runs `update_bodytemp` + `update_body_wetness` at 100 °F for three fabrics with 0.2 °C tolerances;
    - `player_body_temperatures_converge_on_expected_values` (`:114`, `[.bodytemp]`);
    - `npc_bodytemp_updates_during_turn` (`tests/npc_test.cpp:1165`);
    - `drying_rate` (`tests/limb_test.cpp:190`).
  - The first two are **hidden-tag** tests, so a default or `[weather]` run never executes them.
  - The proposed step 5 ("differ by < the current AT-only delta") is not a well-defined assertion.
- **Required fix:**
  - Name these tests.
  - Run `"[.bodytemp]"`, `[limb]` and the npc case with the option off (they must stay unchanged) and on (the `sweating` targets must be re-baselined or asserted to be unchanged at the test's default humidity).
  - Model the new test on `temperature_and_sweat_check` (`tests/player_test.cpp:76-91`).

**D9 (R2): the ba gác can immobilise itself under a one-sided load.**
- **Claim (§5.c):** "The bed is symmetric, so the rounded centre of mass … stays at y = 0. That keeps it inside the wheel triangle." K7's test asserts `valid_wheel_config` only on the prototype, which is unloaded.
- **Evidence:**
  - Cargo mass enters the COM (`src/vehicle.cpp:8838-8856`), and the COM is rounded (`:8864-8869`).
  - With base mass M0 on y = 0 and a cargo load L on the y = −1 row, the COM y is −L/(M0+L). It rounds to −1 once L ≥ M0, roughly 150–200 kg of rice sacks on one side.
  - At COM (0,−1), the wheels at (2,0), (−1,−1) and (−1,1) give angles 0.46, 3.14 and 2.03 rad. The wrap gap is 3.60 rad, which is more than π.
  - `balanced_wheel_config` is then false, and `thrust` stops with "doesn't have enough wheels" (`src/vehicle_move.cpp:482-487`).
- **Required fix:**
  - Add a loaded test with one-sided cargo ≥ vehicle mass.
  - Either accept the behaviour and document it as a mechanic ("an unbalanced load stalls the trike") or widen the rear axle.

### MINOR

- **D-m1 (R2): date arithmetic.**
  - Midwinter is turn-day 318.5 ≈ **5 Feb**, not 2 Feb.
  - Midsummer and the humidity peak are 136.5 ≈ **5–6 Aug**, not 4 Aug. CDDA months: Mar 30, Apr 31, May 30, Jun 30, Jul 31, Aug 30 … (`src/calendar.cpp:880-890`).
  - "Nov 30 (doy 254)" is wrong: Nov 30 is doy 252 and doy 254 is 2 Dec. The `sgn_wet` window over-runs by about 2 days.
- **D-m2 (R2): heat-effect levels.**
  - In "humid shade at 33 °C: 43.2 − 1.0 = 42.2 → `hot` level 2", 42.2 °C is below `BODYTEMP_VERY_HOT` (43 °C, `src/weather.h:42`).
  - It gives `hot` 1 + `hot_speed` 1 (`src/character_body.cpp:732-741`). K5's "permanently hot 2" is wrong for the same reason.
- **D-m3 (R2):** "a `veh_at`-free `is_sheltered`" is wrong. `game::is_sheltered` calls `here->veh_at( p )` (`src/game.cpp:4923`). Also, `update_body_wetness( const w_point & )` receives neither a shelter flag nor a `weather_id`, so B4c must pass or compute them.
- **D-m4:** for 33 °C at RH 90, `evap_eff` = (56.0 − 45.1)/56.0 = **0.195**, not 0.23. The 0.25 floor masks this.
- **D-m5: determinism wording.**
  - `get_weather` is not a pure function. Wind uses `rng(1,2)`, `rng(9,peaks)`, `rng_float`, `one_in` and the static `current_winddir` (`src/weather_gen.cpp:207-225`).
  - `rainstorm`, `mist` and `fog` conditions read `windpower`, so forecasts and back-fill already diverge from live weather.
  - The B4b "identical across two runs" assertion must be limited to T/H/P.
- **D-m6:** "`sort_weather` keeps `clear` regardless" is wrong. `|| wt.id == WEATHER_CLEAR` applies only in the white-list branch (`src/weather_gen.cpp:377-379`). It holds for B4a only because `clear` is not black-listed.
- **D-m7: flood transform scope.**
  - The flood transform acts only on the avatar's z, so it misses a player on a rooftop (a Bible §3 movement hook).
  - K11's rationale is also wrong. `f_transform_radius` checks bounds itself and, when out of bounds, loads a separate `map tm` (`src/npctalk.cpp:4686-4700`) rather than hitting the `debugmsg`.
  - Radius 60 is always in bounds for an avatar inside the centre submap anyway.
- **D-m8:** `sgn_underbone` has **20** parts (5 + 6 + 4 + 5), not 17.
- **D-m9 (R4, labelling):** `sgn_longtail`'s `extend: PROTRUSION` is a no-op. `can_mount` only checks the *first* part in a square (`src/vehicle.cpp:1287`), and the water-drag count only looks at structure parts (`:4941`). The "long-tail engine" is therefore a renamed `engine_1cyl_large`. See the R4 assessment below.
- **D-m10:** the horde spawn gating is omitted: `SPAWN_CITY_HORDE_THRESHOLD` (4) and `SPAWN_CITY_HORDE_SMALL_CITY_CHANCE` (`src/overmap.cpp:3447-3455`). Small Saigon "cities" may receive no hordes at all.
- **D-m11 (R7):** "Near-zenith noon sun gives ≈ +3 °C … all year" ignores the weather `sun_multiplier`.
  - With `base_pressure` 1009, `cloudy` (P < 1010, `sun_multiplier` 0.3) holds for roughly half of all hours.
  - `sunny` needs P ≥ 1020 (`data/json/weather_type.json:19`), which is rare.
  - So the typical figure is about +0.9 to +3 °C. Mark it UNVERIFIED.
- **D-m12:** B4b's `interp_month` treats a month as 1/12 of the year, but CDDA months are 30 or 31 days (`src/calendar.cpp:880-890`). State which one is used.
- **D-m13 (R7):** the "≥ 70 % of wet-season rain hours between 13:00 and 19:00" target is contradicted at runtime (0.52–0.57 with the implemented chain), because the dda humidity/pressure arms fire at every hour. Keep it as a tuning target and do not assert it.

## R4 assessment: vehicles

| Vehicle | vs dda | Mechanically distinct? |
|---|---|---|
| `sgn_underbone` | `scooter` (3 tiles, 1 seat, 10 L, 7.37 kW) | **Stat variant.** It has 2 seats (a pillion), a 20 L basket and a 15 L rack, a 4 L tank and 6.3 kW, and it is heavier. The physics are identical. The capacity difference (a xe ôm carrying a passenger) is real content, but no two-wheeler mechanic exists until P2-4 (wet traction, tip-over, filtering). |
| `sgn_ba_gac_may` | `motorcycle_3wheel_abstract`, mirrored | **Structurally distinct.** It is 3 tiles wide with 1 front and 2 rear wheels, has a 7 × 500 L flatbed, and cannot enter 2-tile hẻm. Its hauling role, footprint and load-balance behaviour (D9) all differ. This one passes. |
| `sgn_xich_lo` | bicycle | **Reskin.** It is a 1-wide, inline, two-wheel bicycle with a front `seat`. The real cyclo is 3-wheeled with two wheels in front, and that form is deferred. |
| `sgn_xuong` | canoe | Variant: oars at 900 W against 720 W paddles, and 2 muscle engines. |
| `sgn_ghe` | `boat_motor_single` | **Reskin** on a new 2 × 5 hull. The long-tail is a renamed engine (D-m9). Shallow-canal travel is existing dda behaviour. |

**Verdict on R4.** The report does not *claim* new vehicle mechanics. §0.6 and §5.d say plainly that no lean or balance model exists, and they defer it to P2-4. So R4 is not a rejection trigger here. The next revision must still:
- label the xích lô and ghe as pass-1 reskins;
- tie each vehicle to the P2 seam that will make it distinct: underbone → P2-4.2/4.3, xích lô → a 2-front-wheel build after the §5.d COM test, ghe → P2-6 `CURRENT` drift plus a shallow-draft or long-tail rule.

## B4b and B4c: design judgment

**B4b (monthly curves, noise keys, rain intensity, funnel fix)**

| Axis | Judgment |
|---|---|
| Determinism | OK for T/H/P, which are simplex noise of (location, time, seed). Wind is RNG-driven today (D-m5), so the determinism test must exclude it. The `weather_time` context variable (preferred over hacking `calendar::turn`) needs `sgn_doy()` rewritten as `value_or(_weather_time, time('now'))`, because other callers have no such context. |
| Save compatibility | OK. There are no new saved fields, and weather is regenerated from the seed. Side effect: item-rot catch-up (`src/item_degrade.cpp:1365-1373`) re-reads the generator for past hours, so an existing save's off-bubble rot silently follows the new curve. That is acceptable, but document it. |
| Balance | Required to remove the 5–46 °C sawtooth (D2). A noise of 1.5 K is realistic for Saigon, but it collapses day-to-day variation. Validate with a `mean_abs_running_diff` band like `weather_realism`, not only the monthly means. Add the water-temperature curve (D7). |
| Performance | OK. One lerp per call. The hottest caller is the per-item, per-hour rot catch-up loop, and this still counts as negligible. The funnel change sits off the hot path. |
| Tests touched | `weather_realism`, `eternal_season` and `local_wind_chill_calculation` (`tests/weather_test.cpp:113,163,194`) must stay unchanged. The `snow_*` and `widgets_showing_weather_conditions` cases run under `[weather]`. The new `monthly_climate_curve` test is needed. A new funnel live-vs-retro test is needed for every precip class (D5). The Saigon monsoon test must advance `calendar::turn` (D1). |

**B4c (`HUMID_SWEAT_MODEL`)**

| Axis | Judgment |
|---|---|
| Determinism | OK: no RNG. |
| Save compatibility | Low risk. A missing option loads as its default. However, `load_external_option` writes the mod's value into the live option (`src/worldfactory.cpp:2059-2090`). Check that the value is not written into the world's saved options, where it would outlive the mod. |
| Balance | Wet-season shade at 33 °C gives 42.2 °C: `hot` 1 + `hot_speed` 1, not level 2 (D-m2). Sun at noon gives about 44 °C, which is `hot` 2. Nights at 26 °C and RH 90 go from 36.5 to about 39.5 °C, which is not hot. It is **unsafe to enable before B4b**, because the B4a 36 °C ramps would give `hot` 3 (D2). |
| Performance | OK: O(characters). It adds one `exp` pair and one `veh_at` through `is_sheltered` (D-m3), which is not free but is small. |
| Tests touched | `sweating` and `player_body_temperatures_converge_on_expected_values` (`tests/player_test.cpp:186,114`, **hidden `[.bodytemp]`**), `npc_bodytemp_updates_during_turn` (`tests/npc_test.cpp:1165`), `drying_rate` (`tests/limb_test.cpp:190`), and `local_wind_chill_calculation` (AT unchanged). There is no `bodytemp_test.cpp`. `tests/temperature_test.cpp` covers **item** temperature and is unaffected (D8). |

## Missed topics (spot-check)

1. **Water temperature**, hard-coded for New England (`src/weather_gen.cpp:301-330`). Promoted to D7.
2. **Item thermal model and ice.** The Bible §3 and §5 make ice the key resource and fast spoilage a core mechanic. The report covers rot only through the generator. It does not cover:
   - `item::calc_temp` (`src/item.cpp:4203`);
   - `process_temperature_rot` (`src/item_degrade.cpp:1286`), including insulation for the thùng xốp cooler;
   - how quickly an ice block melts at 27–35 °C.

   Add a short section with one measurement: the lifetime of an ice block in a styrofoam cooler at 30 °C.
3. **Weather sound masking.** `weather_type.sound_attn` affects hearing. It is relevant to the stealth-in-storms claim in §4.1, which mentions only scent.
4. **`vehicle::update_time`** evaluates `sum_conditions` → `get_weather_conditions`, including the new jmath gates, once per minute per vehicle that has funnels, solar panels, wind turbines or water wheels (`src/vehicle.cpp:8608-8624`). The report's "no FUNNEL or solar on parked bikes" rule is right, but the JSON-condition cost should be counted in B6.

## Required changes for next revision

1. **D1.** Rewrite the B4a validation: a collector that sets `calendar::turn` per sample, and targets that match the measured behaviour (wet ≥ 0.05, dry ≤ 0.02, wet ≥ 4× dry; afternoon share reported, not asserted at 0.70).
2. **D2.** Report the real pass-1 extremes (≈ 5–46 °C, confirmed at runtime). Remove "`hot` does not depend on the ramp". Make B4b a prerequisite for B4c and for heat tuning.
3. **D3.** Replace the §2.4(c) example with per-type escalating conditions. Say which dda arms are kept, and explain how the `required_weathers` chain yields the intensity mix.
4. **D4.** Add a `condition` to the flood-on EOC and a global-flag gate to flood-off. Pin the transform to z=0 via `target_var`. Re-state the dry-weather cost.
5. **D5.** Fix the funnel analysis: the `int` truncation at `src/weather.cpp:334,368`, and over-credit of 2.67× (heavy), 4× (light) and unbounded (very light). The B4b fix must change the signatures. Add a live-vs-retro test for each precip class.
6. **D6.** Correct the horde composition (≈ 2.4 % dormant) and rebuild the §6.2 budget. Dormant density must come from explicit mapgen groups. Mention the threshold and small-city gating (D-m10).
7. **D7.** Add water temperature to B4b (seam: `weather_generator::get_water_temperature`, `src/weather_gen.cpp:301`) with a test. Note that it affects the §4.3 flood and canal swimming.
8. **D8.** Name the B4c regression tests (`sweating`, `player_body_temperatures_converge_on_expected_values`, `npc_bodytemp_updates_during_turn`, `drying_rate`) and the hidden-tag run command. Replace the step-5 assertion with a concrete one.
9. **D9.** Add a loaded ba gác COM test, and decide whether the stall is a mechanic or a bug.
10. Fix D-m1 through D-m13 in the text:
    - dates and doy 252;
    - `hot` levels;
    - `is_sheltered` calls `veh_at`;
    - `evap_eff` value;
    - determinism scope;
    - `sort_weather`;
    - the K11 rationale;
    - part count;
    - `PROTRUSION` no-op;
    - `sun_multiplier`;
    - month length;
    - the afternoon target.
11. Add the R4 labelling from the table above, and map each vehicle to the P2 seam that will make it mechanically distinct.
12. Add the missed topics: the item thermal model and ice lifetime, `sound_attn`, and the per-vehicle `update_time` condition cost.
