# Saigon 2000s fork: progress ledger

Base: upstream `CleverRaven/Cataclysm-DDA` @ `fe6a10c2b1425882574b4ad7bfbebc4c6170dbf8` (2026-09-28)
Branch: `saigon/pass1-vertical-slice`. Remotes: `upstream` = CleverRaven (the fork `origin` gets added when the user provides its URL).
Plan: see `doc/saigon/PLAN.md`.

## Resume protocol
1. Read this file, then run `git log --oneline -10` and `git status`.
2. If a unit is marked `in-progress`, check `git diff`. Either finish that unit or revert its partial changes.
3. Pick the first `todo` unit whose dependencies are `done`. Mark it `in-progress`, do the work, mark it `done` with the commit SHA, and commit with the message `saigon: <ID> <summary>`.
4. Build (incremental): `CXXFLAGS=-D_XOPEN_SOURCE_EXTENDED make -j4 RELEASE=1 DEBUG_SYMBOLS=1 LOCALIZE=0 TILES=0 SOUND=0 NCURSES_PREFIX=ncurses cataclysm`. Validate the mod: `tools/saigon/check_mod.sh saigon_2000s` (checks exit code, 'Error loading data', and debug.log ERROR/WARNING lines).

## Units
| ID | Status | Commit | Output | Depends | Next action / notes |
|---|---|---|---|---|---|
| S0.1 clone + branch | done | - | repo | - | |
| S0.2 deps | done | - | - | - | Upstream is SDL3-only since 2026-08-11 (doc/c++/COMPILING.md). Homebrew on macOS 13 builds from source (hours), so it was aborted; nothing installed. Curses build needs no deps. |
| S0.3a curses build (RelWithDebInfo equiv.) | done | - | ./cataclysm | S0.2 | `CXXFLAGS=-D_XOPEN_SOURCE_EXTENDED make -j4 RELEASE=1 DEBUG_SYMBOLS=1 LOCALIZE=0 TILES=0 SOUND=0 NCURSES_PREFIX=ncurses cataclysm` (macOS: wide-char define only set when LOCALIZE=1, and there is no libncursesw → upstream Makefile bug, candidate fork fix), log in ~/code/cdda-saigon-logs/. Used for --check-mods on every unit |
| S0.3b cata_test | done | - | tests/cata_test | S0.3a | `CXXFLAGS=-D_XOPEN_SOURCE_EXTENDED make -j4 RELEASE=1 DEBUG_SYMBOLS=1 LOCALIZE=0 TILES=0 SOUND=0 NCURSES_PREFIX=ncurses tests`. Smoke: `./tests/cata_test --user-dir=<dir>/ --mods=dda,saigon_2000s "[force_load_game]"` → 1/1 passed; mod pack load 18 ms vs dda 20.9 s |
| S0.3c SDL3 tiles build | todo | - | cataclysm-tiles | - | needed only for V1 screenshots. Needs SDL3>=3.4 frameworks (libsdl-org dmg → ~/Library/Frameworks, FRAMEWORK=1) + glslang; build with BUILD_SHADER_FORMATS=spv and run with CATA_DISABLE_SPRITE_SHADERS=1 to avoid building shadercross. Ask the user before downloading |
| S0.4 ledger + plan | done | - | doc/saigon/ | - | |
| A4.1 modding analyst draft | done | (this) | analysis/d4_r1.md | S0.1 | Key: ITEM+subtypes; vehicle_group append-only → C1; --check-mods exit-code bug → C2; region feature_flag whitelist |
| A4.2 modding critic r1 | done | - | analysis/critic_d4_r1.md | A4.1 | |
| A4.3 modding rev + critic r2 | done | - | d4_r2 / critic_d4_r2 | A4.2 | r1 REJECT: 0/3 major/10 minor, cite fail 0.7%; majors: C1 has JSON routes, add item MIGRATION, missing schemas vehicle_part/placement/nested_mapgen/ter/furn |
| A4.4 modding rev + critic r3 | done — PASS (0/0/4 minor, 0/627 cite fail); risk entries RR-D4-1..11 in critic_d4_r3.md | - | d4_r3 / critic_d4_r3 | A4.3 | r2 REJECT 0/1 major/5 minor, cite fail 0%; major: C6 missed double options init (already fixed in 2efb03fe98); C2 is really rc 134 abort, not exit 0 |
| A2.1 mapgen analyst draft | done | (this) | analysis/d2_r1.md | S0.1 | Key: city streets hardcoded in overmap_city.cpp; 6x6 GLOBALLY_UNIQUE district special for pass 1; nhà ống via omt_stack+check_z; canals only in specials; bugs: regional_settings.cpp:809, overmap_city.cpp:268-277 infinite loop |
| A2.2 mapgen critic r1 | done | - | critic_d2_r1.md | A2.1 | |
| A2.3 mapgen rev + critic r2 | done | - | d2_r2 / critic_d2_r2 | A2.2 | r1 REJECT: 0 blocker/2 major/14 minor, cite fail 3.2%; majors: bike parking destroys shutters, roof connectivity |
| A2.4 mapgen rev + critic r3 | done — PASS (0/0/9 minor, 0/633 cite fail) | - | d2_r3 / critic_d2_r3 | A2.3 | r2 REJECT 0/1 major/9 minor, cite fail 0.5%; major: roof-walk corner continuity (PREFIX ignores rotation) |
| A3.1 climate/vehicle analyst draft | done | (this) | analysis/d3_r1.md | S0.1 | JSON can't hit Saigon temps (±12 K annual swing hardcoded weather_gen.cpp:38,42) → B4b GO; monsoon timing via weather_type time conditions OK in JSON; B4c GO (humidity-limited sweat); vehicles designed + load-tested |
| A3.2 critic r1 | done | - | | A3.1 | |
| A3.3 rev + critic r2 | in-progress (d3_r2 written; critic r2 running) | - | d3_r2 / critic_d3_r2 | A3.2 | r1 REJECT 0/9 major/13 minor, cite fail 0%; B4b must precede B4c; flood EOC never deactivates; water temp hardcoded; funnel int truncation; horde mostly awake; ghe/xích lô are reskins (label + tie to P2) |
| A3.4 rev + critic r3 | todo | - | | A3.3 | skip if r2 PASS |
| A1.1 rendering analyst draft | done | - | analysis/d1_r1.md | S0.1 | |
| A1.2 critic r1 | done | - | | A1.1 | |
| A1.3 rev + critic r2 | done (r2 REJECT 0/4 major/8 minor, 0.8%: vsync blocks present; NPC light colour stale; emitter rule wrong bubble size; R3/R4 merge footprint) | - | d1_r2 / critic_d1_r2 | A1.2 | r1 REJECT 0/10 major/9 minor, cite fail 1.6%; present unthrottled on map path; camera z not viewer z; lightmap rebuilt every turn; cast_zlight bench synthetic; iso spans 15+ fns; golden test misses GPU path |
| A1.4 rev + critic r3 | in-progress | - | d1_r3 / critic_d1_r3 | A1.3 | final round |
| A5 integration critic | todo | - | analysis/integration.md | A1–A4 | |
| A6.1 TDD ch 1–2 | todo | - | TDD.md | A5 | |
| A6.2 TDD domain chapters | todo | - | TDD.md | A6.1 | |
| A6.3 TDD roadmap + risks | todo | - | TDD.md | A6.2 | |
| A6.4 citation check | todo | - | tools script | A6.3 | zero misses |
| B0 content bible | done | - | CONTENT_BIBLE.md | - | |
| C6 curses test-mode fixes | done | (this) | src/game.cpp, src/main.cpp, tools/saigon/check_mod.sh | - | (a) init_ui looped forever in ensure_term_size (stdscr uninitialized in test_mode); (b) non-TILES --check-mods ran options init() twice → ~106k option errors, exit 1. Baseline `check_mod.sh dda` = OK in ~60 s |
| B1 mod skeleton | done | 20f1e7d394 | data/mods/saigon_2000s/modinfo.json | A4, A2 | check_mod.sh OK; negative control (typo'd key) correctly FAILs. GENERIC_*_ID options deferred to B2/B3 |
| B2a scenario + start locations | done | dc99fe7e0c | scenario/*.json | B1 | Start locs are PLACEHOLDERS (copy-from sloc_house / sloc_grocery_store): retarget in B8b/B8d. Starts in CDDA 'winter' (= Dec dry season), so B4a must route the Saigon region + weather or the player starts in snow |
| B2b backstory/intro EOC + snippets | done | f3c5b2adde | scenario/eoc_intro.json, snippets/ | B2a | Snippet categories sgn_loa_phuong/sgn_radio/sgn_newspaper/sgn_note need carrier items (B7b) and speaker/radio sources (B8) to surface in play |
| B2.R review | todo | - | review/B2.md | B2b | |
| B3a professions 1–5 | done | c690cd630b | professions/professions.json | B1 | sgn_xe_om, sgn_street_vendor, sgn_market_trader, sgn_student, sgn_cong_an. PLACEHOLDER dda items (flip_flops, helmet_motor, portable_stove, straw_hat) and vehicles (scooter, bicycle); swap after B5c/B6a |
| B3b professions 6–11 | done | ff710000cd | professions/professions.json, modinfo GENERIC_*_ID | B3a | + sgn_survivor generic; scenario profession whitelist |
| B3.R review | todo | - | | B3b | |
| B4a weather JSON | done | b811a25b42, 531563aa68 | region/*.json, tests/saigon_weather_test.cpp | B1 | Test [saigon] PASSES (3 seeds): mean 27.4 C, wet-season rain hours 22% vs dry 1.4%, storms afternoon-clustered. Extremes 5–46 C = B4a defect → B4b must tighten test to min≥18, max≤40 |
| B4b monsoon C++ + test | todo | - | | A3, B4a | only if A3 says JSON is insufficient |
| B4c heat-index C++ + test | todo | - | | A3 | only if A3 says needed |
| B4.R review | todo | - | | B4a | |
| B5a street food | done | 17739cf864 | items/food/street_food.json | B1 | 12 items. TODO B5d: whole durian + whole bánh chưng via recipes/disassembly; B8f: rau muống harvestable near canals; B5e/B10: patch dda mango description ('imported') |
| B5b drinks + condiments | done | edb5a24615 | items/food/drinks_condiments.json | B5a | 7 items; ice (đá) as a resource deferred: needs FROZEN-water handling (pass 2 / A3) |
| B5c gear/clothing/tools | done | 1cca7bcdcb | items/gear/gear.json | B1 | 9 items. Engine note: any worn RAINPROOF item blocks ~98% rain wetting (src/weather.cpp:395-396) → nón lá is SUN_GLASSES+WATER_FRIENDLY only; per-part rain cover = pass-2 (A3) |
| B5d recipes | done | 729fd8a7a0 | recipes/*.json | B5a–c | 6 food + 2 vehicle-part recipes with book_learn. TODO: whole durian/bánh chưng disassembly; nước mắm fermentation |
| B5e loot item_groups | done | 18e0c8e552 | itemgroups/loot.json | B5a–c | 9 sgn_* location groups + default_zombie_clothes override. Groups get wired into mapgen in B8 |
| B5.R review | todo | - | | B5e | |
| B6a motorbike + scooter | done | 27be0aaa7d | vehicles/*.json | B1 | sgn_veh_underbone (3 tiles), sgn_veh_xe_tay_ga; professions switched to sgn gear. TODO: drag/efficiency tuning test (d3 §5.b step 2) |
| B6b ba gác + xích lô + bicycle | done | 44b4673f75 | vehicles/vehicles.json | B6a | sgn_veh_ba_gac_may is 3 wide → street-only (not hẻm) placement rule for B8/B6d |
| B6c riverboats | done | 44b4673f75 | vehicles/*.json | B1 | sgn_veh_xuong (oars), sgn_veh_ghe (long-tail). TODO: boat_navigates_shallow_canal test before boats are placed in canals (B8f) |
| B6d vehicle_groups/placement | todo | - | | B6a–c | |
| B6.R review | todo | - | | B6d | |
| B7a skill books | done | c56f35800e | items/books/skill_books.json | B1 | 7 books |
| B7b fiction/sutras/newspapers + book_learn | done (book_learn moves to B5d) | dc907d64fb | items/books/fiction_media.json | B7a | snippet carriers sgn_newspaper/sgn_ward_notice/sgn_note_handwritten need spawning via B5e item_groups |
| B7.R review | todo | - | | B7b | |
| B8a shared palettes | todo | - | | B1 | |
| B8b nhà ống | todo | - | | B8a | |
| B8c hẻm block | todo | - | | B8a | |
| B8d chợ | todo | - | | B8a | |
| B8e pagoda + café + chung cư | todo | - | | B8a | |
| B8f canal | todo | - | | B8a | |
| B8g region city pools + specials | todo | - | | B8b–f | |
| B8.R review | todo | - | | B8g | |
| B9a monsters + monstergroups | todo | - | | B1 | |
| B9b NPCs + talk_topic + mission | todo | - | | B2 | |
| B9.R review | todo | - | | B9b | |
| B10 de-Americanize blacklists | todo | - | | B8g | |
| V1 playtest + screenshots | todo | - | | all B | |

## Naming note
The domain reports each number their own C++ seams. Modding (d4) uses C1 = vehicle_group override, C2 = check-mods exit code, C6 = curses test mode. Mapgen (d2_r3) proposes its own "C1" rotation-aware neighbour check, tracked here as **M-C1** to avoid a clash.
