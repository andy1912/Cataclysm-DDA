# Critic verdict: D4 (JSON Ecosystem & Modding), round 3 (FINAL)

- **Audited report:** `doc/saigon/analysis/d4_r3.md` (626 lines).
- **Rubric:** `doc/saigon/analysis/CRITIC_RUBRIC.md` (N=4, k=3).
- **Code under audit:** base SHA `fe6a10c2b1`.
  - `src/game.cpp` and `src/main.cpp` citations were each resolved against the revision their label names: `git show fe6a10c2b1:` for base, the working tree for HEAD.
  - All other cited files are identical to base. `git diff fe6a10c2b1 HEAD --stat` outside `doc/saigon` and `data/mods/saigon_2000s` shows only `src/game.cpp`, `src/main.cpp`, `tools/saigon/check_mod.sh` and `tools/saigon/format_mod.sh`.
- **Runtime:** HEAD curses `./cataclysm` (built 07:53 from `2efb03fe98`; `2f59828f4b` changed comments only). Every run used a scratchpad `--userdir`. Nothing was written to the repo except this file.

## Verdict

**PASS.** There are 0 BLOCKER, 0 MAJOR and 4 MINOR defects. The citation failure rate is 0.0% (0 of 627 line refs).

All r2 defects (D1–D6) and the missed shared-namespace topic are fixed in substance. The residual-risk section (U1–U11) contains no false assertion. U1 is honestly UNVERIFIED, and a critic runtime probe (below) now supports its central premise. The four MINOR defects are wording and scope errors, and none of them would mislead Part B into an unsafe action. They go into the risk register below.

## Summary

### r2 follow-through (verified against code and runtime, not against the changelog)

| r2 item | Status | Evidence |
|---|---|---|
| D1 C6 incomplete (MAJOR) | FIXED | `git diff fe6a10c2b1 HEAD -- src` matches the report's description exactly. Hunk 1: `game_ui::init_ui` at HEAD `src/game.cpp:549-559`, where `if( test_mode )` sets `TERMY/TERMX = EVEN_MINIMUM_TERM_HEIGHT/WIDTH` and skips `ensure_term_size()`. Hunk 2: HEAD `src/main.cpp:777-784`, where the `cli.check_mods` re-init is under `#if defined(TILES)`. The base `:759-762` unconditional `#if !defined(TILES)` init is unchanged at HEAD. The comment says "report 0", which matches `src/ncurses_def.cpp:105-118`. Commits `2efb03fe98`, `cc765965c0` and `2f59828f4b` exist. `tools/saigon/check_mod.sh:14-26` fails on rc≠0, on `Error loading data`, or on any `ERROR`/`WARNING` in `debug.log`, as stated. |
| D2 exit-0 / C2 redesign | FIXED (with residual scope error, D1 below) | `src/generic_factory.h:455-462`: `reset()` calls `allow_omitted_members()` on every deferred pair before `deferred.clear()`. `src/recipe_dictionary.cpp:917-920` does the same for the only other `deferred_json` holder (`src/recipe_dictionary.cpp:80`). Those two are the **only** `deferred_json` holders in `src/` (grep). `DynamicDataLoader::unload_data()` (`src/init.cpp:645`) calls `MonsterGenerator::generator().reset()`, `recipe_dictionary::reset()`, `items::reset()` and so on. **Runtime-confirmed (critic):** see probe P1. After a failed load, `unload_data()` silently discards all of dda's deferred copy-from JSON: 0 ERROR lines, no abort. |
| D3 MIGRATION hazards | FIXED | The full `migrate_id` caller list reproduces exactly: `src/map.cpp:5829`, `src/mapgen.cpp:2362,2495,2865`, `src/mattack_actors.cpp:1455,1459`, `src/savegame_json.cpp:345,3379`, `src/veh_type.cpp:600,1578-1579`. The count is 0 in `profession.cpp`, `harvest.cpp`, `activity_handlers.cpp`, `butchery.cpp`, `butchery_requirements.cpp`, `npc_class.cpp` and `item.cpp`. `find_template` (`src/item_factory.cpp:3057-3088`) does not migrate either. Single-hop is confirmed three ways: `migrate_id` (`:4720-4735`); the finalize `replacements` map is built once, with no chain resolution (`:1723-1749`); and `replace_items` does a single `find` (`src/item_group.cpp:397-401`). Turret hiding is confirmed: `NO_INSTALL_HIDDEN` (`src/veh_type.cpp:599-603`). Its effect is on the install menu. |
| D4 route (a)/(c) lists | FIXED | Script-verified. The only dda `mapgen` objects targeting `road_*`/`bridge*` are the 5 road objects (6 om_terrains; weights at `road.json:5,162,257,531,744`) and 4 bridge objects (`bridges.json:43,78,117,175`, `vanilla_bridge_weight`). The road/bridge mapgen objects contain no direct vehicles. The only vehicle-bearing nested entry points reachable from them are the 8 listed ids, and every reference and definition line matches. Each id has exactly one definition at weight 1000. One weight-0 `24x24_sidewalk_curved_curvy_outer` variant has `place_vehicles`, but weight 0 is never added, so it is not a gap. |
| D5 counts | FIXED | Re-run: 342 `profession` objects, 125 with no `items` (123 of them hobbies). 5,054 ITEM copy-froms, 4,208 of which restate `subtypes`. |
| D6 `map_extra_id` | FIXED | Per-file declaration counts: 13 in `map_extras.cpp`, 1 in `timed_event.cpp`, 1 in `overmap.cpp:651` and 1 in `overmapbuffer.cpp:470`. The last two are null ids, as stated. The 14 unique ids reproduce. |
| Missed 3 (shared namespace) | FIXED | §1.3 row, §8.1 `vehicles/` and R8 all cite `src/veh_type.cpp:1342` (`vgroups[vgroup_id( id.str() )].add_vehicle( id, 100 )`) and the append semantics at `src/vehicle_group.cpp:80-87`. The mitigation is concrete: `sgn_veh_*`/`sgn_vg_*` prefixes plus a CI grep. |

### Runtime probes (critic, r3)

| # | Command (scratch `--userdir`) | rc | debug.log ERROR | Finding |
|---|---|---|---|---|
| P1 | `./cataclysm --check-mods c3_syntax zz_ok` (c3_syntax = truncated JSON; zz_ok = one valid snippet; both depend on dda) | **0** | **0** | The set order was c3_syntax then zz_ok. c3_syntax printed `Error loading data: … end of file`. zz_ok's `load_core_data()` then calls `unload_data()` (`src/game_io.cpp:220-225`), which discarded the stale deferred JSON **silently**, and the process exited cleanly after 233 s. (a) This is empirical support for C2's mechanism. (b) It shows the report's "does not exit 0 / rc 134" claim holds only when the failing mod is the last one checked (D1). |
| P2 | `SAIGON_USERDIR=<scratch>/ud_live tools/saigon/check_mod.sh saigon_2000s` (fresh userdir, live mod at `25bb166b5b`) | 0 | 0 | Printed `OK: saigon_2000s`, 353 s wall on a loaded machine. |

## Citation verification

Method: a script extracted every `path:line[-line][,…]` and every `:NNN` shorthand, binding each shorthand to the last path on the same report line. It resolved `game.cpp`/`main.cpp` by their `(base SHA; HEAD …)` labels, range-checked every ref, and dumped ±2 lines of each unique pair. A token heuristic flagged the pairs where no backticked word from the report line appeared within ±5 lines. I read all 42 flagged pairs by hand, and I also read every citation that is new in r3 by hand. All of them hold.

| Metric | Count |
|---|---|
| Line refs extracted | 627 |
| Unique (path, range, revision) pairs | 480 |
| Out of range / nonexistent | 0. `tools/saigon/check_mod.sh:14-26,19-20` is HEAD-only and correct at HEAD. |
| Symbol or claim not at cited line (±5) | 0 |
| `game.cpp`/`main.cpp` refs with the wrong revision label | 0. All base/HEAD pairs checked: `681-700`/`688-707`, `995-1016`/`1002-1023`, `1063`/`1070`, `1072`/`1079`, `715`/`722`, `695-697`/`702-704`, `548-552`/`549-559`, `797`/`801`, `794-797`/`798-801`, `877-882`/`881-886`, `882`/`886`, `931`/`935`, `771-780`/`771-784`, `759-762` (base = HEAD), `259` (base = HEAD), `540-546` (base = HEAD). |
| **FAIL** | **0 (0.0%)** |

The global backticked-identifier grep was aborted for time, so it is not claimed here. Every new r3 identifier was grepped individually: `unload_data`, `allow_omitted_members`, `deferred`, `migrate_id`, `replace_items`, `NO_INSTALL_HIDDEN`, `EVEN_MINIMUM_TERM_*`, `test_mode`, the 8 nested ids and the 4 bridge om_terrains. All were found.

## Defects

### D1 (MINOR, R2/R7): "A hard JSON/load error does not exit 0" is false for multi-mod `--check-mods`
- **Claim:** §0.5 says "A hard JSON/load error does not exit 0. It aborts with rc 134." §6.2 gotcha 2 and R2 say the same.
- **Evidence:** probe P1 exited **rc 0** with 0 ERROR lines despite a hard JSON error in the first mod checked.
  - The abort happens only if the failing mod is the **last** one iterated. Any later iteration's `load_core_data()` → `unload_data()` cleans up silently, and `check_mod_data` returns `true` (`src/game_io.cpp:210`).
  - Iteration order is interned `std::set<mod_id>` order (the report's own §1.4), so which mod is last is not controllable.
  - The gate itself stays safe, because `check_mod.sh` greps `Error loading data`. The C2 seam's "local `bool failed`" must be function-scoped (declared before the loop) so that it persists across iterations.
- **Required fix (carried to TDD):** qualify R2 to "rc 134 if last; rc 0 otherwise". In C2, declare `failed` at function scope. Add P1 as the C2 multi-mod test case.

### D2 (MINOR, R2): stale and self-contradicting statements
- §7 (line 537) still says per-pack timing "could not be run: C6 blocks `--check-mods`". C6 has landed. Also, `load_packs` timing is not on the `check_mod_data` path, which uses `load_data_from_dir`.
- §6.2 (line 499) says "Wall time for a dda-only check is ~60-95 s", but the evidence it cites reads 3 min 32 s wall / 58 s user. The critic measured 233 s and 353 s wall on a loaded machine.
- **Fix:** state CPU-user time as the metric (≈58 s), and give wall time as load-dependent (1.5–6 min).

### D3 (MINOR, R2): MIGRATION exposure overstated for NPC classes and professions
- **Claim:** §2.3 says "A migrated US item still appears from professions, NPC classes and harvest lists that name it directly". U9 says "Grep profession/harvest/npc_class references".
- **Evidence:**
  - `npc_class` has no `itype_id` fields. It references only `item_group_id`s (`src/npc_class.h:57,119-121`), so the finalize group rewrite (`src/item_factory.cpp:1753`) covers it.
  - In dda, 587 of 600 profession `items.both/male/female` sub-entries are item-group **objects**, which are migrated. Only 13 are legacy arrays, which are not.
  - Harvest direct `drop` ids are the real unmigrated path.
- The rule is conservative, so it is harmless. **Fix:** drop npc_class from the "names it directly" list, and scope the profession caveat to legacy arrays.

### D4 (MINOR, R2): header offset rules imprecise
- Line 7 says "`main.cpp` base ≥ 778 → +4". Base 778–779 actually map to HEAD 781–782 (+3), and only base ≥ 780 is +4.
- Line 6 says "base 548-552 were rewritten". Base 548 (`#else`) is unchanged, and only 549–552 were rewritten.
- No individual citation is wrong. **Fix:** correct the two offset notes.

No R1, R3, R4, R5 or R6 violations. C2, C1 and C6 all have a seam, ordered steps and a validation. All proposals are load-time or tooling. Route (a)/(c) constant weights have no per-OMT cost.

## Residual risks U1–U11 (final-round judgement)

| U | Judgement |
|---|---|
| U1 C2 untested | **Acceptable.** Honestly UNVERIFIED, with a concrete mitigation (`check_mod.sh:19-20` is correct). P1 now shows `unload_data()` discards dda's deferred JSON silently after a syntax failure. Remaining gap: an exception thrown *inside* `finalize_loaded_data()`, which P1 did not exercise. |
| U2 route (b) timing | Acceptable. Route (a) is primary, and the citation is correct. |
| U3 faction append | Acceptable. `src/faction.cpp:52-56` `emplace_back` is confirmed. The mitigation (new ids only) is sound. |
| U4 update_mapgen | Acceptable (new ids only). |
| U5 mission leak | Acceptable. The mitigation is a concrete grep. |
| U6 wall-time costs | Acceptable if the metric is **user** time. Wall time is too noisy for a 5% threshold (see D2). |
| U7 polib | Acceptable (needs user approval). |
| U8 tiles headless | Acceptable. |
| U9 C++-constructed items | Acceptable, but scope it per D3. |
| U10 relative year | Acceptable. `src/calendar.cpp:836` is confirmed. |
| U11 C6 merge conflicts | Acceptable. Both hunks are small, and the dda re-check is the regression test. |

No U item contains a false assertion.

## Missed topics

1. Multi-mod `--check-mods` exit code (D1, P1).
2. The only `deferred_json` holders in the tree are `generic_factory<T>::deferred` and the file-static in `recipe_dictionary.cpp:80`. This narrows U1's "holders outside the reset list" to factories whose `reset()` is not called from `unload_data()`, which is auditable by grep. P1 showed none left for the dda content set.

## Live mod audit (`data/mods/saigon_2000s` at HEAD `268f5d9439`), for Part B review

| Rule (report) | Status |
|---|---|
| `"type":"ITEM"` + `subtypes` | OK. All 19 items have `subtypes:["COMESTIBLE"]`. The 4 copy-from items (`sgn_ca_phe_sua_da`←`coffee`, `sgn_tra_da`←`tea`, `sgn_ruou_de`←`moonshine`, `sgn_bia_hoi`←`beer`) restate `subtypes`. |
| `sgn_` prefixes, new ids | OK: items, professions, scenario, start_locations, EOC `SGN_EOC_intro`, snippet categories. The `<male_full_name>`/`<female_full_name>`/`<given_name>` overrides are the documented hunvre idiom. |
| No blacklist/migration of §3.1 ids | OK. There are no `ITEM_BLACKLIST`/`MIGRATION` objects yet. |
| No new npc | n/a (none yet). |
| Profession items migratable | OK. All 12 professions use the item-group object form. The 0 referenced ids are MIGRATION sources, and all are defined. |
| SEASON_LENGTH not set | OK. |
| `check_mod.sh saigon_2000s` | OK (P2, at `25bb166b5b`, before the B5b drinks commit). |
| **`conflicts` = every total_conversion + region mods (§5.1)** | **VIOLATION (L1).** `modinfo.json` omits `xedra_evolved_innawoods` (`data/mods/XedraWood/modinfo.json`, `category: total_conversion`). It lists `no_hope` (a content mod) and `defense_mode` (an obsolete TC), which is harmless. Add `xedra_evolved_innawoods`. |
| B10a whitelists before B2 (§8.2 order) | Deviation, not a violation. The scenario and professions landed before the `SCENARIO_BLACKLIST`/`profession_blacklist` whitelists. The ledger schedules B10 later. Part B should confirm that this ordering is intended. |

## Required changes (non-blocking; carry into TDD)

1. [ ] D1: qualify R2/§0.5/§6.2. In C2, `failed` must be function-scoped. Add the P1 two-mod case to the C2 validation.
2. [ ] D2: fix §7 line 537 and §6.2 line 499 (user-time metric).
3. [ ] D3: rescope the npc_class/profession caveat.
4. [ ] D4: fix the header offset notes.
5. [ ] L1: add `xedra_evolved_innawoods` to `saigon_2000s` `conflicts`.

## Final disposition for TDD

Domain 4 is **accepted (PASS)**. Carry the following into the TDD risk register:

| ID | Risk | Severity | Owner / mitigation | Test |
|---|---|---|---|---|
| RR-D4-1 | `--check-mods` load errors: rc 134 abort when the failing mod is last, **rc 0 when not** (P1). ~2.2k spurious ERRORs. | High (gate integrity) | Always gate via `tools/saigon/check_mod.sh` (greps `Error loading data`). Check one mod per invocation. Land C2 (function-scoped `failed`, `unload_data()` in the catch, return false). | `sgn_syntax`/`sgn_badtype` alone → rc 1, no `libc++abi`. The P1 pair → rc 1. `check_mod.sh dda` → OK. |
| RR-D4-2 | C6 hunks lost on upstream merge (U11, R16) | Medium | Keep `game_ui::init_ui` test-mode branch + `initialize_interface` TILES guard | `check_mod.sh dda` after every merge |
| RR-D4-3 | Residual dda traffic ~0.1% per road/bridge OMT (R1) | Low | Route (a) on the 6 road + 4 bridge om_terrains, and route (c) on the 8 nested ids, at weight 1,000,000. Route (d) for `parkinglot`/`crashed_helicopters`. C1 only if exact removal is needed. | Script: every one of the 8 ids and 10 om_terrains has a Saigon definition. Sample-generate several OMTs. |
| RR-D4-4 | Vehicle prototype/group shared appending namespace (R8) | Medium | `sgn_veh_*` / `sgn_vg_*` | CI grep: no `vehicle_group` id equals any `vehicle` id |
| RR-D4-5 | MIGRATION: single-hop, recipe deletion, turret hiding, unmigrated harvest drops and legacy profession arrays (R14, U9) | Medium | Migrate directly to the final target. Never migrate §3.1 ids or turret guns. Patch harvest `drop` and legacy-array refs. | Lint: no MIGRATION source ∈ §3.1 list or turret base guns. No MIGRATION target is itself a migration source. |
| RR-D4-6 | Whitelist bypasses: mission/EOC specials, trailheads, forced placements (R15, U5) | Medium | Own trailheads, `highways: null`, grep `om_special` in reachable dda NPC/mission data | Several-seed world-gen check |
| RR-D4-7 | Singleton blacklists vs other TCs; `conflicts` not enforced by `--check-mods`/`cata_test` (R4) | Low | Complete the `conflicts` list (**L1: add `xedra_evolved_innawoods`**) | Script: `conflicts` ⊇ all `total_conversion` ids |
| RR-D4-7b | ITEM copy-from slot patches without `subtypes` (§5 row 9) | Low | Restate `subtypes` | `check_mod.sh` (unvisited-member error) |
| RR-D4-8 | Load-time cost growth (U6) | Low | Per-unit comparison of `check_mod.sh` **user** CPU time against the dda baseline (~58 s), with a 5% threshold | Recorded in the ledger per unit |
| RR-D4-9 | `SEASON_LENGTH`/`ETERNAL_SEASON` never set in the mod (R9) | Low | Rule | Grep lint |
| RR-D4-10 | Translation extraction needs `polib`; `-r` file is appended to (U7) | Low | Scratch `-r` only, after user-approved `pip install polib` | Dry run on the scratch pot |
| RR-D4-11 | C2 path when an exception is thrown inside `finalize_loaded_data()` (U1 remainder) | Low | Part of C2 validation | Scratch mod that throws during finalize, not during parse |
