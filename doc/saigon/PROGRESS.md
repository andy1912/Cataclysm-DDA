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
| S0.3b cata_test | todo | - | tests/cata_test | S0.3a | `make -j4 RELEASE=1 DEBUG_SYMBOLS=1 LOCALIZE=0 TILES=0 tests` |
| S0.3c SDL3 tiles build | todo | - | cataclysm-tiles | - | needed only for V1 screenshots. Needs SDL3>=3.4 frameworks (libsdl-org dmg → ~/Library/Frameworks, FRAMEWORK=1) + glslang; build with BUILD_SHADER_FORMATS=spv and run with CATA_DISABLE_SPRITE_SHADERS=1 to avoid building shadercross. Ask the user before downloading |
| S0.4 ledger + plan | done | - | doc/saigon/ | - | |
| A4.1 modding analyst draft | done | (this) | analysis/d4_r1.md | S0.1 | Key: ITEM+subtypes; vehicle_group append-only → C1; --check-mods exit-code bug → C2; region feature_flag whitelist |
| A4.2 modding critic r1 | done | - | analysis/critic_d4_r1.md | A4.1 | |
| A4.3 modding rev + critic r2 | in-progress (critic r2 running) | - | d4_r2 / critic_d4_r2 | A4.2 | r1 REJECT: 0/3 major/10 minor, cite fail 0.7%; majors: C1 has JSON routes, add item MIGRATION, missing schemas vehicle_part/placement/nested_mapgen/ter/furn |
| A4.4 modding rev + critic r3 | todo | - | d4_r3 / critic_d4_r3 | A4.3 | skip if r2 PASS |
| A2.1 mapgen analyst draft | done | (this) | analysis/d2_r1.md | S0.1 | Key: city streets hardcoded in overmap_city.cpp; 6x6 GLOBALLY_UNIQUE district special for pass 1; nhà ống via omt_stack+check_z; canals only in specials; bugs: regional_settings.cpp:809, overmap_city.cpp:268-277 infinite loop |
| A2.2 mapgen critic r1 | done | - | critic_d2_r1.md | A2.1 | |
| A2.3 mapgen rev + critic r2 | done | - | d2_r2 / critic_d2_r2 | A2.2 | r1 REJECT: 0 blocker/2 major/14 minor, cite fail 3.2%; majors: bike parking destroys shutters, roof connectivity |
| A2.4 mapgen rev + critic r3 | in-progress | - | d2_r3 / critic_d2_r3 | A2.3 | r2 REJECT 0/1 major/9 minor, cite fail 0.5%; major: roof-walk corner continuity (PREFIX ignores rotation) |
| A3.1 climate/vehicle analyst draft | todo | - | analysis/d3_r1.md | S0.1 | |
| A3.2 critic r1 | todo | - | | A3.1 | |
| A3.3 rev + critic r2 | todo | - | | A3.2 | |
| A3.4 rev + critic r3 | todo | - | | A3.3 | skip if r2 PASS |
| A1.1 rendering analyst draft | todo | - | analysis/d1_r1.md | S0.1 | |
| A1.2 critic r1 | todo | - | | A1.1 | |
| A1.3 rev + critic r2 | todo | - | | A1.2 | |
| A1.4 rev + critic r3 | todo | - | | A1.3 | skip if r2 PASS |
| A5 integration critic | todo | - | analysis/integration.md | A1–A4 | |
| A6.1 TDD ch 1–2 | todo | - | TDD.md | A5 | |
| A6.2 TDD domain chapters | todo | - | TDD.md | A6.1 | |
| A6.3 TDD roadmap + risks | todo | - | TDD.md | A6.2 | |
| A6.4 citation check | todo | - | tools script | A6.3 | zero misses |
| B0 content bible | done | - | CONTENT_BIBLE.md | - | |
| C6 curses test-mode fixes | done | (this) | src/game.cpp, src/main.cpp, tools/saigon/check_mod.sh | - | (a) init_ui looped forever in ensure_term_size (stdscr uninitialized in test_mode); (b) non-TILES --check-mods ran options init() twice → ~106k option errors, exit 1. Baseline `check_mod.sh dda` = OK in ~60 s |
| B1 mod skeleton | todo | - | data/mods/saigon_2000s | A4, A2 | |
| B2a scenario + start locations | todo | - | | B1 | |
| B2b backstory/intro EOC + snippets | todo | - | | B2a | |
| B2.R review | todo | - | review/B2.md | B2b | |
| B3a professions 1–5 | todo | - | | B1 | |
| B3b professions 6–11 | todo | - | | B3a | |
| B3.R review | todo | - | | B3b | |
| B4a weather JSON | todo | - | | B1 | lat 10.82 / lon 106.63 via EXTERNAL_OPTION |
| B4b monsoon C++ + test | todo | - | | A3, B4a | only if A3 says JSON is insufficient |
| B4c heat-index C++ + test | todo | - | | A3 | only if A3 says needed |
| B4.R review | todo | - | | B4a | |
| B5a street food | todo | - | | B1 | |
| B5b drinks + condiments | todo | - | | B5a | |
| B5c gear/clothing/tools | todo | - | | B1 | |
| B5d recipes | todo | - | | B5a–c | |
| B5e loot item_groups | todo | - | | B5a–c | |
| B5.R review | todo | - | | B5e | |
| B6a motorbike + scooter | todo | - | | B1 | |
| B6b ba gác + xích lô + bicycle | todo | - | | B6a | |
| B6c riverboats | todo | - | | B1 | |
| B6d vehicle_groups/placement | todo | - | | B6a–c | |
| B6.R review | todo | - | | B6d | |
| B7a skill books | todo | - | | B1 | |
| B7b fiction/sutras/newspapers + book_learn | todo | - | | B7a, B5d | |
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
