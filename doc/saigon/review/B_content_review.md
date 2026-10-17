# D3 content review: B2 to B9 (closes B2.R to B9.R)

Reviewer: D3 content review, read-only. Date: 2026-10-17.
Scope: the **committed** tree at `HEAD` (`c5bd1b3c40`, branch `saigon/pass1-vertical-slice`), read with
`git show HEAD:<path>` / `git archive HEAD`. Uncommitted NPC, monster and map-extra edits by other agents are
not reviewed here. Canon: `doc/saigon/CONTENT_BIBLE.md`.

Method notes.
- A read-only script indexed every id in `data/json` plus the committed mod and resolved every item, item group,
  `copy-from`, recipe component, mapgen item/group and monster/monster-group reference in the mod.
  Result: **0 unresolved references**. The findings below are about what the content says and does, not about
  dangling ids.
- Every `tools/saigon/gen_*.py` was re-run on a scratch copy of `HEAD`. Its output is **semantically identical** to
  the committed JSON, so the generated mapgen files and their generators are in sync. (`gen_road_traffic.py` was not
  re-run because it reads `data/json` at a relative path the scratch copy did not have.)
- Line numbers refer to the committed files.

## Summary verdicts

| Group | Verdict |
|---|---|
| B2 setting and story | Good, period-true writing, but most of the story content is never seen: radio snippets are unused, the loudspeaker is inert, and the intro is one popup. A real brand name appears in a lore note and in the scenario title. |
| B3 professions | Sound skills and points. The kits use generic dda items where the mod has its own; the công an has no uniform; the street vendor cannot cook her own dishes. |
| B4 climate | Climate curves are well researched and tested. The flood mechanic has a drain bug that leaves flooded streets behind, and it floods too much. |
| B5 items, food, recipes, loot | Broad, well-written and authentic, with correct macros. Ice, the bible's key chợ resource, does not exist. Gold has an exploitable price split, food prices are inflated, and there are a few anachronisms and brand names. |
| B6 vehicles | Good. The right fleet, 99 % dilution of dda groups, sensible part stats. A few small geometry and power issues. |
| B7 books and media | Good flavour (wuxia, lịch bloc proverbs, nhạc vàng). Weak hooks: only 2 of 7 skill books teach any recipe, and the cookbook teaches only 3 dishes. |
| B8 mapgen | Strong structure: lot-based nhà ống, hẻm, chợ and kênh generators reproduce exactly. The bible's promised mechanics (loud gates, ice store, smelly market) are missing, and Co.op Mart is a trademark. |
| B9 monsters and NPCs | **Blocker.** City hordes are 100 % dda (`GROUP_ZOMBIE_HORDE`), including zombie soldiers and SWAT that drop guns. Three missions are broken (wrong item or wrong timer), the Vietnamese in the dialogue has errors, and the NPC pronouns ignore gender. |

---

## B2 setting and story (scenario/, snippets/, intro EOC)

What works: the scenario texts are period-correct (Phú Mỹ bridge open in 2009, Thủ Thiêm still marsh, Miền Đông
on Đinh Bộ Lĩnh, the 2004 "new bird flu" and 2009 "swine flu" framings). The loa phường and newspaper snippets
read like the real thing. The start dates are right: Dec 21 cataclysm, Dec 26 start, dry season.

1. **major**: `snippets/lore.json:45`, category `sgn_radio` (`sgn_radio_1`…`_5`). The five radio broadcasts are
   referenced nowhere in the mod: no item, furniture or EOC uses this category. They are dead content, and they are
   the only place the evacuation rumours (Củ Chi, the stadium) appear.
   Fix: give `sgn_radio_cassette` (or a new `sgn_radio_tape`) `"snippet_category": "sgn_radio"`, or have a
   recurring EOC show one when the player carries a working radio.
2. **major**: `furniture/furniture.json:21`, `f_sgn_loa_phuong`, is a plain `copy-from: f_utility_pole`. It has no
   examine action, sound or snippet. The bible makes the loa phường the voice of the outbreak (§1, §2), but in play
   its text only appears when a `sgn_ward_notice` item is read.
   Fix: add an `examine_action` (`effect_on_condition` with a `u_message` drawn from `sgn_loa_phuong`), or a
   once-per-day EOC that plays a loa message when the player is within N tiles of one. Also consider a one-time
   broadcast in `SGN_EOC_intro`.
3. **minor**: brand names, against the bible's no-trademark rule.
   - `snippets/lore.json:104`: "I took **the Wave** and two cans of gasoline" (Honda Wave). Fix: "took the bike" or
     "took the Wave-style".
   - `scenario/scenarios.json:5`: `"name": "Sài Gòn, 2004 (Vietmap)"`, and `modinfo.json` uses the same word.
     VIETMAP is a real Vietnamese navigation/map brand. Fix: "Sài Gòn, 2004 (generated city)".
4. **minor**: `snippets/lore.json:62`, `sgn_radio_4`: "Go north toward Củ Chi, or **west toward the river**". From the
   city the Saigon River is east and north-east. West is Bình Chánh and Long An. Fix: "east to the river" or
   "south-west toward the delta".
5. **nit**: `scenario/scenarios.json:7`: "the city of **eight million** people". HCMC had about 6.1 M in 2004 and
   7.16 M in the 2009 census. The same paragraph has "dripping air conditioners" right after the intro says the power
   went out. Fix: "six million", and drop the dripping air conditioners.
6. **nit**: `snippets/lore.json:100`, `sgn_note_1`: "Con ơi, **Mẹ** went to find Ba". "Mẹ" with "Ba" is northern usage
   mixed with southern. A Saigon note would say **Má**. Fix: "Má went to find Ba … If Má is not back".
7. **nit**: the hẻm start (`sgn_sloc_hem`) is only allowed in the 2009 scenario, although `sgn_hem_block` exists in the
   2004 city. Fix: add it to `sgn_saigon_2004.allowed_locs`.

## B3 professions (professions/professions.json)

What works: skill and point budgets are reasonable. The VEGETARIAN monk and BADBACK veteran are good. Nobody gets
a gun. The xe ôm's motorbike and the student's bicycle are real starting vehicles.

1. **major**: the kits use dda generics where the mod has its own item, so the mod's items never reach the player at
   start and the professions read as dda.
   - `sgn_fisherman` (line 227): `net`, `fishing_rod_basic`, `knife_folding`, while `sgn_luoi_chai` (cast net),
     `sgn_can_cau_tre` and `sgn_dao_rua` exist.
   - `sgn_mechanic`: no `sgn_bo_va_xe` and no `sgn_book_moto_repair`.
   - `sgn_market_trader`: the bible's scale, rice and cash bag are a `jerrycan` and a `backpack`.
     `sgn_ro_nhua`, `sgn_quang_ganh` and `dry_rice` are available.
   - `sgn_monk`: no `sgn_book_sutra`, although it exists.
   - `sgn_street_vendor` (line 52): no `sgn_nuoc_mam` and no `sgn_banh_mi_bread`.

   Fix: swap these in. Each is a one-line change.
2. **major**: `sgn_street_vendor`: cooking 3 and no `"recipes"`. `sgn_pho_bo` needs the cookbook or cooking 5
   (`recipes/food.json:22`), and `sgn_com_tam` needs the cookbook or cooking 4. A vendor who "fed half the ward"
   cannot make phở or cơm tấm at start. Fix: `"recipes": [ "sgn_pho_bo", "sgn_com_tam", "sgn_che" ]` on the
   profession.
3. **minor**: `sgn_cong_an` (line 138) wears `longshirt` and `pants_cargo`. `sgn_ao_cong_an` and `sgn_quan_cong_an`
   exist (`items/gear/clothing.json`), and the bible lists "Uniform". The description (line 140) also says "You never
   fired your **service weapon**", which contradicts the recorded no-pistol decision. Fix: use the uniform items.
   Reword to "You were never issued a gun; the district office kept the only one in a drawer."
4. **minor**: `sgn_nurse` (line 167) wears `longshirt` and `pants_cargo` and has `mask_dust`. The bible asks for scrubs
   and bird-flu masks. Fix: add a `sgn_dong_phuc_y_ta` (white nurse's áo blouse, `copy-from: coat_lab` or
   `dress_shirt`) plus `sgn_khau_trang`.
5. **nit**: `sgn_construction` says "climb bamboo scaffolding barefoot" but wears `boots_steel`. Site workers in 2004
   wore dép or rubber boots. Fix: `sgn_dep_lao` or `sgn_ung_cao_su`. Also add the bible's bamboo pole.
6. **nit**: `sgn_student` gets `sgn_sgk_ngu_van`, a high-school Ngữ văn textbook, as a university student.

## B4 climate (region/weather.json, region/flood.json)

What works: the monthly curves (April peak 29.2 °C, Dec 25.9 °C, wet-season humidity 79–85 %) match HCMC normals
within about 1 °C. Snow is blacklisted. The B4b peer-review re-tune (F1) is applied. `sgn_wet()` (doy 41–252 from
the Mar 21 turn zero) lines up with the engine's month table. `NO_SCENT` on flooded tiles is a nice mechanical touch.

1. **major (bug)**: `region/flood.json:85` and `:111`. The flood is applied around the player
   (`u_transform_radius: 24`) every 20–40 min while it rains. The drain runs **once**, around the player's *current*
   position (`radius 30`), and then clears `sgn_flooding`. Any street flooded at an earlier position more than 30 tiles
   away, for example while the player rode through a storm, stays `t_sgn_ngap_*` for good, with
   `move_cost 4` and an endless `water_murky` source. It only drains if a later rain/drain cycle happens to land
   nearby. Fix: make the drain EOC recurring (no one-shot flag), so it keeps draining wherever the player is while it
   is dry. Alternatively, have `t_sgn_ngap_*` revert on their own via `transforms_into`/`ter_furn_transform` with a
   `"post_terrain"` timer, or make the drain radius ≥ the largest distance travelled while flooding is set.
2. **major (balance and authenticity)**: `sgn_tft_flood` turns **80 %** of pavement and hẻm into knee-deep water on the
   *first* rainy check (`[ "t_sgn_ngap_duong", 4 ], [ "t_pavement", 1 ]`). That happens on almost every wet-season
   afternoon in every district. Real Saigon flooding is local (low wards, triều cường peaks Sep–Nov, rain > ~40 mm).
   Fix: scale by intensity (thunder 4:1, rain 1:3) and/or require two consecutive rainy checks. Optionally weight by
   month: higher Sep–Nov for the tides.
3. **minor**: the flood transform also turns `t_pavement_y` into `t_sgn_ngap_duong`, and the drain turns that back into
   `t_pavement`, so road markings are erased. Fix: add a `t_sgn_ngap_duong_y` or exclude `t_pavement_y`.
4. **nit (design note)**: with a Dec 26 start the player sees no rain or flood for about 4 months (until doy 41). That
   is correct for the dry season, but rain as a water asset (bible §9) is then out of reach early. Consider a rare
   off-season shower: the dry-season `light_drizzle` arm at humidity ≥ 80 almost never fires with dry-season humidity
   capped near 84 %.

## B5 items, food, recipes, loot (items/, recipes/, itemgroups/)

What works: the food line-up is excellent and Southern (cơm tấm, hủ tiếu, bánh xèo, trứng vịt lộn, bún thịt nướng,
nước mía, bia hơi spoiling in a day). Macros are realistic (mì gói 340 kcal / 75 g, mooncake 800 kcal / 200 g).
Short `spoils_in` values fit the heat. `sgn_thung_xop` has real insulation. The rooftop tanks hold untreated `water`.
The đồng notes are priced at the real 2004 rate (10 000 đ = $0.63). Firearms appear in exactly one group,
`sgn_npc_guard_weapon`, at 25 %.

1. **major (missing mechanic)**: **there is no ice anywhere in the mod.** No item, recipe or loot group contains `ice`,
   although the bible makes ice "the key resource" of the chợ (§3) and lists "đá (ice block)" (§5).
   - The chợ "ice store" (`tools/saigon/gen_cho.py:82`) holds only empty `sgn_thung_xop`.
   - `sgn_tra_da` (trà đá) is brewed hot with no ice (`recipes/food.json:107`).
   - `sgn_ca_phe_sua_da` says "Served over ice when there is any", but no recipe uses ice.
   - Cô Ba's line "it's cooler by the ice" points at nothing.

   Fix: dda at this revision has no ice item, so add `sgn_da_cay` (ice block, material water). Make it melt with a
   `countdown_interval` + `countdown_action` transform into `water_clean`, which `sgn_thung_xop`'s insulation slows.
   Place it in the chợ ice store inside `sgn_thung_xop`, and make it an optional component for trà đá, cà phê sữa đá
   and chè. That gives the cooler a job.
2. **major (balance)**: gold has inconsistent post-apocalypse prices. `sgn_vang_chi` is `"price_postapoc": "40 USD"`
   (`items/currency.json:44`), but `sgn_vang_luong` (= 10 chỉ, 38 g) is `"price_postapoc": "60 USD"`
   (`items/gear/work_trade.json:118`). A lượng trades for 1.5 chỉ, so NPC trade is lopsided and splitting is
   exploitable. Fix: set `sgn_vang_luong` to 400 USD post-apocalypse. Alternatively drop both to the same per-gram
   figure, e.g. chỉ 10 USD and lượng 100 USD.
3. **minor**: food prices are 3–10× the 2004 street price, and they contradict the mod's own note text.
   - `sgn_dong_10k` says 10 000 đ "bought a bánh mì and a cup of coffee", yet `sgn_banh_mi_thit` is `1 USD`
     (≈ 16 000 đ).
   - `sgn_pho_bo` is `2 USD` (≈ 32 000 đ; real price 10–15 000 đ).
   - `sgn_banh_chung` is `5 USD` **per slice** (`items/food/street_food.json:108`; a whole cake cost 30–50 000 đ).
   - `sgn_ve_so` is `10 cent`, but tickets were 5 000 đ ≈ 32 cent.

   Fix: phở 75 cent, bánh mì thịt 30 cent, cơm tấm 60 cent, bánh chưng slice 40 cent, vé số 32 cent.
4. **minor**: `sgn_pho_bo` `"material": [ "flesh", "wheat" ]` (`items/food/street_food.json:17`). Phở is **rice**
   noodle (the description itself says "Flat rice noodles"). `sgn_hu_tieu`, `sgn_bun_bo_hue` and `sgn_chao_long`
   inherit this through `copy-from`. Fix: `[ "flesh", "veggy" ]` (or `"rice"` if the material exists).
5. **minor (anachronism)**: `default_zombie_clothes` (`itemgroups/loot.json:70`) gives `sgn_non_bao_hiem` at prob 35,
   the most common garment. Helmets became compulsory on city streets only on **15 Dec 2007**. In 2004 few riders in
   the inner city wore them, and the item's own description says "after the helmet law was first discussed". Fix:
   prob ~8 for the 2004 scenario. If one group must serve both maps, accept the 2009 figure but say so in the bible.
6. **minor (brand)**: `items/gear/household_2.json:6`: `"Rạng Đông vacuum flask"`. Rạng Đông is a real, living
   manufacturer. The bible's own §11 lists it, which conflicts with its brand rule. Fix: "bình thủy (vacuum flask)",
   with the description saying "from the state flask factory".
7. **minor**: `sgn_pharmacy` (`itemgroups/loot.json:283`) has aspirin, dầu gió, oresol and masks, but no antibiotics,
   vitamins or cough syrup. In 2004 a nhà thuốc sold amoxicillin over the counter, and the outbreak is a *fever*.
   Fix: add `antibiotics` (~15) and `vitamins` (~20). Fever reducers are already covered by aspirin.
8. **nit**: `sgn_quan_cong_an` (`items/gear/clothing.json:80`) is "Olive-green uniform trousers". The 2004 công an
   summer uniform was yellow-khaki top and bottom; olive green came with the 2008/2009 change. Please check before
   changing, but "khaki trousers" fits 2004.
9. **nit**: inert or reskinned items. `sgn_mung` (mosquito net) has no use. `sgn_oresol` is `copy-from: salt`, so
   eating it raw is eating salt. `sgn_thuoc_bac` says "to be simmered for hours" but has no brewing recipe.
   `default_zombie_items_pockets` still uses dda `cig`/`cell_phone` instead of `sgn_thuoc_la`/`sgn_dien_thoai`.

## B6 vehicles (vehicles/)

What works: the fleet matches the bible: underbone, tay ga, ba gác máy, xích lô, xe đạp, xuồng, ghe, plus 2009
four-wheelers. The underbone (6.3 kW, 4 L tank, pillion with a 15 L rack) is believable. The dda city, parking,
highway and police groups are diluted to about 99 % Saigon. Moored boats are placed wholly on water.

1. **minor**: `sgn_veh_ba_gac_may` (`vehicles/vehicles.json:55`) uses `engine_1cyl_large`, a **21 kW** single. A ba gác
   máy runs a 100–150 cc Chinese engine (≈ 6–9 kW), so it gets ~3× the power. Fix: `sgn_engine_110cc` or a 150 cc
   variant. The same applies to the ghe's `sgn_longtail` (`copy-from: engine_1cyl_large`). Long-tails mostly used
   8–13 hp engines, so a ~10 kW part fits.
2. **minor**: `sgn_veh_xich_lo` (line 72) has one front wheel and one rear wheel. A xích lô has **two front wheels**
   with the passenger seat between them, and one rear wheel under the rider. The described "folding black canopy" is
   also not a part. Fix: a 2-wide front row with `wheel_bicycle` on each side, plus a canopy (`roof_cloth` or
   similar) over the seat.
3. **nit**: the tay ga share is ~20 % in every group. That fits 2009, but it is high for 2004, when automatic scooters
   were still a luxury import. Optionally lower it for the 2004 map. `horn_car` on the underbone and the ba gác
   should be a motorbike horn.

## B7 books and media (items/books/, book_learn recipes)

What works: the seven skill books match bible §8, with sensible levels and int requirements and good Vietnamese
subtitles in the descriptions. The wuxia titles are fictional. The lịch bloc proverbs are correct and well
translated. The robot-cat comic avoids the trademark.

1. **minor**: only `sgn_book_southern_cooking` (phở, cơm tấm, chè) and `sgn_book_moto_repair` (the 4 L tank) appear in
   any `book_learn`. Nursing, tailoring, fishing, TV repair and construction teach skill only. The cookbook does not
   teach the mod's own other dishes: hủ tiếu and xôi are autolearn, and bánh xèo, gỏi cuốn, bánh mì, bún bò Huế and
   bánh chưng have **no recipe at all**. Fix: add recipes for bánh xèo, gỏi cuốn and bánh chưng (a long-keeping
   staple, useful in play) under the cookbook. Add `book_learn` on dda recipes that fit, e.g. tailoring patterns →
   basic clothing, fishing almanac → fish trap, TV repair → radio/flashlight repairs.
2. **nit**: the bible's "Thể Thao" sports weekly is not present. `sgn_newspaper` covers the daily only.
3. **nit**: `sgn_book_almanac` ("your grandmother never made a decision without it") has `intelligence: 4` and no
   effect. A small morale bonus on reading (`read_fun` is only 2), or a snippet set of lucky days, would make it more
   than a name.

## B8 mapgen (mapgen/, overmap/, region_settings, furniture/, gen_*.py)

What works: the nhà ống generator is the highlight. It uses 4-tile lots (4 m frontage, ~18 m depth), consistent
storeys per OMT column with `omt_stack`, 15 ground-floor businesses, barred upper windows, rooftop tanks with untreated
water, AC units and a shared roof walk, which together deliver the bible's "rooftops connect". The hẻm has 1–2 tile
alleys with ports that cap against non-hẻm neighbours. The chợ is zoned correctly. The kênh has bờ kè and moored boats.
Flora is tropical (bàng, me, sao, coconut, bougainvillea) with harvestable fruit. Generators and JSON are in sync.

1. **major (missing mechanic)**: the bible's gameplay hooks for the gates are not implemented.
   `t_sgn_cua_sat_keo_c` (`furniture/terrain.json:4`) is a `t_door_metal_c` that anyone can open from either side,
   silently. Its own description says it "padlocks to the wall" and "makes a screech the whole alley hears". The bible
   §3 promises "Gates and window bars make loud, slow entries". No shopfront or hẻm door is ever locked.
   Fix: place a locked variant (`t_sgn_cua_sat_keo_locked`, `"lockpick_result"`, a high `bash.str_min`) on some
   share of shopfronts and hẻm doors. Give the open/close transition a sound via `"open"`/`"close"` messages plus a
   `sound` on examine, or an EOC.
2. **major (missing mechanic)**: the chợ's bible hook "food-rich but it spoils fast … it smells and draws zombies" has
   no mechanic. There is no emission or scent, and the "ice store" holds no ice (see B5-1). Fix: give the fish/meat
   counters (`'F'`/`'M'`) a furniture with an `emit_` of a stench field, or place `fd_` fields in the wet hall, so the
   hall attracts zombies and the player smells it.
3. **minor (brand)**: `overmap/places.json:24` and others: `"name": "Co.op Mart"`. This is the trademark of the Saigon
   Co.op chain, used as a generic, repeating building type in the generated city. Landmarks of the real map (Rex,
   Diamond Plaza) are places and acceptable, but a chain store type is not. Fix: "siêu thị (supermarket)" or a
   fictional "Hợp Tác Mart".
4. **minor**: chợ garment stalls `'G'` use `default_zombie_clothes` (`tools/saigon/gen_cho.py:79`). That group includes
   `ring_wedding` at 25 and favours helmets and masks. The proper `sgn_cho_cloth` group exists but is only used by
   Bến Thành. Fix: point `'G'` at `sgn_cho_cloth`. Consider one gold stall in the dry-goods zone (bible §3) using
   `sgn_gold_shop` at a low chance.
5. **minor**: hẻm homes are all single-storey (one roof chunk at z1), and the generator has only two quadrant layouts,
   mirrored, so every hẻm block looks the same. Real 2004 hẻm housing was mostly 2–3 storey nhà ống. Fix: add a
   2-storey variant per quadrant (reuse the nhà ống floor chunks) and a third layout. Add a `f_sgn_lu_nuoc` or a
   rooftop tank: the hẻm homes currently have no water source at all.
6. **nit**: every nhà ống ground floor has an `f_oven` (`'O'` in the pho template) and every lot shares the identical
   rows 9–17. A 2004 Saigon kitchen had a two-burner gas hob on a `bình gas`, not an oven. Fix: replace `f_oven` with a
   counter plus `sgn_binh_gas`/`sgn_bep_ga_mini` loot, or a custom hob furniture with `crafting_pseudo_item: hotplate`.

## B9 monsters and NPCs (monsters/, npcs/)

What works: the delta wildlife relabelling (snakehead, pangasius, swamp eel, myna, egret, monocled cobra), NO_BREED zoo
animals, the chó ta and gà ta, and the street-level NPC cast are all good. Names use correct southern family-name
frequencies and birth-order nicknames. The NPC dialogue has a strong voice.

1. **blocker**: city hordes are entirely vanilla dda, including **gun-carrying American zombies**. The mod appends its
   four zombies to `GROUP_ZOMBIE` (`monsters/monsters.json:105`), but overmap city hordes spawn from
   **`GROUP_ZOMBIE_HORDE`** (`src/overmap.cpp:3538`), which the mod never touches. That group (weight 10 477) contains:
   - `mon_zombie_soldier` 100, whose drops include `military_standard_assault_rifles`
   - `mon_zombie_cop` 200 and `mon_zombie_swat` 100, with US cop armour and gear
   - `mon_zombie_survivor`/`_elite` and `mon_zombie_paramilitary`
   - `mon_feral_soldier`, `GROUP_FERAL`, `mon_zombie_fursuit` and `mon_beekeeper`

   At `SPAWN_CITY_HORDE_SCALAR` 80 and city size 12, that is ~960 horde zombies per city, about 4 % of them gun or
   body-armour carriers (~40 per city). **None** of them is a Saigon variant. This breaks the bible's no-guns and
   no-American-content rules on every road. (`GROUP_ZOMBIE` itself also still carries those dda members, at ~84 % of
   its weight.)
   Fix: override `GROUP_ZOMBIE_HORDE` (and `GROUP_ZOMBIE`) with `"override": true` and a Saigon list: mon_zombie,
   fat, child, rot, crawler, tough, runner, brainless, the four `sgn_` variants, zombie dogs, `GROUP_VANILLA_DORMANT`
   and the cocoon groups. Keep `mon_zombie_medical` (hospital staff) and `mon_zombie_fireman` if wanted, but drop
   soldier, SWAT, cop, survivor, paramilitary, feral soldier, fursuit and beekeeper. Add a test that no group reachable
   from a Saigon region spawns a monster whose death drops include a GUN.
2. **major (bug)**: `MISSION_SGN_CHINH_PHUC` (`npcs/missions.json:233`) succeeds on
   `time_since('cataclysm', 'unit':'days') >= 7`. The game starts about 4.3 days after the cataclysm (Dec 21 22:00 to
   Dec 26 06:00), so "survive seven days" completes **~2.7 days** after the game starts. If it is offered later, it is
   complete the moment it is accepted. Fix: store the acceptance time in `start` (`{ "math": [ "u_sgn_chinh_phuc_t =
   time('now')" ] }`) and test `time_since(u_sgn_chinh_phuc_t, 'unit':'days') >= 7`.
3. **major (wrong item and wrong word)**: `MISSION_SGN_THAO_DUOC` (`npcs/missions.json:203`) asks for "thirty leaves of
   **thuốc lá**" and checks `u_has_items sgn_thuoc_la` × 30. **Thuốc lá means tobacco**: `sgn_thuoc_la` is the "Sao Mai
   cigarette". The herbalist's lesson (telling a medicinal leaf from a poisonous one) needs *lá thuốc* / *thảo dược*.
   As written, the player completes it by buying three packs of cigarettes. Fix: rename to "Lá thuốc của thầy" and use
   a herb item, either dda `wild_herbs` or a new `sgn_la_thuoc` foraged from the `t_sgn_shrub_*` flora.
4. **major (wrong item)**: `MISSION_SGN_SO_TAY_SO_CUU` (`npcs/missions.json:57`) is titled "Sổ tay số điện thoại"
   ("notebook of phone numbers") and asks for "her handwriting … the yellow one", but the goal item is
   `sgn_so_tay_so_cuu`, the printed **Red Cross first-aid handbook**. Any first-aid booklet completes it. Fix: add an
   `sgn_so_dien_thoai` item (a yellow handwritten phone book) and place it on hẻm/nhà ống altars, or spawn it at the
   mission target with `update_mapgen`.
5. **major**: NPC dialogue hard-codes pronouns while the NPC templates in `npcs/places.json` set no `gender`. Thirteen
   topics are affected, including `TALK_SGN_MONK` ("bows **her** head"), `TALK_SGN_DOCTOR` ("at **her** elbow"),
   `TALK_SGN_GUARD`/`MECHANIC`/`PETROL_ATTENDANT`/`PARK_ELDER`/`BACKPACKER` ("**he**"), and `TALK_SGN_PARK_ELDER_YEARS`
   ("**My wife**"). `relevant_genders` only gives translators context; the English line is fixed. Fix: set `"gender"` on
   each `sgn_npc_*` template to match its lines (Cô Ba already does), or neutralise the action text.
6. **minor (Vietnamese errors)**, each needs a one-line fix:
   - `dialogue.json:567`: "tập thể **dưỡng**" → **tập thể dục**.
   - `missions.json:190`: "Bà ấy **đứa quá khỏi** (passed away, the southern way of saying it)" is not Vietnamese.
     Use "Bà đi rồi" or "Bà mất rồi".
   - `missions.json:68`: "**Nó ống vàng**" → "Cuốn màu vàng".
   - `missions.json:67`: "**Số** tay mà" → "**Sổ** tay mà".
   - `dialogue.json:479`: "for two **bao lít**" is garbled. Use "vài lít" (a few litres).
   - `dialogue.json:289`: "the **mụ** is feeding them": *mụ* is a pejorative for an old woman. For the nun of a chùa
     use **sư cô** / **ni cô**.
   - `MISSION_SGN_VANG_CHI` offer: "twenty **chi**" → **chỉ**.
   - `sgn_class_fisherman` name: "Can Gio" → **Cần Giờ**.
7. **minor (geography)**: `dialogue.json:618`: "One train, **south**, as far as **Bình Dương**". Bình Dương is north of
   Saigon, and the only line out of Ga Sài Gòn runs north (the Mỹ Tho line closed in 1958). Fix: "One train, north, as
   far as Dĩ An".
8. **minor**: `MISSION_SGN_KINH_THANH` asks for the grandmother's "prayer book" but requires `sgn_kinh_thanh` (a full
   Bible), then says "I will burn it with her". A Catholic grandmother's book is the `sgn_sach_kinh` (prayer book),
   and Catholics do not burn it. Fix: require `sgn_sach_kinh` and change the success line to "I will put it in her
   hands".
9. **minor**: `sgn_npc_guard_worn` (`itemgroups/npc_gear_places.json:130`) dresses every guard, including the private
   bảo vệ at STC and the mall, in `sgn_ao_cong_an` + `sgn_quan_cong_an`. With `sgn_npc_guard_weapon`, one in four
   carries the công an pistol. Private guards wore their company's uniform and never carried pistols. Fix: split
   `sgn_npc_ward_police` (uniform, pistol chance) from `sgn_npc_bao_ve` (blue or grey shirt, baton only), and place
   the latter at STC and Diamond Plaza.
10. **minor (depth)**: the four Saigon zombies are thin reskins. `sgn_mon_zombie_sot` is "burning hot to the touch",
    but only gets speed +15 and hp −15. The market zombie "smelling of fish sauce" has no scent. Cheap upgrades: give
    the fevered dead an `attack_effs` heat/fever effect, or make it `FLAMMABLE`-resistant. Give the market zombie a
    stench emission, which also helps B8-2. The mission rewards are mostly `value: 0` and have no `end` effect, apart
    from Cô Ba's 2 chỉ. Add small rewards (a chỉ, food or a map reveal) so the missions matter.

---

## Top 10 fixes (across all groups)

1. **B9-1 (blocker)**: override `GROUP_ZOMBIE_HORDE` and `GROUP_ZOMBIE` with a Saigon-only list. Remove zombie
   soldiers, SWAT, cops, survivors, paramilitary and ferals, and add the four `sgn_` zombies. Add a test that no
   Saigon-reachable monster group drops a gun.
2. **B9-2**: fix `MISSION_SGN_CHINH_PHUC` to count seven days from acceptance, not from the cataclysm.
3. **B9-3, B9-4**: fix the two wrong-item missions. Thuốc lá (tobacco) → a herb item. The first-aid handbook → a
   handwritten phone notebook item.
4. **B4-1**: make the flood drain recurring or self-timed, so flooded streets away from the player do not stay flooded
   forever. With **B4-2**, scale flooding by rain intensity.
5. **B5-1 / B8-2**: add an ice block. Stock the chợ ice store with it, use it in trà đá, cà phê sữa đá and chè, and give
   the wet hall a stench that draws zombies.
6. **B5-2**: fix the gold price split (`sgn_vang_luong` post-apocalypse 60 USD vs 10 × chỉ at 40 USD).
7. **B2-1, B2-2**: wire up the dead radio snippets, and give the loa phường an examine or proximity broadcast.
8. **B8-1**: implement the loud, lockable cửa sắt kéo (locked variant, sound on open) promised by the bible and the
   item's own description.
9. **B9-5, B9-6**: set `gender` on NPC templates to match the pronouns in their lines, and fix the eight Vietnamese
   errors (tập thể dục, sổ tay, sư cô, chỉ, Cần Giờ, …).
10. **B3-1, B3-2**: give professions the mod's own kit items (cast net, dao rựa, bơm vá xe, sutra, uniform, nurse's blouse),
    and give the street vendor the phở, cơm tấm and chè recipes.
