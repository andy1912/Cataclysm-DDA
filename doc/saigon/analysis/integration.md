# A5 Integration critique: cross-domain (d1 rendering, d2 mapgen, d3 climate/vehicles, d4 modding)

- Unit: A5 (integration critic). Read-only audit; this file is the only output.
- Inputs: `d1_r3`/`critic_d1_r3` (accepted with conditions), `d2_r3`/`critic_d2_r3` (PASS), `d3_r3`/`critic_d3_r3` (accepted with conditions), `d4_r3`/`critic_d4_r3` (PASS), `CONTENT_BIBLE.md`, `PLAN.md`, `PROGRESS.md`.
- Code audited: base `fe6a10c2b1`; started at HEAD `b9367f68de`, finished at HEAD `d4e5e1c03d`. `ceefd022ff` committed the chợ (`12ef4728e5`: `tools/saigon/gen_cho.py`, `mapgen/cho/cho.json`, `overmap/cho.json`, Saigon-only `shops` pool, chợ start location; the reviewed working-tree version is identical). Also seen late: B8e (chùa + chung cư; `tools/saigon/gen_b8e.py`, committed as `461916d7aa` while this audit ran) and an untracked B6d `vehicles/vehicle_groups.json`; they are reviewed only where noted (I2-7, I7-1, I7-8).
- Method: every generator was re-run into a scratch directory and compared with the committed JSON (all 6 outputs identical). The nhà ống lot stack was simulated in Python for all 3^6 lot-height combinations (stairs, caps, tanks, items under walls). Engine behaviour was checked against `src/` where a finding depends on it.
- Labels: **CONTRADICTION** (two sources disagree), **GAP** (nobody owns it / not implemented where a report assumes it), **BUG** (implementation defect). Severity: BLOCKER / MAJOR / MINOR. IDs: `I<section>-<n>`.
- Unit names: Part B ids from `PROGRESS.md` (B4b, B6d, B8b-2, B8g-2, B9a, B10 …); renderer phases R0/R1 from d1; C-seams from d4; M-C1 from d2. New sub-units proposed here are marked *(new)*.

## Verdict in one paragraph

The four domain reports are individually sound, but they were closed in sequence (d4 and d2 on 30 Sep, d1 and d3 on 2 Oct), and the later reports' constraints were never pushed back into the earlier ones or into the code. Three cross-domain contracts are broken in the implementation: (1) the **flood toggle (d3) targets a terrain id (`t_sgn_hem_low`) that no mapgen (d2/B8) places** — the alleys and frontage use `t_concrete`/`t_sidewalk`; (2) **rooftop tank refill is assigned by d2 to A3 and by nobody in d3**, and the engine cannot refill a `SEALED` keg furniture from rain; (3) **the per-turn budgets do not sum**: d1 allots ≤ 13 ms (critic: ≤ 8 ms) to all simulation while d3 alone budgets ≤ 25 ms for 300 awake monsters. The implementation also has defects that no domain critic could see: **the hẻm block and the new chợ have no roof level** (sunlit, open-topped "indoor" spaces), lot 5 furniture and loot end up inside the east end-cap wall, every profession starts with US dollars and a credit card, and the Saigon region still inherits dda highways, map extras, trailheads and the full random-special batch. Totals: **0 BLOCKER, 19 MAJOR, 21 MINOR** (16 CONTRADICTION, 16 GAP, 8 BUG). Nothing blocks continuing Part B, but the MAJOR items must be resolved before B6d, B8g-2, B9a and the TDD (A6) lock. Details, the consolidated budget, the seam ordering and the owner list follow.

---

## 1. Multi-storey shophouses × rendering (d2 × d1)

**What the code places.** `tools/saigon/gen_nha_ong.py` builds one `sgn_nh_solo` row per OMT, z0..z5 (`overmap/nha_ong.json`, city building `sgn_nhaong_row_1`), six 4-tile lots, heights h3:h4:h5 = 3:4:1 (`gen_nha_ong.py:177`), z3 roof walk on rows 16–19 (`WALK`, `:75`), stairs alternating (2,13)/(2,11) per storey (`:25-31`). The simulation confirms: every `t_stairs_up` has a `t_stairs_down` directly above and vice versa for all 729 height combinations (critic_d2 D1 fixed); the tank sits at lx = 2 (`:97`, `:105`, `:110`; critic_d2 D3 fixed for the tank); `liquids` amount is [120, 720] (`:162`; critic_d2 D5 fixed); setback rooms write their own east wall `W..W` (`:77`; critic_d2 D4 fixed).

**I1-1 — GAP, MAJOR — The d1 emitter budget never reached d2 or the generators.**
- d1_r3 §7 rule 2 says the ≤ 1 lit fixture per OMT rule (≈ 40 emitters per ≈ 30-OMT bubble, ≈ 10 reserved for traffic and characters; critic_d1 m7 bounds a 6×6-OMT touch at ≈ 36 fixtures) "is the rule to copy into the d2 mapgen guidance". d2_r3 was closed before d1_r2 and contains **no** lighting rule (no occurrence of `light_emitted`, emitter or lamp in `d2_r3.md`).
- Implementation: **zero emitters** in all three palettes (`sgn_nhaong`, `sgn_hem`, `sgn_cho`; `grep light_emitted data/mods/saigon_2000s` = 0). The budget is therefore trivially met, but shop interiors, the hẻm and the chợ are pitch dark at night, and d1's R0 benchmark ("6×6 Saigon district, 0/16/32/64 emitters", d1_r3 §6.1) has no real content to measure.
- The latent risk is the altar. `f_sgn_ban_tho` (`furniture/furniture.json`) says "flickering electric candles" but has no light. It is placed once per lot on z0 (all three `GROUND` variants, `gen_nha_ong.py:57-64`, `'A'`) = 6 per row OMT, and up to 16 per hẻm OMT (4 per `homes` quadrant, `gen_hem.py:29-39`). Giving the altar `light_emitted` would put 180–480 emitters in a bubble, 4.5–12× the d1 budget.
- Resolution (owner **B8a** palettes, with **R0** re-deriving N_max): (a) `f_sgn_ban_tho` must never emit light — use a non-emitting glow sprite later (d1 R4 emissive layer); (b) at most one lit fixture per OMT, chosen by an `omt`-scoped parameter (e.g. one shop sign or street lamp at z0), weighted so the mean is ≤ 0.8 per OMT (36-OMT touch bound), or ≤ 0.5 if the tier-a 4 ms lightmap target of §8 is adopted; (c) copy d1 §7 rule 2 verbatim into the TDD mapgen chapter (A6.2) as a d2 rule; (d) add a static JSON lint in `tools/saigon/` counting `light_emitted` placements per OMT column.

**I1-2 — CONTRADICTION, MAJOR — d1 recommends `light_color` for neon, but d1's own multi-floor colour bugs make colour on non-camera z unsafe, and Saigon content is mostly non-camera z.**
- d1_r3 §7 rule 2: "Use `light_emitted` + `light_color` … for neon/shop signs, altar lamps". d1_r3 §2.2 items 2–5 and critic_d1 D1 (TDD-RR-D1-01): colour on any level other than the camera z is stale, can grow without bound under an NPC, and fix (a) as written wipes fresh colour in look mode. In a 3–5-storey street every floor above the player and every floor below a rooftop player is a non-camera z.
- Resolution (owner **B8a** for the rule, **R1** for the fix): in pass 1, coloured light (`light_color`) only on z0 fixtures that face the street (camera z for street play); every fixture on z ≥ 1 is white light only, until R1 lands the epoch-keyed fix (a) with `[lightmap][multiz]` steps 7–8. Record this in the TDD as a pass-1 authoring rule tied to TDD-RR-D1-01.

**I1-3 — CONTRADICTION, MINOR — d1's multi-floor test scenes assume geometry the shophouse does not have.**
- d1_r3 §2.2 item 4 and the `[lightmap][multiz]` fixture use "a z1 open-air atrium over z0" and "look down the atrium" from the z3 walk. The implemented row has no atrium: z1/z2 floors cover rows 2–19 in every lot (`FLOOR`, `gen_nha_ong.py:66-73`), and the only views down are rows 0–1 (street) and rows 20–23 (back alley, open air from z1 up).
- d1_r3 §6.2's Z̄ = 2–4 "on a z3 roof walk over an alley" does match: from rows 16–19 at z3 the player sees rows 20–23 at z0, 3 levels down.
- Resolution (owner **R0**): keep the synthetic atrium fixture for `[lightmap][multiz]` (it isolates the mechanism), but run the `[lightmap][saigon]` and `[seen_cache][saigon]` benchmarks on the real `sgn_nh_*` stacks with the four avatar spots d1 lists, using the rear-alley edge (x, 18, z3) as the "roof walk" spot.

**I1-4 — GAP, MAJOR — "Rooftops connect for movement" (Bible §3) is not met anywhere in the implementation.**
- Only the `solo` role exists. Its z3 walk is capped at x = 0 and x = 23 (`row_mapgen` caps, `gen_nha_ong.py:186-187`), so every OMT's walk is an isolated 22-tile strip. The `endw/mid/ende/pair` roles (d2_r3 §4.a.2 R-ROOF), the district special (§7.2) and the cross-building M-C1 seam are all still todo (`PROGRESS.md` B8b-2, B8g-2).
- d1's R0 benchmark also assumes "the 3×3 shophouse block (z0–z3 plus roof walk)".
- Resolution (owner **B8b-2**, then **M-C1**): land the role oters and `sgn_nhaong_row_2/3`/`pair_1x2` before B8g-2; add `saigon_rooftop_walkability` cases 1–3 from d2_r3; M-C1 follows for cross-building links.

**I1-5 — GAP, MINOR — Tall stacks raise the lighting floor for almost every bubble.**
- P(at least one h4/h5 lot in an OMT) = 1 − (3/8)^6 ≈ 99.7 %, and P(at least one h5) = 1 − (7/8)^6 ≈ 55 %. So a Saigon bubble almost always has non-uniform z4, and usually z5. `build_sunlight_cache` then starts at z6 (`src/lightmap.cpp:371`, `calc_max_populated_zlev() + 1`) and walks the slow quadrant path for z5..z0 over most of the bubble. d2_r3 §6.3 compares this only to vanilla downtown peaks; d1's F ≈ 2 ms assumption does not cite a level count.
- Resolution (owner **R0**): measure F at dusk with coloured weather (critic_d1 m7) on a bubble whose max populated z is 5, and feed the result to the §8 budget table. If F > 2 ms, B8b-2 may cap h5 at weight 0 (h3/h4 only) as the cheap lever.

---

## 2. Vehicles (d2 parking × d3/B6 prototypes × d4 namespaces)

**State.** Landed prototypes (`vehicles/vehicles.json`): `sgn_veh_underbone` (parts x = −1..1, y = 0: 3 tiles), `sgn_veh_xe_tay_ga` (copy-from `scooter`, 3 tiles), `sgn_veh_ba_gac_may` (x = −1..2, y = −1..1: **4 long × 3 wide**), `sgn_veh_xich_lo` (3 tiles), `sgn_veh_xe_dap` (copy-from `bicycle`, 3 tiles), `sgn_veh_xuong` (3 tiles), `sgn_veh_ghe` (5 × 2). There is **no** `vehicle_group`, `vehicle_placement` or `place_vehicles` anywhere in the mod, and the shophouse frontage rows 0–1 are bare `t_sidewalk` (`gen_nha_ong.py:191-192`).

**I2-1 — CONTRADICTION, MAJOR — The d2 parking group is out of date on three counts; B6d must not copy it.**
- d2_r3 §4.f: `sg_parked_twowheelers` = `scooter` 80 / `bicycle` 20 (dda ids, `sg_` prefix). critic_d2 D8: the frontage is scooter-dominated against Bible §1 ("110cc underbones … a few 50cc scooters"), "until the underbone is authored with x ∈ [−1, 1]".
- d4_r3 §8.1 / RR-D4-4: groups must be `sgn_vg_*` and must never reuse a prototype id, because `src/veh_type.cpp:1342` auto-creates a same-named group for every prototype and groups append (`src/vehicle_group.cpp:80-87`).
- The underbone now **is** 3 tiles, so the D8 precondition is met.
- Resolution (owner **B6d**): define `sgn_vg_parked_twowheelers` = `sgn_veh_underbone` 70, `sgn_veh_xe_tay_ga` 15, `sgn_veh_xe_dap` 15 (optionally `sgn_veh_xich_lo` in a District 1 variant; it is also x ∈ [−1, 1], y = 0). All members satisfy the d2 static footprint test (x ∈ [−1, 1], y = 0). Place them only through the d2 `sgn_frontage_row` chunk (owner **B8b-2**: rows 0–1 belong exclusively to it), mounts (1,0)…(21,0), `rotation: 0`, `status: 0`, `chance: 50`. Add `saigon_frontage_parking_safe` with the corrected group. Add the d4 CI grep (no `vehicle_group` id equals a `vehicle` id).

**I2-2 — CONTRADICTION, MAJOR — d2 drops road-side traffic as impossible; d4 shows how to replace it; nobody owns it, and dda US traffic currently spawns on Saigon streets.**
- d2_r3 §4.f "Budget": "Road-side parking is dropped for pass 1. Weights are additive … vanilla road vehicles would still appear". d4_r3 §2.2 gives routes (a)/(c): same-id nested vehicle chunks for the 8 dda entry ids at weight 1,000,000 leave ≈ 0.1 % dda traffic and cost nothing per OMT.
- The Saigon cities use dda road OMTs, so today every city street draws `24x24_road_*_vehicles` (US cars, police cars, pile-ups).
- Resolution (owner **B6d**, sub-unit *(new)* **B6d-2 road traffic**): implement d4 route (c) for all 8 ids in `mapgen/roads/` with `sgn_vg_street_traffic` (underbones, xe tay ga, ba gác, a rare bus/van), plus route (d) dilution for `parkinglot`/`crashed_helicopters` if those spawns stay reachable (see I4-2). Budget: ≤ 150 vehicles per bubble (d2 §6.3, d3 §5.f) − ≤ 90 frontage worst case ⇒ **≤ 60 road vehicles per bubble, ≈ ≤ 6 per road OMT**.

**I2-3 — GAP, MAJOR (for B6d placement) — The ba gác is 3 wide and fits nowhere that d2 designed.**
- `sgn_veh_ba_gac_may` occupies y = −1..1. The ledger's "street-only (not hẻm)" rule (`PROGRESS.md` B6b row) is necessary but not sufficient:
  - hẻm spine is 2 tiles (x = 11–12, `gen_hem.py:113-117`) and sub-alleys 1 tile: it cannot enter, which matches Bible §3 ("hard to drive through except by motorbike");
  - the shophouse frontage has 2 rows (0–1) in front of the shutter row 2: a ba gác parked parallel to the curb at y = 0 or 1 overlaps row 2 or leaves the OMT. Per `src/mapgen.cpp:7065-7085` an overlap with the shutter **destroys the shop front and smashes the vehicle**; a mount on y = 0 with y = −1 parts is rejected out of bounds (`src/mapgen.cpp:6877-6881`).
  - the rear strip (rows 20–23, 4 deep, open at x = 0 and x = 23) is the only in-building place where it fits, lengthwise along x with its mount on y = 21 or 22.
- Resolution (owner **B6d**): ba gác appears only (i) in the road traffic chunks of I2-2 and (ii) optionally in the rear strip, mount y ∈ {21, 22}, rotation 0 or 180. Extend the static footprint test to every group used in a frontage chunk (reject |y| > 0) and add a test that a ba gác placed in the rear strip does not touch row 19 (the rear wall).

**I2-4 — GAP, MINOR — 3-tile two-wheelers in the 2-tile hẻm spine are untested.**
- Bible §3 and d2 imply a motorbike can drive the hẻm. The spine crossing is a 2 × 2 square; whether a 3-tile vehicle can make the 90° turn there depends on the vehicle pivot and 15° rotation steps, which neither d2 nor d3 analysed.
- Resolution (owner **B6d**): `hem_underbone_turns_at_spine` test: spawn `sgn_veh_underbone` on the N arm of a generated `sgn_hem_block`, drive it south then east through (11–12, 11–12) and assert no collision. If it fails, widen the crossing to 3 × 3 in `gen_hem.py`.

**I2-5 — CONTRADICTION, MINOR — Scooter power and canon.** `sgn_veh_xe_tay_ga` copy-from `scooter` keeps dda's "50 cc" `engine_1cyl` at 7,370 W (d3_r3 §5.a table), more than the 110 cc underbone's 6,300 W (`vehicles/vehicle_parts.json`, `sgn_engine_110cc`). Resolution (owner **B6a** follow-up): give the xe tay ga its own 50–125 cc engine part at ≤ the underbone's power, or re-label it as a 125 cc scooter with ≈ 7 kW.

**I2-6 — CONTRADICTION, MINOR — Profession vehicles.** `sgn_student` still spawns the dda `bicycle` (`professions/professions.json`, `"vehicle": "bicycle"`), although `sgn_veh_xe_dap` exists (B3a placeholder note in `PROGRESS.md`). Resolution (owner **B3.R**): switch to `sgn_veh_xe_dap`.

**I2-7 — GAP, MAJOR — Late addition: the uncommitted B6d dilution (route d) misses half of the dda road placements.**
- Seen at the end of this audit (HEAD `d4e5e1c03d`, untracked `vehicles/vehicle_groups.json`): route (d) appends Saigon vehicles at ≈ 99 % weight to `city_pileup`, `city_vehicles`, `highway`, `parkinglot`, `police_pileup`, and defines `sgn_vg_parked_twowheelers` = underbone 70 / xe tay ga 20 / xe đạp 10 (consistent with I2-1).
- But the 8 dda road entry chunks also place `semi_truck` ×6, `truck_trailer` ×6, `4x4_car` ×2, `small_cars_only` ×2, `back_alley` ×1 and `food_trucks` ×1 (`grep '"vehicle":' data/json/mapgen/nested/road_vehicles_nested.json`). The first three are **prototype ids** resolved through their auto singleton groups (`src/veh_type.cpp:1342`), so US semis, trailers and 4×4s still spawn at 100 % in those slots. Diluting them would mean appending to groups named like prototypes, which d4's namespace rule (RR-D4-4) forbids.
- Resolution (owner **B6d-2**): use d4 route (c) (same-id nested chunks at weight 1,000,000) for every road chunk that places a prototype id directly or uses `small_cars_only`/`back_alley`/`food_trucks`; keep route (d) only for the C++-referenced `parkinglot` (and `crashed_helicopters` if `mx_helicopter` stays reachable). Add the d4 RR-D4-3 script: every vehicle reference reachable from the 6 road and 4 bridge om_terrains resolves to a Saigon-dominated group. Also check that the 4 × 3 ba gác added to `city_vehicles`/`city_pileup` fits the dda slot geometry (those chunks were authored for cars; an overlap merges or smashes per `src/mapgen.cpp:6964-7085`).

---

## 3. Climate × mapgen × items (d3 × d2 × B5)

**I3-1 — CONTRADICTION, MAJOR — The flood toggle cannot flood anything: its terrain id is not placed by any mapgen.**
- d3_r3 §4.3 item 3: "Mapgen (A2) places low-lying street and hẻm tiles as `t_sgn_hem_low` (copy-from `t_pavement`)". `t_sgn_hem_flooded` reverts to `t_sgn_hem_low` (`transforms_into`, F-drain).
- d2_r3 never mentions `t_sgn_hem_low`. The implemented outdoor ground is:
  - hẻm spine, sub-alleys and café courtyard: `t_concrete` (`gen_hem.py:86-88`, symbols `a`, `,`, `T`, `C`);
  - shophouse rear strip and fill: `t_concrete` (`gen_nha_ong.py:190-192`);
  - shophouse frontage rows 0–1: `t_sidewalk` (`gen_nha_ong.py:191-192`);
  - city streets: dda road mapgen (`t_pavement`, dda `t_sidewalk`).
- Simply listing `t_concrete`/`t_sidewalk` as `valid_terrain` is wrong: a single `transforms_into` cannot restore two different originals, and dda uses `t_concrete` for indoor garage and factory floors that would then flood at z0.
- Resolution (owners **B8a** for the ids, *(new)* **B4d flood toggle** for the EOCs, **B6d-2** for roads): define now, before more mapgen lands, `t_sgn_hem_low` (copy-from `t_concrete`, `looks_like` `t_concrete`) and `t_sgn_sidewalk_low` (copy-from `t_sidewalk`), each with its own flooded twin (`t_sgn_hem_flooded`, `t_sgn_sidewalk_flooded`, both copy-from `t_water_murky`) and `transforms_into` back. Switch `gen_hem.py` (`a`, `,`, `T`, `C` terrain) and `gen_nha_ong.py` (rear strip `P`, frontage `S`) to them. The Saigon road chunks of I2-2 may use the sidewalk variant. d3's `saigon_flood_toggle` case 1 must use a generated `sgn_hem_block`, not hand-placed tiles.

**I3-2 — GAP, MAJOR — Rooftop tank refill is owned by nobody, and the engine cannot do it.**
- d2_r3 §4.a.2 item 6: "Rain refilling is **not** designed here; it is deferred to A3". critic_d2 TR-D2-05: "A3 (rain)". d3_r3 contains no mention of `f_standing_tank` or rooftop tanks (grep); its §4.3 item 1 designs only new funnel traps.
- Engine: `fill_funnels` (`src/weather.cpp:334-366`) adds charges to the largest `is_funnel_container` **item** on a funnel trap tile. `f_standing_tank` is furniture with `CONTAINER, LIQUIDCONT, NOITEM, SEALED` (`data/json/furniture_and_terrain/furniture-storage.json:1324-1327`); its water is a liquid item on a `NOITEM` tile, not a funnel container. So the six tanks per OMT never refill. Bible §3 "Rooftop tanks provide water" + §9 "Rain is an asset for water collection" are met only once.
- Resolution: pass 1 JSON (owner **B8b-2** + *(new)* **B5f collectors**): add d3's `sgn_tr_roof_gutter` funnel trap on a z3/z4/z5 deck tile next to each tank, with a placed `is_funnel_container` jar/drum item (e.g. a `sgn_lu_nuoc` water jar) — ≤ 1 per lot. Pass 2 C++ (owner **B4b follow-up**, same function as B4b's funnel fix): let `fill_funnels` also credit `LIQUIDCONT` furniture on the funnel tile up to `keg_capacity`. Either way add a test: 1 h of forced `rain` on a deck with a gutter raises stored water by the d3 §4.3 arithmetic (radius 1500 ⇒ ≈ 85 charges/h at 3 mm/h). Budget note: 180 gutter traps per bubble are visited by `fill_water_collectors` every rainy turn (§8).

**I3-3 — GAP, MINOR — Ice, the thùng xốp and the chợ "ice store".**
- d3_r3 §4.5 computes that a 1 L ice block lasts ≈ 16 h in `sgn_thung_xop` (insulation 4) at 30 °C and that water never freezes in the world, so ice exists only where mapgen or loot places it. Bible §3: "Ice is the key resource" at the chợ.
- The new chợ places an "ice store" of **empty** coolers (`gen_cho.py:39-41`, palette `item` `I` → `sgn_thung_xop`, `:80`). B5b deferred the ice item. `sgn_ca_phe_sua_da` and `sgn_tra_da` are crafted without ice (`recipes/food.json`), although Bible §5 says trà đá "needs ice".
- Resolution (owner *(new)* **B5b-2 ice**): add a frozen-water block item (or reuse dda frozen `water` via `"item": "water", "container-item"`), spawn it inside the chợ coolers, add it as an optional component of the two iced drinks, and land d3's `ice_lifetime_in_cooler` test. UNVERIFIED and to be tested: the temperature at which a mapgen-spawned frozen item starts, since the chợ is generated on first visit, days after the outbreak.

**I3-4 — CONTRADICTION, MAJOR (ordering) — Water temperature vs canals and floods.**
- d3_r3 §2.5 item 5 / critic_d3 K12: the hard-coded New England water temperature (`src/weather_gen.cpp:301-330`) gives 1–12 °C water in Sep–Nov and ≈ 4 °C at the 21 Dec scenario start, which chills a wading or swimming character (`src/character_body.cpp:487-488,551-556`). The `sgn_fisherman` profession has swimming 3; d2's hẻm ports and canal design (`sg_kenh`, wadeable `t_water_murky`, §4.b/§4.d) and d3's flood twins are all `t_water_murky`-based.
- Resolution (owners **B4b** item 5, then **B8f** and **B4d**): B8f (canal) and B4d (flood toggle) are gated on B4b's `water_temperature_curve` test. Until then no `t_water_murky` content ships in a placed overmap terrain.

**I3-5 — GAP, MINOR — Hẻm ports ignore canals.** `OPEN_NEIGHBOURS` (`gen_hem.py:107-108`) lists only `sgn_hem` PREFIX and `road` TYPE; d2_r3 §4.b also opens toward canal cells. Resolution (owner **B8f**): when the canal oter lands, add `{ "om_terrain": "sgn_kenh", "om_terrain_match_type": "PREFIX" }` and the all-canal configuration to `saigon_hem_connectivity`.

**I3-6 — CONTRADICTION, MINOR — d2 ids use `sg_`, the mod uses `sgn_`.** d2_r3 writes `sg_nh_*`, `sg_hem`, `sg_kenh`, `sg_frontage_row`, `sg_parked_twowheelers`, and its M-C1 examples match `"om_terrain": "sg_nh"`. The implementation and d4's namespace rule use `sgn_`. A PREFIX match on `sg_nh` would silently match nothing. Resolution (owner **A6.2**): the TDD restates every d2 id with `sgn_`; M-C1 tests use `sgn_nh` PREFIX.

---

## 4. Modding boundary (d4) against the actual mod

**I4-1 — GAP, MINOR (now) / MAJOR (at B8g-2) — The `SAIGON` flag on city buildings is inert, and the whitelist will not do what the test comment expects.**
- All three city buildings carry `"flags": [ "SAIGON" ]` (`overmap/nha_ong.json`, `overmap/hem.json`, `overmap/cho.json`). City buildings are placed from the region pools by `place_building` (`src/overmap_city.cpp:268-303`), which reads only `CITY_UNIQUE`/`GLOBALLY_UNIQUE`/`OVERMAP_UNIQUE`. The feature-flag filter runs only over the random special batch in `overmap::populate` (`src/overmap.cpp:259-292`) and on region-random map extras (d4_r3 §2.1). So the flag has no effect on city buildings, today or after the whitelist.
- `region/region_settings.json` has no `feature_flag_settings`, so it inherits dda's (`blacklist: [EXTRADIMENSIONAL]`, empty whitelist, `regional_map_settings.json:44`): **every dda random special** (farms, labs, evac shelters, gas stations, military sites …) is placed in the Saigon overmap. `tests/saigon_mapgen_test.cpp:187-194` tolerates ≤ 5 dda houses "from dda overmap specials … which the SAIGON feature-flag whitelist removes in B10", while the ledger puts the whitelist in **B8g-2** (`PROGRESS.md`). Two owners are named for one change.
- Resolution (owner **B8g-2**): add `"feature_flag_settings": { "blacklist": [ "EXTRADIMENSIONAL" ], "whitelist": [ "SAIGON" ] }` together with the first Saigon *specials* (the d2 district special and, if chosen, a chợ special); put `SAIGON` on those specials (that is where it matters); keep it on city buildings only as documentation. Fix the test comment to B8g-2 and tighten `dda_houses` to 0 there. Note d4's bypasses (mission/EOC `om_special`, trailheads, forced placements) remain (I4-2).

**I4-2 — CONTRADICTION, MAJOR — d4 assumes the Saigon region does not inherit dda's extras, highways and trails; the implementation inherits all of them.**
- d4_r3 §2.1: "A Saigon region that does not inherit dda's `map_extras` collections never draws them anyway"; §8.1 plans `trails.json` (own trailheads or none), `map_extras.json` (own collections) and `highways: null`.
- `sgn_saigon` is `copy-from: default` (`region/region_settings.json:3`) and overrides only `weather` and `cities`. It therefore inherits `"highways": "default"`, `"forest_trails": "default"`, `"map_extras": "default"`, `rivers`, `lakes`, `forests` and the `connections` (`data/json/region_settings/region_settings/regional_map_settings.json:2-51`). Highways bring US interstate segments and on-ramp specials (which bypass the whitelist, `src/overmap_highway.cpp:232-237`); trailheads bypass it too (`src/overmap.cpp:2024-2030`).
- Resolution (owner **B8g-2**, with **B10** for the extras list): set `"highways": null`, `"forest_trails": null` (or own flagged trailheads), and a Saigon `region_settings_map_extras` that keeps only setting-neutral extras. Add a several-seed worldgen test (RR-D4-6) asserting no `hw_*`, no trailhead and no dda-only extra in 3 overmaps.

**I4-3 — CONTRADICTION, MINOR — Default dimension override and the conflicts list.**
- `region/dimension.json` overrides `dimension "default"` → `sgn_layout` (UNIFORM `sgn_saigon`). That is the d4 "whole region" route (`src/game.cpp:259`) and is correct.
- critic_d4_r3 calls `no_hope` in `conflicts` "a content mod … harmless". It is in fact **required**: `No_Hope/region_settings/dimensions.json` also redefines `dimension "default"`, so with both loaded the last one wins. Keep it.
- Not in `conflicts` but interacting: `railroads/region_overlay.json:3-9` patches `region_settings "default"` (`place_railroads: true`, `highways: null`) and `region_settings_city "default"` (`extend houses`). Through `copy-from: default` these patches flow into `sgn_saigon`/`sgn_city` when railroads loads first. `Magiclysm`, `DinoMod`, `MindOverMatter` extend `region_settings_city "default"` the same way; Saigon's plain `houses`/`shops` arrays drop their buildings, but their `parks` additions survive because `sgn_city` does not override `parks`.
- `MindOverMatter`/`BombasticPerks` add dimensions whose regions are `copy-from default` (New England weather generator), while the mod's same-id `weather_type`s (I4-4) apply globally.
- Resolution (owner **B8g-2**): set `place_railroads: false` explicitly in `sgn_saigon`; give `sgn_city` its own `parks` (B8e) so extensions cannot leak; add a script check "every mod that overrides `dimension default` or `weather_generator default` is in `conflicts`" (extends RR-D4-7). `conflicts` already has all 12 total conversions (critic_d4 L1 `xedra_evolved_innawoods` fixed) plus `tropicata`, `desertpack`, `ruralbiome` (d3 K4).

**I4-4 — GAP, MINOR — Same-id overrides in use, and what each one leaks.**

| Override | Where | Semantics (d4 §1.3) | Leak / risk | Resolution (owner) |
|---|---|---|---|---|
| `weather_type` `light_drizzle`, `drizzle`, `rain`, `thunder` | `region/weather.json:43-117` | replace (generic_factory) | Global: also gates rain in every other dimension (dda highland/netherum, MoM, BombasticPerks) to Saigon's wet-season afternoons. Expected for a TC, undocumented. | Document in TDD; d3 K4 (**B4a** note) |
| `item_group default_zombie_clothes` | `itemgroups/loot.json` | replace | Intended. But the chợ re-uses it for clothing-stall loot (`gen_cho.py:77`), so stall garments spawn damaged 1–4 like corpse clothes. | Own `sgn_cho_garments` group (**B8d**) |
| snippet `<male_full_name>`, `<female_full_name>`, `<given_name>` (`"override": true`) | `snippets/names.json:2-21` | override | Correct hunvre idiom. **Gap:** city names come from `region_settings_city.name_snippet` (default `<city_name>`, `src/regional_settings.cpp:581`); `sgn_city` does not set it, so Saigon cities get dda US town names. | `"name_snippet": "<sgn_city_name>"` with phường/quận-style names (**B2** or **B8g-2**) |
| `dimension default` | `region/dimension.json` | replace | See I4-3. | — |

**I4-5 — GAP, MAJOR — No blacklist or whitelist objects exist yet; d4's step order put them before content.**
- d4_r3 §8.2 step 2 (B10a: scenario/profession whitelists before B2) was skipped (critic_d4 "deviation, not a violation"). Today: no `SCENARIO_BLACKLIST`, no `profession_blacklist`, no `ITEM_BLACKLIST`, no `MIGRATION`, no monster lists. All dda scenarios (with US start locations, which now exist in the Saigon overmap via I4-1) and all dda professions and hobbies are selectable; dda parks, specials, extras and road traffic still spawn US loot, vehicles and uniforms.
- Resolution (owner **B10**, split): *(new)* **B10a** whitelists now (`SCENARIO_BLACKLIST` whitelist = `sgn_saigon_2004`; `profession_blacklist` whitelist = the 12 `sgn_*`), independent of B8; **B10b** item MIGRATION/BLACKLIST per the d4 §2.3 rule after B8g-2; currency handled as in I6-2.

**I4-6 — C++ seams across domains: see §9 for the ordering and the file-collision map.**

---

## 5. Performance budgets across domains (findings; the table is §8)

**I5-1 — CONTRADICTION, MAJOR — The per-turn budgets of d1 and d3 cannot both hold.**
- d1_r3 §6.3: ≤ 33 ms per turn for 30 moves/s = 20 ms renderer-adjacent + "≤ 13 ms of turn simulation". critic_d1 D2: the move's own redraw adds ≥ 4.8 ms, so simulation must be ≤ 8 ms (TDD-RR-D1-02).
- d3_r3 §6.4 B5a: "awake 300 costs ≤ 25 ms/turn" for `monmove` alone; B5b(ii) ≤ 2 ms dormant steady state; B6 ≤ 1 ms for 150 bikes; B5d ≤ 0.5 ms rain overhead. The d3 bubble cap is ≤ 300 awake (§6.2).
- Sum at targets: 20 + 4.8 + 25 + 2 + 1 + 0.5 = **53.3 ms ≈ 19 moves/s**, before the unbudgeted rows of I5-2. The 30 moves/s target and the 300-awake cap are mutually exclusive.
- Resolution (owner **A6.3** for the TDD decision, **R0** + *(new)* **B5-perf** for measurement): replace the single 30 moves/s target by tiers, using the consolidated table in §8. (a) **Street tier, 25 moves/s (≤ 40 ms):** ≤ 100 awake monsters in the bubble (≈ 8.3 ms if `monmove` scales linearly from d3's 25 ms/300) and critic_d1's lowered renderer targets (FOV ≤ 6 ms, lightmap ≤ 4 ms); §8 sums this to ≈ 38 ms. (b) **Horde tier, ≈ 17 moves/s (≤ 60 ms):** up to d3's 300 awake while a horde is engaged. (c) 30 moves/s holds only where ≤ ≈ 40 monsters are awake. The d3 dormant-crowd rule (density via `sgn_GROUP_ZOMBIE_DORMANT`, not awake hordes) is what makes tier (a) the normal case, so B9a must follow it strictly. P2-5 (awake governor) is the pass-2 lever if tier (a) fails measurement. TDD-RR-D1-02's exit gate becomes "p50 ≤ 40 ms on the Saigon district with ≤ 100 awake".

**I5-2 — GAP, MAJOR — Per-turn costs that no domain budgets.**
- `overmap_buffer.move_hordes()` every turn (`src/do_turn.cpp:587`; d3 §6.1 item 4); `mon_info_update()` up to 3× per turn (`src/do_turn.cpp:642,692,749`); `map::process_items` over loot and the ≤ 1,200 dormant corpses (`src/item.cpp:4452-4468`); `fill_water_collectors` over every funnel trap while raining (`src/weather.cpp:334-374`, ≤ 180 if I3-2's gutters are used); the extra full redraw and present of `FORCE_REDRAW` on non-acting turns (critic_d1 Missed 1, `src/do_turn.cpp:754-756`); R1's per-turn memorize loop (critic_d1 D2).
- Resolution (owner **R0** for instruments, **B5-perf** *(new)* for the Saigon district run): each row gets a timer and a provisional target in §8; the district benchmark sums them per turn (TDD-RR-D1-02 exit gate).

**I5-3 — GAP, MINOR — Spikes are budgeted per domain but not as events.** Bubble shift into unvisited OMTs runs mapgen per column (d2 B2: ≤ 1.25× vanilla, no absolute ms) and can trigger a whole neighbouring overmap generation (d2 §6.1 "hidden trigger"); the dormant first-load spike is ≤ 250 ms (d3 B5b); a flood activation is ≤ 20 ms (d3 B5d). Resolution (owner **A6.3**): one spike rule: ≤ 250 ms per event, never two spike events in one turn (flood activation must not coincide with a bubble shift; the 10-min EOC cadence makes this cheap to enforce by deferring one turn).

**I5-4 — GAP, MAJOR — Monster density: canon asks for "much higher" density; the implementation places no monsters at all in Saigon buildings.**
- Bible §10: "much higher human-zombie density per OMT than in dda cities … needs a spawn and performance budget from A2/A3". critic_d2 TR-D2-08 assigned it to "A2 / A3 (assign)"; d3_r3 §6.2 took it (tier table, explicit `density`, dormant crowds).
- Implementation: no `place_monsters`/`place_monster` in any Saigon mapgen (`grep -c monster` = 0 in `mapgen/nha_ong`, `hem`, `cho`, `b8e`). The Saigon oters inherit `mondensity: 2` from `generic_city_building_no_sidewalk` (`data/json/overmap/overmap_terrain/overmap_terrain.json:44`), which only matters for `place_monsters` entries without `density`, and there are none. So the only zombies are the city hordes on road OMTs (`src/overmap.cpp:3459,3479`; 960 entities at `city_size` 12 and scalar 80) plus dda specials. Shophouses, hẻm and the chợ are empty.
- Resolution (owner **B9a**): add `sgn_GROUP_ZOMBIE_DORMANT` and explicit-`density` `place_monsters` to the lot ground chunks, hẻm quadrants and the chợ per d3_r3 §6.2 tiers (rows ≤ 4 awake / ≤ 20 dormant per OMT, chợ ≤ 20 / ≤ 60). Never omit `density`: the z1..z5 oters copy `generic_city_building_roof`, which also carries `mondensity: 2`, so an implicit density would apply once per storey. Extend d2 B3 / d3 B5c to count monsters per Saigon column.

---

## 6. Canon (CONTENT_BIBLE) against content and designs

**I6-1 — CONTRADICTION, MAJOR — A New England newspaper in a Saigon kit.** `sgn_xe_om` starts with `newest_newspaper` (`professions/professions.json`), whose dda description reads "one of the last issues printed before New England was overwhelmed" (`data/json/items/newspaper.json:393`). The mod already has `sgn_newspaper` ("Tin Nhanh Sài Gòn", B7b). Resolution (owner **B3.R**): swap it.

**I6-2 — CONTRADICTION, MAJOR — Every profession starts with US dollars and a credit card.** All 12 professions include `starter_wallet_full` (`professions/professions.json`), a dda collection of `credit_card` plus `banknotes` (`money_one` … `money_fifty`, "featuring a portrait of George Washington", `data/json/items/generic/currency.json:235-236`) and `coins` (`data/json/itemgroups/Clothing_Gear/wallets.json:259-291`). Bible §1 and §6: Đồng notes and gold chỉ/lượng; in 2004 a street vendor would not carry a credit card. Resolution (owner **B5e** for items, **B10b** for the rule): add `sgn_dong_*` notes and `sgn_vang_chi`, a `sgn_wallet` group, and use it in all professions. Per d4 §2.3, do **not** MIGRATE `money_*` globally (dda shops and NPC trade construct them); replace the group references instead, or same-id override `banknotes`/`coins` (both are plain item groups).

**I6-3 — CONTRADICTION, MINOR — Profession kits that drift from Bible §4.** `sgn_cong_an` has melee/bashing skills and a baton but no pistol (Bible: "melee 2, pistol 2 … pistol and limited ammo, radio"); `sgn_nurse` has no scrubs and carries dda `manual_first_aid` although `sgn_book_nursing` exists; `sgn_veteran` lacks the medal; `sgn_student` has the dda bicycle (I2-6). The pistol omission may be deliberate (tone), but it is not recorded. Resolution (owner **B3.R**): either amend the Bible table or the kits; record the decision.

**I6-4 — GAP, MAJOR — US content still reachable in a Saigon world.** Through I2-2 (dda road traffic), I4-1 (all dda random specials), I4-2 (highways, trailheads, dda map extras including the `build` extras collection that every Saigon oter inherits via `"extras": "build"`, `overmap_terrain.json:43`), I4-5 (dda scenarios and professions), and the dda monster roster (zombie cops and soldiers in US gear; B9a). Resolution: owners as listed in those findings; B10 closes the residue with the d4 §2.3 rule.

**I6-5 — CONTRADICTION, MINOR — Canon details the content gets right but the designs or recipes miss.** Iced drinks without ice (I3-3); the chợ has no ice, fish smell or crowd draw (Bible §3 "it smells and draws zombies"; needs B9a groups and a scent/field source); "iron accordion gates … loud, slow entries" are `t_rdoor_c` (a plain `DOOR` with `open`, `data/json/furniture_and_terrain/terrain-doors.json:1605-1618`), so entries are neither loud nor slow (critic_d2 Missed 2). Resolution (owner **B8a**): a `t_sgn_cua_sat_keo` gate terrain (copy-from a metal door, with lock, a long `open` time via `examine_action` or a two-step open, and noise on bash); (owner **B5b-2**) ice.

**Canon checks that pass.** Period and premise (scenario text, `scenario/scenarios.json`); no wartime setting (the veteran's description refers to a war "that ended thirty years ago", allowed by Bible tone rule); no trademarks (scan for real brands and media names: none); English prose with diacritic Vietnamese terms throughout; climate start in the dry season (scenario `winter` + `sgn_wet`); Southern naming order and frequencies (`snippets/names.json`).

---

## 7. Implementation bugs the domain critics could not see

**I7-1 — BUG, MAJOR — The hẻm block, the chợ and the chùa have no roof level.**
- `sgn_hem_block_1` (`overmap/hem.json`), `sgn_cho_1` (`overmap/cho.json`) and `sgn_chua_1` (`overmap/chua_chungcu.json`, committed in `461916d7aa`; `tools/saigon/gen_b8e.py:228-229`) list only z0 cells. CDDA does not auto-roof buildings: `map::actualize`'s top-level fill only roofs `TREE` and `NATURAL_UNDERGROUND` terrain (`src/map.cpp:9913-9937`); vanilla buildings ship explicit `_roof` oters. The z1 OMT above is therefore `open_air`.
- Effects: `build_sunlight_cache` sees no floor at z1 and lights every "indoor" tile with full daylight (`src/lightmap.cpp:409-425`), contradicting d1's indoor `inside_light_level` assumption and making nights/days identical inside homes; the interiors are visible from the z1+ windows and z3 walks of neighbouring rows and chung cư; nothing stops a future rooftop route from dropping into a home. (`t_thconc_floor` keeps `INDOORS`, so rain does not wet the player; the defect is lighting, visibility and verticality.)
- d2_r3 §4.c explicitly specified "a z = 1 roof stack sits above it" for the chợ.
- Resolution (owners **B8c** for hẻm, **B8d** for chợ, **B8e** for chùa): add a z1 roof oter per building (copy-from `generic_city_building_roof`) whose mapgen puts `t_concrete_roof` (or a tin-roof terrain) over every non-alley tile and `t_open_air` over the alleys and courtyards; add to each structure test: "every `INDOORS` z0 tile has a non-`NO_FLOOR` tile above".

**I7-2 — BUG, MINOR — Lot 5's furniture is erased by the east end cap, and its loot is left inside the wall.**
- The cap `sgn_nh_cap_wall` (x = 23, rows 2–19, z0–z3; `gen_nha_ong.py:138-143`, `:186`) runs with `ERASE_FURNITURE_BEFORE_PLACING_TERRAIN` and `ALLOW_TERRAIN_UNDER_ITEMS` (`:22-23`). Lot chunks still place furniture with item spawns on lx = 3: beds `b` (z0 row 17 in all three ground variants; z1/z2 rental rows 3, 5), racks `m` (moto rows 4–5), dresser `d` (z1/z2 family row 18), toilet `T` (z1/z2 row 16), and doors on lx = 3 (family rows 6, 15). In lot 5 the furniture vanishes and its `sgn_shophouse_living`/`sgn_moto_shop` items stay on a `t_brick_wall` tile.
- critic_d2 D3 asked to move *all* per-lot fixtures off lx = 3; only the tank was moved (`:97`).
- Resolution (owner **B8b-2**): shift those fixtures to lx ≤ 2 in `GROUND`/`FLOOR`, or give end roles a dedicated lot-5 chunk set. Test: no item on any `t_brick_wall` tile; every lot has a toilet on z1.

**I7-3 — BUG, MINOR — Chợ doors open onto stall counters.** The office door (5, 6) and the ice-store door (41, 6) (`gen_cho.py:46`, `:54`) face the first produce stall row at y = 7–8 (`zone_rows` `( 7, 'P' )`, `:29`; stall columns 3–6 and 39–42). Both doorways are blocked by `f_counter`. Resolution (owner **B8d**): skip stall blocks whose x-range contains a door column on row 7, or move the doors to x = 8 and x = 44.

**I7-4 — BUG, MINOR — Chợ placement contract drifts from d2.** d2_r3 §4.c: `CITY_UNIQUE` with `city_sizes: [8, -1]` (near the centre) plus a non-unique fallback, and a roof. Committed: no flags beyond `SAIGON`, no `city_sizes`, weight 8 (`region/region_settings.json`), commit message "~9 markets per overmap". Nine markets per overmap is plausible for Saigon, but it is a design change, not recorded in d2 or the ledger. The `sgn_sloc_cho` start location now depends on a chợ existing near the start city; whether start-location search fails gracefully when none is found is UNVERIFIED. Resolution (owner **B8d**): record the decision; add a test that 20 seeds of overmap (0,0) each contain ≥ 1 `sgn_cho_*` cell, or keep `sgn_sloc_cho` out of the scenario's default start.

**I7-5 — BUG, MINOR — Structure tests do not test what d2's critic required.** `saigon_nha_ong_row_structure` (`tests/saigon_mapgen_test.cpp:92-153`): the z3 BFS treats `t_railing` as walkable (critic_d2 D6a), never asserts the cap tiles, never asserts same-lot landing (D1) or that every `t_stairs_down` has a `t_stairs_up` below, and would not catch I7-2. `saigon_cities_use_shophouses` (`:155-195`) checks dda *houses* only; after the shops pool swap it should assert 0 dda shop ids. `saigon_monsoon_climate` keeps `min > 5` (critic_d3 K1: B4b must tighten to ≥ 18 / ≤ 40). Resolution (owners **B8b-2**, **B8g-2**, **B4b**).

**I7-6 — BUG, MINOR — Recipes.** `sgn_moto_tank_4l` (`recipes/vehicle_parts.json`): 6 `sheet_metal_small` with hammer and saw, no welding, while dda's 2 L `metal_tank_little` needs `welding_standard` 30 and metalworking proficiencies (`data/json/recipes/tools/containers.json:66-77`): an easier route to a watertight fuel tank. `sgn_engine_110cc_item` converts any `1cyl_combustion` plus 4 scrap into the 110 cc engine with only WRENCH/SCREW: a relabel (R4 "name swap" risk). The two iced drinks have no ice (I3-3). Resolution (owner **B5d**): add `welding_standard` (or a soldering alternative) to the tank; make the engine recipe a disassemble/rebuild with real parts or drop it until P2; ice per B5b-2.

**I7-7 — BUG, MINOR — `looks_like` missing on 16 standalone items.** `copy-from` implies `looks_like` for items, furniture and vehicle parts (`src/item_factory.cpp:4616-4618`, `src/mapdata.cpp:1206`, `src/veh_type.cpp:230-244`), but the 15 standalone comestibles in `items/food/*.json` (e.g. `sgn_pho_bo`, `sgn_nuoc_mam`, `sgn_durian`) and `sgn_thung_xop` (`items/gear/gear.json`) have neither. d1_r3 §7 rule 3 requires a chain to a vanilla id. Resolution (owner **B5** follow-up): add `looks_like` (e.g. `sgn_pho_bo` → `soup_meat`, `sgn_thung_xop` → `styrofoam_cup`, the nearest vanilla polystyrene sprite).

**I7-8 — BUG, MINOR — Ledger inconsistencies.** `PROGRESS.md` lists `B8a shared palettes` as `todo` and also `B8a shared palettes + B8b-1` as done; in fact each building has its own palette (`sgn_nhaong`, `sgn_hem`, `sgn_cho`, `sgn_chua`, `sgn_chungcu`) and nothing is shared, which is exactly why I3-1's terrain ids diverged. The test comment (I4-1) names B10 for the whitelist while the ledger names B8g-2. Resolution (owner **B8a**): make B8a a real unit: one `sgn_common` palette with the flood-aware ground ids, the gate terrain, the altar and the lighting rule, used by every generator.

**Checked and correct.** C6 hunks (`git diff fe6a10c2b1 -- src/`): `game_ui::init_ui` test-mode branch and the `#if defined(TILES)` guard on the check-mods options re-init match d4_r3 §4.3 exactly. The generators reproduce the committed JSON byte-for-byte in content. Stairs line up for every lot-height combination. Hẻm ports and quadrants are rotation-invariant and the café courtyard opens onto its arm (`gen_hem.py:40-51`). The underbone, xe tay ga, xe đạp and xích lô all satisfy d2's 3-tile footprint. Weather gates match the test window (`sgn_wet` `< 253`, `tests/saigon_weather_test.cpp:40` `<= 252`). The chung cư has a roof level, alternating stair columns and filled tanks.

---

## 8. Consolidated per-turn performance budget

Scenario: one avatar move (speed 100, so one move = one turn) while auto-moving along a dense Saigon street at dusk in light rain, bubble ≈ 30 OMT (132 × 132 tiles, `src/map_scale_constants.h:11,16`), max populated z = 5. Every figure is a **target** unless marked measured; all targets are UNVERIFIED until the named instrument runs on the B8g-2 district. "Tier a" / "tier b" refer to I5-1.

### 8.1 Per-turn CPU (main thread)

| # | Stage | Source | Original target | Tier a (street, 25 moves/s) | Tier b (horde, ≈ 18 moves/s) | Instrument / owner |
|---|---|---|---|---|---|---|
| 1 | FOV `build_seen_cache` (`cast_zlight`) | d1_r3 §6.3; measured synthetic 6.9–19.2 ms (§6.1) | ≤ 8 ms | ≤ 6 ms | ≤ 8 ms | `[seen_cache][saigon]` — R0 |
| 2 | `generate_lightmap` = F + N·c; F includes `build_sunlight_cache` from z6 down (I1-5) | d1_r3 §6.3, §7; critic_d1 m7 | ≤ 5 ms (F ≈ 2, N ≤ 40, c ≈ 75 µs) | ≤ 4 ms (N ≤ 26 at c = 75 µs) | ≤ 5 ms | `[lightmap][saigon]` 0/16/32/64 at dusk — R0 |
| 3 | `update_visibility_cache` (downward recursion, ≤ 11 levels) | d1_r3 §6.3 | ≤ 3 ms | ≤ 3 ms | ≤ 3 ms | timer `uvc` — R0 |
| 4 | Draw-point generation / R1 snapshot (C·Z̄ ≈ 3–8k cells) | d1_r3 §6.3 | ≤ 4 ms | ≤ 4 ms | ≤ 4 ms | timer `snapshot` — R0 |
| 5 | The move's own redraw: per-frame rows (bmc 0.3 + emission 2.5 + ImGui 2) | critic_d1 D2 | not counted | ≥ 4.8 ms | ≥ 4.8 ms | timers `bmc_frame`, `emit`, `imgui_ui` — R0 |
| 6 | Memorize loop (≤ 14,641 calls; per frame today, per turn after R1) | d1_r3 §6.2; critic_d1 D2 | none | ≤ 1 ms (proposed) | ≤ 1 ms | counter `memorize_calls` — R0 |
| 7 | Present on auto-repeat (vsync) | d1_r3 §6.3; critic_d1 Missed 1 (`FORCE_REDRAW`) | 0 coalesced / ≤ 16.7 unpaced | 0 (coalesced) | 0 (coalesced) | present-duration timer — R0 |
| | **Renderer-adjacent subtotal** | | 20 (+4.8 omitted) | **22.8 ms** | **25.8 ms** | |
| 8 | `monmove` (awake, materialised) | d3_r3 §6.2, B5a | ≤ 25 ms @ 300 | ≤ 8.3 ms @ ≤ 100 (linear, UNVERIFIED) | ≤ 25 ms @ 300 | B5a — B5-perf *(new)* |
| 9 | Dormant crowd steady state (`process_items` over corpses + traps) | d3_r3 B5b(ii) | ≤ 2 ms @ 1,200 | ≤ 2 ms | ≤ 2 ms | B5b — B5-perf |
| 10 | Vehicles: `vehmove` + `do_vehicle_caching` (no dirty gate, `src/map.cpp:10819-10821`) | d2_r3 §6.3; d3_r3 §5.f, B6 | ≤ 1 ms @ 150 | ≤ 1 ms (≤ 90 frontage + ≤ 60 road, I2-2) | ≤ 1 ms | B6 / d2 B3 — B6d |
| 11 | Weather: `update_weather` + `handle_weather_effects` + `update_bodytemp`, rain | d3_r3 §1.4, B5d | ≤ 0.5 ms | ≤ 0.5 ms | ≤ 0.5 ms | B5d — B4b |
| 12 | Funnel/gutter visits while raining (≤ 1 per lot, ≤ 180 per bubble) | I3-2 (new) | none | ≤ 0.2 ms | ≤ 0.2 ms | extend B5d — B5f *(new)* |
| 13 | `move_hordes` + `mon_info_update` ×3 + loot `process_items` | I5-2 (new) | none | ≤ 2 ms (proposed) | ≤ 3 ms | new timers — B5-perf |
| 14 | `build_map_cache( levz, skip_lightmap )` in `do_turn` (`src/do_turn.cpp:739`) dirty scans | d2_r3 §6.3 | none | ≤ 0.5 ms (proposed) | ≤ 0.5 ms | d2 B3 — R0 |
| 15 | Other simulation (fields, scent decay in rain over 17,424 ints, player) | d3_r3 §1.3–1.4 | "≤ 13 ms remainder" (d1), unsourced | ≤ 1 ms | ≤ 1 ms | existing profiling — B5-perf |
| | **Simulation subtotal** | | | **15.5 ms** | **33.2 ms** | |
| | **Total per turn** | | "≤ 33 ms" (d1; does not close, critic_d1 D2) | **≈ 38.3 ms ⇒ ≥ 26 moves/s** | **≈ 59 ms ⇒ ≈ 17 moves/s** | district run, p50 and p95 — R0 exit gate |

Notes: (i) Tier a closes under 40 ms with ≈ 1.7 ms headroom; any row over target must be paid for elsewhere. (ii) Today's implementation sits far below these rows (0 emitters, 0 vehicles, 0 mapgen monsters), so current playtests will look fast; the budget bites when B6d, B8b-2 lighting and B9a land. (iii) At 30 moves/s (33.3 ms) the simulation subtotal must be ≤ 10.5 ms, i.e. ≈ 40 awake monsters.

### 8.2 Per-bubble entity budgets (the inputs to 8.1)

| Entity | Budget | Source | Enforced by |
|---|---|---|---|
| Light emitters | ≤ 40 per bubble at d1's 5 ms lightmap target: ≤ 1 lit fixture per OMT mean (≤ 0.8 to respect the 36-OMT touch bound), ≈ 10 dynamic. **≤ 26 if tier a's 4 ms target is adopted: fixtures ≤ 0.5 per OMT** | d1_r3 §6.3/§7; critic_d1 m7; I1-1 | B8a lint; R0 re-derives N_max |
| Coloured emitters | z0 street-facing only until R1 | I1-2 | B8a rule |
| Vehicles | ≤ 150: frontage ≤ 6 per row OMT (mean 3) ≈ 45–90; road ≤ 60 (≈ ≤ 6 per road OMT) | d2_r3 §4.f/§6.3; d3_r3 §5.f; I2-2 | `saigon_frontage_parking_safe`; road-chunk test (B6d) |
| Awake monsters | tier a ≤ 100; tier b ≤ 300 | d3_r3 §6.2; I5-1 | B9a explicit `density`; B5c count |
| Dormant monsters | ≤ 1,200 (first-load spike ≤ 250 ms) | d3_r3 §6.2, B5b | B9a |
| Funnel traps | ≤ 180 (1 per lot) | I3-2 | B5f |
| Populated z-levels | z0..z5 (sunlight starts z6) | d2_r3 §6.3; I1-5 | B8b-2 (h5 weight) |
| Nests per mapgen level | ≤ 18 (d2 estimate); implemented: nhà ống 13–14 (6 lot + 6 z-chunk + 1–2 caps), hẻm 8 (4 quadrants + 4 ports), chợ 0 | d2_r3 §6.2; this audit | d2 B2 static nest count |
| Items per column | ≤ 2× vanilla downtown | d2_r3 §6.4 B2 | B2 |

### 8.3 Spike events (not per turn)

| Event | Budget | Source |
|---|---|---|
| Bubble shift into unvisited OMTs (mapgen per column, 6 non-uniform levels) | ≤ 1.25× vanilla downtown per column; proposed absolute ≤ 250 ms per shift | d2_r3 §6.2/§6.4 B2; I5-3 |
| Neighbouring overmap generation triggered by mapgen look-ups | ≤ 1.5× vanilla (B1); unavoidable once per overmap | d2_r3 §6.1 |
| Dormant pseudo-monster conversion on first load | ≤ 250 ms total | d3_r3 B5b(i) |
| Flood toggle activation (14,641-tile transform) | ≤ 20 ms; never in the same turn as a bubble shift | d3_r3 §4.3, B5d; I5-3 |
| Weather regeneration | ≈ 0 (amortised over ≥ 300 turns) | d3_r3 §1.4 |

---

## 9. C++ seam ordering and file-collision map

### 9.1 Inventory of proposed seams (all domains)

| Seam | Domain / unit | Pass | Files and functions touched |
|---|---|---|---|
| C6 (landed) | d4 | 1 | `src/game.cpp` `game_ui::init_ui` (HEAD `:549-559`); `src/main.cpp` `initialize_interface` (HEAD `:777-784`) |
| C2 clean `--check-mods` failure | d4 | 1 (tooling) | `src/game_io.cpp` `check_mod_data` catch (`:187-210`) |
| C1 `vehicle_group` override/delete | d4 | 1, optional | `src/vehicle_group.cpp` `VehicleGroup::load` (`:80-87`); uses `src/weighted_list.h:64,86-100`; `doc/JSON/VEHICLES_JSON.md` |
| C3 `vi` language | d4 | 2 | `src/options.cpp` language array (`:1365-1392`) |
| C4 / C5 | d4 | optional | `src/item_factory.cpp:1670-1674`; `src/init.cpp:943-946` |
| M-C1 rotation-aware neighbour predicate | d2 | 1 | `src/mapgen.cpp` `neighbor_oter_check` load + `test` (`:3569-3621`); reads `src/mapgendata.h:186,244-245`, `src/overmap_terrain.cpp:851-863`; `doc/JSON/MAPGEN.md` |
| I1 nest counter (optional) | d2 | 1, optional | `src/mapgen.cpp` `mapgen_function_json_nested::nest` (`:6380`) |
| P2.0 vanilla worldgen fixes | d2 | 2 | `src/regional_settings.cpp:464-472,806-810`; `src/overmap_city.cpp:204,235-278`; `src/savegame.cpp:924-927` |
| B4b monthly climate, water temperature, rain intensity, funnels | d3 | 1 | `src/weather_gen.h:28-85`; `src/weather_gen.cpp` load (`:389-409`), temperature/humidity (`:38,42,145-152,184-205`), conditions dialogue (`:248`), `get_water_temperature` (`:301-330`); `src/weather.cpp` back-fill (`:192-250`), funnel rate (`:283-307`), `fill_funnels`/`fill_water_collectors` (`:334-374`), intensity cap (`:444-452`) |
| Tank refill C++ (I3-2 option) | this audit | 1 follow-up | `src/weather.cpp` `fill_funnels` (`:334-366`) |
| B4c humidity-limited sweat | d3 | 1 | `src/character_body.cpp` (`:191`, bodytemp path); `src/options.cpp` (new `HUMID_SWEAT_MODEL`) |
| F-drain loader revert | d3 | 1 | `src/map.cpp` `map::actualize` (`:9822-9884`); new terrain flag in `src/mapdata.h`/`src/mapdata.cpp` (flag enum, `transforms_into` at `:1380`) |
| P2-0 weather passive-effect early return | d3 | 2 (trivial) | `src/weather.cpp:484` |
| P2-3 `flood_manager` | d3 | 2 | `src/weather.h`, `src/weather.cpp` `update_weather` (`:1076`); lazy apply in `map::loadn` (`src/map.cpp`, near `:9328-9335`) |
| P2-5 awake-monster governor | d3 | 2 | `src/do_turn.cpp` `monmove` (`:279-360`); `src/options.cpp` (`MONSTER_THINK_RADIUS`) |
| P2-4/P2-6 two-wheeler and boat physics | d3 | 2 | `src/vehicle_move.cpp` (`:1606-1611`, `:2262-2276`), `src/vehicle.cpp` |
| R0 measurement harness | d1 | 1→2 (gate) | timers in `src/cata_tiles.cpp` (`:588,1589,2711`), `src/cata_shader.cpp:761`, `src/sdltiles.cpp` (`:980,1038`), `src/map.cpp` `build_map_cache` (`:10804`), `src/lightmap.cpp` `generate_lightmap` (`:503`) / `build_seen_cache` (`:1264`); `src/options.cpp` (`RENDER_BACKEND`); tests |
| R1 snapshot + stale-colour fix | d1 | 2 | `src/lightmap.cpp` (`:503-546`, fix a), `src/map.cpp` `invalidate_map_cache` (`:513-522`), `src/level_cache.h` (`colour_stale`/epoch), `src/do_turn.cpp` (`:607-610`, epoch bump), `src/game.cpp` `game::draw` (`:3380-3382`), `src/cata_tiles.cpp` (builders) |

### 9.2 File-collision map

| File | Seams touching it | Same function? | Risk | Rule |
|---|---|---|---|---|
| `src/weather.cpp` | B4b (funnels, back-fill, intensity), tank refill, P2-0, P2-3 | **Yes**: B4b and tank refill both edit `fill_funnels` (`:334-366`) | High (semantic: the funnel rate fix and tank credit must agree on charges/turn) | B4b first; tank refill as a B4b follow-up in the same file, re-running B4b's live-vs-back-fill test; P2-0 any time after; P2-3 last |
| `src/weather_gen.cpp` / `.h` | B4b only | — | Low | — |
| `src/map.cpp` | F-drain (`actualize`), R0 (`build_map_cache` timer), R1 (`invalidate_map_cache`), P2-3 (`loadn`) | No, but `actualize`/`loadn` are adjacent and P2-3 generalises F-drain | Medium (upstream churn factor 32, critic_d1 m4) | F-drain lands as the hook P2-3 later extends (same flag, same loop); R0 timers as one-line macros; R1 last |
| `src/lightmap.cpp` | R0 (timers), R1 (fix a at top of `generate_lightmap`) | **Yes** (`generate_lightmap`) | Low (same domain) | R0 then R1 |
| `src/options.cpp` | B4c (`HUMID_SWEAT_MODEL`), R0/R1 (`RENDER_BACKEND`), C3 (language array), P2-5 (`MONSTER_THINK_RADIUS`) | No (different `add_options_*` blocks) | Medium (parallel branches conflict on adjacent inserts) | Serialise option additions; one option per commit |
| `src/do_turn.cpp` | R1 (epoch after `:607-610`), P2-5 (`monmove`) | No | Low | — |
| `src/game.cpp` | C6 (`init_ui`), R1 (`game::draw`) | No | Low; C6 must survive every upstream merge (RR-D4-2) | `check_mod.sh dda` after each merge |
| `src/mapgen.cpp` | M-C1 (`neighbor_oter_check`), optional nest counter (`nest`) | No | Low | M-C1 alone in pass 1 |
| `src/mapdata.h` / `.cpp` | F-drain flag | — | Low | Use an enum flag (critic_d3 D-m2) |
| `src/character_body.cpp` | B4c only | — | Low | — |
| `src/vehicle_group.cpp` | C1 only | — | Low | — |
| `src/game_io.cpp` | C2 only | — | Low | — |
| `tests/saigon_*_test.cpp` | B4b, B4c, B4d, B6d, B8x, R0 `[saigon]` benchmarks | — | Low; keep `[.]` perf cases separate in `tests/saigon_perf_test.cpp` | — |

No two domains edit the same function **except** B4b × tank refill (`fill_funnels`) and R0 × R1 (`generate_lightmap`, same domain). `src/map.cpp` and `src/options.cpp` are the multi-domain hot files.

### 9.3 Proposed ordering

1. **C2** (tooling; protects every later unit's gate). Independent of everything.
2. **B4b** (blocks B4c, all heat tuning, I3-4 water temperature for B8f/B4d, and the tank-refill option). In parallel, on disjoint files: **M-C1** (blocks B8b-2 cross-building roofs, hẻm rear-facing ports and the district special).
3. **B4c** (after B4b, with the fixed `humid_sweat_efficiency` test, critic_d3 K13). In parallel: **F-drain** together with the B4d flood JSON (needs I3-1's terrain ids from B8a).
4. **Tank refill** (only if the JSON gutter route of I3-2 is rejected): after B4b, same file.
5. **R0** after B4b and F-drain, so its `[saigon]` benchmarks measure the pass-1 per-turn pipeline that ships, on the B8g-2 district with B6d traffic and B9a monsters present (the §8 exit gate).
6. **C1** only if B6d routes (a)/(c)/(d) leave measurable dda traffic.
7. Pass 2: **P2-0** (trivial), **R1** (needs R0), **P2-5** (if §8 tier a fails), **P2-3** (extends F-drain), **P2.0** worldgen fixes, **C3** with the `vi` pass, P2-4/P2-6 vehicle physics.

---

## 10. Resolution list for TDD and Part B

Ordered by when the owner unit runs. *(new)* = a sub-unit this audit proposes for `PROGRESS.md`. Severity is that of the source finding.

1. **B8a** (MAJOR, I7-8, I3-1, I1-1, I1-2, I6-5): turn B8a into a real shared palette `sgn_common` used by every generator, containing `t_sgn_hem_low`/`t_sgn_sidewalk_low` and their flooded twins with `transforms_into`, the cửa sắt kéo gate terrain, the altar (never an emitter), and the lighting rule (≤ 1 lit fixture per OMT mean, ≤ 0.5 under tier a; colour only on z0 street-facing fixtures until R1). Add a `tools/saigon/` lint for emitters per column.
2. **B8c / B8d / B8e** (MAJOR, I7-1): add a z1 roof oter and mapgen to `sgn_hem_block_1`, `sgn_cho_1` and `sgn_chua_1`; add the "every INDOORS z0 tile has a floor above" assertion to each structure test.
3. **B8c** (MAJOR, I3-1): switch hẻm alley/courtyard ground to `t_sgn_hem_low`; **B8f** (MINOR, I3-5) adds `sgn_kenh` to the hẻm port list.
4. **B8d** (MINOR, I7-3, I7-4, I4-4): unblock the two chợ doors; record the 9-markets/no-`CITY_UNIQUE` decision in the TDD; own `sgn_cho_garments` group; test that a chợ exists for `sgn_sloc_cho`.
5. **B8b-2** (MAJOR, I1-4, I2-1, I7-2, I7-5, I3-1, I3-2): role oters `endw/mid/ende/pair` and `sgn_nhaong_row_2/3`, `pair_1x2`; move all lot fixtures off lx = 3 (or end-role lot-5 chunks); the `sgn_frontage_row` chunk with `sgn_vg_parked_twowheelers`; rear strip and frontage on the low-ground ids; one gutter funnel per lot (with B5f); tests `saigon_rooftop_walkability` 1–5 with the D6a walk-surface definition, cap-tile and same-lot-landing assertions, and "no item on a wall tile".
6. **B6d** (MAJOR, I2-1, I2-3, I2-4): `sgn_vg_parked_twowheelers` = underbone 70 / xe tay ga 15 / xe đạp 15; ba gác only on roads or the rear strip (mount y ∈ {21, 22}); static footprint test over every frontage group; `hem_underbone_turns_at_spine`; CI grep group-id ≠ prototype-id.
7. *(new)* **B6d-2 road traffic** (MAJOR, I2-2, I2-7, I6-4): d4 route (c) for the 8 dda nested road/bridge vehicle ids at weight 1,000,000 with `sgn_vg_street_traffic` (required at least for every chunk that places `semi_truck`, `truck_trailer`, `4x4_car`, `small_cars_only`, `back_alley` or `food_trucks`); keep the uncommitted route-(d) dilution only where route (c) does not reach; route (d) dilution for `parkinglot`/`crashed_helicopters` if still reachable; ≤ 60 road vehicles per bubble; Saigon road chunks use `t_sgn_sidewalk_low`.
8. **B6a follow-up** (MINOR, I2-5): xe tay ga engine power ≤ underbone, or relabel as 125 cc.
9. **B3.R** (MAJOR/MINOR, I6-1, I6-3, I2-6): `newest_newspaper` → `sgn_newspaper`; student → `sgn_veh_xe_dap`; nurse → `sgn_book_nursing` + scrubs; record the công an pistol decision (amend Bible or kit).
10. **B5e** with **B10b** (MAJOR, I6-2): `sgn_dong_*` notes, `sgn_vang_chi`, a `sgn_wallet` group in every profession; no global MIGRATION of `money_*`.
11. *(new)* **B5b-2 ice** (MINOR, I3-3, I6-5): ice block item, spawned in the chợ coolers; optional ice component for cà phê sữa đá and trà đá; `ice_lifetime_in_cooler` test; check mapgen spawn temperature of frozen items (UNVERIFIED).
12. *(new)* **B5f collectors** (MAJOR, I3-2): d3 §4.3 `sgn_tr_roof_gutter`/`sgn_tr_tarp_catch` traps plus a funnel-container jar; placed by B8b-2 next to each tank; rain-fill test.
13. **B5d** (MINOR, I7-6): welding on `sgn_moto_tank_4l`; rework or drop the engine relabel recipe.
14. **B5 follow-up** (MINOR, I7-7): `looks_like` on the 16 standalone items.
15. **B4b** (MAJOR, I3-4, I7-5, §9): as d3_r3 §2.5, including the water-temperature curve; tighten `saigon_monsoon_climate` to min ≥ 18 / max ≤ 40; if I3-2's C++ option is chosen, the tank credit in `fill_funnels` follows B4b in the same file.
16. *(new)* **B4d flood toggle** (MAJOR, I3-1, I3-4): d3_r3 §4.3 EOCs and transforms against the B8a ids; gated on B4b's water temperature; `saigon_flood_toggle` on a generated `sgn_hem_block`; with **F-drain** C++ per §9.3 step 3.
17. **B4c** (per critic_d3 K13): only after B4b, with the fixed test.
18. **B9a** (MAJOR, I5-4, I5-1, I6-4, I6-5): `sgn_GROUP_ZOMBIE_DORMANT`; explicit-`density` `place_monsters` in lot ground chunks, hẻm quadrants and the chợ per d3 §6.2 tiers; never implicit density on z1..z5; reflavoured zombie variants replacing US-uniformed ones; a chợ smell source.
19. *(new)* **B10a whitelists now** (MAJOR, I4-5): `SCENARIO_BLACKLIST` whitelist `sgn_saigon_2004`, `profession_blacklist` whitelist of the 12 `sgn_*` professions (and hobby policy).
20. **B8g-2** (MAJOR, I4-1, I4-2, I4-3, I4-4): `feature_flag_settings` whitelist `SAIGON` with the first Saigon specials carrying the flag; `highways: null`, `forest_trails: null` (or own trailheads), Saigon `map_extras`, `place_railroads: false`, own `parks` (landing in B8e), `name_snippet` `<sgn_city_name>`; tighten `saigon_cities_use_shophouses` to 0 dda houses and 0 dda shops; several-seed worldgen check for `hw_*`, trailheads and dda extras; conflicts script for `dimension default` / `weather_generator default` overriders.
21. **B10b** (MAJOR, I6-4): d4 §2.3 MIGRATION/BLACKLIST/reskin pass over whatever dda content is still reachable after items 7, 19, 20.
22. **M-C1** (MAJOR via I1-4; I3-6): rotation-aware neighbour predicate with critic_d2 D9 semantics; every example and test uses `sgn_` ids.
23. **C2** (critic_d4 D1): function-scoped `failed`; the P1 two-mod test.
24. *(new)* **B5-perf** with **R0** (MAJOR, I5-1, I5-2, I5-3, I1-5, TDD-RR-D1-02/04): `tests/saigon_perf_test.cpp` on the B8g-2 district with B6d/B9a content: every row of §8.1 timed per turn, p50/p95; F measured at dusk with coloured weather and max populated z = 5; exit gate p50 ≤ 40 ms with ≤ 100 awake (tier a).
25. **R0** (MINOR, I1-3): run `[lightmap][saigon]`/`[seen_cache][saigon]` on real `sgn_nh_*` stacks (rear-alley edge at z3 as the roof spot); keep the synthetic atrium only for `[lightmap][multiz]`.
26. **R1** (MAJOR via I1-2; TDD-RR-D1-01): epoch-keyed fix (a) with `[lightmap][multiz]` steps 7–8 before any z ≥ 1 coloured light is allowed.
27. **A6.2 / A6.3 TDD** (all): restate d2 ids as `sgn_` (I3-6); copy the d1 emitter rule into the mapgen chapter (I1-1); replace "≤ 33 ms / 30 moves/s" by the §8 tiers (I5-1); adopt the §8.3 spike rule (I5-3); record I4-4's global weather-type leak and I4-3's `no_hope` rationale; put §9.2 into the merge-maintenance section; register every MAJOR above with its owner.

