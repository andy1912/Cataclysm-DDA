# Plan: CDDA "Saigon 2000s" Fork: Architecture TDD + Pass 1 Playable Vertical Slice

## Context
The user wants a fork of Cataclysm: Dark Days Ahead set in **Saigon in the 2000s**, with vehicles, items, books and story all consistent with that setting. The long-term vision also includes a 2.5D isometric and dynamic-lighting revamp.

There are two outputs:
- **Part A.** An evidence-backed architecture TDD, produced by 4 domain analysts, each checked by an adversarial critic for up to 3 rounds. It pins every claim to real source and drives Part B.
- **Part B.** A coding phase that delivers a **playable vertical slice**: a `saigon_2000s` total-conversion mod plus only the minimal C++ changes it requires. It must build and run on macOS.

Decisions made by the user:
- GitHub fork plus a local clone.
- Pass 1 is the vertical slice.
- Text is English with authentic Vietnamese terms; the `vi` translation comes later via `.po`.
- The isometric renderer is **analysis and roadmap only** for now.

## Working rules: small, resumable units (credit/session limits)
- **Units.** All work is broken into small units, roughly one sitting each (≈30–60 min of agent time or less). Each unit is independently useful and leaves the repo building and passing `--check-mods`. The unit IDs below (A1.1, B5a, …) are the granularity.
- **Progress ledger.** `doc/saigon/PROGRESS.md` in the fork is the single source of truth. It has one line per unit: `ID | status (todo/in-progress/done/blocked) | commit SHA | output file | next action`. It is updated **at the start** (in-progress) and **at the end** (done + SHA) of every unit and committed along with the unit's work.
- **Commits.** Every unit ends with one git commit, formatted `saigon: <unit ID> <summary>`. Nothing is left uncommitted between units. If a unit is interrupted, the ledger says "in-progress" and the next session resumes that unit or reverts its partial changes with `git status` / `git diff`.
- **State on disk.** All agent outputs (analyses, critic verdicts, review notes) are written to files under `doc/saigon/`, never kept only in agent context. A critic round that gets interrupted restarts from the latest `d{N}_r{k}.md` and `critic_d{N}_r{k}.md` files with a fresh agent. It does not depend on SendMessage continuity.
- **Resume protocol.** A new session reads `PROGRESS.md`, runs `git log --oneline -10` and `git status`, picks the first non-done unit, and continues. The baseline build is also incremental (the Ninja build dir persists), so re-running it is cheap.
- **No parallel waste.** Run at most 2 background agents at once, so that running out of credit loses at most one unit's worth of work per agent.

## Step 0: Repo & environment (units S0.1–S0.4: fork/clone, deps, baseline build, ledger scaffold)
1. The user forks `CleverRaven/Cataclysm-DDA` on GitHub. I get their username with `gh api user` and `change_directory` into a folder they approve (suggested `~/code/cdda-saigon`).
2. `git clone --filter=blob:none <fork>`. This is a blobless clone, so upstream merges stay possible. Then `git remote add upstream`, create branch `saigon/pass1-vertical-slice`, and record the base SHA. Every TDD citation is pinned to that SHA.
3. Build dependencies. **I'll ask before installing**, because it changes the system: `brew install cmake ninja pkg-config sdl2 sdl2_image sdl2_ttf sdl2_mixer gettext libvorbis`.
4. Baseline build: CMake + Ninja, `-DTILES=ON -DSOUND=ON -DCMAKE_BUILD_TYPE=RelWithDebInfo`, targets `cataclysm-tiles` + `cata_test`. It runs in the background (about 20–40 min) while Part A proceeds. Confirm an unmodified `./cataclysm-tiles --check-mods` passes.

## Part A: Architecture analysis (starts while the baseline build runs)
Each domain is split into units:
- `A{N}.1` analyst draft
- `A{N}.2` critic round 1
- `A{N}.3` revision + critic round 2
- `A{N}.4` revision + critic round 3, only if needed

Domains run two at a time, in the order 4 → 2 → 3 → 1. The domains that gate Part B go first, and rendering goes last because it's roadmap-only. The analyst for each domain writes `doc/saigon/analysis/d{N}_r{k}.md`.

| # | Domain | Seed files | Must answer for Part B |
|---|---|---|---|
| 1 | Rendering & UI | `src/sdltiles.cpp`, `src/cata_tiles.{h,cpp}`, `src/cursesport.cpp`, `src/ui_manager.cpp`, `game::draw` in `src/game.cpp`, `src/lightmap.cpp`, `src/shadowcasting.*`, map caches in `src/map.cpp` | Isometric/normal-map/shader seams (roadmap only). Also whether the existing `iso` tileset mode is reusable. |
| 2 | Mapgen & Worldgen | `src/mapgen*.cpp`, `src/overmap*.cpp`, `src/omdata.h`, `src/regional_settings.*`, `src/coordinates.h`, `data/json/mapgen/`, `data/json/overmap/`, region settings JSON | Which parts of the city/street grid are hardcoded in C++ (`overmap::place_cities` / street builder) versus overridable in JSON (`city` building pools, `overmap_special`, palettes). Also how to express hẻm, nhà ống, chợ and canal in JSON today. |
| 3 | Climate & Vehicles | `src/weather*.cpp`, `src/weather_gen.*`, body-temperature code in `src/character*.cpp`, `src/vehicle*.cpp`, `src/vehicle_move.cpp`, `src/veh_type.*`, `data/json/vehicle*` | Whether the region `weather` params can express a 2-season monsoon and 27–35°C humid heat. Whether humidity feeds heat stress. What limits two-wheeler and three-wheeler handling. What boat/hull support already exists. |
| 4 | JSON & Modding | `src/init.cpp`, `src/generic_factory.h` (`copy-from`/`extend`/`delete`), `src/mod_manager.cpp`, `src/item_factory.cpp`, `src/recipe*.cpp`, `src/mtype.*`, `src/monfaction.*`, `data/mods/` (existing total conversions), `tools/format/` | The fork-vs-mod boundary. Which core IDs are hardcoded and can't be removed. The right blacklist/override mechanisms for removing US-specific content. |

**Critic loop, up to 3 rounds per domain.** A separate critic agent verifies every `path:line` and symbol against the clone. It REJECTs a finding in any of these cases:
- The finding is uncited or abstract.
- It ignores performance (single-threaded `do_turn`, cache invalidation, tile-draw cache misses, allocations).
- It proposes Vietnam changes that are only asset or name swaps.
- It is not actionable.

Revisions go through SendMessage to the same analyst. Anything still open after round 3 goes into the risk register.

**Integration critic.** One agent checks that the 4 domain reports agree with each other. Examples: shophouse z-levels versus the isometric plan, and the mod/fork boundary versus the C++ work each domain asks for.

**Deliverable.** `doc/saigon/TDD.md` in the fork. It contains: the architecture decision, the current baseline with Mermaid data-flow diagrams, the 4 domain chapters, a performance and threading budget, a phased roadmap (pass 2+: organic alley/canal overmap generator, two-wheeler physics, isometric renderer), a risk register, and a citation index. An automated citation-check script must report zero misses.

The integration critic is unit `A5`. The TDD is written in units: `A6.1` chapters 1–2, `A6.2` domain chapters, `A6.3` roadmap and risk register, `A6.4` citation check.

**Gate.** Part B can start once A4 (modding) and A2 (mapgen) are done. B4b (climate C++) additionally waits for A3. Part B does not wait for A1 or A6. Before any content is written, the Part A findings confirm or correct the JSON keys that Part B assumes.

**Pass 1 unit breakdown.** Every row in the Part B table below is split into sub-units of about 5–15 JSON objects or one C++ change each, for example:
- B5a street food, B5b drinks and condiments, B5c gear/clothing, B5d recipes, B5e loot item_groups
- B6a motorbike + scooter, B6b ba gác + xích lô + bicycle, B6c riverboats, B6d vehicle_groups/placement
- B8a shared palettes, B8b nhà ống, B8c hẻm block, B8d chợ, B8e pagoda + café + chung cư, B8f canal, B8g region city pools + specials
- B4a weather JSON; B4b monsoon C++ + test; B4c heat-index C++ + test (each B4b/B4c only if A3 confirms it's needed)

Each sub-unit ends with `--check-mods` passing and a commit.

## Part B: Pass 1 vertical slice, mod `data/mods/saigon_2000s/`
Architecture (to be confirmed by domain 4): a total-conversion mod that depends on `dda`, because the engine needs core IDs. It overrides region settings and blacklists American-specific content. C++ changes live in the fork and are limited to gaps that JSON can't express. Real brands are fictionalized, for example a "110cc underbone ('Wave-style')" instead of a trademarked model name. Each task below is committed separately.

| Task | Content | Main JSON types / files |
|---|---|---|
| **B1 Mod skeleton** | `modinfo.json` (category `total_conversion`, deps `["dda"]`), README, folder layout: `region/ scenario/ professions/ items/ food/ recipes/ vehicles/ books/ snippets/ mapgen/ overmap/ monsters/ npcs/ blacklist/` | `MOD_INFO` |
| **B2 Setting & story** | Scenario "Sài Gòn, 2004" with start locations (upper floor of a nhà ống, a chợ stall, a hẻm). Localized outbreak backstory and intro message/EOC. Lore snippets: radio broadcasts, loudspeaker (loa phường) announcements, newspapers, handwritten notes. | `scenario`, `start_location`, `effect_on_condition`, `snippet` |
| **B3 Professions** | About 10: xe ôm driver, street-food vendor, market trader, university student, ward police (công an phường), nurse, construction worker, Cần Giờ fisherman, motorbike mechanic, Buddhist monk, war veteran. Each gets fitting kits and skills. | `profession`, `item_group` |
| **B4 Climate** | Saigon `weather` params in region settings: high base temperature and humidity, low seasonal amplitude, heavy wet-season rain. **Conditional C++ (B4b):** if domain 3 confirms JSON can't express a wet (May–Nov) / dry (Dec–Apr) monsoon, or humid heat stress, add an optional monsoon profile to `weather_generator` and/or a humidity heat-index term in body temperature. Each C++ change gets a new JSON key and a unit test in `tests/`. | `region_settings`, `src/weather_gen.cpp` |
| **B5 Items & food** | Food and drink: phở, bánh mì, cơm tấm, nước mắm, cà phê sữa đá, rau muống, instant noodles, bánh chưng. Gear: nón lá, áo mưa (poncho), dép tổ ong, rựa, portable gas stove, thùng xốp, plastic jerrycans. Plus recipes and Saigon loot `item_group`s. | `COMESTIBLE`, `GENERIC`, `TOOL`, `ARMOR`, `recipe`, `item_group` |
| **B6 Vehicles** | 110cc underbone motorbike, automatic scooter, xe ba gác (motor tricycle cargo), xích lô (pedal cyclo), bicycle, ghe/xuồng riverboats (using existing hull/boat parts). Dense street-parking `vehicle_group`s. Any handling limits get logged for pass 2. | `vehicle`, `vehicle_part` (copy-from), `vehicle_group`, `vehicle_placement` |
| **B7 Books & media** | Localized skill books (motorbike repair manual, Southern cookbook, first-aid handbook, fishing, tailoring), fictional wuxia novels and sutras for morale, textbooks, newspapers. Recipes are linked through `book_learn`. | `BOOK`, `recipe.book_learn` |
| **B8 Mapgen, one district** | New overmap terrains and mapgen for: nhà ống shophouse rows (multi-z, narrow deep lots, several per OMT), hẻm alley blocks (1–2-tile alleys), chợ wet market, pagoda, sidewalk café, old chung cư apartment block, canal (kênh) segment, all sharing palettes. Region `city` building pools are swapped to these. Organic street layout stays in the pass-2 roadmap: the C++ grid remains, but density comes from alleys inside each OMT. | `overmap_terrain`, `mapgen`, `palette`, `overmap_special`, `city_building`, `region_settings.city` |
| **B9 Monsters & NPCs** | Reflavored zombie variants and dense-city `monstergroup`s. Two story NPCs (xe ôm driver, market vendor) with a talk_topic and one starter mission. | `MONSTER` (copy-from), `monstergroup`, `npc`, `talk_topic`, `mission_definition` |
| **B10 De-Americanize** | Blacklist or zero-weight US-specific specials and items the slice would otherwise spawn, such as US-specific stores and brands. | `ITEM_BLACKLIST` / `MONSTER_BLACKLIST` / region overrides (keys per domain 4) |

**Critic for Part B.** After each B-group (B2 … B9) is complete, run one review unit `B{n}.R`. The reviewer agent writes `doc/saigon/review/B{n}.md` and checks three things: cultural and period authenticity (Saigon in the 2000s, not wartime or modern), mechanical depth (no pure name swaps), and JSON correctness.

## Verification
- `./cataclysm-tiles --check-mods saigon_2000s` shows zero errors after every task.
- JSON style: build and run the repo's JSON formatter (`tools/format`) on everything under `data/mods/saigon_2000s/`.
- Translatable strings: run `lang/extract_json_strings.py` (or the repo's current extractor) with no failures, which keeps the future `vi` `.po` path clean.
- Any C++ change: `cata_test` passes, including new unit tests for the monsoon and heat index.
- End-to-end playtest: launch tiles, create a world with the mod, start the Saigon scenario, and take screenshots of a nhà ống/hẻm district, a motorbike drive, reading a book, and the weather/temperature panel during the wet season (use debug time-skip).
- The TDD citation checker reports zero misses.

## Notes
- The brief's "/loop" means the bounded analyst↔critic rounds, not the recurring `/loop` skill.
- Pushing to GitHub or opening a PR happens only when the user asks.

---

## Update 2026-10-07: review and next plan (appended; nothing above is changed)

### Where things stand
- Pass 1 and most follow-on tracks are done. The ledger `doc/saigon/PROGRESS.md` has 145 done units:
  - G art, V/P content, L landmarks;
  - the R real map of 2009 from OpenStreetMap (ODbL);
  - L-loc localization;
  - RF4 (the 2009 scenario was hidden from character creation) and L-loc7 (delta wildlife).
- [PR andy1912/Cataclysm-DDA#1](https://github.com/andy1912/Cataclysm-DDA/pull/1) brings the branch `saigon/pass1-vertical-slice` into the fork's `master`. It is open, MERGEABLE/CLEAN, with 164 commits and 1,034 files. Auto-fix is on.
- Gates are green: `[saigon]` passes with 26 cases / 7,578 assertions, `check_mod.sh` is clean, `qa_game_load.sh` LOADED.

### Decisions recorded (user, 2026-10-07)
- **The project is standalone.** Updates flow only **from** CleverRaven upstream **into** this fork, after a check. Nothing is ever proposed or pushed back to CleverRaven.
- **First priority: playable and verified.**
- **The control problem from the first playtest is the mouse.** A click does not land on the tile under the pointer.
- **Plan documents are appended to, never rewritten.** This record goes at the end of `doc/saigon/PLAN.md` as well.

### Review findings (ranked)
1. **Mouse clicks land on the wrong tile (tiles build, macOS).**
   - The user's config: `FULLSCREEN windowedbl`, `RENDERER software`, `SCALING_FACTOR 1`, SDL3, Retina display.
   - Clicks go through `window_to_display_buffer_coords` / `convert_event_to_display_buffer_coords` (`src/sdltiles.cpp:~1100–1160`) via `SDL_RenderCoordinatesFromWindow`.
   - The fork has not touched that file, so this is upstream SDL3 behaviour. None of the 87 newer upstream commits on `sdltiles.cpp` mention the mouse.
   - Likely suspects:
     - window points vs backing pixels (Retina density 2);
     - the logical presentation not being set on the software renderer;
     - the mouse → map tile step in `cata_tiles` (zoom, sidebar offset).
2. **Nothing tests the real way a player reaches the real map** (new game → `sgn_saigon_2009` → `game::start_game` → on the real map). That gap let RF4 through.
   - `qa_game_load.sh` opens a ready-made save.
   - The tests set the map global themselves.
   - `saigon_new_game_start_locations` (`tests/saigon_mapgen_test.cpp:698`) covers only the Vietmap starts.
3. **The fork lags upstream.**
   - The branch base is `fe6a10c2b1` (Sep 28). The fork's `master` already carries 87 newer upstream commits (SDL/GPU renderer and input-loop changes among them).
   - The fork's engine edits sit in busy files: `src/overmap.cpp`, `savegame.cpp`, `scenario.{h,cpp}`, `game.cpp`, `weather_gen.{h,cpp}`, `overmapbuffer.cpp`.
   - The `upstream` remote still has a push URL.
4. **The `vi` translation hasn't started.** `lang/extract_json_strings.py` has never run on the mod.
5. **Content reviews B2.R–B9.R are still "todo".** Only B4b/B9b were peer-reviewed.
6. **Art gaps:**
   - the redescribed delta fish, frogs and turtle still use dda sprites;
   - the cobra wears the rattlesnake sprite;
   - H1 (hand art) is still todo.
7. **Smaller items:** R6b port/shipyard, PERF pass 2 (skip unchanged overmaps on save), I-B8a/I-B8b2, B4c heat index, the megacity decision.

### Next units (in order; same working rules as above)
**Phase A: playable and verified**
- **A0 Plan record.** Append this update to `doc/saigon/PLAN.md` (nothing removed) and add ledger rows for the units below.
- **A1 Mouse fix.**
  1. Add debug logging (behind a debug-log check, removed or kept quiet afterwards) in `convert_event_to_display_buffer_coords`. Log:
     - the raw window point;
     - the converted point;
     - window size in points and in pixels (`SDL_GetWindowSize` / `SDL_GetWindowSizeInPixels`);
     - the renderer output size;
     - the tile the game picks.
  2. The user clicks four marked spots in a QA world (via `qa_game_load.sh`'s throwaway userdir) and reports where the cursor highlight lands. I read the log; I can't capture the screen.
  3. Fix the mapping in `src/sdltiles.cpp`. Expected shapes of fix:
     - scale by pixel density;
     - or set `SDL_SetRenderLogicalPresentation` consistently;
     - or correct the tile offset.
  4. Add a unit test where the mapping can be computed headless.
  5. Recheck with the user on both `windowedbl` and windowed, and on `software` and `metal`/`gpu` renderers.
- **A2 New-game test for 2009.** Add `saigon_new_game_realmap_2009` in `tests/saigon_realmap_test.cpp`, reusing the `saigon_new_game_start_locations` pattern and `sgn_clear_map_and_reset_player`.
  - Pick `sgn_saigon_2009` as character creation does.
  - Run the `game::start_game` start path for each of its `allowed_locs`.
  - Assert the player stands on a passable tile inside the real map (overmaps −1..3 × −2..1) at that start's terrain.
  - The test must fail if the scenario's map choice is dropped.
- **A3 Guided playtest V1 (with the user).**
  - New world → "Sài Gòn, 2009" → each start.
  - Click-to-move and click-to-examine (verifies A1).
  - Walk into a hẻm, ride the motorbike over a bridge, take the ferry, fish, visit three landmarks.
  - Screenshots by the user go into `doc/saigon/art/`. Close ledger row V1 and record any new findings as units.

**Phase B: upstream intake (one way: CleverRaven → this fork)**
- **B0.** Make the remote fetch-only: `git remote set-url --push upstream no_push`. This is a local git config change and reversible.
- **B1 Intake check.**
  - `git fetch upstream`.
  - Write `doc/saigon/UPSTREAM_INTAKE.md` (appended each time): the incoming commit range, the files that overlap the fork's engine edits and the mod's dda dependencies (JSON ids the mod copies from or overrides), and the risks.
  - The user approves the intake before merging.
- **B2 Merge.**
  - On a branch `saigon/upstream-intake-YYYYMMDD`, merge `upstream/master` (merge, never rebase or force-push).
  - Resolve conflicts, keeping the fork's behaviour.
  - Rebuild curses, tiles and tests. Run all gates, plus `cata_test` without mods for the touched engine areas.
  - Merge into the fork's main line and push to `origin` only.
  - Repeat B1–B2 per intake.

**Phase C: Vietnamese translation**
- **C1.** Run `lang/extract_json_strings.py` on `data/mods/saigon_2000s`, fix its failures, and add it to `check_mod.sh`.
- **C2.** Write a `vi` `.po` for the mod's strings in chunks: names, then descriptions, snippets and dialogue. Check it with a `LOCALIZE=1` build.
- **C3.** Add `doc/saigon/GLOSSARY.md` for the Vietnamese terms used in the English text.

**Phase D: content and art polish**
- **D1.** Derive recipes for the snakehead, tilapia, pangasius, walking catfish, swamp eel, cobra and rùa ba gờ sprites. Add a contact sheet.
- **D2.** R6b port and shipyard corrections on the real map.
- **D3.** One content review `doc/saigon/review/B_content_review.md` (authenticity, mechanics, JSON) closes B2.R–B9.R. Fixes become units.

**Phase E: later**
- PERF pass 2.
- B4c heat index, if the playtest shows a need.
- I-B8a/I-B8b2.
- The megacity decision.

### Verification for every unit
- `tests/cata_test --mods=dda,saigon_2000s "[saigon]"` passes. Each new test fails before its fix.
- `tools/saigon/check_mod.sh` is clean.
- `tools/saigon/qa_game_load.sh` shows LOADED after any engine or gfx change.
- A1 is verified by the user's clicks.
- B2 also runs the unmodded `cata_test` areas around the merged engine files.
- No push except to `origin` (andy1912/Cataclysm-DDA). Nothing goes to CleverRaven.

---

## Update 2026-10-08: Saigon NPCs, their inventory and missions (appended; nothing above is changed)

### Context
The user shared an outside evaluation ("vanilla NPCs are not missing from the Saigon mod") and asked for a plan to enrich Saigon's NPC lists, inventory and missions. Units A0–A2 are committed. A3 (the user's mouse check) runs in parallel; the user chose to start the NPC work now.

### What the evaluation got right and wrong (checked against the code)
**Wrong, or already done:**
- `ITEM_BLACKLIST` and `MONSTER_BLACKLIST` exist (`src/init.cpp:317,449`), and dda mods use them.
- The region already has `highways`, `forest_trails` and railroads off and `map_extras: no_map_extras` (B8g-2).
- Overmap specials are whitelisted to `SAIGON`, so dda's refugee center, labs and evac shelters are not placed.
- Zombie cops and soldiers are not reachable (the L-loc7 audit lists every reachable monster).
- Street traffic is Saigon's (L-loc5).

**Right, and the real gaps:**
1. **Random wanderers are dda's.** `game::perhaps_add_random_npc` (`src/game.cpp:10440`) picks `npc_class::random_common()` (`src/npc_class.cpp:363`) from every class with `"common": true`, which is the default. dda has 20 such classes: cowboy, bounty hunter, moonshiner, hunter, soldier, farmer, thug, lab mutant, robofac intercoms… The mod's two classes are `common: false`.
2. **Names are American.** NPC names expand `<male_full_name>` / `<female_full_name>` (`data/json/snippets/names.json`), built from `data/names/en.json`. Mod snippets *append* weighted entries to a category (`src/text_snippets.cpp:37–82`).
3. **Missions are American.** Each random NPC gets one mission from the `ORIGIN_ANY_NPC` pool. dda's pool: find an American flag, corporate accounts, patient records, a weather log, a holy symbol, software, an inhaler; kill a Jabberwock (`forest_thick`); kill Zombie Mom (`house`); cattail jelly. The terrain targets barely exist on the real map.
4. **Gear is dda's.** The two mod classes have no `worn_override` / `carry_override` / `weapon_override`, so they get dda's default clothes and skill-based weapons (American guns included). The mod has no firearms.
5. **There are only 2 Saigon NPCs** (cô Ba, chú Tư in the chợ) and 1 mission.

### Decisions (user, 2026-10-08)
- Random NPCs are Vietnamese, plus a rare backpacker or expat (about 3%).
- Firearms: only công an and the army veteran, rarely (a fictionalised K54-style sidearm). Everyone else carries melee weapons and tools.
- Start now, alongside A3.

### Units (same working rules; each ends green and is committed)
- **N0 NPC audit.** Add an `npcs()` section to `tools/saigon/audit_us_content.py`, next to `fauna()`, so `check_mod.sh` fails on any regression. It fails on:
  - a non-`sgn_` class that is still `common`;
  - a non-`sgn_` mission left in the `ORIGIN_ANY_NPC` / `ORIGIN_SECONDARY` pools;
  - class gear groups that reach flagged items (reusing `walk()` / `entry()`).
  - Baseline expected: 20 classes and 10 missions flagged.
- **N1 Turn off dda's wanderers and missions.**
  - In `data/mods/saigon_2000s/npcs/vanilla_off.json`, add same-id `copy-from` overrides (the pattern of `monsters/wildlife.json`): each of the 20 common dda `npc_class` gets `"common": false`, and each pool mission gets `"origins": []`.
  - If `npc_class` or `mission_definition` copy-from does not take, fall back to a small engine seam guarded by a test.
- **N2 Vietnamese names** (`snippets/names.json`), written family name first:
  - `<sgn_family_name>`: Nguyễn, Trần, Lê, Phạm, Huỳnh, Võ, Phan, Trương, Đặng, Bùi, Đỗ, Hồ, Ngô, Dương, Lý…
  - middle names (Văn, Thị, Ngọc, Minh, Thanh, Hoàng, Hữu…) and given names, split by gender;
  - southern birth-order nicknames (anh Hai, chị Ba, Tư, Năm, Sáu, Út).
  - They're appended to `<male_full_name>` / `<female_full_name>` with weights that leave dda's English entries at about 3%.
- **N3 Saigon NPC classes (common).** In `npcs/classes.json`, matching the 12 professions plus the street, about 12 classes:
  - xe ôm, street vendor, market trader, student, công an phường, nurse, construction worker, fisherman, mechanic, monk, army veteran, and a rare backpacker/expat;
  - each with `common_spawn_weight`, skills, stat bonuses, traits, and `worn_override` / `carry_override` / `weapon_override` from new `sgn_npc_*` item groups (`itemgroups/npc_gear.json`) built from existing mod items (nón lá, áo mưa, dép, rựa, dao, ống tuýp, phone, VND wallet, food).
  - The two existing classes get gear overrides too.
- **N4 Firearms for công an and veterans.**
  - A fictionalised K54-style pistol (`items/gear/sidearm.json`, `copy-from` a dda 7.62×25 or 9×18 pistol plus its ammo and magazine, renamed) appears only in the công an and veteran weapon groups, at a low chance.
  - The item audit allow-list records why.
- **N5 Saigon missions** (`npcs/missions.json`). About 10 `ORIGIN_ANY_NPC` missions using existing goals (`MGOAL_FIND_ITEM`, `MGOAL_GO_TO_TYPE` on `sgn_*` / `sgn_lm_*` terrains, `MGOAL_KILL_MONSTER_TYPE`, `MGOAL_RECRUIT_NPC`). Examples:
  - medicine from a nhà thuốc; the family altar photo; rice sacks from a kho;
  - a motorbike part; a message to the monks at Vĩnh Nghiêm;
  - a student trapped at a trường; clearing the market of the fevered dead;
  - water during the dry season; escort to Ga Sài Gòn / Tân Sơn Nhất.
  - New items are added where needed (e.g. `sgn_anh_tho` altar photo).
- **N6 People at places.** NPC templates placed by the landmark and place generators (`tools/saigon/gen_saigon_landmarks.py`, `gen_places.py` via their NPC placement, as `sgn_npc_co_ba` is placed in the chợ):
  - a monk (Vĩnh Nghiêm), a ward police officer (UBND), a nurse (hospital), a stranded backpacker (Tân Sơn Nhất), a ticket clerk (Ga Sài Gòn), a xe ôm (Bến Thành).
  - Each has a short `talk_topic` and offers one N5 mission.
  - Shopkeepers trade in VND (`items/currency.json`).
- **N7 Dialogue flavour.** Saigon greeting and small-talk snippets for the classes, plus a background topic per class (where they were when the sốt lạ began). Translation-ready (feeds T1/T2).

### Tests (each fails before its unit)
- `tests/saigon_npc_test.cpp`, `saigon_random_npcs`: with the mod loaded, 300× `npc_class::random_common()` plus `npc::randomize`. Checks:
  - every class is `sgn_`;
  - ≥ 90% of names use a Vietnamese family name;
  - no firearm outside the công an / veteran classes;
  - a random NPC's mission comes from the Saigon pool.
- `saigon_npc_missions_place`: each N5 mission finds its target on the 2009 real map (reuse the `saigon_new_game_realmap_2009` setup).
- N6: the landmark structure test also checks each placed NPC is spawned and talkable.

### Verification
- `tools/saigon/check_mod.sh` is clean, including the N0 NPC audit at 0 flagged.
- `tests/cata_test --mods=dda,saigon_2000s "[saigon]"` passes.
- `tools/saigon/qa_game_load.sh` LOADED.
- In-game spot check with the user: debug-spawn a few random NPCs (debug menu "spawn NPC"), read their names, gear and offered mission.
- Append this record to `doc/saigon/PLAN.md` and add ledger rows N0–N7 (append-only). Push only when asked.

### Correction 2026-10-08 (N1, appended)
Nothing in the engine picks NPC classes at random: `npc_class::random_common()` has no callers, and `"common"` only adds a hobby background (`npc::randomize`). A random wanderer (`game::perhaps_add_random_npc`, and the starting NPC) is classless (`NC_NONE`):
- `Character::randomize` gives it a profession the scenario allows. That is already Saigon's, through the whitelist.
- `npc::starting_inv_passtime` dresses and arms it from the item groups `NC_NONE_<what>` / `NC_NONE_HARDENED_<what>`.

So N1 overrides those 40 groups with Saigon gear and no firearms, plus the 14 random-pool missions, instead of the class `common` flags. N3's Saigon classes serve the people placed at landmarks and places (N6), where a class is chosen explicitly.


---

## Update 2026-10-18: state against the plan, and the enrichment plan (appended; nothing above is changed)

### Where things stand
The ledger has 166 done units and 20 open. Gates are green at `e948a72cc6`: `check_mod.sh` is clean and `[saigon]` passes 33 cases / 7,884 assertions (seed 1021).

**Done against the plan:**
- **Pass 1 (B1–B10)** is complete, and so are both maps. Vietmap is procedural with a landmark pool; the 2009 real map is built from OpenStreetMap.
- **Phase A (playable and verified):** done. A1, the mouse fix, was verified in game by the user. A2 added the 2009 new-game test.
- **Phase B (upstream intake):** B0–B2 done. The fork is one-way and fetch-only.
- **Phase D:**
  - D1 (delta sprites), D2 (R6b, the 2009 port) and D3 (the content review closing B2.R–B9.R) are done.
  - Since then, the review's blocker (zombie hordes with guns) is fixed, as are the missions and NPC text (E1/E2), ice and the radio/loa phường (V1/V3), and the ba gác/ghe engines and xích lô wheels (V4).
- **N0–N7 (NPCs):** done, including the 2026-10-08 correction.
- **Since 2026-10-08:**
  - S1 separation;
  - E1 factions, chains and traders;
  - E2 zombies, hordes and encounters;
  - W1–W4: Vietnamese weapons, weapons in the world, police and army sites, everyday items;
  - V1–V4: food and ice, 11 everyday places, the city's voice, period vehicles.

**Open against the plan:**
1. **Tests owed** for agent-built content: E-tests, W-tests, V-tests (ledger rows).
2. **D3 fixes still open:**
   - B4-1/B4-2: the flood drain runs only around the player; flooding is not scaled by rain.
   - B5-2: gold prices.
   - B8-1: a locked, noisy cửa sắt kéo.
   - B8-2: the chợ stench.
   - B3-1/B3-2: profession kits with the mod's own items, and street-vendor recipes.
   - Brands: Co.op Mart in 6 files, Rạng Đông.
   - Smaller items: phở is listed as wheat, the population is "eight million" (6.1 M in 2004), the pharmacy has no antibiotics, the mosquito net is inert, the almanac, the horn part.
   - The old ice-less iced-drink recipes, and the `sgn_ao_cong_an` colour variants.
3. **Never played:** E1, E2, W1–W4 and V1–V4 are verified only by gates and tests. V1, the guided playtest, is still todo, and `qa_game_load.sh` needs a world with a saved character.
4. **Engine items:**
   - B4c heat index; I-B8a/I-B8b2/I-B5f.
   - The countdown that ignores insulation (V1).
   - Scheduled broadcasts that reach only the player's z-level (V3).
5. **Release S2–S5** waits on the user's decisions: name, platforms, dylibbundler, scenario names.
6. **T2 (vi translation) stays deferred** (user, 2026-10-18). T1 keeps every new string extractable, so nothing is lost by waiting.
7. **H1 hand art** waits for an artist.

### Decision recorded (user, 2026-10-18)
Keep enriching Vietnam. The translation stays delayed.

### The plan
Same working rules as before: small units, one commit each, gates green, ledger rows appended, push only when asked. Parallel agents get disjoint file ownership and do not commit.

**Phase F: make what exists solid (first, because content is outrunning verification)**
- **F1 Tests owed.** E-tests, W-tests and V-tests as listed in the ledger. Each test must fail when its content is removed.
- **F2 D3 remainder:**
  - a flood drain that runs on its own timer, with flooding scaled by rain;
  - gold prices;
  - the cửa sắt kéo (locked variant, loud when opened);
  - the chợ stench that draws zombies;
  - profession kits and recipes;
  - brand fixes (Co.op Mart → a fictional co-op chain, Rạng Đông → a fictional flask maker);
  - the smaller items.
- **F3 Guided playtest V1 with the user.** New world → each scenario → each start, then:
  - a loudspeaker and the radio, cooking with ice, a ride on the xích lô and the ghe máy;
  - a police HQ armory, a đình, a bia hơi;
  - two NPC missions.
  - Findings become units.
- **F4 Save-game QA.** Make a world with a saved character for `qa_game_load.sh`, so engine and graphics changes are load-tested again.

**Phase X: enrichment (in this order; each unit about one agent's sitting)**
- **X1 The calendar.** Events keyed to the date, through EOCs:
  - Tết: bánh chưng and bánh tét, mai and peach blossoms, lì xì, the family visit on the altar, and the empty streets of the first days.
  - Mid-Autumn: lanterns, mooncakes.
  - Vu Lan.
  - Rằm and mùng một: incense and offerings at altars and pagodas.
  - Starts are set in late December, so Tết arrives in the first in-game month.
- **X2 Monsoon life:**
  - flooded streets as gameplay: wading slows you, the xuồng works in flooded hẻm, things float off;
  - rain barrels and collectors next to tanks (I-B5f);
  - áo mưa that matters;
  - mosquitoes, so the net is useful; dengue as a slow illness;
  - heat in the dry season (B4c, only if the playtest shows a need).
- **X3 The street economy:**
  - gold as the money that keeps its value (with the F2 prices); a tiệm vàng trader;
  - ve chai scrap collectors who buy scrap;
  - sidewalk fuel sold in bottles (xăng lẻ);
  - xe ôm hire as a service.
  - Trader stock and wealth rules are tested.
- **X4 Makeshift crafts:**
  - bamboo (tre) and coconut working: ladders, rafts, baskets, water dippers, a bamboo spear set;
  - casting nets, mending boats, weaving mats and nón lá;
  - Recipes use the mod's items and tools. Books teach them (B7-1: more `book_learn`).
- **X5 Folk medicine and health:**
  - cạo gió and giác hơi as weak treatments;
  - thuốc nam herbs from gardens and canal banks, thuốc bắc from the herbalist;
  - an oresol that rehydrates;
  - antibiotics in the pharmacy (B5-7);
  - heat stroke and dengue tied to X2.
- **X6 Animals and the food chain:**
  - rats and stray dogs in the hẻm, chickens and ducks in yards;
  - fishing in the kênh with nets and traps;
  - market livestock;
  - farmland on the outskirts: rice paddies, cassava, vegetable plots that can be harvested.
- **X7 Districts with their own identity:**
  - **Chợ Lớn:** Hoa assembly halls (hội quán), Chinese herbal shops, roast-duck noodle shops, the clan associations.
  - **Thủ Thiêm:** the marsh across the river.
  - **Cần Giờ:** mangroves.
  - **Củ Chi:** the tunnels as the 2009 tourist site, not wartime.
  - **Bình Tây:** the wholesale market.
  - Each gets 1–3 buildings and a region or real-map rule.
- **X8 Faiths of the city:**
  - Cao Đài temple, Hòa Hảo home altars;
  - the Chăm mosque, the Mariamman Hindu temple;
  - parish life around the Catholic churches (bells, the evening rosary);
  - each with keepers, items and a small mission.
- **X9 The sound of the city:**
  - the noisy gates (from F2);
  - karaoke speakers and firecrackers as lures;
  - temple bells and the chợ stench;
  - generators that draw the dead.
  - Built on V3's sound pattern.
- **X10 Reading and media:**
  - the sports weekly (B7-2), the almanac with a use (B7-3);
  - fictionalised martial-arts novels and children's comic serials, cải lương tapes and VCDs for morale;
  - more skill books with `book_learn`.
- **X11 Professions and starts:**
  - new professions: lottery seller, ve chai collector, karaoke owner, returning Việt kiều, tour guide, dân phòng (ward militia);
  - their kits from the mod's items;
  - a start for each of the V2 places that suits one (nhà trọ, bia hơi, the đình);
  - the hẻm start in the 2004 scenario too (B2-7).
- **X12 The people, part 2:**
  - dân phòng as a faction;
  - Chợ Lớn clan elders;
  - recurring characters met in several places;
  - a three-step chain per district from X7.
- **X13 Vehicles, part 2:**
  - a motorbike horn part;
  - sidewalk repair (sửa xe vỉa hè) as a service and a skill path;
  - motorbike theft and locks;
  - a dinghy for flooded streets (with X2).
- **X14 Zombies, part 2 (B9-10):**
  - the Saigon zombies get behaviour, not just new skins: the fevered radiate heat, the xe ôm dead still wear helmets, market dead smell;
  - one city-specific mutation line, with evolutions.

**Later (unchanged):** T2 vi translation (after enrichment settles); release S2–S5 (after the user's decisions); H1 art; PERF; megacity.

### Verification for each unit
- `check_mod.sh` is clean.
- `[saigon]` passes, with new tests that fail without the unit.
- The audit stays at 0: no American content, and guns only through `POLICE_ARMY_GUN_GROUPS` and the guard.
- Every new string extracts (T1).
- New places pass the structure test.
- Phase X content goes into F3-style playtests as it lands.

---

## Update 2026-10-19: art and sound as downloadable packs (appended; nothing above is changed)

### Decision (user, 2026-10-19)
The Saigon graphics and, later, the Saigon sound will both be revised and offered as downloads.

### Where things stand
- **Graphics:** the mod's sprites live inside the mod (`data/mods/saigon_2000s/gfx`, 984 KB): mod tilesets for UltimateCataclysm and the Larwick Overmap, derived and drawn by the G/D units, sources in `art/saigon/`. With any other tileset they are not loaded (the log says "not compatible", which is harmless). H1, the hand-art pass, is still open.
- **Sound:** the game now builds with sound (`SOUND=1`, SDL3_mixer 3.2.4; see `doc/saigon/SOUND_PLAN.md`). CC-Sounds (CC-BY-SA-4.0) is installed locally in `./sound/`, which is gitignored and never committed. The Saigon pack (SND1–SND5) is not started.

### The plan
- **DL1 Saigon tileset pack.** After H1 and the art revisions, publish the sprites as a download attached to a GitHub Release on the fork (andy1912/Cataclysm-DDA), named by version (`saigon-tiles-<version>.zip`).
  - The user chooses the form: a mod tileset overlay (as now, needs UltimateCataclysm), or a full standalone tileset.
  - The mod keeps a small built-in set so the game is complete without the download.
  - Credits and licences go in the pack: derived work from CC-BY-SA tilesets stays CC-BY-SA.
- **DL2 Saigon soundpack.** Units SND1–SND5 build `sound/Saigon/`: CC-Sounds plus Saigon variants and overrides, under CC-BY-SA with per-file credits (sourcing rules in SOUND_PLAN.md). It is published as a Release download (`saigon-sound-<version>.zip`), not committed: audio is large and the base pack is third-party.
- **DL3 Packaging script.** `tools/saigon/package_assets.sh` builds both zips from their sources, writes a manifest (file list, sizes, sha256, licences), and checks every file has a credit line. It uploads nothing; the user attaches the zips to a Release.
- **DL4 Install guide.** A section in the player docs: unzip the tileset into `gfx/`, unzip the soundpack into `sound/`, select both in Options, restart.
- **Release builds (S2–S5)** ship the code and mod only, without the playtest mod. They link to the two downloads.

---

## Update 2026-10-20: the Cataclysm Saigon release (appended; nothing above is changed)

### Decisions (user, 2026-10-20)
- **Name:** Cataclysm Saigon.
- **Platforms:** macOS (Apple Silicon and Intel), Windows and Linux.
- **Scenarios:** "Somewhere in Nam" (procedural, `sgn_saigon_2004`) and "Saigon 2009" (real map, `sgn_saigon_2009`). The ids are unchanged, so saves and tests are unaffected.
- **Contents:** all resources are included: every tileset, the CC-Sounds soundpack, both maps and the full mod.

### How it is built
`.github/workflows/saigon-release.yml` runs on GitHub's machines, because one Mac cannot produce the Windows, Linux and universal macOS builds. It is adapted from upstream's `release.yml`, which already ships these platforms (same pinned actions, the same source-built SDL3 stack, dylibbundler, ad-hoc codesigning).

| Platform | Output |
|---|---|
| macOS | one universal dmg (arm64 + x86_64) |
| Windows | x64 zip (MSVC + vcpkg) |
| Linux | x64 tar.gz |

Each file gets a sha256 and is attached to the release `Cataclysm Saigon <version>` (tag `saigon-v<version>`).

The packaged tree differs from the repo in four ways:
- `data/mods/default.json` preselects `dda` + `saigon_2000s`;
- the `saigon_playtest` cheat mod is removed;
- README.md is replaced by `doc/saigon/RELEASE_README.md`;
- the build is English only, because the fork has no translation catalogues yet (T2 is deferred).

**To start it:**

```bash
git tag saigon-v0.1.0 && git push origin saigon-v0.1.0
```

Once the workflow file is on `master`, it can also be started from the Actions tab (Run workflow).

### Known limits
- **macOS** apps are ad-hoc signed, not notarised, so the first launch needs right-click → Open. Notarisation needs an Apple Developer account.
- **Windows** builds are unsigned, so SmartScreen warns.
- **Untested on Windows:** the fork's engine patches have only been built with clang on macOS. The first MSVC build is their first test there.
