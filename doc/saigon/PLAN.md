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
