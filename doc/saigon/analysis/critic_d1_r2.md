# Critic D1 r2: Rendering & UI Pipeline (audit of d1_r2.md)

- Critic unit: A1.4-equivalent, round 2. Rubric: `doc/saigon/analysis/CRITIC_RUBRIC.md` (N=1, k=2).
- Code under audit: base SHA `fe6a10c2b1`; HEAD source differs only in the C6 hunks of `src/game.cpp` and `src/main.cpp`.
- Status: complete. Final sections first; the working notes from the interrupted first pass are kept as an appendix at the end.

## Verdict

**REJECT.** 0 BLOCKER, 4 MAJOR, 8 MINOR. Citation failure rate: 3/391 = 0.8%, under the 2% bar. The verdict fails on the MAJOR count only.

## Summary

r2 is a substantial, honest revision. Most r1 defects are fixed in the body, not just in the changelog. I checked these against code:
- Camera z definition and the look-mode path (`src/game.cpp:3374-3381`, `:6235-6246`).
- The 12-row `build_map_cache` caller table. All 12 sites exist with the stated z.
- The per-turn `set_lightmap_cache_dirty` loop (`src/do_turn.cpp:607-610`).
- The synthetic caveats for `cast_zlight`: zero `floor_cache`, `BOTH`, "TODO: add roofs", `UP`-only on `no_floor_gaps` (`src/lightmap.cpp:1295-1297`). The `-Os` claim is verified at `Makefile:279-281` and `:441-446`, with the build line at `doc/saigon/PROGRESS.md:19`.
- The 18-function projection inventory. A grep of every `is_isometric()`/`iso`/`zlevel_height` line in `src/cata_tiles.cpp`, mapped to its enclosing function, gives exactly the 16 rows listed, plus `set_draw_scale`, which only copies `zlevel_height` and is not a projection branch.
- The horizontal flip in iso (`:2826`, `:2849-2850`, `:2888-2893`; facing at `src/ranged.cpp:3352-3358` and `src/monmove.cpp:1272-1277`).
- The software-lane blind spot (`src/cata_shader.cpp:696-701`, `:819-820`).
- The four tile contexts sharing `ts_cache` (`src/sdltiles.cpp:6268-6318`).
- The platform guards: the `"gpu,opengl"` hint sits outside the `!__ANDROID__` block at `:657-669`, so it applies on Android as claimed.
- The churn table: all 13 rows re-run and matching.

What still fails is concentrated in the areas the brief flagged:
1. **The present model is still wrong.** The hardware renderer is created with present-vsync on. "Unthrottled" holds only for the software renderer, and the per-frame and per-turn budgets ignore a main-thread vsync block (D1).
2. **The multi-floor lighting finding misses the stale buffer's main effect.** On non-camera floors the stale `light_source_buffer` also supplies the colour of every character light, accumulated additively. Fix (a) as ordered is re-polluted by it, and the `[lightmap][multiz]` step-4 oracle cannot detect staleness (D2).
3. **The per-turn emitter budget is converted to a per-OMT authoring rule with the wrong bubble size.** It uses 9 OMTs instead of about 30, so the rule allows about 3× the budget (D3).
4. **The rewritten merge-risk table understates R3 and R4.** It calls R4 "new files only", yet R4a/R4b/the light list edit upstream `cata_shader.cpp`, `lightmap.cpp`, `tileset_loader.cpp` and `cata_tiles.h`. R3's upper-z work edits `map.cpp` and `game.cpp` (D4).

## r1 defect closure check

| r1 item | Claimed fix | Verified in body? | Residual |
|---|---|---|---|
| D1 throttle | §0.2, §1.1, §6.2 | Yes: 2 `try_sdl_update` callers (`src/sdltiles.cpp:6094`, `:6473`) and 44 `refresh_display();` sites (45 grep hits minus 1 declaration) | **New D1:** vsync omitted |
| D2 camera z | header, §2.2 | Yes | m6 (caller-table nits) |
| D3 multi-z light | §2.2 items 1–4, R0 test | Mostly | **New D2** |
| D4 per-turn lightmap | §2.4, §6.3, §7 | Yes | m4 ("every turn" is an upper bound tied to redraws) |
| D5 cast_zlight | §6.1 | Yes; `-Os` correct | m3 (benchmark spec calls protected API) |
| D6 iso inventory | §4.2 | Yes: 16 + 2 functions confirmed by grep | none |
| D7 golden lanes | §5.6 | Yes | m7 (determinism of goldens) |
| D8 merge rules | §8 | Partly | **New D4** |
| D9 budget | §6.3 | Rows added | **D1, D3** (vsync, emitter arithmetic); m5 |
| D10 snapshot inputs | §5.1 | Mostly | m1, m2 |
| m1–m9 | various | All verified fixed (m1 offset −3/−4 matches the diff hunks; m6 `:4089-4091`/`:2877-2878` exact; m8 `game.cpp` 21/59 re-run) | m8-new on the m9 fix (viewport offset) |
| Missed topics (contexts, platforms, overmap/minimap) | §5.7 | Yes | none blocking |

## Citation verification table

Method: a regex extractor over every `path:line[-line]` plus inherited `` `:N` `` / `, :N` continuations on the same line, with a range check against each file. A heuristic then looked for any backticked identifier from the same report line within ±5 lines of the cited range. All 42 non-matches were printed and read by hand. About 70 more high-impact citations were spot-printed: present path, lightmap, `build_map_cache` callers, flip, shader probe, contexts, platform guards, benchmark, Makefile.

| Check | Count |
|---|---|
| Citation occurrences | 477 |
| Unique (path, range) | 391 (the report says 383; it uses a different extractor, and this is not a defect) |
| Path missing | 0 |
| Line out of range | 0 |
| Heuristic non-match, manually reviewed | 42; 41 symbol-adjacent OK, 1 FAIL (F1) |
| Symbol present but claim contradicts code | 2 (F2, F3) |
| **Failure rate** | **3 / 391 = 0.8%** |

FAIL rows:

| # | Report line | Citation | Claim | Actual |
|---|---|---|---|---|
| F1 | 412 | `src/do_turn.cpp:524` | `world` epoch "incremented on every `calendar::turn` advance in `game::do_turn` (`src/do_turn.cpp:524`)" | `:524` is the `bool game::do_turn()` head. The advance is `calendar::turn += 1_turns;` at `src/do_turn.cpp:540`, 16 lines away |
| F2 | 47, 81-83, 579 | `src/sdltiles.cpp:6470-6471` | "The map path presents unthrottled … bounded by input and invalidation events" | `create_game_renderer` → `CreateRenderer( ::window, renderer_name.c_str(), false, true )` (`src/sdltiles.cpp:414`) → `SDL_PROP_RENDERER_CREATE_PRESENT_VSYNC_NUMBER = ( vsync && !software ) ? 1 : 0` (`src/sdl_wrappers.cpp:1157-1158`). The accelerated present is vsync-paced (D1) |
| F3 | 228 | `src/map.cpp:7701-7713` | `update_visibility_cache` recurses "to camera z − 10" | The bound is `pos.z() - zlev < fov_3d_z_range`, where `pos` is the **avatar** position (`src/map.cpp:7704`, `:7711`). In look-up mode it recurses from camera z down to avatar z − 10, i.e. 12 levels, not 11 |

## Defects

### MAJOR

**D1 (R2/R3): The present model omits vsync; budgets ignore a main-thread present block.**
- Claim:
  - §0 item 2: "The map path presents unthrottled."
  - §1.1: "the map frame rate is bounded by input and invalidation events."
  - §6.2: "On the map path it is unthrottled."
  - §6.3: "ImGui + UI + present … ≤ 2 ms."
  - Per-turn table: "≤ 33 ms for 30 moves/s".
- Evidence:
  - Every accelerated renderer is created with vsync requested: `src/sdltiles.cpp:409-415` (`false, true`), `src/sdl_wrappers.cpp:1157-1158`. Only the software renderer (`:412`, `true, false`) has it off.
  - So `RenderPresent` (`src/sdltiles.cpp:1022-1038`), reached from `get_input_event` (`:6470-6471`) and from the 44 direct `refresh_display()` sites, is paced by display refresh on the default `gpu` driver. Blocking depth per driver is UNVERIFIED.
  - Animation loops call `refresh_display()` per step (`src/animation.cpp:70`), as does the activity UI (`src/do_turn.cpp:514`). Each of these presents is paced.
  - Consequences the report does not draw:
    - (a) "Unthrottled" is true only on the L1 software lane, which is exactly the lane that is not the default path.
    - (b) Every move that redraws pays up to one refresh interval on the main thread. The ≤ 2 ms present target and the ≥ 30 moves/s per-turn table (whose targets already sum to 8 + 5 + 3 + 4 = 20 ms with no total row) are not reconciled with a ~16.7 ms present at 60 Hz.
    - (c) §6.4's "fixed-rate render tick in the `SDL_Delay(1)` wait" must be designed around vsync pacing.
    - (d) The R0 "presents/s by call site" counter needs a present-duration timer alongside it.
- Fix:
  - State the vsync creation flag in §0, §1.1 and §6.2.
  - Restate the model as "event-driven, vsync-paced on accelerated renderers, unpaced on software".
  - Add a present-time row to both §6.3 tables and a total row to the per-turn table.
  - Add an R0 timer around `RenderPresent` per call site, and record the driver's vsync mode in `debug.log`.
  - Evaluate making vsync an option, or decoupling presents from move processing.

**D2 (R2/R5): The multi-floor lighting finding is incomplete, fix (a) as ordered is defeated, and the R0 oracle cannot detect the bug.**
- Claim (§2.2 item 2): the stale `light_source_buffer` on a non-camera floor L "may then skip ray directions". Fix (a): "in `generate_lightmap`, after `build_sunlight_cache`, clear `light_color_cache` and `has_colored_lights` for every z ≠ `zlev` …". Test step 4: "that cell is deterministic across two runs (stale `light_source_buffer` check)".
- Evidence:
  - `apply_light_source` reads `light_source_buffer[p]` of **L** as the colour source of every character light: `buf.color.is_colored()` → `source_color = buf.color / buf.luminance`, then `light_color_cache[p] += source_color * luminance; has_colored_lights = true` (`src/lightmap.cpp:1466-1474`). Colour then propagates through `castLight` with a per-channel max (`:1165-1170`).
    - On L, nothing clears either array (`:518-519` and `:530-531` act only on `zlev`). So an NPC standing on L, on a tile that was a coloured emitter when L was last generated, re-injects that colour **additively every turn**, and the source tile's colour grows without bound until clamped downstream.
    - This is a second stale-colour mechanism, and it is driven by NPCs.
  - Ordering: `apply_character_light` for the avatar and all NPCs runs at `src/lightmap.cpp:584-587`, **after** `build_sunlight_cache` (`:546`). Fix (a) as specified ("after `build_sunlight_cache`, clear …") is re-polluted by step 1 on the same pass unless L's `light_source_buffer` is cleared too, or character lights on L skip the buffered colour.
  - Fix (b) compares against an undefined `current_generation`. It does not say who increments it, or whether the per-turn bump or a per-generation counter is meant.
  - Test step 4's oracle (determinism across two runs) cannot detect staleness, because stale data is deterministic. The test must assert absence of colour, or a bounded colour, on L at an NPC tile that was previously a coloured emitter, across N turns.
  - Item 3 ("ter/furn lights on L are absent") omits a transient case. `Character::on_move` runs `build_map_cache( posz )` when an NPC changes z (`src/character.cpp:2795-2799`), which fully generates L, colour included. The next `game::draw` → `build_sunlight_cache` then overwrites L's `lm` with sunlight (`src/lightmap.cpp:388-393`) but leaves L's fresh colour. So the mismatch also arises without the avatar ever having stood on L.
  - `game::update_map` invalidates every z (`src/game.cpp:10314-10317`), but `invalidate_map_cache` does not clear colour (`src/map.cpp:513-522`). After a bubble shift, L's colour sits at pre-shift bubble coordinates. Reading-based; runtime UNVERIFIED.
- Fix:
  - Add the colour-injection path and the shift case to §2.2.
  - Specify fix (a) as clearing `light_color_cache`, `has_colored_lights` **and** `light_source_buffer` for non-generated z **before** `apply_character_light`.
  - Define the counter for fix (b).
  - Replace test step 4 with "an NPC on z0, on a former coloured-emitter tile, avatar on z1, 10 turns: z0 colour at that tile is zero (fix a) / tint skipped (fix b) / bounded (today: documents growth)".
  - Add a bubble-shift case.

**D3 (R2/R3): The per-turn emitter budget is converted with the wrong bubble size, so the authoring rule allows about 3× the budget.**
- Claim:
  - §6.3: "≤ 64 artificial emitters in the reality bubble at night (≈ 0.5 per Saigon-block OMT side)".
  - §7 item 2: "about ≤ 7 lit fixtures per OMT on average (64 / 9 OMTs of a 3×3 block view)".
- Evidence:
  - The bubble is `MAPSIZE_X × MAPSIZE_Y` = 132 × 132 tiles (`MAPSIZE = 11`, `SEEX = 12`, `src/map_scale_constants.h`). That is 5.5 × 5.5 ≈ 30 OMTs of 24 × 24 tiles, not 9.
  - `generate_lightmap` scans and casts every emitter in the whole bubble (`src/lightmap.cpp:589-758`). A city block authored at 7 per OMT therefore yields ≈ 210 emitters, which is 3.3× the 64 budget and ≈ 15 ms by the report's own 75 µs assumption.
  - "0.5 per OMT side" has no defined meaning.
  - The derivation "5 ms ÷ 75 µs" also assigns no share to the fixed 17,424-cell scan, `build_sunlight_cache` or the 3×3 colour blur (`:777-805`).
- Fix:
  - Divide by the bubble's OMT count (≈ 30): **≤ 2 emitters per OMT on average**.
  - Subtract a fixed-cost term (to be measured in R0) before dividing.
  - Drop the "per side" phrase.
  - Mirror the corrected rule in §7 and in the d2 mapgen guidance.

**D4 (R5/R2): The per-phase merge footprint understates R3 and R4, so the "Decision" rests on an incomplete table.**
- Claim:
  - The §8 table row "R2b, R4, R5 | New files only (`src/render/*` …); `sdltiles.cpp` backend selection; `tileset_loader.cpp` optional keys | ≈ 60".
  - The R3 rows: "R3 without yaw | 18 renderer functions …; gameplay sites untouched".
- Evidence (from the report's own R3/R4 steps):
  - R4a needs non-zero `num_sampler_bindings` in `render_state::create`, a `cata_shader.cpp` hunk (`src/cata_shader.cpp:195-201`), plus a variant shader that samples it.
  - The R4 light list is emitted "from the same scan points" inside `generate_lightmap`, a `lightmap.cpp` hunk across `:584-770`.
  - R4b extends `atlas_replay_descriptor` and the `tileset` parallel vectors (`src/cata_tiles.h:280-289`, `:316-321`) and `parse_atlases` (`src/tileset_loader.cpp:524-533`).
  - R4c changes `atlas_bake_plan` (`src/atlas_bake_plan.h:20-48`).
  - R3 step 2 needs upward `update_visibility_cache` (`src/map.cpp:7701-7713`; `map.cpp` has 32 commits in 6 months) and extra `build_map_cache` z in `game::draw` (`src/game.cpp:3381-3382`).
  - R3 step 4 (z-aware weather) edits drop generation in `src/handle_action.cpp:310-322`.
  - None of these appear in the R3/R4 rows, so their conflict surface is understated. `lightmap.cpp` and `map.cpp` are the files that D2's fix and R3 both touch.
- Fix: add every upstream file and hunk named by the phase steps to each row, recompute "Lines touched" and "Conflict surface", and re-check that rule 2's decision still holds for R3/R4. In particular, decide whether the upper-z `update_visibility_cache` change goes upstream-first.

### MINOR

- **m1 (R2) Epoch increment sites are incomplete.**
  - The `world` sites are listed as "exactly where `set_draw_cache_dirty()` is called today" but omit `src/game.cpp:6193` (`game::look_around`, called every loop iteration).
  - The turn-advance site is `src/do_turn.cpp:540`, not `:524` (F1).
  - `view` should also bump on `g->display_overlay_state` toggles, because overlay strings are materialized in draw-point generation (`src/cata_tiles.cpp:821-990`).
- **m2 (R6) The snapshot-inputs table claims "Every input" but omits some.**
  - Zone-manager marks: `draw_zone_mark` reads `g->is_zones_manager_open()` and `zone_manager::get_manager()`, which change inside a menu with no turn passing.
  - The per-frame overlay row omits explosions, bullets, lines, cursor, highlight, zones, async anims, the view-offset cursor and the vehicle direction indicator (`src/cata_tiles.cpp:1502-1565`). The `frame_snapshot::overlays` comment covers only part of this list.
- **m3 (R5) The R0 benchmark spec is not executable as written.**
  - "time 1,000 calls of `map::build_seen_cache`" and "`generate_lightmap( z )`": both are `protected` in `map` (`src/map.h:2083-2085`).
  - Specify driving them through public `build_map_cache` after `set_seen_cache_dirty( z )` / `set_lightmap_cache_dirty( z )` (`src/map.h:491-498`) with the other sub-builders clean, or add a test-only friend.
  - A 3×3-OMT block also fills only 9 of the bubble's ≈ 30 OMTs. Say what fills the rest (it changes the emitter scan and FOV).
- **m4 (R7) "Every turn" for `generate_lightmap` is an upper bound.**
  - Generation is lazy, on the next non-skip `build_map_cache`. During activities and sleep, `handle_progress_ui` redraws only every `wait_refresh_rate` (5 min / 30 min; 1 turn for `ACT_AUTODRIVE`) (`src/do_turn.cpp:472-516`).
  - Label the per-turn cost as "per interactive or auto-drive turn".
- **m5 (R2) The `update_visibility_cache` gate is incomplete.**
  - §2.4 gives "when `visibility_cache_dirty` or player moved", but `do_turn` calls `m.invalidate_visibility_cache()` unconditionally every turn (`src/do_turn.cpp:765`).
  - The depth bound is avatar-relative (F3).
- **m6 (R2) Caller-table nits.**
  - `avatar_action::move` (`src/avatar_action.cpp:570`) is the safe-mode AUTOPEEK branch only.
  - `src/map_helpers.cpp:75` (test helper, `skip_lightmap`) is a 13th site in `src/`. State the exclusion.
- **m7 (R5) The golden lanes lack a determinism seam.**
  - R0 requires "L1 and L2 golden images each stable across 3 runs", and R1 requires 0-diff.
  - But animated tiles pick frames from `steady_clock` (`src/cata_tiles.cpp:2325-2338`), hit animations use timestamps (`:4429`), and weather drops are randomized (`src/handle_action.cpp:310-322`).
  - The fake-clock injection is specified only for the animated-tile unit test. Extend it, plus a fixed RNG seed, to both golden lanes, or require the golden map to contain no animated, weather or SCT content.
- **m8 (R5) The screen-aligned light texture (m9 fix) assumes the world viewport starts at render-target origin.**
  - `gl_FragCoord` is in `display_buffer` space, and `w_terrain` sits at a sidebar-dependent offset (`src/sdltiles.cpp:3662-3665`, `win->pos * fontwidth`).
  - Without a uniform, the texture must cover the whole `display_buffer`, with the offset baked in on the CPU. Say so.

## Missed topics

1. **Vsync pacing of presents** (D1). It is absent from both r1 and r2, and from the r1 critic.
2. **NPC-driven stale colour** through `light_source_buffer` on non-camera floors, and colour staleness after a bubble shift (D2).
3. **Lightmap freshness for gameplay during long activities.** `ambient_light_at` and `lm` consumers such as monster and NPC vision read a lightmap that is only regenerated on redraw (m4). This is out of renderer scope, but R1's "idle frames re-present the snapshot" and any frame/turn decoupling must not move lightmap generation further away from turn processing. Flag it for d4/simulation.

## Required changes for next revision

1. [ ] Add vsync to the present model (§0.2, §1.1, §6.2). Add present-time rows and a per-turn total to §6.3, and add an R0 present-duration timer per call site (D1, F2).
2. [ ] In §2.2, document the buffered-colour injection by character lights on non-camera floors and the bubble-shift case. Re-specify fix (a) to clear `light_source_buffer` too, before `apply_character_light`. Define fix (b)'s counter. Replace the `[lightmap][multiz]` step-4 oracle with an absence- or boundedness-of-colour assertion over N turns (D2).
3. [ ] Recompute the emitter rule with ≈ 30 OMTs per bubble (≤ 2 per OMT), subtract a fixed-cost term, and fix §6.3, §7 item 2 and the "per side" wording (D3).
4. [ ] Complete the §8 per-phase footprint for R3 (`map.cpp` upward visibility, `game.cpp` extra z, `handle_action.cpp` weather) and R4 (`cata_shader.cpp`, `lightmap.cpp`, `tileset_loader.cpp`, `cata_tiles.h`, `atlas_bake_plan.h`). Recompute conflict surfaces and re-confirm the decision (D4).
5. [ ] Fix the epoch sites: add `src/game.cpp:6193`, use `src/do_turn.cpp:540`, and add the overlay-toggle bump (m1, F1).
6. [ ] Add zone-manager state and the full per-frame overlay list to the snapshot-inputs table (m2).
7. [ ] Make the R0 benchmarks callable (public `build_map_cache` + dirty setters, or a test friend) and specify the bubble fill outside the 3×3 block (m3).
8. [ ] Qualify "every turn" (m4). Fix the `update_visibility_cache` gate and depth bound (m5, F3). Apply the caller-table nits (m6).
9. [ ] Add a clock and RNG seam to the L1/L2 golden lanes (m7), and add the viewport-offset handling to the screen-aligned light texture (m8).

## Appendix A: working notes from the first pass

- WN-1 Citations: mechanical extractor found 477 occurrences, 391 unique (path, range); 0 missing paths, 0 out of range. 42 heuristic non-matches queued for manual review.
- WN-2 Present model: `try_sdl_update` callers (`src/sdltiles.cpp:6094`, `:6473`) and `needupdate` → `refresh_display()` (`:6470-6471`) confirmed. **But the hardware renderer is created with present-vsync on**: `create_game_renderer` → `CreateRenderer( ::window, renderer_name.c_str(), false, true )` (`src/sdltiles.cpp:414`) → `SDL_PROP_RENDERER_CREATE_PRESENT_VSYNC_NUMBER = ( vsync && !software ) ? 1 : 0` (`src/sdl_wrappers.cpp:1157-1158`). The report never mentions vsync. "Unthrottled" holds only for the software renderer (`:412`, vsync false).
- WN-3 `build_map_cache` callers: 13 in `src/` (report's 12 + `src/map_helpers.cpp:75`, test helper, `skip_lightmap = true`). The 12 rows check out; `avatar_action::move` (`src/avatar_action.cpp:570`) is the AUTOPEEK branch only (safe mode), not every move.
- WN-4 Epoch `world` increment sites: report lists `src/handle_action.cpp:280`, `src/map.cpp:10852`, `:7758`, `src/cata_tiles.cpp:701-707`. **Missed: `src/game.cpp:6193`** (`game::look_around` loop calls `tilecontext->set_draw_cache_dirty()` every iteration). "`calendar::turn` advance in `game::do_turn` (`src/do_turn.cpp:524`)": line 524 is the function head; the advance is `calendar::turn += 1_turns` at `src/do_turn.cpp:540`.
- WN-5 Multi-floor lighting: stale `light_source_buffer` on non-generated L is read not only for neighbour suppression (`src/lightmap.cpp:1489-1495`) but also **as the colour source of every character light** (`buf.color`, `:1467-1474`), which does `light_color_cache[p] += source_color * luminance` (additive) into L's never-cleared colour cache, then castLight max-writes colour. Report misses the colour-injection path; fix (a) as written (clear after `build_sunlight_cache`, before `apply_character_light` at `:584-587`) is re-polluted by it unless L's `light_source_buffer` is also cleared.
- WN-6 Per-turn lightmap: `do_turn` dirties all z every turn (`src/do_turn.cpp:607-610`), but generation is lazy on the next non-skip `build_map_cache`. During activities/sleep, redraws happen only every `wait_refresh_rate` (5 min / 30 min; 1 turn for ACT_AUTODRIVE) (`src/do_turn.cpp:472-516`), so "every turn" is an upper bound tied to redraws.
