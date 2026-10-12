# Critic D1 r1: Rendering & UI Pipeline (audit of d1_r1.md)

- Critic unit: A1.2, round 1. Rubric: `doc/saigon/analysis/CRITIC_RUBRIC.md` (N=1, k=1).
- Code under audit: base SHA `fe6a10c2b1`. HEAD source differs only in the C6 hunks (`src/game.cpp` +7 net lines after base 552; `src/main.cpp` +4). Every claim was checked against the files as they are at HEAD, using the offsets in HC-1.
- Status: complete.

## Verdict

**REJECT.** 0 BLOCKER, 10 MAJOR, 9 MINOR. The citation failure rate is 5/312 = 1.6% (under the 2% bar), but there are 10 MAJOR defects.

## Summary

This is a strong, well-cited report. All 312 unique `path:line` citations exist and are in range. After manual review of the 36 citations my heuristic could not auto-match, every cited line contains the named symbol. Most high-impact structural claims survive falsification:
- the frame chain;
- 8 `.frag` / 0 `.vert` and a fragment-only `SDL_GPURenderStateCreateInfo`;
- z → row → 11 layers → column with no sort;
- string-keyed sprite lookup per layer call;
- draw-path mutation of map memory and overmap-seen;
- emission bounded at `center.z()`;
- `generate_lightmap` having a single caller;
- `tile_isometric`, with `tile_iso` absent;
- 14 gameplay `is_tileset_isometric()` sites;
- the churn table (7 of 8 rows exact).

It fails on the points the brief marked as critical:
1. **Frame and present model.** The ≥ 25 ms throttle does not apply to the main map frame (D1).
2. **Multi-z Saigon claims.** "Viewer" is the camera z, and upper storeys are viewable via look-mode `<` (D2). "Other levels get sunlight only" is false: character lights land on their own z, and lower-z colour tint reads a stale `light_color_cache` (D3).
3. **Performance.**
   - The lightmap is unconditionally dirtied for all z **every turn**, which the report misses (D4).
   - The `cast_zlight` 6.9–19.2 ms figures come from a no-floor, all-21-level synthetic benchmark using `BOTH` directions, unlike production `build_seen_cache` (D5).
   - "60 fps movement CPU-bound" conflates turns with frames (D5).
   - The §6.3 budget omits the memorize loop, the per-turn lightmap and the upper-z cost that R3 itself introduces (D9).
4. **Seams and roadmap.**
   - The iso math is not "in 5 functions" (D6).
   - The snapshot's invalidation inputs are unlisted, and the proposed `map_epoch` does not exist (D10).
   - Headless goldens cannot exercise the default GPU shader path (D7).
   - The merge rules contradict R1/R3 (D8).

## Citation verification table

Method: a regex extractor over every `path:line[-line]` and inherited `` `:N` `` continuation, with a range check against the file. A heuristic then looked for any backticked identifier from the same report line within ±5 lines of the cited range. The 36 non-matches were reviewed manually. In addition, about 60 auto-matched citations on high-impact claims were spot-checked by printing the cited line.

| Check | Count |
|---|---|
| Citation occurrences | 363 |
| Unique (path, range) | 312 |
| Path missing | 0 |
| Line out of range | 0 |
| Heuristic no-match, manually reviewed | 36 → all symbol-adjacent OK |
| Symbol present but **claim contradicts cited code** (R2, counted as FAIL) | 5 |
| **Failure rate** | **5 / 312 = 1.6%** |

FAIL rows:

| # | Report line | Citation | Claim | Actual |
|---|---|---|---|---|
| F1 | 20, 39 | `src/sdltiles.cpp:125`, `:1042-1050` | "Presents are throttled to ≥ 25 ms apart" (frame contract) | `try_sdl_update` is called only at `:6094` and `:6473` (ImGui path when `needupdate` is false). The map frame sets `needupdate` (`:3783-3784`) and presents unthrottled via `:6470-6471`. (D1) |
| F2 | 125 | `src/cata_tiles.cpp:1053` | "upper storeys … appear only when the player climbs" | `center` = `ter_view_p`, whose z = `u.posz() + view_offset.z` (`src/game.cpp:3380`). `LEVEL_UP` in look-around sets `view_offset.z` (`src/game.cpp:6235-6242`). (D2) |
| F3 | 128, 168 | `src/lightmap.cpp:366-420` | "Other levels get sunlight only"; sunlight "fills `lm` for **every** z" | Skips the avatar z when `pzlev != avatar z` (`:389-393`). `apply_character_light` → `apply_light_source` writes into `get_cache( p.z() )` for every NPC (`:344-355`, `:1442-1444`). (D3) |
| F4 | 113 | `src/cata_tiles.cpp:2394` | a `get_option` string lookup per call | `apply_night_vision_goggles && get_option<bool>(…)` short-circuits; it runs only with NV goggles active. (m2) |
| F5 | 403 | `src/cata_tiles.cpp:1466-1500` | "another … 14,641 `draw_terrain(memorize_only)` calls per redraw" | The loop `continue`s on vision-effect tiles (`:1477`) and on iso on-screen tiles (`:1470`), so 14,641 is an upper bound, not a count. (m3) |

## Defects

### MAJOR

**D1 (R2): Present throttle misstated as the frame contract.**
- Claim (line 20): "Presents are throttled to ≥ 25 ms apart." Line 39: "the SDL present is throttled to one per `interval = 25` ms." Line 405: "Today the tiles build cannot exceed 40 Hz on the throttled path."
- Evidence:
  - `try_sdl_update` (`src/sdltiles.cpp:1042-1050`) has 2 callers: `:6094` and `:6473`. The latter runs only in `else if( ui_adaptor::has_imgui() )`, i.e. when `needupdate` is false.
  - `curses_drawwindow` sets `needupdate = true` after the tiles draw (`:3783-3784`), and `get_input_event` then calls `refresh_display()` directly (`:6470-6471`).
  - `catacurses::doupdate()` → `refresh_display()` (`src/cursesport.cpp:204-207`) is also unthrottled, as are about 24 direct `refresh_display()` sites (`src/animation.cpp:70`, `src/do_turn.cpp:269/272/514/756`, `src/game.cpp:695/815/1556/1597/9242/10522`, …).
- Fix: restate the present model in §0, §1.1 and §6.2 as "unthrottled on the map/needupdate path; 25 ms throttle only on the ImGui-idle and `CheckMessages` paths". Remove the "cannot exceed 40 Hz" conclusion, or scope it to that path. Add an R0 counter for presents/s split by call site.

**D2 (R2/R6): "Viewer z" conflated with avatar z; upper storeys ARE viewable.**
- Claim (§0 item 4, §2.2): "Only z ≤ viewer is drawn … upper storeys and balconies appear only when the player climbs." §2.2/§3.1: lightmap "only for the viewer's z-level".
- Evidence:
  - `game::draw` sets `ter_view_p.z() = ( u.pos_bub() + u.view_offset ).z()` (`src/game.cpp:3380`). `game::look_around` handles `LEVEL_UP/LEVEL_DOWN` by `u.view_offset.z() = center.z() - u.posz()` (`src/game.cpp:6235-6242`). `zone_sort_viewport` also overrides `view_offset` (`src/game.cpp:3374-3378`).
  - `build_map_cache( ter_view_p.z() )` → `generate_lightmap( zlev )` builds artificial light for the **camera** z.
  - `build_map_cache` has 8 call sites with different z (`src/game.cpp:882, 3381, 5815, 6245, 6320, 9761, 10318`; `src/do_turn.cpp:739` skip-lightmap). Look-up also calls `build_map_cache( u.posz() )` (`src/game.cpp:6245`), so 2 levels get lit in that mode.
  - `update_visibility_cache` recurses only **downward** (`zlev - 1`, `src/map.cpp:7712`). No `visibility_cache` exists above the camera z, which R3 "draw upper z with cut-away" will need.
- Fix:
  - Define "camera z" and use it throughout.
  - Document the look-mode path and the `build_map_cache` caller set.
  - For the Saigon façade problem, say that today's workaround is look-up, and that R3 needs `visibility_cache`/`lm` for z > camera (new cost, see D9).

**D3 (R2): "Other levels get sunlight only" is false; stale colour on lower z missed.**
- Claim (§2.2 line 128, §3.1 sunlight row): other levels get sunlight only; sunlight fills `lm` for every z.
- Evidence:
  - `generate_lightmap` calls `apply_character_light` for the avatar and **all NPCs** (`src/lightmap.cpp:584-587`). Each writes into the character's own z (`apply_light_source` → `get_cache( p.z() )`, `:1442-1444`). So NPC flashlights on other floors light their floor.
  - `light_color_cache`/`has_colored_lights` are cleared only for the generated z (`:518-519`; ctor `src/level_cache.cpp:28`). Yet the draw prepass tints **every** drawn z from `zlev_cache.light_color_cache` (`src/cata_tiles.cpp:1058-1061`, `:1090-1101`), so lower floors show colour left over from when they were last the camera z, combined with a fresh sunlight-only `lm`.
  - `build_sunlight_cache` skips the avatar z when called for another z (`:389-393`).
- Fix:
  - Correct §2.2/§3.1.
  - Add "stale lower-z colour tint" as a finding, mark it reading-based / UNVERIFIED-runtime, and propose either clearing colour for non-generated z or a per-z `lightmap_generation` stamp checked by the renderer.
  - Add an R0 test: a lit neon shop on z0, the player on z1 looking down over an atrium.

**D4 (R3): Per-turn lightmap rebuild missed.**
- Claim (§2.4 row 3): `generate_lightmap` gate = "`lightmap_dirty`; char-light changes force it".
- Evidence:
  - `game::do_turn`: `reset_light_level(); for( z = -OVERMAP_DEPTH … OVERMAP_HEIGHT ) m.set_lightmap_cache_dirty( z );` (`src/do_turn.cpp:607-610`), unconditionally, every turn.
  - So the full emitter scan (`src/lightmap.cpp:584-770`), `build_sunlight_cache` over all populated z, and per-source shadowcasting run on the first `game::draw` after **every** turn.
  - `do_turn` also runs `build_map_cache( levz, true )` every turn (`:739`).
- Fix:
  - Correct §2.4.
  - Put `generate_lightmap` per turn into §6.3 as a measured line (R0 benchmark with N emitters on the Saigon block).
  - Restate §7 item 2's emitter cap as a per-turn budget, with a number derived from the R0 benchmark.

**D5 (R7/R2): `cast_zlight` timing over-generalized; frames and turns conflated.**
- Claim (§0 item 8, §6.1): "One 3D FOV rebuild costs 6.9–19.2 ms … 60 fps movement is therefore CPU-bound before drawing."
- Evidence:
  - `do_3d_benchmark` uses zero `floor_cache` (no floors on any level) and the default `vertical_direction::BOTH` (`tests/shadowcasting_test.cpp:353-389`). The random case randomizes **all 21 levels**, and the file itself says "TODO: add roofs" (`:413`).
  - Production `build_seen_cache` casts UP only when the origin level has `no_floor_gaps` (`src/lightmap.cpp:1284-1300`) and uses real floors.
  - `build_seen_cache` is gated on a position/range change or dirty caches (`src/map.cpp:10839-10855`), i.e. per move/turn, not per frame. The report's own §6.3 row 1 puts it "outside the frame budget".
  - Build flags (`RELEASE=1`, i.e. optimized; `doc/saigon/PROGRESS.md:19`) are not stated.
- Fix:
  - Present 6.9–19.2 ms as synthetic bounds.
  - Add an R0 benchmark calling `map::build_seen_cache` on a loaded map (Saigon block, with floors and roofs) on an idle machine.
  - State the build flags.
  - Rephrase the implication as "caps moves/turns per second; frames between moves pay only dirty-gated scans".

**D6 (R2/R5): Iso projection is not isolated in "5 functions"; the R3 seam is under-scoped.**
- Claim (§0 item 6, §4.5, R3 seam): a fixed 2:1 transform in 5 functions; a `projection` object "owns those 5 functions".
- Evidence:
  - §4.5 itself lists 6 functions, and misses `get_window_full_base_tile_range` (`src/cata_tiles.cpp:1711`).
  - Projection-dependent code covers ≥ 15 functions (20 `is_isometric()` calls plus local `iso` flags): `draw` ×6, `draw_sprite_at` (`:2811`), `draw_from_id_string_internal` (`:2411`), `draw_square_below` (`:3067`), `draw_zlevel_overlay` (`:4109`), `draw_weather_frame` (`:4819`), `draw_sct_frame` (`:4869`), `draw_minimap` (`:1600`), `load_tileset` (fog alpha `:519`).
  - Horizontal flip (`rota == -1`) is still applied in iso (`:2824-2826`, `:2849`, `:2888`), which the report omits.
- Fix: inventory every projection-dependent function, and make R3 step 1 "route all of them through `projection`", with the round-trip test plus golden screenshots for SCT, weather, cursor and fog.

**D7 (R5): The validation oracle cannot see the default render path.**
- Claim (R0 step 4, R1/R2a validation): headless golden images on `setup_software_renderer` give 0-diff / ≤ 2 LSB regression protection.
- Evidence:
  - On the software renderer, `SDL_GetGPURendererDevice` returns NULL and the variant path is disabled (`src/cata_shader.cpp:692-700`; "the software fixture never binds", `:820`).
  - Goldens therefore test only the atlas-fallback and silhouette-mask paths. Shader tint, `variant_pass` state switching and the shader flushes, which are exactly what R2a reorders, are untested.
  - The 2-LSB tolerance compares blit against triangle rasterization on the SW renderer (UNVERIFIED).
- Fix: add a GPU-driver golden lane (a real `gpu` renderer on a dev machine/CI runner with a GPU, or an offscreen SDL_GPU readback), plus `render_stats` counter assertions (shader switches, flushes) as a path-independent oracle. State the tolerance per path.

**D8 (R5): Merge-risk rules contradict the roadmap.**
- Claim (§8 rule (i), merge rule 2): upstream files receive only call-site hunks, ≤ 1 per phase.
- Evidence:
  - R1 steps 1/4 rewrite the memorize loop and `draw_terrain`…`draw_critter_at` into builders inside upstream `src/cata_tiles.cpp` (47 commits / 6 months).
  - R3 edits 14 gameplay call sites across 10 upstream files.
  - R2a replaces the emission loop.
- Fix: per phase, list the upstream files and hunks touched, and give a conflict-surface estimate (lines changed × churn). Choose explicitly between "fork-owned copy of `cata_tiles.cpp` draw path + periodic re-port" and "in-place refactor upstreamed first". Give R0/R1 an upstream-PR plan with a fallback.

**D9 (R3): The §6.3 per-frame/per-turn budget is incomplete.**
- Evidence: the table omits:
  - (a) the memorize loop: up to 14,641 `draw_terrain(memorize_only)` calls per redraw, including idle redraws (`src/cata_tiles.cpp:1466-1500`), with `terrain_override.find` ×5 and `get_connect_values` each;
  - (b) the per-turn `generate_lightmap` (D4);
  - (c) `update_visibility_cache` with its downward recursion (`src/map.cpp:7701-7713`);
  - (d) the upper-z multiplier R3 introduces. For 3–5-storey *nhà ống* this needs draw points, visibility and light for z > camera, but K8 only names the risk;
  - (e) no per-call cost baseline, so "≈ 9k `SDL_RenderTextureRotated`/frame" cannot be turned into ms.
- Fix: add rows (a)–(d) with a "today (estimate/UNVERIFIED)" column and a target column, tie each to an R0 counter/timer, and give the R3 budget for 2 extra visible storeys.

**D10 (R5): Seam A snapshot invalidation is under-specified; `map_epoch` does not exist.**
- Claim (§5.1 step 3, R1 step 5): key dirtiness on `map_epoch`/turn. Idle frames re-present the cached snapshot (≤ 0.5 ms).
- Evidence:
  - `grep map_epoch src` = 0.
  - Resolution also depends on:
    - view origin `o` (retract/`_transparent`, `src/cata_tiles.cpp:2405-2432`);
    - transient overrides set by `src/animation.cpp` and voided per draw (`:1456-1464`);
    - wall-clock animated-tile frames (`:2320-2338`);
    - NV goggles (`:721`);
    - per-turn `you.sees(critter)`.
  - A snapshot of resolved `sprite_ref` freezes animated tiles.
- Fix: enumerate every input to sprite resolution and classify it as per-turn, per-view or per-frame. Keep frame-varying selection (animation frame, flicker) in the render-side instance build. Define the epoch counter (where it is incremented). Add a test that animated tiles still advance under snapshot reuse.

### MINOR

- **m1** The main.cpp offset rule "base = N−4 for N ≥ 782" is off by one for HEAD 782–783 (true offset −3 there; −4 from 784). No cited line is affected.
- **m2** `NV_GREEN_TOGGLE` option lookup is short-circuited (F4).
- **m3** The memorize-loop count is an upper bound (F5).
- **m4** Missed draw-path mutations:
  - `cata_tiles::draw` writes `map::prev_top_left/prev_bottom_right/prev_o` (`src/cata_tiles.cpp:701-706`);
  - `generate_lightmap` (reached from `game::draw`) calls `apply_character_light`, which calls `p.add_effect( effect_haslight, 1_turns )` (`src/lightmap.cpp:357-358`), a Character state write from the draw path.

  Add both to `commit_frame_side_effects`.
- **m5** Iso horizontal flip is still applied (see D6). It matters for the directional-sprite plan (R3 step 3).
- **m6** The batching precedent is untextured, and the wrapper has no texture/UV parameters (`src/pixel_minimap_geometry.h:13`, `src/sdl_wrappers.cpp:487-500`). Cite `src/cata_tiles.cpp:4089-4091` as the shader-applies-to-geometry evidence, and specify white vertices on the non-shader path (`:2877-2878`).
- **m7** Benchmark build flags are not stated (D5).
- **m8** Churn: `src/game.cpp` is 21/59, not 21/57.
- **m9** The R4a spike needs a camera uniform for `gl_FragCoord` reconstruction, but the code forbids per-call uniforms (`src/cata_shader.h:169-173`). Say how it would be supplied: a per-camera-move state rebuild, or a storage buffer.

## Missed topics

1. **Stale lower-z `light_color_cache`** and character lights on non-camera z (D3). These directly affect Saigon atrium/stairwell views.
2. **Unconditional per-turn lightmap dirtying** (`src/do_turn.cpp:607-610`) (D4).
3. **Dual tile contexts.** `closetilecontext` + `fartilecontext` (`DISTANT_TILES`, `src/sdltiles.cpp:6268-6285`) load a second tileset. K10 VRAM growth and every R4 extra atlas layer double with it, and `render_backend::upload_atlas` must handle the zoom swap.
4. **Platform matrix.** `EMSCRIPTEN` and `__ANDROID__` branches in `src/sdltiles.cpp` (`:103`, `:582`, `:598`, `:642`, `:4197`). R2b/R4 (`sdl_gpu_backend`) must define which platforms keep `sdl_renderer_backend` permanently. Web has no SDL_GPU, so the legacy path is not just an oracle.
5. **Overmap and minimap draw paths.** `overmap_tilecontext->draw_om` and `pixel_minimap` are outside the snapshot/backend design. State whether they stay on the legacy path.

## Required changes for next revision

1. [ ] Rewrite the present model (§0 item 2, §1.1 intro, §6.2): the map path is unthrottled; the 25 ms throttle applies only on `try_sdl_update` paths. Drop or scope "cannot exceed 40 Hz" (D1).
2. [ ] Replace "viewer z" with "camera z = `u.posz() + view_offset.z`". Document look-mode `LEVEL_UP/DOWN` and the `build_map_cache` caller set. Correct "upper storeys appear only when the player climbs" (D2).
3. [ ] Correct "other levels get sunlight only": character/NPC lights land on their own z, the sunlight pass skips the avatar z, and lower-z tint reads stale `light_color_cache`. Add a fix proposal and an R0 test (D3).
4. [ ] Add the per-turn `set_lightmap_cache_dirty` loop to §2.4/§6.3. Benchmark `generate_lightmap` with N emitters in R0, and restate the §7 emitter cap as a per-turn budget (D4).
5. [ ] Re-scope the `cast_zlight` numbers as synthetic (no floors, `BOTH`, all 21 levels random). State the build flags. Add a production `build_seen_cache` benchmark on a loaded Saigon map. Replace "60 fps movement CPU-bound" with a moves/s statement (D5, m7).
6. [ ] Inventory all projection-dependent functions (≥ 15) and re-scope the R3 `projection` seam and its tests to cover them, including the iso horizontal flip (D6, m5).
7. [ ] Add a GPU-driver golden lane and counter-based oracles. State per-path tolerances, since the software renderer never binds shaders (D7).
8. [ ] Reconcile the merge rules with R1/R2a/R3: list the upstream files and hunks per phase, estimate conflict surface, and decide fork-copy versus upstream-first (D8).
9. [ ] Complete the §6.3 budget with the memorize loop, per-turn lightmap, `update_visibility_cache`, the upper-z multiplier for 3–5 storeys, and a per-call baseline, each tied to an R0 counter (D9).
10. [ ] Enumerate the snapshot's invalidation inputs (view origin, overrides, animation clock, NV, creature visibility), define the epoch counter, keep animation-frame selection render-side, and add an animated-tile test (D10).
11. [ ] Add the missed draw-path mutations (`prev_*`, `effect_haslight`) to `commit_frame_side_effects` (m4).
12. [ ] Fix minor items m1, m2, m3, m6, m8 and m9.
13. [ ] Cover the missed topics: dual tile contexts (VRAM), the platform matrix (web/Android keep the legacy backend), and the overmap/minimap paths.

---

## Appendix: working notes (high-impact claim checks)


### HC-1 Line-number convention (report line 4)
- `git diff -U0 fe6a10c2b1 HEAD -- src/game.cpp src/main.cpp` hunks: game.cpp `@@ -549,2 +549,8 @@`, `@@ -552 +558,2 @@` → HEAD N ≥ 560 ↔ base N−7. **Correct.**
- main.cpp `@@ -777,0 +778,3 @@`, `@@ -779,0 +783 @@` → HEAD 781–782 = base 778–779 (offset −3); HEAD N ≥ 784 = base N−4. The report says "base = N−4 for N ≥ 782", which is off by one for HEAD 782–783. No cited main.cpp line falls in that window (cites are 875–889), so this is cosmetic → MINOR.

### HC-2 Mechanical citation range check
- Script (`pathre` over every `path:line[-line]` plus inherited `` `:N` `` continuations): 363 citation occurrences, **312 unique (path, range)**, **0 missing paths, 0 out of range**.
- Report self-reports "231 unique citations"; the real count is 312 under a stricter extractor. Not a defect (undercount of its own work).

### HC-3 "Only z ≤ viewer is drawn; artificial light only at viewer z" (§0 item 4, §2.2, §3.1)
Verified in code, with two corrections the report misses:
1. Emission loop `while( cur_zlevel <= center.z() && !draw_aborted )` (`src/cata_tiles.cpp:1053`). Draw-point generation walks `for( int zlevel = center.z(); zlevel >= draw_min_z; zlevel-- )` (`:778`, `:785`). **No z above `center.z()` is ever emitted. Confirmed.**
2. But `center` is `ter_view_p`, set in `game::draw` as `ter_view_p.z() = ( u.pos_bub() + u.view_offset ).z()` (`src/game.cpp:3380`). `game::look_around` handles `LEVEL_UP`/`LEVEL_DOWN` by `u.view_offset.z() = center.z() - u.posz()` (`src/game.cpp:6235-6245`). So **upper storeys ARE viewable without climbing** (look mode, `<`). The report's statement "upper storeys and balconies appear only when the player climbs" (§2.2 line 125) is false. "Viewer" must be defined as the camera z (`u.posz() + view_offset.z`), not the avatar z.
3. `game::draw` calls `here.build_map_cache( ter_view_p.z() )` (`src/game.cpp:3381`), and `build_map_cache` ends with `generate_lightmap( zlev )` (`src/map.cpp:10910-10912`, sole caller). So artificial light is generated for the **camera z**, not strictly the avatar's z. The cited comment (`src/character.cpp:2680-2684`) is about NPC/character ambient light and is correct only for the non-look case. Also `build_map_cache` is called with other z (`src/game.cpp:882`, `:5815`, `:6245`, `:6320`, `:9761`, `:10318`; `src/do_turn.cpp:739` with `skip_lightmap = true`). The report's "single caller" is true of `generate_lightmap` but hides that `build_map_cache` has 8 callers with different z.
4. **Missed stale-colour hazard.** `generate_lightmap(zlev)` clears `light_color_cache` and `has_colored_lights` only for `zlev` (`src/lightmap.cpp:518-519`). `build_sunlight_cache` rewrites `lm` for every z from top down (`src/lightmap.cpp:388-420`), but nothing clears `light_color_cache` on other levels (only `level_cache.cpp:28` ctor and `lightmap.cpp:518`). Yet the emission prepass tints **lower** z tiles from `zlev_cache.light_color_cache` and `zlev_cache.has_colored_lights` (`src/cata_tiles.cpp:1058-1061`, `:1090-1101`). Lower-z tiles therefore get **stale colour** from the last time that level was the camera z, combined with sunlight-only `lm`. This bites exactly the Saigon multi-storey case (the player walks up from a neon-lit z0 shop to the z3 roof walk and looks down). Not runtime-verified (reading-based), but the report should have flagged it.
5. `build_sunlight_cache` skips the avatar's z when `pzlev != avatar z` (`src/lightmap.cpp:389-393`). So when you look up one level, the avatar's own level keeps its old `lm`, while the viewed level gets fresh sunlight plus artificial light. The report's §3.1 "Fills `lm` for **every** z" omits this exception.

### HC-4 Frame path and "presents throttled to ≥ 25 ms" (§0 item 2, §1.1, §6.2)
- The chain `run_game_loop` → `ui_manager::redraw_invalidated` → `game::draw` → `wnoutrefresh( w_terrain )` → `curses_drawwindow` → `tilecontext->draw` → `draw_sprite_at` → `render_copy_ex` → `refresh_display` is **correct**. Checked: `src/cursesport.cpp:179-187`; dispatch `src/sdltiles.cpp:3653-3668`; `update = true` in the tiles branch and `needupdate = true` at `src/sdltiles.cpp:3783-3784`; `refresh_display` `:980-1039`.
- **The throttle claim is wrong as stated.** `try_sdl_update()` (the only code that checks `interval = 25`) has exactly 2 callers: `src/sdltiles.cpp:6094` (end of `CheckMessages` when `needupdate`) and `:6473` (the `else if( ui_adaptor::has_imgui() )` branch, i.e. only when `needupdate` is **false**). The normal map frame goes `curses_drawwindow` → `needupdate = true` → `input_manager::get_input_event` → `if( needupdate ) refresh_display();` (`:6470-6471`), which is **unthrottled**. `catacurses::doupdate()` → `refresh_display()` (`src/cursesport.cpp:204-207`) is also unthrottled, and there are ~25 direct `refresh_display()` call sites (`src/animation.cpp:70`, `src/do_turn.cpp:269/272/514/756`, `src/game.cpp:695/815/1556/1597/…`).
- The §6.2 statement admits the bypass in one sentence, but §0 item 2 and §1.1 (line 39) present "presents are throttled to ≥ 25 ms apart" as the frame contract. The conclusion "cannot exceed 40 Hz" therefore holds only for the minor ImGui-idle path. → **MAJOR (R2: claim contradicts code; it feeds the budget model).**

### HC-5 Lightmap rebuild frequency (§2.4 table row 3, §6.3 row 1, §7 item 2)
- The report gates `generate_lightmap` on "`lightmap_dirty`; char-light changes force it". **It misses the dominant trigger.** `game::do_turn` dirties the lightmap for **all 21 z every turn** with no condition: `reset_light_level(); for( int z = -OVERMAP_DEPTH; z <= OVERMAP_HEIGHT; z++ ) m.set_lightmap_cache_dirty( z );` (`src/do_turn.cpp:607-610`). So `generate_lightmap` (a full light-source scan of the bubble + `build_sunlight_cache` over every z + per-source `castLight`) runs **once per game turn** on the next non-`skip_lightmap` `build_map_cache`, i.e. on the first `game::draw` after each turn.
- Consequences the report should have drawn:
  - (a) the per-OMT emitter cap in §7 item 2 bounds a **per-turn** cost, not an occasional one;
  - (b) during `wait`/driving/auto-move every turn pays it, so it belongs in the R0 benchmark list *as the main per-turn renderer-adjacent cost*, beside `cast_zlight`;
  - (c) R1's "idle frames re-present the cached snapshot" is fine, but any frame/turn decoupling must budget `generate_lightmap` per turn.
- `do_turn` also calls `m.build_map_cache( levz, true )` (skip lightmap) every turn (`src/do_turn.cpp:739`), so the 21-level dirty scans run at least twice per turn. → **MAJOR (R3: hot-path gate mischaracterized).**

### HC-6 `cast_zlight` timing method (§6.1)
- Build: `tests/cata_test` was built with `RELEASE=1 DEBUG_SYMBOLS=1` (`doc/saigon/PROGRESS.md:19`), so it is optimized (`-O2`/`-O3`, `Makefile:444-464`). The report does not state the build flags. It should, since the ms figures depend on them → MINOR.
- **Representativeness.** `do_3d_benchmark` passes zero-initialized `floor_cache` (no floors on any z) and `vertical_direction::BOTH` (default arg) (`tests/shadowcasting_test.cpp:353-389`; `src/shadowcasting.h:137-146`). Production `map::build_seen_cache` uses the real `floor_cache` and casts **UP only** when `no_floor_gaps` on the origin level (`src/lightmap.cpp:1284-1300`). Case 1 fills **all 21 levels** with 1/11 random opacity, which is unlike any real map (underground is solid).
  - So 19.2 ms is a synthetic worst case, not "one 3D FOV rebuild".
  - 13.0 ms ("flat plain", no floors) is a closer outdoor proxy.
  - The report does not mention `directions_to_cast`, nor that the benchmark cannot model roofs ("TODO: add roofs", `tests/shadowcasting_test.cpp:413`) — exactly the Saigon shophouse case.
- Contention: the ran-alongside-another-`cata_test` caveat is disclosed (K11), and 72% CPU share on a 2C/4T part makes the numbers upper-ish bounds. Acceptable as disclosed.
- **The headline "60 fps movement is CPU-bound before drawing" (§0 item 8, §6.1) conflates turns with frames.** `build_seen_cache` runs only when `player_prev_pos != p`, range changes, or a cache is dirty (`src/map.cpp:10839-10855`), i.e. per player move/turn, not per frame. A player moves at keyboard-repeat rate (one turn per keypress), so a 7–19 ms FOV caps **moves/s**, not frame rate. Frames between moves only pay the dirty-gated scans. The report's own §6.3 row 1 puts FOV "outside the frame budget", which contradicts the §0 wording. → **MAJOR (R7/R2: unrepresentative synthetic number presented as the per-move cost; frame/turn conflation in the executive summary).**

### HC-7 Shaders: 8 `.frag`, 0 `.vert`, fragment-only render state (§0 item 1, §1.2)
- `ls data/shaders` = `grayscale, memory_blue_dark, memory_darken, memory_sepia_dark, memory_sepia_light, nightvision, overexposed, tint` (all `.frag`). **Confirmed.**
- `render_state::create` fills only `info.fragment_shader` and sets `num_sampler_bindings`, `num_storage_textures` and `num_storage_buffers` to 0 (`src/cata_shader.cpp:189-210`). **Confirmed.** "No instancing / depth / MRT" holds for the `SDL_Renderer` path.
- No local SDL3 header was found to check the `SDL_GPURenderStateCreateInfo` field list itself. The field names match their use in code, so the R4a "extra sampler bindings" spike is plausible, and the report correctly flags it UNVERIFIED.
- Missing nuance: the report never cites the in-code fact "SDL3 gpu renderer applies the bound custom fragment shader to every draw command, textured or not" (`src/cata_tiles.cpp:4089-4091`). This is the load-bearing evidence that a textured `SDL_RenderGeometryRaw` batch (R2a) would run under the variant shader. → see D-list (MINOR).

### HC-8 Draw order and per-sprite lookup (§0 item 3, §2.1)
- 11 `drawing_layers`, the z → row → layer → column loop, and no sort: **confirmed** (`src/cata_tiles.cpp:1026-1033`, `:1053`, `:1063`, `:1120-1123`).
- String-keyed lookup per sprite: **confirmed**. `draw_from_id_string_internal` → `find_tile_looks_like` → `find_tile_with_season` (per-season `unordered_map<std::string, season_tile_value>`, `src/cata_tiles.h:345-348`). Concatenations: `id + "_transparent"` (`:2428`), `id + "_int" + std::to_string(…)` (`:2438`), `id + variant` / `id + "_var_" + variant` / vehicle-part `id + "_" + chunk` loop (`:2008-2026`).
- Overstatement: "a `get_option<bool>( "NV_GREEN_TOGGLE" )` string lookup" per call. The expression is `apply_night_vision_goggles && get_option<bool>(…)` (`:2394`), which short-circuits, so the option lookup runs only while NV goggles are active. → MINOR.
- Vehicle-part variant suffix loop: allocates up to k strings per vpart per frame (`:2013-2026`). The report covers this in its range citation. OK.

### HC-9 Draw path mutates game state (§0 item 3, §2.1)
- **Confirmed.**
  - `draw_terrain` → `get_avatar().memorize_terrain(…)` (`src/cata_tiles.cpp:3136`) and `here.memory_cache_ter_set_dirty( p, true )` (`:3130`).
  - The memorize loop → `you.memorize_clear_decoration` (`:1491`).
  - `you.prepare_map_memory_region` (`:708-711`).
  - `memory_cache_ter_set_dirty( …, false )` (`:1451`).
  - `game::draw` → `map::update_visibility_cache` → `overmap_buffer.set_seen` (`src/map.cpp:7750`).
- The memorize loop size "14,641 calls per redraw" is an **upper bound**. It `continue`s on every tile with `would_apply_vision_effects` (`:1477`) and skips iso on-screen tiles (`:1470`). Report states it as a fixed count → MINOR.
- Missed mutation: `cata_tiles::draw` itself calls `set_draw_cache_dirty()` and writes `here.prev_top_left/prev_bottom_right/prev_o` (`:701-706`). These are `map` members written from the renderer, which also matters for a snapshot split → MINOR.

### HC-10 Iso facts (§4)
- `tile_isometric` field, loader key `"iso"`, `tile_iso` absent: **confirmed** (`src/cata_tiles.h:301`, `src/tileset_loader.cpp:397`; grep `tile_iso\b` = 0).
- "No rotation or vertical flip": **confirmed** (`src/cata_tiles.cpp:2909-2950`). Horizontal flip (`rota == -1`) **is** still applied in iso (`:2824-2826`, `:2849`, `:2888-2892`). The report omits this; it matters for directional sprite design → MINOR.
- Colored-light mask fallback disabled in iso: **confirmed** (`zlev_has_color = … && ( shader_tint || !iso )`, `:1058-1061`).
- **14 gameplay call sites: confirmed.** `grep is_tileset_isometric()` = 15 uses outside the definition, 1 in `src/sdltiles.cpp:6671`. The 14 others: action.cpp 543/576, input_context 609, handle_action 310/2113, game 2556, advanced_inv 259, monmove 1265, ranged 3346, avatar_action 307, construction 808/865, output 2619/2666.
- **"Fixed 2:1 transform in 5 functions" is wrong and internally inconsistent.**
  - The report names **6** functions in §4.5 (`get_window_base_tile_counts, get_window_any_tile_range, tile_to_player, player_to_tile, player_to_screen, screen_to_player`), and misses a 7th, `get_window_full_base_tile_range` (`:1711`).
  - More importantly, projection-dependent math is spread across **≥ 15 functions** in `src/cata_tiles.cpp` (20 `is_isometric()` calls plus local `iso` flags): `draw` (×6), `draw_sprite_at` (`:2811` destination offset), `draw_from_id_string_internal` (`:2411` occlusion distance), `draw_sct_frame` (`:4869`), `draw_weather_frame` (`:4819`), `draw_zlevel_overlay` (`:4109`), `draw_square_below` (`:3067`), `draw_minimap` (`:1600`), `load_tileset` (fog alpha `:519`).
  - The R3 seam ("a `projection` object owns the 5 transform functions") is therefore **under-scoped**. A rotatable camera would leave SCT, weather, fog, cursor/square-below and sprite offsets in the old projection. → **MAJOR (R2/R5).**

### HC-11 Seams and roadmap feasibility (§5, §8)
- **Seam A (frame_snapshot)** is feasible in shape, but its invalidation inputs are not enumerated. Resolved sprites today depend on per-draw inputs beyond map state:
  - the view origin `o` (occlusion retract distance and the `_transparent` swap, `src/cata_tiles.cpp:2405-2432`);
  - transient draw overrides (`init_draw_*_override` from `src/animation.cpp`, voided at the end of every draw, `:1456-1464`);
  - wall-clock animated-tile frame selection (`std::chrono::steady_clock` in the sprite pick, `:2320-2338`);
  - NV-goggle state read per draw (`:720-721`);
  - per-turn creature visibility.

  `map_epoch` (the proposed key) does not exist (`grep map_epoch src` = 0). A snapshot that freezes `sprite_ref` would freeze animated tiles on "idle-frame reuse", contradicting the §6.3 "animations, flicker, rain" row.
- **Seam C (batching)**: the precedent `minimap_vertex_batch` is **untextured**. The header says "one untextured SDL_RenderGeometryRaw" (`src/pixel_minimap_geometry.h:13`), and the wrapper passes no texture/UV (`src/sdl_wrappers.cpp:487-500`). Textured geometry is unproven in-tree. Feasibility is supported by the in-code note that the gpu renderer applies the bound fragment shader to every draw command (`src/cata_tiles.cpp:4089-4091`), but the report does not cite it. Vertex-colour tint is correct only while a shader is bound; without a shader SDL multiplies by it (`src/cata_tiles.cpp:2877-2878`), so the atlas-fallback path must send white vertices.
- **Validation oracle (R0/R1/R2a)**: the headless golden test uses `setup_software_renderer` (dummy video + software renderer). On it `SDL_GetGPURendererDevice` returns NULL and the shader variant path is disabled (`src/cata_shader.cpp:692-700`; "the software fixture never binds", `:820`). Goldens would cover only the atlas-fallback and silhouette-mask path, **not the default runtime (gpu driver + `variant_pass`) path**. R2a's "within 2 LSB of legacy" on the software renderer also compares `RenderTexture` blits against `RenderGeometry` triangle rasterization, whose edge coverage may differ (UNVERIFIED).
- **Merge rules vs roadmap**: rule (i)/rule 2 ("upstream files get only call-site hunks", "≤ 1 call-site hunk per phase") contradicts:
  - R1 step 1/4 (move memorization out of `draw_terrain`/the memorize loop; turn the `draw_*` layer functions into builders, i.e. a rewrite of ~3,000 lines of `src/cata_tiles.cpp`);
  - R3 (replace `tile_isometric` across 14 gameplay call sites in 10 files).

  There is no estimate of conflict surface per phase, and no upstream-first option for R0 counters is evaluated beyond "offer upstream".
- Churn numbers recomputed: cata_tiles 12/47, sdltiles 13/53, cata_shader 6/15, tileset_loader 4/12, lightmap 3/8, shadowcasting 0/2, map 14/32 all match. `src/game.cpp` is **21/59**, not 21/57 → MINOR.
