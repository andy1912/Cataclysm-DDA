# How the game draws the Saigon mod, and how to update its sprites

## 1. How a sprite is chosen today (re-evaluated against the engine)
For every thing on screen, the tiles renderer looks up a **tile id** in the loaded tileset(s):

1. **Season variant first.** If `<id>_season_<season>` exists it wins (`src/cata_tiles.cpp:378-396`). The Saigon scenario starts in CDDA **winter**, which is December, so any `_season_winter` art in the base tileset (bare or snowy trees, brown grass) shows unless we override it.
2. **The id itself.** Terrain, furniture, items, monsters and fields use their game id. Vehicle parts use **`vp_<part id>`** (`src/cata_tiles.cpp:2096`). Clothing drawn on the character uses `overlay_male_worn_<item id>` / `overlay_female_worn_<item id>`, then the generic `overlay_worn_<item id>`; held items use `overlay_wielded_<item id>` the same way (`src/cata_tiles.cpp:2135-2175`).
3. **`looks_like` chain.** If there's no sprite, the engine follows `looks_like` and copy-from (`find_tile_looks_like`, `src/cata_tiles.cpp:1975-2040`). Every Saigon id has one. For example, `sgn_non_la` draws as the dda straw hat, `sgn_banh_mi_thit` as a sandwich, and the shophouse overmap tile as a house.
4. **`unknown`** sprite, then the ASCII symbol and colour from the JSON.

**Where tiles come from**
- **Base tileset.** This repo does *not* contain one; `gfx/` only has ASCII, overmap and test packs. Community tilesets come from I-am-Erk/CDDA-Tilesets. Our targets:
  - `UltimateCataclysm`: 32×32 top-down, id verified.
  - `Ultica_iso`: the same art family in isometric, for renderer phase R3.
  - `Larwick Overmap`: overmap icons, 16×16.
- **Mod tileset.** `data/mods/saigon_2000s/gfx/mod_tileset.json` and its sheets. Mod tilesets load **after** the base, and only when the base's id is in their `compatibility` list (`src/tileset_loader.cpp:419-427`).
- **Same-id overrides.** `create_tile_type` overwrites existing ids (`src/cata_tiles.cpp:366-368`). So the mod can **restyle dda sprites too**, such as `t_sidewalk` or `f_fridge`, without forking the base tileset.
- **Offsets come from the declaring sheet.** A tile is drawn with the sprite offset of the `tiles-new` sheet it is *declared under* (`tileset_loader.cpp` `parse_atlases`), while sprite indices are global. So an entry must sit under the sheet of its own sprite size. The packers do this, and `validate_tileset.py` fails on any mismatch. Until G17 they didn't, and 427 entries were drawn misplaced.
- **Rotation:** a tile only turns with its vehicle, or with `rotates_to`, when it is `multitile` or says `"rotates": true`, because `rotates` defaults to `multitile`. Vehicle-part sprites must set it.
- **Overmap icons** come from the separate overmap tileset option (`OVERMAP_TILES`, `src/options.cpp:2580`). That's why the packer writes a second mod tileset for `Larwick Overmap`.

**Derived Saigon sprites (G6).** `tools/saigon/art/derive_sprites.py` makes Saigon sprites by applying recorded edits from `art/saigon/derive_recipes.json` to the original UltimateCataclysm art. That keeps the original style, and the licence is CC-BY-SA with per-sprite provenance in `art/saigon/SOURCES_DERIVED.md`. It writes `data/mods/saigon_2000s/gfx/derived_*.png` plus `derived_tileset.json`, and `doc/saigon/art/derived_preview.png` shows before and after. Current recipes:
- **Tropical seasons:** all 263 winter and autumn variants use summer art, so there's no snow or bare trees in December.
- **Pastel stucco walls**, **teal rolling shutters**, a **red-lacquer ancestor altar**, **red plastic stools** and a **stainless rooftop tank**.
- **Street and interiors:** warm red-grey sidewalk tiles, cream ceramic floor tiles, green-painted doors and window grilles.
- **Saigon outfit:** the nón lá (pale palm leaf), red nón bảo hiểm, blue bat-wing poncho and foam dép tổ ong, each as an item icon plus `overlay_male_worn_*` and `overlay_female_worn_*`. The shapes still come from the originals; a conical nón lá needs hand art.
- **Zombies:** a khaki ward-police zombie, the fevered dead in a pale gown, a market zombie with an orange apron, and a helmeted xe ôm zombie.

The `overmap` set (`derive_sprites.py overmap`, recipes in `art/saigon/derive_overmap_recipes.json`) gives each Saigon building type a distinct map colour: pastel nhà ống, terracotta hẻm, orange chợ, red chùa and white chung cư, plus their roofs. Hand-drawn PNGs always win over derived ones. Validate both with `python3 tools/saigon/art/validate_tileset.py`, which applies the loader's index and capacity rules (mod tilesets only load with a world, so a main-menu launch can't test them).

**What a Saigon world looked like before G6 in tiles mode:** American dda art for walls, furniture, cars and trees, `looks_like` stand-ins for Saigon ids, and winter tree variants in December. Current status is in [`SPRITE_REVISION_SUMMARY.md`](SPRITE_REVISION_SUMMARY.md).

**Text in graphics.** Names and descriptions are translated through gettext, not drawn into sprites, so localization of text is separate from art. The tiles UI font chain is Terminus → Unifont (`data/fontdata.json`). Unifont covers Vietnamese diacritics, but mixed glyph styles are possible; check this in the tiles build.

## 2. How to update a sprite (works today, no extra installs)
1. **Pick what to draw.** [`SPRITE_REVISION_SUMMARY.md`](SPRITE_REVISION_SUMMARY.md) lists what still needs Saigon art and what deliberately keeps the original art. `python3 tools/saigon/art_coverage.py --list T1` lists on-screen ids without Saigon art.
2. **Choose a route.** The first route that exists for an id wins:
   - **Hand-drawn PNG** under `art/saigon/tiles/`, at the size of the original sprite: 20×20 items, 32×32 terrain and furniture, 32×64 tall furniture, 32×36 worn overlays, 32×48 monsters, 64×64 or 96×96 trees. Any pixel editor works, such as Aseprite, LibreSprite or Piskel. Use a transparent background and save non-interlaced.
   - **Code-drawn:** a Python program in `art/saigon/drawn/` that uses `tools/saigon/art/draw.py` (shapes, soft outlines, foliage, shadows). `python3 tools/saigon/art/draw_sprites.py` writes the PNGs to `art/saigon/generated/`. Examples: `food.py` (phở, bánh mì…), `flora.py` (palms, bàng, bồ đề…), `home.py` (gas stove, squat toilet).
   - **Derived:** a recipe in `art/saigon/derive_recipes.json` that recolours or flattens original art (stucco walls, drinks, the salon sofa…). Run `python3 tools/saigon/art/derive_sprites.py`.
3. **Name it after the tile id**, for example `sgn_non_la.png`, `f_oven.png` or `t_sgn_tree_dua.png`:
   - Vehicle parts use `vp_<part id>`.
   - Seasonal art uses `<id>_season_winter`.
   - Worn clothing uses `overlay_male_worn_<id>` and `overlay_female_worn_<id>`.
   - Overmap icons are 16×16 PNGs under `art/saigon/overmap16/`, named after the oter id.
4. **Optional sidecar** `<same name>.json` holds extra tile keys. In code-drawn programs, pass them as keywords to `@sprite(...)`. `"@name"` refers to another sprite in the same source root, and a file name containing `__` marks a helper sprite with no tile entry of its own. Examples:
   - trees use `{"bg": "@sgn__ground96"}`;
   - a rotating sprite uses `{"rotates": true, "fg": ["@f_x", "@f_x__e", "@f_x__s", "@f_x__w"]}`;
   - connecting walls need the multitile keys from `doc/TILESET.md`.
5. **Build:** `python3 tools/saigon/art/build_sprites.py` packs hand-drawn and code-drawn art into `data/mods/saigon_2000s/gfx/` (`saigon_<w>x<h>.png` + `mod_tileset.json`). The tool is pure Python, with no Pillow needed.
6. **Review and validate:** `python3 tools/saigon/art/contact_sheet.py OUT.png <id> ...` shows the original next to the Saigon version, or use `--files a.png b.png`. Then run `python3 tools/saigon/art/validate_tileset.py` and `tools/saigon/check_mod.sh`.
7. **See it in game:** run `./play_saigon.sh` and create a **new world**, because mod tilesets load with a world.
8. **Commit** the program or PNG, the generated PNGs and the packed sheets. Original art copied into a sprite, such as the grass under trees, is named in the program's docstring (`STYLE_GUIDE.md` §7).

**3D route.** When Blender is available, `tools/saigon/art/render_sprites.py` renders into the same `art/saigon/tiles/` folder, and step 5 onward is unchanged. The isometric set (R3) will get its own `tiles_iso/` folder and a `Ultica_iso` compatibility entry.

## 3. What to make next
See [`SPRITE_PLAN.md`](SPRITE_PLAN.md). The T1 restyle list that used to be here is done (G6–G16).
