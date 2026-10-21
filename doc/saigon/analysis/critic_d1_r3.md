# Critic D1 r3: Rendering & UI Pipeline (audit of d1_r3.md), final round

- Critic unit: round 3 (final). Rubric: `doc/saigon/analysis/CRITIC_RUBRIC.md` (N=1, k=3).
- Code under audit: base SHA `fe6a10c2b1`. The working tree equals HEAD `2302b8813d`, whose source differs from base only in the C6 hunks of `src/game.cpp` and `src/main.cpp`; the r3 header's numbering rule was applied.
- Status: complete. Working notes are in Appendix A.

## Verdict

**REJECT** under the rubric: 0 BLOCKER, 2 MAJOR, 9 MINOR. The citation failure rate is 1/462 = 0.2%, under the 2% bar, so the verdict fails on the MAJOR count only.

Final-round disposition: **accept into TDD with conditions.** Both MAJORs are specification errors with a known one-paragraph fix, not missing analysis. Each is carried into the risk register below as a TDD entry gate, and no further analyst round is requested. RR1–RR9 are accepted as honest downgrades. RR3 and RR4 are accepted only with the amendments listed.

## Summary

r3 is a real revision. All four r2 MAJORs were fixed in the body, not just in the changelog, and I checked each against the code:
- **Vsync.** `create_game_renderer` (`src/sdltiles.cpp:409-415`) has exactly 4 callers (`:691`, `:708`, `:1767`, `:2192`). No other `CreateRenderer` or `SDL_CreateRenderer*` call exists in `src/` or `tests/`. The property is set at `src/sdl_wrappers.cpp:1157-1158`, and no vsync option exists.
- **NPC colour injection.** `src/lightmap.cpp:1466-1474` matches exactly. The NPC z-change at `src/character.cpp:2795-2799` and the bubble shift (`src/game.cpp:10314-10317` with `src/map.cpp:513-522`) are correctly described.
- **Emitter arithmetic.** N_max = (5 − 2)/0.075 = 40, and 132²/24² = 30.25 OMTs; both are correct.
- **§8 footprint.** I re-ran the churn for every factor, including the files absent from the table. The sums R1 ≈ 71.9k, R3 = 20,515 and R4 = 5,210 recompute exactly.

The MINORs are also fixed:
- the epoch sites `src/game.cpp:6193` and `src/do_turn.cpp:540`, with the `set_draw_cache_dirty` grep complete at 5 sites;
- the per-turn `src/do_turn.cpp:765`;
- the avatar-relative depth bound (`src/map.cpp:7704`, `:7711`);
- the benchmark through public setters (`src/map.h:494`, `:497`; protected at `:2083-2085`);
- `rng_set_engine_seed` (`src/rng.h:28`) and the clock seam, which covers all 3 `steady_clock` reads;
- the overlay list (`src/cata_tiles.cpp:1502-1565`) and the zone-manager row.

Two new MAJORs remain, both in the areas this round was told to scrutinize:
1. **Fix (a)'s `colour_stale` flag is set on the level that is currently valid.** So any generation of a different z wipes fresh colour. The worst case is look-up mode, the report's own route to viewing upper storeys: the avatar floor loses its tint while its `lm` is deliberately preserved. Two r3 statements are false for this case: "only the previous camera z is flagged" and "white light only, which is correct". `[lightmap][multiz]` has no case that can detect it (D1).
2. **The per-turn total of ≤ 33 ms omits the move's own redraw.** By the report's own table headers, the per-frame rows (≥ 4.8 ms at target) are paid on that redraw, and R1 moves the memorize loop to per turn with no row. The "≤ 13 ms turn simulation" slice has no source. At target values the budget does not close even with presents coalesced (D2).

## r2 defect closure check

| r2 item | Verified in body? | Evidence / residual |
|---|---|---|
| D1 vsync | **Yes** | §0 item 2, §1.1, §6.2, §6.3 rows, R0 timer + log, options (1)–(3). Residual m1 (grep claim incomplete) |
| D2 NPC colour / fix (a)(b) / test | **Partly** | Mechanism, z-change and shift are correct. Fix (a) is mis-specified (**new D1**). Fix (b) over-invalidates (m6). The test cannot run as written (m5) |
| D3 emitter arithmetic | **Yes** (§6.3, §7) | §0 item 10 still says "≤ 64" (m2). Window nit and F omits the twilight pass (m7) |
| D4 R3/R4 footprint | **Yes** | All hunks are listed and the arithmetic recomputes. The R1 row omits the `map.cpp` and `level_cache.h` hunks needed by the D2 fix (m4) |
| m1/F1 epoch sites | Yes | `src/game.cpp:6193`, `src/do_turn.cpp:540`; the grep of `set_draw_cache_dirty` is complete |
| m2 snapshot inputs | Yes | `src/cata_tiles.cpp:1502-1565` list matches the code; zone manager at `:4048`, `:4052` |
| m3 benchmark callable | Yes in §6.1 | R0 step 3 still says 3×3 OMT and 0/16/64 (m3) |
| m4 "every turn" | Yes | `src/do_turn.cpp:472-516` values match (`:478`, `:486`, `:488`, `:490`) |
| m5/F3 visibility gate | Yes | `src/do_turn.cpp:765`; 11–12 levels is correct |
| m6 caller nits | Yes | `src/avatar_action.cpp:567-570`, `src/map_helpers.cpp:75` |
| m7 golden determinism | Yes | `src/rng.h:28`, `ANIMATIONS` at `src/handle_action.cpp:285`, clock seam. Fixed `calendar::turn` not stated (m8) |
| m8 light-texture offset | Yes | `src/sdltiles.cpp:3662-3663` |
| Missed: lightmap freshness | Yes (§6.4, RR5) | Wording nit (m9) |

## Citation verification table

Method: a regex extractor for `path:line[-line]` plus same-line `` `:N` `` continuations, then a range check and a backticked-symbol ±5-line heuristic. Every heuristic non-match was read by hand. I also printed about 60 high-impact citations for a claim-level check. See Appendix A, WN-10.

| Check | Count |
|---|---|
| Citation occurrences | 609 (matches r3's own count) |
| Unique (path, range) | 462 (matches) |
| Path missing | 0 |
| Line out of range | 0 |
| Orphan continuations | 0 |
| Heuristic non-match, manually reviewed | 29; all OK |
| Symbol present but claim contradicts code | 1 (F1) |
| **Failure rate** | **1 / 462 = 0.2%** |

FAIL rows:

| # | Report line | Citation | Claim | Actual |
|---|---|---|---|---|
| F1 | 109 | `src/sdl_wrappers.cpp:1130`, `:1157-1158` | "`[GREP]` … `vsync` appears only in `src/sdl_wrappers.cpp:1130`, `:1157-1158`" | Also in `src/sdl_wrappers.h:372` (declaration) and `:369`, whose comment reads "vsync via SDL_SetRenderVSync". The conclusion (no option) stands, but the grep result is misquoted (m1) |

## Defects

### MAJOR

**D1 (R2/R5): Fix (a)'s `colour_stale` flag also marks the level that is currently valid, so the fix wipes fresh colour; the `[lightmap][multiz]` test cannot detect this.**
- Claim (§2.2, fix (a)):
  - "clear `light_color_cache`, `has_colored_lights` **and** `light_source_buffer` for every z ≠ `zlev` marked `colour_stale`. `colour_stale` … is set when that level was generated …"
  - "Normally only 1–2 levels are flagged (the previous camera z)."
  - "Character lights on L then carry no buffered colour: white light only, which is correct because L has no scanned colour emitters."
- Evidence:
  - The flag is set on *every* generated level, including the one generated a moment ago, so it means "has ever been generated", not "stale". Any `generate_lightmap( z' )` with z' ≠ z clears z's fresh colour.
  - **Look-up mode** (`LEVEL_UP`, `src/game.cpp:6235-6246`):
    - `invalidate_map_cache( center.z() )` dirties the camera z **and every level below**, because it calls `set_transparency_cache_dirty( z )`, which calls `set_lightmap_cache_dirty_below( z )` (`src/map.cpp:390-395`, `:456-463`). The avatar z is therefore dirty.
    - `build_map_cache( u.posz() )` then fully generates the avatar floor with colour, and the flag is set.
    - The redraw at the top of the loop (`src/game.cpp:6195-6196`) generates the camera z, and fix (a) clears the avatar floor's colour and buffer.
    - Yet `build_sunlight_cache` deliberately preserves the avatar z's `lm` in exactly this case (`src/lightmap.cpp:388-393`). The drawn avatar floor, below the camera, keeps its lit lamps but loses all tint for the whole look session. Today it shows correct tint.
    - So the claims "only the previous camera z is flagged" and "L has no scanned colour emitters" are false here.
  - **Mid-turn NPC z-change.**
    - The camera z is generated during `handle_action` (`src/do_turn.cpp:662`).
    - `monmove()` (`:742`) → `Character::on_move` → `build_map_cache( L )` (`src/character.cpp:2795-2799`) → fix (a) clears the camera z's colour. The camera z is not dirty, so it is not regenerated until the next turn's loop (`src/do_turn.cpp:607-610`).
    - The `FORCE_REDRAW` redraw (default true, `src/do_turn.cpp:754-756`) and NPC attack animations in between therefore show the camera floor untinted. This is a regression that fix (a) introduces.
  - **Test.** The `[lightmap][multiz]` steps 3–6 assert only that colour is *absent* on non-camera levels. None asserts that fresh colour survives on a legitimately generated non-camera level, so an over-clearing fix passes every step.
- Required fix:
  - Re-key fix (a) on fix (b)'s epoch. Clear level z ≠ zlev only when `get_cache( z ).lightmap_epoch != map::lightmap_epoch`, i.e. when it was not generated in the current epoch. Equivalently, set `colour_stale` when a level is *dirtied without being regenerated*, not when it is generated.
  - Add test step 7, look-up: the avatar on z0 beside the red lamp; `LEVEL_UP` path (`invalidate_map_cache( 1 )`, `build_map_cache( 0 )`, `build_map_cache( 1 )`). Assert that z0 colour at T is non-zero and equal to a fresh z0-only generation.
  - Add step 8, mid-turn: generate the camera z, then an NPC z-change on another level. Assert that the camera-z colour is unchanged.
  - Delete "gameplay-neutral … white light only, which is correct" unless the re-keyed version is used.

**D2 (R3/R2): The per-turn total of "≤ 33 ms" omits the move's own redraw and the R1 per-turn memorize cost, so the closure is false.**
- Claim (§6.3, total row): "≤ 33 ms: 8 + 5 + 3 + 4 = 20 ms of renderer-adjacent CPU, plus ≤ 13 ms of turn simulation, plus 0 ms present on auto-repeat."
- Evidence:
  - The per-turn table header says its rows are "paid once per turn or move, on the first redraw after it". The per-frame header says its rows are "paid on every redraw".
  - Under option (2) the move's redraw still runs, because RR5 and §6.4 require `generate_lightmap` to stay on that path. So the move also pays the per-frame rows at target: `bmc_frame` 0.3 + emission 1.5 + 1 + ImGui 2 = **≥ 4.8 ms**.
  - R1 moves the memorize loop (≤ 14,641 calls) into `commit_frame_side_effects`, "per turn", but no per-turn row carries it.
  - The 13 ms simulation slice has no source; it is the remainder after subtracting 20 ms from 33.
  - At the report's own targets the per-turn sum is therefore ≥ 37.8 ms with coalescing, above the 33.3 ms limit for 30 moves/s, and ≥ 54.5 ms without coalescing.
  - The "36.7 ms" figure is 20 + 16.7. It is arithmetically right, but it is not the total.
  - RR4's trigger ("if p50 present ≥ 10 ms … implement coalescing") is computed against this incomplete total, so it fires on the wrong condition: the budget is already over at 0 ms present.
- Required fix:
  - Add rows for "move redraw (per-frame rows at target)" and "memorize (R1, per turn)".
  - Label the simulation slice "remainder, UNVERIFIED; to be measured with existing profiling".
  - Recompute the total, and either lower the renderer targets (for example FOV ≤ 6 ms and lightmap ≤ 4 ms) or state that 30 moves/s requires simulation ≤ 8 ms.
  - Make RR4's trigger "total per-turn p50 > 33 ms with present > 0", not "present ≥ 10 ms".

### MINOR

- **m1 (R2) The vsync grep result is misquoted** (F1). Add `src/sdl_wrappers.h:369`, `:372`. Note that the header comment already names `SDL_SetRenderVSync`, which is partial in-tree evidence against RR9.
- **m2 (R2) §0 item 10 still says "≤ 64 in the bubble at night".** That is r2's withdrawn budget, and it contradicts §6.3 and §7 (≈ 40 per bubble, ≤ 1 fixture per OMT). The executive summary is what gets copied. Fix it.
- **m3 (R5) R0 step 3 contradicts §6.1.** Step 3 says "a fixed 3×3-OMT shophouse block" and "0/16/64 emitters"; §6.1 (the r3 m3 fix) says a 6×6-OMT district and 0/16/32/64. §6.3 also says 0/16/64. Unify them.
- **m4 (R5) The R1 footprint misses the D2-fix hunks.**
  - Fix (a) ("set for all z on `invalidate_map_cache`") and fix (b) ("incremented in `map::invalidate_map_cache`") both edit `src/map.cpp:513-522`. R1's row omits `map.cpp`, although rule 2 says "R1 (D2 fix)" touches it.
  - `colour_stale` is defined as a `level_cache` bool, so it belongs in `src/level_cache.h`, not `map.h`.
  - RR3's fallback, "≈ 30-line fork hunk in `lightmap.cpp` (≈ 0.24k)", should also count `map.cpp` (churn 32) and `level_cache.h` (churn 2): ≈ 30·8 + 6·32 + 2·2 ≈ 0.44k.
- **m5 (R5) `[lightmap][multiz]` is not executable as written.**
  - (i) "Advance 10 turns, running `build_map_cache( 1 )`" never re-dirties z1. A static NPC does not trip the `cached_char_lights` detector (`src/map.cpp:10893-10907`), so `generate_lightmap( 1 )` returns at the gate (`src/lightmap.cpp:506-508`). Today's "strictly increasing" characterization would then fail for the wrong reason. Each turn must call `set_lightmap_cache_dirty( z )` for all z, mirroring `src/do_turn.cpp:607-610`.
  - (ii) The fix (b) oracle "the prepass reports tint skipped" lives in `cata_tiles::draw` (TILES-only, `src/cata_tiles.cpp:1058-1061`), but the test is declared curses-buildable. Specify a map-side predicate, for example `bool map::level_colour_is_current( int z ) const`, that the prepass calls and the test asserts.
- **m6 (R2) Fix (b) over-invalidates.**
  - A global epoch bump inside `invalidate_map_cache( z )` makes **every** level stale, but it dirties only z and the levels below it.
  - Callers whose z can lie below the camera (for example `src/teleport.cpp:158`, `src/ranged.cpp:3716`, `src/timed_event.cpp:317`, `src/npctalk.cpp:5065`) therefore make the camera floor's fresh tint skip until the next turn.
  - Bump the epoch only in `do_turn`, and mark the invalidated levels with a per-level "stale" stamp instead. Also state the `set_lightmap_cache_dirty_below` behaviour in §2.2 item 5.
- **m7 (R7) Emitter-rule edge terms.**
  - A 5.5×5.5-OMT bubble at arbitrary alignment touches up to 6×6 = 36 OMTs. "≤ 1 per OMT averaged over any 5×5 window" therefore admits about 36 fixtures in a bubble, plus 10 for traffic and characters, which is about 46 against the budget of 40.
  - F omits the dawn/dusk/weather colour pass, a full 17,424-cell loop when `ddc.is_colored()` (`src/lightmap.cpp:549-581`). F must be measured at dusk under coloured weather, not only at 0 emitters at noon.
- **m8 (R5) The golden lanes also need a fixed `calendar::turn`.** It drives the season sprite lookup (`src/cata_tiles.cpp:1969`) and natural light (`g->natural_light_level`, `src/lightmap.cpp:544`). Add it to the determinism seam.
- **m9 (R7) RR5 and §6.4 say `generate_lightmap` "stays on the per-turn path".** Today it is redraw-tied, as §2.4 itself says. Rephrase as a requirement: "must be on the per-turn path". Note that today, during sleep, NPC/monster vision and `Character::fine_detail_vision_mod` read an `lm` up to 30 minutes old (`src/lightmap.cpp:883-890` reads `lm` with no dirty check).

## Residual risks RR1–RR9: final-round judgement

| RR | Judgement | Reason |
|---|---|---|
| RR1 no tiles binary | **Accept** | True: no SDL3 headers or tiles binary in the clone. The mitigation, an R0 entry gate with every UNVERIFIED line as an R0 checklist item, is concrete |
| RR2 synthetic perf | **Accept** | Honest; concrete benchmarks and a re-derivation commit. It must also re-derive the D2 total |
| RR3 multi-floor bugs reading-based | **Accept with amendment** | The runtime-unverified status is honest, and the mechanism checks out by reading. But the planned mitigation, "land fix (a)+(b)", must land the re-keyed fix (a) of D1 together with tests 7–8, and the fallback surface is ≈ 0.44k (m4), not 0.24k |
| RR4 vsync × throughput | **Accept with amendment** | Honest unknown. The trigger must be keyed on the corrected per-turn total (D2), and coalescing must account for the `FORCE_REDRAW` present (Missed 1) |
| RR5 lightmap freshness | **Accept** | Correct handoff to d4, with a test. Wording fix m9 |
| RR6 upstream acceptance | **Accept** | Staged PRs, a fallback trigger (2 merge cycles) and tracking (K6) are concrete |
| RR7 platform reach | **Accept** | The permanent legacy backend plus `caps()` is a sound mitigation |
| RR8 art cost | **Accept** | The gating (ortho + R4a first, `looks_like`) is concrete |
| RR9 SDL API names | **Accept** | True (no headers). Note the partial in-tree evidence (m1) |

No false assertion was found among RR1–RR9. The false assertions this round are inside §2.2 fix (a) (D1) and the §6.3 total row (D2).

## Missed topics

1. **`FORCE_REDRAW` is on by default** (`src/options.cpp:2394-2397`). `game::do_turn` calls `ui_manager::redraw(); refresh_display();` in every turn where `u.get_moves() < 0` (`src/do_turn.cpp:754-756`). At avatar speed below 100, or for actions costing more than 100 moves, every non-acting turn pays an extra full redraw and a vsync-paced present. It is absent from the §1.1 present inventory, from §6.3 and from coalescing option (2). Add it as a per-turn present source, and let coalescing suppress its present but not its redraw, since that redraw is also what regenerates the lightmap in non-acting turns.
2. **A zero-code vsync lever for R0, UNVERIFIED.** SDL3 may honour the `SDL_RENDER_VSYNC` hint or environment variable when creating a renderer. If so, R0 can A/B the present-duration timer without a code option. Check it against the SDL3 headers in R0 step 1 (RR9).
3. **The look-mode lighting path as a test fixture.** It is the route the report recommends for viewing upper storeys today, yet no test covers its lighting (see D1, test steps 7–8).

## Required changes (for the TDD hand-off; no further analyst round)

1. [ ] Re-key fix (a) on fix (b)'s epoch (or "dirtied without regeneration"). Remove the false "previous camera z only" and "correct" claims. Add `[lightmap][multiz]` steps 7 (look-up preserves the avatar-floor colour) and 8 (a mid-turn NPC z-change preserves the camera-z colour) (D1).
2. [ ] Fix the §6.3 per-turn total: add the move-redraw and R1 memorize rows, label the simulation remainder, recompute, rebalance the targets, and re-key RR4's trigger (D2).
3. [ ] Make `[lightmap][multiz]` executable: dirty all z per simulated turn, and add a map-side `level_colour_is_current( z )` predicate for the fix (b) oracle (m5).
4. [ ] Bump fix (b)'s epoch only per turn, with per-level stale stamps on invalidation. Document `set_lightmap_cache_dirty_below` (m6).
5. [ ] Fix §0 item 10 (≈ 40 per bubble) and unify R0 step 3 with §6.1 (6×6 district; 0/16/32/64) (m2, m3).
6. [ ] Add `map.cpp` and `level_cache.h` to the R1 row and to the RR3 fallback surface (m4).
7. [ ] Correct the vsync grep quote; add the emitter window bound, the F-at-dusk measurement, the fixed `calendar::turn` for goldens, and the RR5 wording (m1, m7, m8, m9).
8. [ ] Add `FORCE_REDRAW` to the present inventory, the budget and coalescing (Missed 1).

## Appendix A: working notes
- WN-1 Vsync (D1 closure): `create_game_renderer` at `src/sdltiles.cpp:409-415` (software `true,false` :412; accelerated `false,true` :414). Callers exactly 4: `:691` (accelerated), `:708` (software fallback), `:1767` (recreation, `software` param), `:2192` (test-fixture software). No other `CreateRenderer`/`SDL_CreateRenderer*` call in `src/`/`tests/` outside `src/sdl_wrappers.cpp:1162`. `SDL_PROP_RENDERER_CREATE_PRESENT_VSYNC_NUMBER = ( vsync && !software ) ? 1 : 0` at `src/sdl_wrappers.cpp:1157-1158` OK. No option: grep confirms no `VSYNC` option. Nit: the "vsync appears only in `src/sdl_wrappers.cpp:1130`, `:1157-1158`" grep claim omits `src/sdl_wrappers.h:369` (comment "vsync via SDL_SetRenderVSync") and `:372` (declaration). The header comment also names the SDL3 API (`SDL_SetRenderVSync`) that r3 calls UNVERIFIED -> MINOR (n1). Only 2 of the 4 sites can produce an accelerated (vsync) renderer (`:691`, `:1767` when `software==false`); r3 does not say this explicitly but does not contradict it.
- WN-2 Stale-colour mechanism (D2 closure): `src/lightmap.cpp:1466-1474` exact (`buf.color.is_colored()` -> `source_color = buf.color * (1/buf.luminance)`; `light_color_cache[p] += source_color * luminance`; `has_colored_lights = true`). Per-channel max at `:1165-1170` OK. Clears only for generated z at `:518-519` (colour) and `:530-531` (buffer) OK. Growth is at the source tile only (neighbours get `max(source_color*intensity)`, constant); "pinned tint around that NPC" is slightly loose but the cap claim (`src/tile_tint.cpp:22-23`, alpha = ratio*80) is OK. NPC z-change: `Character::on_move` -> `get_map().build_map_cache( this->posz() )` at `src/character.cpp:2795-2799` OK; `build_map_cache` -> `generate_lightmap( zlev )` when not skip (`src/map.cpp:10910-10912`) OK; `build_sunlight_cache` avatar-z skip at `src/lightmap.cpp:388-393` OK. Bubble shift: `src/game.cpp:10314-10317` OK; `invalidate_map_cache` sets only dirty flags (`src/map.cpp:513-522`) OK; `[GREP]` no `light_color_cache`/`light_source_buffer` reference outside `lightmap.cpp`, `cata_tiles.cpp:1060/1091`, `level_cache.*` -> claim holds. Note `invalidate_map_cache` -> `set_transparency_cache_dirty(z)` -> `set_lightmap_cache_dirty_below(z)` (`src/map.cpp:390-395`, `:456-463`): it dirties z AND every level below, which r3 does not state.
- WN-3 Fix (a) flaw (new MAJOR): `colour_stale` is "set when that level was generated", so the *current, fresh* level is flagged too. Any generation of a different z then wipes it. Look-up mode: `look_around` LEVEL_UP -> `invalidate_map_cache(center.z)` (dirties center z and below, incl. avatar z) -> `build_map_cache( u.posz() )` regenerates the avatar z with colour -> redraw -> `generate_lightmap(camera z)` -> fix (a) clears the avatar z (flagged, != zlev), including its fresh `light_source_buffer`. `build_sunlight_cache` deliberately preserves the avatar z `lm` in exactly this case (`src/lightmap.cpp:388-393`), so the floor shows lit lamps with no tint. r3's assertions "Normally only 1–2 levels are flagged (the previous camera z)" and "white light only, which is correct because L has no scanned colour emitters" are false for this case. Same shape mid-turn: NPC z-change during `monmove()` (`src/do_turn.cpp:742`, after the draw in `handle_action`) generates L and clears the camera z colour until the next turn's dirty loop; FORCE_REDRAW (`:754-756`) and NPC animations show the camera floor untinted. `[lightmap][multiz]` has no look-mode case, so it cannot detect this. Fix: key (a) on (b)'s epoch (clear z != zlev whose stamp != current epoch) or set `colour_stale` only when a level stops being regenerated.
- WN-4 do_turn order: dirty loop `src/do_turn.cpp:607-610` -> `handle_action` (`:662`, draw/camera-z generation) -> `build_map_cache( levz, true )` `:739` -> `monmove()` `:742` -> FORCE_REDRAW `:754-756` -> `handle_progress_ui` `:763` -> `invalidate_visibility_cache` `:765` OK. Turn advance `calendar::turn += 1_turns` at `:540` OK.
- WN-5 Per-turn total (scrutiny item): §6.3 per-turn total "≤ 33 ms: 8 + 5 + 3 + 4 = 20 ms ... plus ≤ 13 ms of turn simulation, plus 0 ms present on auto-repeat"; 36.7 = 20 + 16.7 arithmetic OK. But the per-turn table's own header says these costs are "paid ... on the first redraw after it", and the per-frame table says its rows are "paid on every redraw". The move's redraw therefore also pays the per-frame rows (bmc 0.3 + emission 1.5+1 + ImGui 2 = 4.8 ms at target), and R1 moves the memorize loop to per turn (`commit_frame_side_effects`) with no per-turn row. The 33 ms closure omits >= 4.8 ms; at the report's own targets the per-turn sum is >= 37.8 ms with coalescing and >= 54.5 ms without. "≤ 13 ms of turn simulation" has no source. New defect.
- WN-6 Emitter formula: (5-2)/0.075 = 40 OK; 132^2/24^2 = 30.25 OK; 40/30 = 1.33 OK; 30 fixtures + 10 traffic OK. Nit: a 5.5x5.5-OMT bubble at arbitrary alignment touches up to 6x6 = 36 OMTs, so "≤ 1 per OMT averaged over any 5x5 window" bounds a bubble at up to ~36 fixtures, not 30 (worst case 46 total vs 40). F omits the dawn/dusk/weather colour pass (`src/lightmap.cpp:549-581`, a full 17,424 pass when `ddc.is_colored()`), so an F measured at noon under clear skies undercounts. MINOR.
- WN-7 §8 churn re-run (`git log --oneline --since=… fe6a10c2b1 -- f | wc -l`): all 13 table rows match; implied factors for files not in the table also match (cata_shader.h 12, data/shaders 4, cata_tiles.h 27, atlas_bake_plan 2, pixel_minimap.cpp 10, map.h 21, cata_imgui.cpp 28). R3 sum 20,515 and R4 sum 5,210 and R1 71,920 recomputed OK. Gap: R1 row omits `src/map.cpp` (`invalidate_map_cache`, `:513-522`, which both fix (a) "set for all z on invalidate_map_cache" and fix (b) "incremented in map::invalidate_map_cache" edit) and puts `colour_stale` in `map.h` although it is defined as a `level_cache` bool (`src/level_cache.h`). Rule 2 text itself says R1 touches `map.cpp`, contradicting the row. RR3's "≈ 30-line fork hunk in `lightmap.cpp` (surface ≈ 0.24k)" understates the same way. MINOR.
- WN-8 Benchmark access: `set_seen_cache_dirty( int )` `src/map.h:494`, `set_lightmap_cache_dirty( int )` `:497` public OK; `generate_lightmap`/`build_seen_cache` protected `:2083-2085` OK; friends at `:425-441` OK. Path (i) works: `build_map_cache` ORs `get_cache(z).seen_cache_dirty` for all z (`src/map.cpp:10810-10816`) and runs `build_seen_cache` around the avatar position (`:10841-10845`); TILES dirtying is `!test_mode` gated. Inconsistency: R0 step 3 still says "a fixed 3×3-OMT shophouse block" and "0/16/64 emitters", while §6.1 (r3 fix) says a 6×6-OMT district and 0/16/32/64. MINOR.
- WN-9 Golden determinism: `rng_set_engine_seed` at `src/rng.h:28` OK (non-zero seed reseeds; used in tests). `steady_clock` sites in `cata_tiles.cpp`: `:2325` (variant seed), `:4429` (`init_draw_hit`), `:4539` (`void_hit` expiry) — the `render_clock` seam names `init_draw_hit`/`expire_hit_animations` (exists, `src/cata_tiles.h:843`, called from `src/handle_action.cpp:443`) and `expire_hit_animations` (`src/cata_tiles.cpp:4548`) calls `void_hit` (`:4536-4539`), so all three clock reads are covered. OK. `ANIMATIONS` gate at `src/handle_action.cpp:285` OK. Nit: goldens also need a fixed `calendar::turn` (season sprite lookup `src/cata_tiles.cpp:1969`, natural light), not stated.
- WN-10 Mechanical citation check (own extractor, same rules as r2 critic): 609 occurrences, 462 unique (path, range) — identical to the counts r3 states. 0 missing paths, 0 out of range, 0 orphan continuations. Heuristic symbol-in-window non-matches: 29; all 29 read by hand and OK (function-body citations such as the 11 `build_map_cache` caller rows, the 16 projection-inventory line refs, `src/lightmap.cpp:1494-1499` neighbour test, `src/sdl_geometry.h:47-52` rect, `src/sdltiles.cpp:583-594` fullscreen). ~60 high-impact citations spot-printed (present path, vsync, lightmap clears, colour injection, on_move, shift, invalidate, update_visibility_cache, benchmark API, map_scale_constants, cata_shader create info, viewport offset, AUTOPEEK, map_helpers, overlay tail 1502-1565, zone manager 4048): all OK. `refresh_display();` call sites re-grepped: 44 OK.
- WN-11 Missed: `FORCE_REDRAW` defaults to **true** (`src/options.cpp:2394-2397`); `do_turn` then calls `ui_manager::redraw(); refresh_display();` every turn in which `u.get_moves() < 0` after `process_turn` (`src/do_turn.cpp:754-756`). At avatar speed < 100 or for > 100-move actions this is an extra full redraw plus a vsync-paced present per non-acting turn. Not mentioned anywhere in r3 (present inventory, per-turn budget, coalescing option 2).

## Final disposition for TDD

The D1 analysis is **closed for analysis and handed to TDD under conditions**. The following risk-register entries carry forward. Each has an owner phase and an entry or exit gate. Items 1–2 are blocking conditions on the TDD *specs*, not on further analysis.

| ID | Entry | Source | Owner / gate | TDD test that closes it |
|---|---|---|---|---|
| TDD-RR-D1-01 | Fix (a) must be epoch-keyed; it must never clear a level generated in the current epoch | critic r3 D1 | R1 spec gate (before any `lightmap.cpp` edit) | `[lightmap][multiz]` steps 1–8, including look-up and mid-turn NPC z-change |
| TDD-RR-D1-02 | The per-turn budget must close at targets, including the move redraw, R1 memorize and the measured simulation | critic r3 D2; RR2 | R0 exit gate | R0 timers summed per turn on the Saigon district; p50 ≤ 33 ms or targets re-negotiated |
| TDD-RR-D1-03 | No tiles binary: every UNVERIFIED runtime claim is an R0 checklist item | RR1 | R0 entry gate | Tiles test binary builds; L1/L2 lanes run |
| TDD-RR-D1-04 | Synthetic/contaminated performance numbers; N_max re-derived from measured F (at dusk, coloured weather) and c | RR2, m7 | R0 → d2 mapgen guidance | `[seen_cache][saigon]`, `[lightmap][saigon]` on an idle machine; §6.3/§7/d2 updated in one commit |
| TDD-RR-D1-05 | Multi-floor stale colour (growth, z-change, shift) reading-based; fallback fork surface ≈ 0.44k | RR3, m4, m5, m6 | R0 test first (characterization), R1 fix | `[lightmap][multiz]` with per-turn dirtying and a map-side freshness predicate |
| TDD-RR-D1-06 | Vsync blocking × move throughput, including the default-on `FORCE_REDRAW` present | RR4, Missed 1 | R0 data → R1 decision | Present-duration timer per call site, vsync log line; coalescing behind an option if the per-turn total > 33 ms |
| TDD-RR-D1-07 | Lightmap freshness for gameplay during long activities and sleep (`lm` up to 30 min old) | RR5, m9 | d4 simulation; R1 review | d4 test: NPC vision and `fine_detail_vision_mod` at dusk update during a 1-hour wait |
| TDD-RR-D1-08 | Upstream acceptance of R0/R1 (≈ 72k surface), with fork-copy fallback after 2 cycles | RR6 | R1 | Merge time per sync (K6) |
| TDD-RR-D1-09 | `sdl_gpu_backend` platform reach (web, Android without Vulkan) | RR7 | R2b | `caps()` selection test; L1 lane on every CI |
| TDD-RR-D1-10 | Art cost for iso and normal/height/emissive layers | RR8 | R3/R4b gate | Art budget sign-off; `looks_like` coverage check |
| TDD-RR-D1-11 | SDL3 API names (`SDL_GetRenderVSync`/`SDL_SetRenderVSync`, extra render-state bindings, threading) unchecked | RR9, m1, Missed 2 | R0 step 1 / R4a spike | Header grep per API; R4a spike report |
| TDD-RR-D1-12 | Golden determinism: clock seam + RNG seed + `ANIMATIONS=false` + fixed `calendar::turn` | m7-r2, m8 | R0 | L1/L2 goldens bit-stable across 3 runs |
