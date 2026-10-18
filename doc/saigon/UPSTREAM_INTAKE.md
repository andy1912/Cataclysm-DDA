# Upstream intake log

The Saigon fork is a standalone project. CleverRaven's changes come **in** to the fork after a check; nothing goes back. The `upstream` remote is fetch-only (`git remote set-url --push upstream no_push`). Each intake is merged on a branch `saigon/upstream-intake-YYYYMMDD`, never rebased, and only reaches `origin` after the gates pass.

This file is appended to, one section per intake.

## 2026-10-15

- **Range:** `fe6a10c2b1` (Sep 28, the fork's base) to `27de780e67` (upstream master, Oct 15).
  - 317 commits, 632 files.
  - By area: `data/json` 188, `data/mods` 120, `data/shaders` 14, `src` and `tests` most of the rest.
- **Branch:** `saigon/upstream-intake-20261015`, merge commit `cd7b1068e9`.
- **Overlap with the fork's engine edits** (9 files): `src/do_turn.cpp`, `game.cpp`, `map.cpp`, `map.h`, `overmap.cpp`, `savegame.cpp`, `scenario.cpp`, `scenario.h`, `sdltiles.cpp`.
  - Git merged all of them without conflicts.
  - Checked by hand that every fork change is still in place and still fits the code around it:
    - the real-map loader and scenario map choice (`overmap.cpp`, `game.cpp`, `scenario.*`);
    - the mouse mapping (`sdltiles.cpp`: upstream rewrote 1,370 lines there, and `get_display_buffer_render_rect` still blits top-left at an integer scale, which `display_buffer_from_render` inverts);
    - the vehicle-cache use-after-free fix (`map.cpp`, `map.h`);
    - the `drop_bash_results` format fix;
    - the `start_new_game_for_tests` hook.
- **What broke, and was fixed on the branch:**
  - Upstream changed the `visit_items` callback to take `const item_location &`. `tests/saigon_npc_test.cpp` was ported.
  - A stale tiles precompiled header (`obj/tiles/pch`): build-only, cleared.
- **Mod dependencies on dda:** `check_mod.sh` is clean, so every dda id the mod copies from or overrides still exists. `audit_us_content.py` reports 0, and `check_refs.py` reports 0.
- **Gates:**
  - `[saigon]`: 33 cases / 7,825 assertions, no logged errors (seed 1015).
  - dda `[map],[vehicle],[overmap],[npc]`: 392 cases / 1,253,120 assertions, green.
  - Tiles build: see the ledger row UB2.
