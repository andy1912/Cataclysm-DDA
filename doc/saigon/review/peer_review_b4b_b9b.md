# Peer review: uncommitted B4b (monthly climate curves) + B9b (chợ NPCs)

Reviewer: senior C++/CDDA peer review (read-only). Date: 2026-10-02.
Scope: `git diff` + untracked files in `/Users/ducpa/code/cdda-saigon` at review time:
`src/weather_gen.{h,cpp}`, `tests/saigon_weather_test.cpp`, `data/mods/saigon_2000s/region/weather.json`,
`tools/saigon/gen_cho.py`, `data/mods/saigon_2000s/mapgen/cho/cho.json`, `data/mods/saigon_2000s/npcs/npcs.json` (new).
Specs: `doc/saigon/analysis/d3_r3.md` §2.5, `critic_d3_r3.md` (binding conditions), `doc/saigon/TDD.md` §3.3.3.

Method note. Nothing in the tree was built or run (a build was in progress). To predict the test
outcome I compiled a **standalone replica** in the session scratchpad: a verbatim copy of
`src/simplexnoise.cpp` plus a line-for-line port of `get_common_data`,
`weather_temperature_from_common_data`, `get_weather` (curve T/H, dda P, wind with a PRNG) and the
mod's weather-type chain (`weather.json` + inherited dda `required_weathers`/priorities). Calibration:
in dda mode (B4a manual mods) the replica reproduces the B4a recorded extremes **exactly** (5.4 °C / 46.4 °C)
and mean 27.44 °C (recorded 27.4). Rain shares are within ~0.03 absolute of the recorded B4a values
(replica wet 0.19–0.20 vs recorded 0.22; dry 0.015–0.020 vs 0.014). Treat rain-share predictions as ±0.03.

---

## Part 1: B4b, C++ seam (`src/weather_gen.h`, `src/weather_gen.cpp`)

### What is correct (verified)

- **Month table.** `monthly_curve_value` (`src/weather_gen.cpp:54-77`) uses exactly the quarter logic of
  `month_and_day` (`src/calendar.cpp:875-910`): `day/91` quarter, 31/30/30 split. Midpoint of month m sits at
  `month_pos = m + 0.5` (e.g. Jan d=15 → 15.5/31 = 0.5). Continuity at month edges holds
  (Jan 31 → 0.984, Feb 1 → 1.017). Wrap-around: 1 Jan gives `pos = -0.484`, `lower = -1`,
  `i = ((-1 % 12) + 12) % 12 = 11` → Dec·0.484 + Jan·0.516. Correct.
- **Fallback** for `year_length() != 364_days` uses `12 * time_past_new_year / year_length` (`:69`),
  the same year fraction as `get_common_data` (`:140-141`). Correct and consistent with `month_and_day`
  returning `month::UNKNOWN` (`src/calendar.cpp:877-879`).
- **Input time.** All four call sites pass `t.t` of a `season_effective_time`
  (`:172`, `:235`, `:248`, `:361`), so `ETERNAL_SEASON` pins the curve to the start day exactly like the
  dda sinusoid (`src/calendar.cpp:114-122`). Correct.
- **Bit-for-bit with no key set.** Every changed branch is guarded by its own optional:
  T (`:171-176`, early return before the untouched dda code), H (`:234-243`, dda expression unchanged in
  the `else`), P (`:247-254`), water (`:359-363`). `mod_h` and `seasonality` are still computed in the
  same order; no RNG call was added or moved (wind `rng(1,2)`, `rng(9,peaks)`, `rng_float`, `one_in` are
  untouched, `:257-273`). Load: the four new scalars are only read inside the curve branches, so their
  defaults cannot leak into dda. **dda behaviour is unchanged.**
- **Determinism.** Same `raw_noise_4d` arguments and seeds (`modSEED`, `+101`, `+211`). Pure function of
  (location, time, seed) for T/H/P/water.
- **JsonObject API.** `has_member(std::string_view)` (`src/flexbuffer_json.h:645`),
  `get_array(std::string_view)` (`:625`), `JsonValue::get_float()` (`:220`),
  `[[noreturn]] throw_error_at(std::string_view, const std::string &)` (`:675`) all exist with these
  signatures; `for( const JsonValue v : jo.get_array(...) )` is the in-repo idiom (`src/bodygraph.cpp:102`).
  Because `throw_error_at` is `[[noreturn]]`, the `std::copy` into a 12-array can never overflow.
- **copy-from / was_loaded.** Absent key → curve keeps the copied value (inherit), present key → replaced.
  `sgn_weather` copies `default`, which has no curves, so it starts from `nullopt`. Correct.
- **Compile under `-Werror -Wall -Wextra -Wpedantic -Wold-style-cast -Wmissing-declarations`**
  (`Makefile:103-118`): `static_cast` only, `monthly_curve_value` is `static`, `<algorithm>` (for
  `std::clamp`/`std::copy`) is already included (`:3`), `<array>`/`<optional>` added to the header, no
  unsigned comparisons (`values.size() != 12` compares `size_t` with an `int` literal constant, which
  `-Wsign-compare` does not flag). `-Wconversion` is not enabled. I see **no compile risk**.
- **Performance.** Hot callers: item-rot catch-up (`src/item_degrade.cpp:1365-1373`, per item per hour),
  `temp_based_phase_change_at` (`src/mapgen.cpp:6478-6483`, 10 calls per tile but only for
  `water_freeze` terrain), forecasts (`src/weather.cpp:581-585`). The curve path costs one `to_days`,
  two integer divisions, one `floor` and one lerp, and it **skips** the dda `seasonal_temp_mod` array
  and noise widening. `get_common_data`'s `cos` is still computed (unchanged). Net cost ≤ dda. The four
  `std::optional<std::array<double,12>>` add ~416 bytes to each by-value copy of `weather_generator`
  (`src/weather.cpp:195,581,977`), which already copy three vectors; negligible.

### Findings

**F1. MAJOR: the step-8 re-tune was not done; with these thresholds `saigon_monsoon_climate` fails.**
`data/mods/saigon_2000s/region/weather.json:46-114` (thresholds unchanged from B4a) vs `:14-19` (new curves).
- Evidence (analytic): dry-season curve ≤ 78 % near 1 Dec, ≤ 76 % Dec–Apr; `humidity_noise` 8 with
  `|raw_noise_4d| < 0.98` gives H ≤ 84.6. The only dry-season root arm is `H >= 99` (`:56`), so
  **dry_share = 0 exactly**, failing `CHECK( dry_share >= 0.002 )` (`tests/saigon_weather_test.cpp:120`).
  The critic predicted exactly this (`critic_d3_r3.md:75`), and d3_r3 §2.5 step 8 / TDD §3.3.3 item 8
  make the re-tune part of this commit.
- Evidence (replica, 3 test seeds): wet 0.125 / 0.121 / **0.117**, dry **0 / 0 / 0**, afternoon 1.00,
  storm **0.09 / 0.09 / 0.05**, light 0.71–0.74, mean 27.33, min 20.0–20.3, max 34.6–34.8.
  Structural reason for the wet ceiling: the only reachable wet arm is the afternoon one (H ≥ 98 never
  happens with H ≤ 93), and it is further gated by `cloudy` (P < 1010, ≈ 50 %): 6/24 × 0.5 ≈ 0.125.
- Prediction for the bands as written: mean, min, max, wet ≥ 4·dry, afternoon **pass**;
  dry floor **fails (certain)**; storm floor 0.10 **fails (likely, all 3 seeds)**; wet floor 0.12
  **coin-flip** (seed 1192447748 at 0.117).
- Fix (replica-verified; change only these four numbers, keep `humidity_noise` 8):

  | Arm | File:line | Now | Proposed |
  |---|---|---|---|
  | `light_drizzle` wet any-hour | `weather.json:55` | `H >= 98` | `H >= 87` |
  | `light_drizzle` dry | `weather.json:56` | `H >= 99` | `H >= 80` |
  | `rain` wet afternoon | `weather.json:88` | `H >= 85` | `H >= 84` |
  | `thunder` wet afternoon | `weather.json:109` | `H >= 88` | `H >= 85` |

  Replica result (3 seeds; 3 different wind-RNG seeds change storm share by ≤ 0.01):
  wet **0.154–0.169**, dry **0.0096–0.0115**, afternoon **0.73–0.79**, storm **0.20–0.23**,
  light (light_drizzle+drizzle) **0.69–0.73**, mean 27.33, min 20.0, max 34.8.
  Every band (including the 0.02 dry ceiling of F5 and the TDD light-rain floor ≥ 0.10) passes with
  ≥ 0.03 absolute margin, which covers the replica's ±0.03 calibration error.
  Reasoning: the dry arm at 80 only fires in the noisy upper tail around late Nov/early Dec and in
  rare humid spells (≈ 1 %, matching the recorded B4a 1.4 % and real HCMC dry-season showers); the wet
  any-hour arm at 87 restores night/morning rain (afternoon share falls from a degenerate 1.00 to ≈ 0.75,
  close to r1's 0.70 target) and those off-afternoon events stay `light_drizzle` because `drizzle`
  still needs H ≥ 97 or P < 1000 off-afternoon, which also resolves d3_r3 F4 (night events were all
  heavy rain); thunder at 85 lifts the storm share into the middle of 0.10–0.60.
  Sensitivity: `humidity_noise` 10 pushes the dry share to 0.015–0.024 (fails 0.02), so keep 8.
  Also update the JSON `//` comment to state the re-tune and its measured shares.

**F2. MINOR: water daily term changes shape vs. dda.**
`src/weather_gen.cpp:359-363`. dda is `2 + 2·sin(...)` °F = 0…+4 °F (mean +2 °F ≈ +1.1 K, critic
`critic_d3_r3.md:84`); the curve path is `±1 K·sin(...)` (zero mean). Units are correct (curve in °C,
`from_celsius`), and the spec only says "curve + 1 K·sin". Zero-mean is arguably better (the curve is
then the true daily mean), but the header comment should say so. Fix: add to the `monthly_water_temperature`
comment in `src/weather_gen.h:62` "daily mean; ±1 K diurnal swing peaking at 12:00". No code change.

**F3. MINOR: the new scalars are silently ignored without their curve.**
`src/weather_gen.h:64-68`, `src/weather_gen.cpp:479-482`. `noise_magnitude`/`daily_magnitude` only act
when `monthly_temperature` is set, `humidity_noise` only with `monthly_humidity`, `pressure_noise` only with
`monthly_pressure`. A modder setting `noise_magnitude` alone gets no effect and no warning. Fix: after
loading, `if( !monthly_temperature && ( jo.has_member( "noise_magnitude" ) || jo.has_member( "daily_magnitude" ) ) ) { jo.throw_error_at( "noise_magnitude", "requires monthly_temperature" ); }`
(and the same for the H/P pairs), or document it in `doc/JSON/REGION_SETTINGS.md` (see F4).

**F4. MINOR: `doc/JSON/REGION_SETTINGS.md` not updated.** The weather-generator keys are documented there
(it lists `winter_humidity_manual_mod` etc.). TDD §1 marks B4b "upstream-first PR"; an upstream PR without
docs will bounce. Fix: add the 8 new keys with units, the "each quantity switches independently" rule, the
12-entry Jan..Dec requirement and the midpoint interpolation.

**F5. NIT: negative `time_past_new_year`.** `time_duration::operator%` truncates
(`src/calendar.h:351-353`), so `time_past_new_year` is negative for `t < turn_zero − 81 days`. The negative
modulo at `:75` keeps the index in range, but the quarter split at `:58-67` mixes quarter 0 with negative
`d`, giving a slightly wrong phase (e.g. −40 days → frac 0.23 instead of 0.18). Unreachable in practice
(nothing samples weather before the cataclysm minus 81 days). Optional fix: `int day = ...; day = ( day % 364 + 364 ) % 364;`.

**F6. NIT:** `std::array<double, 12> arr;` (`src/weather_gen.cpp:471`) is default-uninitialised before
`std::copy`; value-initialise (`arr{}`) to keep clang-tidy (`cppcoreguidelines-pro-type-member-init`) quiet.
Also `base_humidity` is now unused by the Saigon generator (still mandatory), while `base_temperature`
remains live as the underground / root-cellar temperature (`src/item_degrade.cpp:1321,1374,1392`,
`src/weather.cpp:1205,1224`); the JSON comment should say that 27.5 is kept for that reason.

**F7. Scope note (not a defect of this diff).** TDD §3.3.3 items 6 (rain intensity / funnels) and 7
(forecast clock) are not in this change. That is fine for a "curves seam" unit, but `PROGRESS.md` must not
mark B4b done; record it as B4b-1 (items 1–5, 8) with items 6–7 still open (K3, K6).

---

## Part 2: `tests/saigon_weather_test.cpp`

### Verified

- `calendar::turn` handling is right: both cases use `restore_on_out_of_scope` (`:49`, `:137`) and set the
  turn per sample before `get_weather_conditions`, so `sgn_wet()`/`sgn_afternoon()` see the sample's time.
- No vacuous pass inside the climate case: `wet_hours`/`dry_hours` are always > 0; if `wet_rain_hours == 0`
  the storm and afternoon shares are 0 and fail their floors.
- Water turn arithmetic: turn-day 237 + `turn_zero_offset` 81 = Jan-day 318 → quarter 3, d = 45 → **15 Nov**;
  turn-day 318 + 81 = 399 mod 364 = 35 → quarter 0, d = 35 → **5 Feb** (`src/calendar.cpp:856-910`). At 06:00 the
  diurnal term is `sin(0) = 0`, so the test reads the bare curve: 15 Nov = 28.0 °C, 5 Feb = 27.0 °C → pass
  (dda would give 1.0–3.2 °C and 10.4–12.6 °C, so the test does discriminate).
- Storm detection compares against `thunder`/`lightning` ids; `lightning` is the dda type (not overridden), fine.

### Findings

**T1. MAJOR: the dry-season ceiling contradicts a binding condition.** `tests/saigon_weather_test.cpp:121`
asserts `dry_share <= 0.03`. critic_d3_r3 binding condition 7 (D-m6b) and TDD §3.3.3 acceptance
("DECISION: keep the committed 0.02 ceiling") require 0.02. Fix: `CHECK( dry_share <= 0.02 );`
(the F1 thresholds give 0.0096–0.0115, so 0.02 still has 2× margin).

**T2. MAJOR: the acceptance test `monthly_climate_curve` [weather] is missing.** TDD §3.3.3 lists it as
"must pass in the B4b commit", and critic binding condition 7 (D-m6a) adds the H assertion. Without it the
interpolation, the wrap-around and the H curve are only tested indirectly through rain shares, and nothing
runs in a vanilla (`dda`-only) test run. Fix: add a `[weather]` case that builds a `weather_generator` in code
(no mod needed: set `monthly_temperature`/`monthly_humidity` to the Saigon anchors, `noise_magnitude` 1.5,
`daily_magnitude` 4.5, `humidity_noise` 8), samples hourly with `calendar::turn = t`, and asserts:
monthly mean T within ±0.5 K of anchor; range of monthly means ≤ 3.5 K; min ≥ 18 / max ≤ 40;
monthly mean H within ±2 % of anchor; `|H − curve_H| ≤ humidity_noise`; T/H/P identical across two runs per seed;
and one exact interpolation point, e.g. at 15 Jan 12:00 with zero noise weights the value equals `curve[0]`,
and at 1 Jan it equals `0.484·Dec + 0.516·Jan`. Replica values: mean 27.33, min 20.0, max 34.8, all pass.

**T3. MINOR: water test lacks the dda half and its skip guard can hide a regression.**
`:130-146`. (a) TDD `water_temperature_curve` also requires "without the curve the dda values are unchanged":
add a `[weather]` case on a default-constructed `weather_generator` asserting 1.0–3.2 °C on turn-day 237 and
10.4–12.6 °C on turn-day 318 (any hour). (b) The guard `if( !wgen.monthly_water_temperature )` skips silently if
someone deletes the JSON key while the mod is loaded. Guard on the mod instead (same as `:95`,
`base_temperature < 25`) and then `REQUIRE( wgen.monthly_water_temperature )`. (c) Test the diurnal minimum
too: add hour 0 (`sin(-π/2) = -1`, expected ≥ 26 °C on both dates).

**T4. MINOR: the light-rain floor from the TDD is not asserted.** TDD §3.3.3: "light rain ≥ 0.10 of wet rain
hours" catches the d3_r3 F4 collapse (everything escalating to heavy rain). Fix: count
`light_drizzle`/`drizzle` hours in the collector and `CHECK( light_share >= 0.10 )`. Replica: 0.69–0.73 with the F1
thresholds.

**T5. NIT: `rainstorm` hides thunder and is RNG-driven.** `rainstorm` (priority 60, requires `rain`,
`windpower >= 15`) sits between `rain` and `thunder`; when it wins, `thunder` (requires `rain`) cannot match.
`windpower` uses the global RNG (`src/weather_gen.cpp:259-260`), so `storm_share` depends on test order.
Replica spread is ≤ 0.01 across RNG seeds, so it will not flake at the F1 margins; add a comment, or count
`rainstorm` as a storm.

---

## Part 3: `data/mods/saigon_2000s/region/weather.json` (curves and thresholds)

- **Temperature curve** (`:14`): annual mean 27.34 °C, range 25.9–29.2 °C, April peak. Matches Bible §9
  (dry 26–29 °C, April highs ~35 °C: replica April max 34.8 °C; ~3 K annual range) and is within ≈ 0.5 K of
  commonly quoted Tân Sơn Nhất normals. Differs from the TDD anchors in 3 months (Jul 27.4 vs 27.5, Nov 26.6 vs
  26.8, Dec 25.9 vs 26.1): harmless, but say so in the commit message. **Plausible.**
- **Humidity curve** (`:15`): identical to the TDD anchors (the usual HCMC monthly RH normals); dry mean ≈ 72 %
  (Bible 65–75 %), wet 79–85 % (Bible 80–90 %, slightly low end). **Plausible.** No diurnal RH cycle exists in
  the generator (real RH swings ~55 % afternoons to ~90 % nights); note it for B4c.
- **Water curve** (`:16`): 27–30 °C, peak April–May. Plausible for the Sài Gòn river and canals. Apr 29.5 / Dec 27.5
  differ from the TDD anchors (29 / 27): harmless.
- **`daily_magnitude` 4.5**: ±4.5 K (9 K range) is between real dry-season (~10 K) and wet-season (~7 K) ranges.
  Fine for pass 1; a per-month diurnal range is a later refinement. Peak at 17:00 is the hardcoded
  `coldest_hour + 12` (`src/weather_gen.cpp:31,168`), ~3 h late for HCMC: pre-existing, NIT.
- **`noise_magnitude` 1.5**: appropriate for tropical day-to-day variability.
- **Band predictions with the thresholds as committed** (replica, see F1): mean ✓, min ≥ 18 ✓ (20.0),
  max ≤ 40 ✓ (34.8), afternoon ✓ (1.00, degenerate), wet ≥ 4·dry ✓ (trivially), wet ≥ 0.12 **coin-flip**
  (0.117–0.125), dry ≥ 0.002 **fails** (0), storm ≥ 0.10 **fails** (0.05–0.09).
- **Proposed thresholds**: see F1 (`H >= 87` wet any-hour, `H >= 80` dry, rain-afternoon 84, thunder-afternoon 85,
  `humidity_noise` stays 8). Predicted: wet 0.15–0.17, dry 0.010–0.012, afternoon 0.73–0.79, storm 0.20–0.23,
  light 0.69–0.73. All bands, including dry ≤ 0.02 and light ≥ 0.10, pass with margin. The bands themselves
  (wet 0.12–0.35, dry 0.002–0.02, storm 0.10–0.60, min ≥ 18, max ≤ 40, mean 26.5–28.5) are sensible and need no
  change; only the dry ceiling must go back to 0.02 (T1).
- **NIT** (`:6`): the comment should also record the step-8 re-tune and its measured shares, and that
  `base_temperature` 27.5 is kept as the underground temperature; `base_humidity` is now unused by Saigon.

---

## Part 4: B9b NPCs (`npcs/npcs.json`, `tools/saigon/gen_cho.py`, `mapgen/cho/cho.json`)

### Verified against the loaders

- **`npc_class`** (`npcs.json:2-25`): `name`, `job_description` mandatory (`src/npc_class.cpp:238-239`); `common`
  false keeps them out of random spawns; `skills` objects with `"skill"` + `"bonus": { "rng": [a,b] }` match
  `src/npc_class.cpp:330-344` and `load_distribution` (`:138-157`); all six skill ids exist in
  `data/json/skills.json`.
- **`npc`** (`:26-50`): `name_unique`, `name_suffix`, `gender`, `class`, `faction`, `attitude` (0 = `NPCATT_NULL`,
  allowed), `mission` `"GUARD"` (valid `npc_mission` string, `src/npc.cpp:210`), `chat` (mandatory),
  `mission_offered` (string form, `src/npc.cpp:402-403`) all match `npc_template::load` (`src/npc.cpp:353-450`).
  `load_npc_template` reserves the mission per spawned NPC (`:634-636`).
- **`talk_topic`**: the `compare_string` + `u_val` conditional `dynamic_line`, `u_add_var` with `value`
  (`src/npctalk.cpp:3852-3874, 8558`) and the jump to `TALK_MISSION_LIST` from a custom topic are exactly the
  vanilla `TALK_CITY_COP` pattern (`data/json/npcs/TALK_CITY_COP.json:4-21`). An array `dynamic_line` picks a
  random entry (`src/npctalk.cpp:9308-9335`), which is what Chú Tư's tips intend.
- **`mission_definition`** (`:104-127`): `name`, `difficulty`, `value`, `goal` mandatory; `dialogue` with all 9 keys
  is mandatory because the origin is `ORIGIN_SECONDARY` (`src/missiondef.cpp:129-163`); `end.effect` with
  `u_spawn_item` + `count` is a vanilla form (`NPC_arsonist.json:219`); `sgn_vang_chi` exists
  (`items/currency.json:37`). No overmap target, so R15 / RR-D4-6 (missions reference Saigon specials only) holds.
- **Aspirin count semantics.** `aspirin` is a solid `COMESTIBLE` without `stackable`, so
  `count_by_charges()` is false (`src/itype.h:1729-1731`); completion counts **items** via `amount_of`
  (`src/mission.cpp:618-645`), which recurses into containers, and dda spawns aspirin as individual pills
  (`drugs.json:267`). `"count": 10` therefore means ten pills, matching the text.
- **`place_npcs` in a nested chunk** is supported (vanilla `restaurant.json`, robofac chunks);
  `jmapgen_npc` reads `class`/`x`/`y` (`src/mapgen.cpp:2034-2081`). `"null"` as a weighted chunk is the vanilla idiom
  (`Woodworker.json:73`). The chunk lands at (1,1); NPCs at (4,3) and (6,4) are `_` floor in the west office
  (`cho.json` rows 3-4). `cho.json` is byte-identical in structure to `gen_cho.py`'s `palette()/mapgen()/roof_mapgen()`
  output (checked by import, no write), and all three JSON files pass `tools/format/json_formatter.cgi`
  (run on scratch copies).

### Findings

**N1. MAJOR: duplication. "1 in 9 markets" spawns several Cô Ba / Chú Tư per world; the engine already has
uniqueness.** `gen_cho.py:95-97`, `cho.json:106`, `npcs.json:133`. `region_settings.json:23` gives chợ weight 8
of 128 among shops, so a city has several chợ and an overmap several cities: at 1/9 per chợ the player will
meet two identical "Cô Ba, fish seller" with the same dying mother, the same mission and (because the flag is
player-scoped, N3) the second one greets the player as an old friend. The code comment "true uniqueness needs a
global flag: follow-up" is wrong: `place_npcs` supports `"unique_id"`, checked against
`g->unique_npc_exists()` before placement and persisted in the save (`src/mapgen.cpp:2050-2063,2077-2079`;
`src/savegame.cpp:166,326`; vanilla `refugee_center.json:335-339`). Fix:
`"place_npcs": [ { "class": "sgn_npc_co_ba", "x": 3, "y": 2, "unique_id": "sgn_co_ba" }, { "class": "sgn_npc_chu_tu", "x": 5, "y": 3, "unique_id": "sgn_chu_tu" } ]`
and change the chunk weights to always place (`[ [ "sgn_cho_npcs", 1 ] ]`, so the first chợ generated, normally
the nearest, hosts them), or keep 1/9 if a "maybe never" is wanted. Make the change in `gen_cho.py`, regenerate,
and delete the misleading comment.

**N2. MAJOR (canon/tone): the 1975 line.** `npcs.json:100`, "In 1975 I thought I'd seen the end of the world."
Bible tone rule (`CONTENT_BIBLE.md:6`): no Vietnam War setting, respectful and everyday. Framing 30 April 1975 as
"the end of the world" is a political statement about a contested date, exactly what the rule exists to avoid,
and it is the only line in the mod that does so. Fix: replace with an apolitical, everyday line, e.g.
"Thirty years on this corner and I never saw the street empty.  Not even on the first morning of Tết."
(If the 30-year figure stays, see N6.)

**N3. MINOR: the "met" flag is player-scoped and only set by two of four responses.** `npcs.json:55,65,70,75`.
`u_add_var` stores on the avatar; any other NPC reusing the topic (or a duplicate, N1) inherits it. Picking
"I have to go." first leaves it unset, so she shouts "Stop right there!" every time. Fix: use
`{ "npc_add_var": "sgn_met_co_ba", "value": "yes" }` / `{ "npc_val": "sgn_met_co_ba" }` (vanilla
`TALK_TRUE_FOODPERSON.json:8`), set once via the topic's `"speaker_effect": { "effect": { "npc_add_var": "sgn_met_co_ba", "value": "yes" } }`,
and drop the three per-response effects.

**N4. MINOR: dialogue/location mismatch.** The NPCs stand in the west **office** (desks `d`, altar `A`,
`cho.json` rows 1-5, cols 1-8), but she says "I hid in the ice store" (`:84`) and "it's cooler by the ice" (`:58`);
the coolers (`I` = `sgn_thung_xop`) are in the east room (cols 38-46). Her `failure` line ("pray at the altar",
`:124`) fits the office. Fix (text only): `:58` → "Sit down, sit down, out of the sun."; `:84` → "I locked
myself in the office with what I could carry." (Alternative: move the chunk to `x: 38` → NPCs at (41,3)/(43,4),
both `_` floor, but then the altar line no longer fits.)

**N5. MINOR: medicine and canon details.**
- `:90` "Her blood pressure… she has no medicine left" + aspirin: aspirin is not a blood-pressure drug. Fix:
  "Her heart is weak.  The doctor had her on aspirin every morning, and now there is none."
- `:84` "the fever people came": the Bible names them "người bệnh" (official) / "ma" (locals)
  (`CONTENT_BIBLE.md:17`). Fix: "…then the người bệnh came.  The ma, my neighbours call them now."
- `:117`/`:120` point to a nhà thuốc with a green cross, but `sgn_pharmacy` (`itemgroups/loot.json:213`) is placed
  by no mapgen, so the advice points at nothing. Either place a nhà thuốc (B8 follow-up) or generalise the advice
  ("Every nhà ống had a medicine box on the altar shelf…").
- The `sgn_nurse` profession starts with exactly 10 aspirin (`professions.json:185`) and completes the mission
  instantly for 2 chỉ of gold. Acceptable, but consider `"count": 20` or a different item.

**N6. NIT: history.** `:18`, `:90` "Thirty years" of xe ôm (since 1974): motorbike taxis became a mass trade
in the late 1980s, after Đổi Mới. Fix: "Fifteen years" / "since the eighties".

**N7. NIT: kit.** Neither class sets `worn_override`/`weapon_override`; `starting_clothes` falls back to dda
`npc_*` groups (possible jackets/winter wear in 30 °C heat). Cô Ba's best combat skill is cutting, so she draws
from `survivor_cutting` (`src/npc.cpp:1366-1367`), which is fine. Fix: add an item group with
`sgn_ao_ba_ba`, `sgn_dep_to_ong`, `sgn_non_la` (vendor) / `sgn_non_bao_hiem`, `sgn_ao_mua_canh_doi` (xe ôm) as
`worn_override`.

**N8. NIT: survival risk.** The office door (`+`, row 6) opens onto a hall with 1-4 awake + 5-10 dormant zombies
per quadrant (`cho.json:96-105`). `GUARD` NPCs hold position but will fight; they may be dead before the player
arrives. Playtest; if needed, place them on the roof (`sgn_cho_roof_*`) or make the office door locked.

**N9. NIT: Vietnamese usage.** Diacritics are correct throughout (Cô Ba, Chú Tư, Bà Năm, chợ, hẻm, nhà ống,
nhà thuốc, đồng, xe ôm, Cảm ơn con, Trời ơi). "Con đó hả?" and "Cảm ơn con" address the player as younger,
natural for a Southern market woman; keep. TDD acceptance for B9b also lists `check_mod.sh` (`TDD.md:1102`):
run it before committing (not run here).

---

## Verdict

**NOT SAFE** to commit as is: the B4b commit would land with `saigon_monsoon_climate` failing (F1: dry share 0,
storm share < 0.10, wet share borderline), in breach of the B4b acceptance and two critic binding conditions
(T1, T2). The C++ itself is correct, bit-identical for dda, deterministic and compile-safe. It becomes
**SAFE TO COMMIT AFTER FIXES**, in this order:

1. **F1**: re-tune `weather.json` thresholds (`:55` 98→87, `:56` 99→80, `:88` 85→84, `:109` 88→85; keep
   `humidity_noise` 8); update the `//` comment with the measured shares.
2. **T1**: `dry_share <= 0.02`.
3. **T2**: add `monthly_climate_curve` [weather] (T/H anchors, extremes, determinism, one exact interpolation point).
4. **T3**: add the dda half of the water test, guard on the mod rather than on the key, add hour 0.
5. Run `tests/cata_test --mods=dda,saigon_2000s "[saigon]"` and `tests/cata_test "[weather]"`; paste the
   CAPTUREd shares into the commit message and lock the storm band (TDD: "locked from the first CAPTURE run").
6. **N1**: `unique_id` on both `place_npcs` entries (and decide the chunk weight) in `gen_cho.py`, regenerate `cho.json`,
   and fix the comment.
7. **N2**: replace the 1975 line.
8. **N3–N5** (npc-scoped flag via `speaker_effect`; office/ice text; aspirin/heart line; "người bệnh"; pharmacy advice).
9. **T4, F3, F4**, then the NITs (F2, F5, F6, T5, N6–N9) as time allows; split into separate commits per the
   small-units rule: B4b (steps 1–5, 9) and B9b (6–8). Record B4b as items 1–5 + 8 only (F7).
