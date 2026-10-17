# Engine patches carried by the Saigon fork

The fork leaves the original game's resources untouched. Nothing under `data/json/`, the other
mods in `data/mods/`, `gfx/`, `lang/` or the upstream docs differs from the upstream commit the
fork last took in (`git merge-base HEAD upstream/master`). All Saigon content lives in the mod
(`data/mods/saigon_2000s/`), with its tools in `tools/saigon/`, art sources in `art/saigon/`,
docs in `doc/saigon/` and tests in `tests/saigon_*`. The only other changes are the engine
(`src/`) files below. Each one is listed here with the reason the mod needs it and the test that
covers it.

`tools/saigon/check_separation.sh` enforces this. It diffs the working tree and HEAD against the
merge-base, and fails if a changed path is outside the fork-owned places and not in the
allowed list at the end of this file. To change a new engine file, document it here first and
add it to that list.

Marker convention: new engine hunks carry a `Saigon fork` comment (sometimes with the ledger
tag, e.g. `Saigon fork (QA2)`). Some older hunks predate the convention; they are noted below.

Reproduce any section with `git diff $(git merge-base HEAD upstream/master) HEAD -- <file>`.

---

## src/display_buffer_coords.h (new file)

- **What:** `display_buffer_from_render()` maps a mouse position in render (drawable pixel)
  coordinates back into the display buffer by undoing the integer-scaled blit of the buffer
  into the window. It has no SDL dependency, so the curses test build can test it.
- **Why:** on HiDPI windows (macOS Retina, 2 drawable pixels per point) every click landed
  twice as far from the top-left corner as the pointer. The mod is played on macOS tiles.
- **Test:** `tests/saigon_mouse_test.cpp`, `saigon_mouse_click_maps_to_display_buffer`.
- **Marker:** header comment "(Saigon fork, A1)". Commit c624ad6c44.

## src/sdltiles.cpp

- **What:** the SDL3 branch of `window_to_display_buffer_coords()` now takes SDL's render
  coordinates and passes them through `display_buffer_from_render()` with the rect from
  `get_display_buffer_render_rect()`. It also logs the window, drawable, buffer and blit
  sizes once (`D_INFO`) to help diagnose mouse mapping. Adds `#include "display_buffer_coords.h"`.
- **Why:** same HiDPI click offset as above. Before the fix, SDL's render coordinates were
  returned unchanged, without undoing the blit.
- **Test:** `saigon_mouse_click_maps_to_display_buffer` covers the math. The SDL glue itself
  is tiles-only and checked by hand in the game.
- **Marker:** none in the hunk; the comment points to `display_buffer_from_render`, whose
  header carries "Saigon fork, A1". Commit c624ad6c44.

## src/do_turn.cpp

- **What:** `game::do_turn()` calls `gamemode->per_turn()` only if `gamemode` is set.
- **Why:** the turn-time harness runs whole turns without `start_game()`, so there is no gamemode.
  The game always has one in normal play, so nothing changes there.
- **Test:** `tests/saigon_perf_test.cpp`, `saigon_turn_time` (hidden, `[.][saigon_perf]`).
- **Marker:** "Saigon fork: tests drive do_turn() without start_game()...". Commit 6f714d98f2.

## src/game.cpp

Four separate changes:

1. **Test-mode terminal size** (`game_ui::init_ui`, curses build): in `test_mode` the code sets
   `TERMY`/`TERMX` to `EVEN_MINIMUM_TERM_HEIGHT`/`WIDTH` instead of reading curses and calling
   `ensure_term_size()`. Why: curses is not initialized under `--check-mods`, so the size read
   as 0 or -1 and `ensure_term_size()` blocked forever. `tools/saigon/check_mod.sh` depends on
   this. Test: `tools/saigon/check_mod.sh` (curses `--check-mods` run). Marker: none (C6, commit
   2efb03fe98, before the convention).
2. **Scenario map choice** (`game::start_game`): the first game in a world stores the scenario's
   `overmap_pregenerated_path` and `overmap_outside_region` as global vars. Later games in the
   same world keep that choice. Adds includes `global_vars.h` and `math_parser_diag_value.h`. Why:
   the "Sài Gòn, 2009" scenario plays on the pregenerated real map. Tests:
   `tests/saigon_realmap_test.cpp`, `saigon_new_game_realmap_2009`, `saigon_realmap_2009_loads`
   and `saigon_realmap_2009_countryside`. Marker: "Saigon fork: the first game in a world fixes
   which map it uses". Commits 122d6ced6a and d1bd4ef9ef.
3. **Forced placement keeps occupancy** (`place_critter_around`): the occupancy check is split
   into `can_place_creature()`. `forced` now skips only the terrain and sight rules, not the
   check for whether the tile is already taken. Why: horde monsters are placed forced onto
   squares `map::spawn_monsters` may already have filled. `creature_tracker::add` then logged
   "there's already a monster at" and dropped the creature, which fails any suite that treats
   a logged error as a failure. This is an upstream bug, not Saigon content. Test: the `[saigon]`
   suite (any spawn-heavy case, e.g. `saigon_place_spawns_people` in
   `tests/saigon_npc_test.cpp`) with logged errors failing the run. Marker: none; the block
   comment explains it (QA1, commit 578413b837).
4. **Test hook** `start_new_game_for_tests()`: runs `g->start_game()`. Why: tests drive the
   real "New game" path. Test: `saigon_new_game_realmap_2009`. Marker: in `game.h` (below).
   Commit 34b9dc6a24.

## src/game.h

- **What:** declares `start_new_game_for_tests()` and makes it a friend of `game`.
- **Why / test:** see game.cpp item 4.
- **Marker:** "Saigon fork: tests run the real \"New game\" path" and "Saigon fork: runs
  game::start_game ... for tests".

## src/main.cpp

- **What:** for `--check-mods`, `get_options().init()` and `load()` now run only in TILES builds
  (`#if defined(TILES)`).
- **Why:** non-tiles builds had already initialized the options, and a second `init()` left
  duplicate groups and dropped every option. `tools/saigon/check_mod.sh` uses the curses build.
- **Test:** `tools/saigon/check_mod.sh`.
- **Marker:** none; the comment explains it (C6, commit 2efb03fe98).

## src/map.cpp

1. **Vehicle-cache use-after-free** (QA2): new `map::resync_vehicle_lists_from_submaps()`
   rebuilds each level cache's `vehicle_list`/`zone_vehicles` from the vehicles the loaded
   submaps own, and drops dangling entries from `dirty_vehicle_list`. `map::load` calls it
   before `rebuild_vehicle_level_caches()`. In `loadn`, a vehicle with no parts left is
   removed with `remove_vehicle_from_cache()` across all z levels instead of only from the dirty
   list. Why: while `map::load` ran, generating one submap could free a vehicle (a wreck
   merging or losing all its parts) that another submap had already cached. `build_map_cache`
   then read the freed pointer and the game crashed (SIGSEGV) at New game. This is an upstream
   bug that the real map's many wrecks exposed. Test: `saigon_new_game_realmap_2009`, run with
   `--rng-seed-fuzz` through `tools/saigon/run_suite.sh`. Marker: "Saigon fork (QA2)" (two
   hunks). Commit 2e35f1011e.
2. **Format-string fix** in `drop_bash_results` debug messages (`%s` -> `%d` for int counts).
   Why: the wrong format logged an error whenever a vehicle part broke into items, which fails
   suites that treat logged errors as failures. This is an upstream bug. Test:
   `saigon_new_game_realmap_2009` (no logged errors). Marker: none (format-only change). Commit
   34b9dc6a24.

## src/map.h

- **What:** declares `map::resync_vehicle_lists_from_submaps()`.
- **Marker:** "Saigon fork (QA2)". See map.cpp item 1.

## src/map_helpers.cpp

- **What:** `clear_overmaps()` (a test helper compiled into the engine) first clears the
  creature tracker.
- **Why:** monsters left from a previous test were despawned into an overmap's horde map. Two
  on one square made `horde_map::spawn_entity` log "Attempted to insert a zombie at ...", which
  fails the run. This is an upstream bug that the many `[saigon]` world resets exposed.
- **Test:** every `[saigon]` test that calls `clear_overmaps()` (mapgen, landmarks, realmap, npc,
  perf and scene-dump tests).
- **Marker:** none; the comment explains it (QA1, commit 578413b837).

## src/overmap.cpp

- **What:** (1) in `overmap::generate`, a non-empty `overmap_pregenerated_path` global var
  (stored by `game::start_game`) overrides the `OVERMAP_PREGENERATED_PATH` option. Overmaps
  beyond the pregenerated set then start as `field`, not the option's lake. (2) If the loaded
  file is marked final (`pregenerated_final`), the whole procedural layout block (neighbour
  connections, rivers, lakes, oceans, forests, swamps, ravines, highways, cities, trails,
  railroads, roads, specials) is skipped. The diff is large only because that block is
  re-indented inside `if( !pregenerated_final )`. Sublevels, monster groups and radios still
  run. Adds includes `global_vars.h` and `math_parser_diag_value.h`.
- **Why:** the hand-made 2009 real map of Saigon must keep its layout. Without this, the city
  sat in an endless lake.
- **Test:** `saigon_realmap_loads_every_layer`, `saigon_realmap_reads_dda_single_layer_maps`
  (dda's single-layer maps still load and are not final), `saigon_realmap_2009_loads`,
  `saigon_realmap_2009_countryside`.
- **Marker:** "Saigon fork: the world's scenario choice ..." and "Saigon fork: a complete
  hand-made overmap (\"final\": true) keeps its layout". Commits 122d6ced6a and d1bd4ef9ef.

## src/overmap.h

- **What:** new member `bool pregenerated_final = false;`.
- **Marker:** "Saigon fork: set by unserialize_omap when a pregenerated file says \"final\": true".

## src/overmap_worldgen.cpp

- **What:** `overmapbuffer::get_overmap_region()` returns the `overmap_outside_region` global
  for overmaps with no pregenerated `.omap.gz` file, when the world has chosen a pregenerated
  map. The file-exists check is cached per (path, overmap). Adds includes `filesystem.h`,
  `global_vars.h`, `math_parser_diag_value.h`, `path_info.h` and `<map>`.
- **Why:** the countryside around the real city uses the Mekong-delta region
  (`sgn_saigon_delta`) instead of the city region.
- **Test:** `saigon_realmap_2009_countryside` (checks `get_overmap_region` inside and outside
  the map).
- **Marker:** "Saigon fork: with a pregenerated map chosen (game::start_game)...". Commit d1bd4ef9ef.

## src/savegame.cpp

- **What:** `overmap::unserialize_omap` now reads every object in an `.omap` file (one per z
  level), not only the first. The diff is mostly re-indentation. It also reads `"final"` into
  `pregenerated_final` and an optional `"cities"` array (name, x, y, size, population) into
  the overmap's cities. For a final overmap, roads at the map edge are recorded as
  inter-city road exits (`connections_out`), so generated neighbours join their roads to them.
- **Why:** the real map has upper floors and basements, named districts (shown on the overmap
  and used for city hordes), and must connect to the generated countryside.
- **Test:** `saigon_realmap_loads_every_layer`, `saigon_realmap_reads_dda_single_layer_maps`,
  `saigon_realmap_2009_loads` (district cities), `saigon_new_game_realmap_2009` (cities),
  `saigon_realmap_2009_countryside` (edge roads; no direct assertion on `connections_out`).
- **Marker:** three "Saigon fork:" comments (multi-layer/final, cities, road exits). Commits
  122d6ced6a, 6997858ec1 and d1bd4ef9ef.

## src/scenario.cpp

- **What:** loads optional `overmap_pregenerated_path` and `overmap_outside_region` strings and
  adds getters for them.
- **Why:** the scenario names its map (see game.cpp item 2).
- **Test:** `saigon_new_game_realmap_2009`.
- **Marker:** none in the .cpp hunk; the members in scenario.h carry it. Commits 122d6ced6a and
  d1bd4ef9ef.

## src/scenario.h

- **What:** members `_overmap_pregenerated_path` and `_overmap_outside_region`, and their getters.
- **Marker:** "Saigon fork: a pregenerated overmap set ..." and "Saigon fork: the region for
  overmaps beyond the pregenerated set".

## src/weather_gen.cpp

- **What:** optional 12-value monthly curves (`monthly_temperature`, `monthly_humidity`,
  `monthly_pressure`, `monthly_water_temperature`) in `weather_generator`, interpolated between
  month midpoints by `monthly_curve_value()`. A curve, when set, replaces the seasonal sinusoid
  and `*_manual_mod` values for that quantity, with flat noise (`noise_magnitude`,
  `daily_magnitude`, `humidity_noise`, `pressure_noise`). Loading rejects a curve that does not
  have exactly 12 values. Without curves, behaviour is unchanged.
- **Why:** Saigon has a tropical monsoon climate: hot all year, with a wet and a dry season. The
  four-season sinusoid cannot express it.
- **Test:** `tests/saigon_weather_test.cpp`: `monthly_climate_curve`, `saigon_monsoon_climate`,
  `saigon_water_is_warm`.
- **Marker:** none (B4b, commit f6bf096c3d, before the convention). All code is new and sits
  behind `if( monthly_* )`.

## src/weather_gen.h

- **What:** the optional curve members and noise magnitudes above, plus includes `<array>` and
  `<optional>`.
- **Marker:** none; the comment "Optional monthly climate curves" explains them.

## src/zzip.cpp

- **What:** zstd compression level for save archives is 3 instead of 7.
- **Why:** with megacity mode, autosave stalled the game for 4-5 s at level 7. Level 3 compresses
  about 4.6x faster for about 13% larger files, and existing saves load unchanged. See
  `doc/saigon/PERF.md`.
- **Test:** `tests/saigon_perf_test.cpp`, `saigon_zzip_level` (hidden, `[.][saigon_zzip_level]`,
  needs a world archive).
- **Marker:** none (one-token change; P2, commit c53bd510e8).

---

## Allowed engine files

`tools/saigon/check_separation.sh` reads the block below: one path per line, relative to the
repo root.

```allowed-engine-files
src/display_buffer_coords.h
src/do_turn.cpp
src/game.cpp
src/game.h
src/main.cpp
src/map.cpp
src/map.h
src/map_helpers.cpp
src/overmap.cpp
src/overmap.h
src/overmap_worldgen.cpp
src/savegame.cpp
src/scenario.cpp
src/scenario.h
src/sdltiles.cpp
src/weather_gen.cpp
src/weather_gen.h
src/zzip.cpp
```
