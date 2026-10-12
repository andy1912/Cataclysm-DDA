# Peer review: Saigon graphics track (G1–G16)

**Date:** 2026-10-03. **Reviewed at:** `67d072f978`. **Fixes:** G17.
**Scope:**
- every graphics tool in `tools/saigon/art/`: packer, deriver, drawer, validator, contact sheet, status list and scene renderer;
- every sprite they produce;
- the content added for the art: `region/flora.json`, the new vehicle parts, the pagoda palette;
- the art documentation.

The B-unit gameplay content has its own reviews (`peer_review_b4b_b9b.md`, and the `B*.R` units in `PROGRESS.md`).

## Method
1. **Engine source, line by line, against every assumption the tools make:**
   - `tileset_loader.cpp`: `parse_atlases`, the `rotates` default, mod `sprite_id_offset`;
   - `cata_tiles.cpp`: lookup order, multitile subtiles, rotation, overlay ids, vehicle-part ids.
2. **Validator:** rerun after adding the rules found in step 1.
3. **Scene render:** `render_scene.py` was changed to follow the engine exactly (declaring-sheet offsets, rotation defaults), then rerun on a real generated block (`[saigon_scene]`).
4. **Statistics:** sprite size measured against 300 random UltimateCataclysm item sprites.
5. **Mod and tests:** `check_mod.sh`, `[saigon]` tests, and a grep of the docs for stale claims.

## Verdict
The pipeline design holds up: three routes (hand-drawn, code-drawn, derived), reproducible sources, and a review render. The content additions are correct.

The review did find **one critical bug**. It had been in the game since G6 and affected 427 tile entries. The validator and the renderer both missed it because they shared the same wrong assumption. It is fixed and now guarded by a validator rule. Two high-severity sprite bugs are also fixed. One style problem, item icons at 3× UltimateCataclysm's size, is planned rather than fixed: it needs a redraw.

## Findings
| ID | Severity | Area | Finding | Evidence | Status |
|---|---|---|---|---|---|
| R0 | **Blocker** | Packers | *(found in QA after G17; the user reported that no world could be loaded)* Every mod tileset `"file"` was written relative to the JSON file (`derived_0_32x32.png`), but the engine opens it relative to the **mod root** (`tileset_loader.cpp`: `tileset_root = mts.get_base_path()`, the mod directory). Loading any world with the mod, whether a new character or a saved one, aborted with `Could not load image "data/mods/saigon_2000s/derived_0_32x32.png"`. This was broken since G6. `--check-mods` never loads tilesets, and the validator joined paths the same wrong way, so nothing caught it. | User's `config/debug.log`; reproduced and fixed in the real `cataclysm-tiles` | **Fixed (G17b).** Packers write `gfx/<sheet>`; every tool resolves sheets through `sheet_path()` (mod root); `validate_tileset.py` resolves like the engine; `check_mod.sh` now runs the validator |
| R1 | **Critical** | Packers | Every tile entry was declared under the **first** sheet of its mod tileset. The engine applies the offset of the declaring sheet (`parse_atlases` sets `sprite_offset` per `tiles-new` entry and stamps it on the tiles parsed there); indices are global, which is why it loaded at all. Effects: the 263 tropical-season trees, tall furniture, zombies, 20×20 icons and worn overlays from `derive_sprites.py` lost their offsets (trees 32 px left and 64 px down of their spot), and everything from `build_sprites.py` took the 20×20 sheet's (+6, 0), which broke every G12 tree. | Validator rule added in G17: 427 failures on the committed tilesets. Engine-faithful render: the pagoda bồ đề drawn as black squares | **Fixed (G17).** Entries are declared under the sheet of their own size, an entry mixing sizes fails the build, and `validate_tileset.py` checks declaring-sheet geometry |
| R2 | High | Sprites | The 7 code-drawn vehicle parts had neither `multitile` nor `"rotates": true`. `rotates` defaults to `multitile`, and `draw_from_id_string` forces `rota = 0` otherwise, so they stayed upright while the vehicle turned. | `tileset_loader.cpp` (`t_rota = get_bool("rotates", t_multi)`), `cata_tiles.cpp` (`if !display_tile.rotates → rota = 0`) | **Fixed (G17):** `rotates=True` on every `vp_` sprite |
| R3 | High | Sprites | `t_sgn_shrub_hoa_giay` is terrain with a transparent background and no `bg`, so it drew on black. UltimateCataclysm shrubs carry a grass `bg`. | Engine-faithful render | **Fixed (G17):** `sgn__ground32` (UltimateCataclysm grass) as `bg` |
| R4 | High | Tooling | The scene renderer took offsets from the sprite's sheet and rotated any vehicle part, so it agreed with the packers' wrong assumption and hid R1 and R2. | Code review | **Fixed (G17):** follows `parse_atlases` and the `rotates` default |
| R5 | High | Art style | Code-drawn 20×20 item icons are about 3× the area of UltimateCataclysm's: median bounding box 17×16 vs 11×9, about 200 vs 60 opaque pixels. They read as oversized next to dda items on the same floor. Books and boxes are the worst. | Statistics over 300 random `small.png` sprites | **Open → G18** (redraw to the UltimateCataclysm budget, plus a size gate in the validator) |
| R6 | Medium | Content | `t_sgn_tree_chuoi` and `t_sgn_tree_du_du` keep the `TREE` flag and the inherited `roof: t_treetop`. They can be chopped into logs, and a treetop is placed above a banana plant. | `region/flora.json` | **Open → G19** |
| R7 | Medium | Content | The forest-edge pseudo terrains still resolve to New England species: `t_region_shrub_forest*`, `t_region_shrub_plains`, `f_region_flower/weed/forest*`, and `t_tree_young` in `trees_forest`. City blocks are fine. | `regional_map_settings.json` vs `flora.json` | **Open → G19** |
| R8 | Medium | Coverage | 4 Saigon-referenced dda items have no sprite anywhere (`hot_sauce`, `noodles_fast`, `pickle`, `ring_wedding`). 350 deep-loot items are a gap in the base tileset. | `revision_list.py` + grep of mod JSON | **Open → G18** (the 4); the 350 are tracked, not planned |
| R9 | Medium | Verification | Nothing has been seen in the real game window. The validator and renderer model the loader and drawing, but not atlas baking, lighting, shaders, or the actual load path for mod tilesets. | — | **Open:** checklist in `SPRITE_PLAN.md` §0, for the next manual play session |
| R10 | Low | Docs | `UPDATING_SPRITES.md` had the wrong overlay naming, a stale priority list and the "3 placeholders" claim. `PIPELINE.md` and the `TDD.md` status table were stale. No licence statement covered code-drawn art. | grep | **Fixed (G17)** |
| R11 | Low | Tooling | Everything is pure Python. `base_sprite()` decodes the large `normal.png` (about 1 min per program run), `derive_sprites.py` takes about 1 min, and a full-block render about 1.5 min. | Timings | Open: cache decoded sheets (`G-tools` in the plan) |
| R12 | Low | Tooling | `validate_tileset.py` isn't wired into `check_mod.sh`, so a tileset regression could be committed without notice. | — | Open → G18 |
| R13 | Low | Renderer | Not modelled: lighting, fields, monsters, z above 0, item `_var_` variants, vehicle open/broken subtiles. The season is fixed to winter, which matches the scenario's `start_of_game`. | Docstring | Accepted |

## QA (G17b), 2026-10-03
| Check | Result |
|---|---|
| Real game load: `cataclysm-tiles --world` on a copy of the user's Saigon world in a separate QA user folder | Gets past the step that crashed: "Loaded tileset: UltimateCataclysm" (566 MB atlas, Metal) and "Loaded tileset: Larwick Overmap", then the character is drawn in the map. Clean shutdown, no unexpected errors |
| New-game path: test `saigon_new_game_start_locations` runs the `game::start_game` steps for all 3 Saigon start locations | Pass: a site is found, the map prepared, and the player placed on a passable, roofed tile in a `sgn_` building |
| `[saigon]` tests | 13 test cases, 6,860 assertions, all pass |
| `check_mod.sh` (now includes `validate_tileset.py`) | OK, 0 tileset problems |
| Remaining log lines (expected) | "Mod tileset … is not compatible with …": the engine checks every mod tileset against the main, overmap and portrait tilesets and logs each one it skips. "No 'unknown' tile" comes from the repo's `Test_Portrait_Pack`. Both are harmless and existed before |
| Not verified | What the game window looks like: macOS doesn't allow this terminal to capture the screen. Check visually: start a new character and look at a shophouse, a tree, a motorbike and an item on the floor |

## What held up
- **Lookup order:** the season variant first, then the id, then `looks_like`, then mod overrides. All match `cata_tiles.cpp`, and the tropical-season trick works because the scenario really starts in winter (`scenarios.json`: `start_of_game` winter).
- **Multitile subtile selection and connection bits** (S=1, E=2, W=4, N=8) match `get_rotation_and_subtile`, `offsets` and `map::get_known_connections`.
- **Overlay ids** (`overlay_{male,female}_worn_<id>` then `overlay_worn_<id>`) match `cata_tiles.cpp:2135-2175`.
- **Index and capacity rules:** a global `sprite_id_offset` per mod tileset and full-grid sheet capacity match the loader.
- **Content checks:** `check_mod.sh` reports OK, the 12 `[saigon]` test cases pass, and the pagoda flora assertion holds.
- **The art reads as Saigon in context:** stucco fronts, teal shutters, sidewalk, traffic, pagoda, chợ (`scene_preview*.png`).

## Residual risks
- **Real-game check:** until someone loads a new world in `cataclysm-tiles` (R9), the offsets fixed by R1 are only verified by the model of the loader. The fix follows the engine source, but it is not an observation of the game itself.
- **Missing art for new content:** content added later without sprites will draw as fallbacks. `revision_list.py` lists it, and G18 makes `check_mod.sh` run the validator.
