# How the game draws the Saigon mod, and how to update its sprites

## 1. How a sprite is chosen today (re-evaluated against the engine)
For every thing on screen, the tiles renderer looks up a **tile id** in the loaded tileset(s):

1. **Season variant first.** If `<id>_season_<season>` exists it wins (`src/cata_tiles.cpp:378-396`). The Saigon scenario starts in CDDA **winter**, which is December, so any `_season_winter` art in the base tileset (bare or snowy trees, brown grass) shows unless we override it.
2. **The id itself.** Terrain, furniture, items, monsters and fields use their game id. Vehicle parts use **`vp_<part id>`** (`src/cata_tiles.cpp:2096`). Clothing drawn on the character uses `overlay_worn_<item id>`, and held items use `overlay_wielded_<item id>`.
3. **`looks_like` chain.** If there's no sprite, the engine follows `looks_like` and copy-from (`find_tile_looks_like`, `src/cata_tiles.cpp:1975-2040`). Every Saigon id has one. For example, `sgn_non_la` draws as the dda straw hat, `sgn_banh_mi_thit` as a sandwich, and the shophouse overmap tile as a house.
4. **`unknown`** sprite, then the ASCII symbol and colour from the JSON.

**Where tiles come from**
- **Base tileset.** This repo does *not* contain one; `gfx/` only has ASCII, overmap and test packs. Community tilesets come from I-am-Erk/CDDA-Tilesets. Our targets:
  - `UltimateCataclysm`: 32×32 top-down, id verified.
  - `Ultica_iso`: the same art family in isometric, for renderer phase R3.
  - `Larwick Overmap`: overmap icons, 16×16.
- **Mod tileset.** `data/mods/saigon_2000s/gfx/mod_tileset.json` and its sheets. Mod tilesets load **after** the base, and only when the base's id is in their `compatibility` list (`src/tileset_loader.cpp:419-427`).
- **Same-id overrides.** `create_tile_type` overwrites existing ids (`src/cata_tiles.cpp:366-368`). So the mod can **restyle dda sprites too**, such as `t_sidewalk` or `f_fridge`, without forking the base tileset.
- **Overmap icons** come from the separate overmap tileset option (`OVERMAP_TILES`, `src/options.cpp:2580`). That's why the packer writes a second mod tileset for `Larwick Overmap`.

**Derived Saigon sprites (G6).** `tools/saigon/art/derive_sprites.py` makes Saigon sprites by applying recorded edits from `art/saigon/derive_recipes.json` to the original UltimateCataclysm art. That keeps the original style, and the licence is CC-BY-SA with per-sprite provenance in `art/saigon/SOURCES_DERIVED.md`. It writes `data/mods/saigon_2000s/gfx/derived_*.png` plus `derived_tileset.json`, and `doc/saigon/art/derived_preview.png` shows before and after. Current recipes:
- **Tropical seasons:** all 263 winter and autumn variants use summer art, so there's no snow or bare trees in December.
- **Pastel stucco walls**, **teal rolling shutters**, a **red-lacquer ancestor altar**, **red plastic stools** and a **stainless rooftop tank**.
- **Zombies:** a khaki ward-police zombie, the fevered dead in a pale gown, a market zombie with an orange apron, and a helmeted xe ôm zombie.

The `overmap` set (`derive_sprites.py overmap`, recipes in `art/saigon/derive_overmap_recipes.json`) gives each Saigon building type a distinct map colour: pastel nhà ống, terracotta hẻm, orange chợ, red chùa and white chung cư, plus their roofs. Hand-drawn PNGs always win over derived ones. Validate both with `python3 tools/saigon/art/validate_tileset.py`, which applies the loader's index and capacity rules (mod tilesets only load with a world, so a main-menu launch can't test them).

**What a Saigon world looked like before G6 in tiles mode**
- **No base tileset installed:** ASCII-style tiles.
- **With UltimateCataclysm:** American-styled dda art for walls, furniture, cars and trees, `looks_like` stand-ins for Saigon ids, and winter tree variants in December.
- **Saigon sprites so far:** three code-generated placeholders (nón lá, ancestor altar, shophouse overmap icon) that prove the pipeline.

**Text in graphics.** Names and descriptions are translated through gettext, not drawn into sprites, so localization of text is separate from art. The tiles UI font chain is Terminus → Unifont (`data/fontdata.json`). Unifont covers Vietnamese diacritics, but mixed glyph styles are possible; check this in the tiles build.

## 2. How to update a sprite (works today, no extra installs)
1. **Pick what to draw.** Run `python3 tools/saigon/art_coverage.py --list T1` to list every on-screen id without Saigon art. Do T1 first: about 193 ids.
2. **Draw a 32×32 PNG** following `STYLE_GUIDE.md`. Any pixel editor works, such as Aseprite, LibreSprite or Piskel. Use a transparent background and save non-interlaced.
3. **Name it after the tile id** and put it anywhere under `art/saigon/tiles32/`:
   - Saigon ids: `sgn_non_la.png`, `f_sgn_ban_tho.png`, …
   - Restyled dda ids: `t_sidewalk.png`, `f_counter.png`, `mon_zombie.png`, …
   - Vehicle parts: `vp_sgn_engine_110cc.png`, `vp_wheel_motorbike.png`, …
   - Seasonal override: `t_region_tree_season_winter.png`.
   - Worn on the character: `overlay_worn_sgn_non_la.png`.
   - Overmap icons: 16×16 PNGs under `art/saigon/overmap16/`, named after the oter id (`sgn_cho_nw.png`, …).
4. **Optional sidecar** `<same name>.json` holds extra tile keys copied into the tile entry, for example `{"rotates": true}`, `{"bg": "<id>"}`, or the multitile keys for connecting walls (see `doc/TILESET.md`).
5. **Build:** `python3 tools/saigon/art/build_sprites.py` for hand-drawn art, and `python3 tools/saigon/art/derive_sprites.py` for derived art. Add a rule to `derive_recipes.json` to restyle an original sprite by recolouring it. It packs everything into `data/mods/saigon_2000s/gfx/` (sheets plus `mod_tileset.json`). There are no dependencies: it uses a pure-Python PNG reader and writer, `tools/saigon/art/pngio.py`.
6. **Validate:** `tools/saigon/check_mod.sh` and `python3 tools/saigon/art_coverage.py`.
7. **See it in game.** Use the SDL3 tiles build (`cataclysm-tiles`, unit S0.3c) with `CATA_DISABLE_SPRITE_SHADERS=1`. Choose tileset **UltimateCataclysm** and overmap tileset **Larwick Overmap** in Options → Graphics, then start the Saigon scenario.
8. **Commit** the source PNGs and the generated sheet, with a provenance line per sprite (`STYLE_GUIDE.md` §7).

**3D route.** When Blender is available, `tools/saigon/art/render_sprites.py` renders into the same `art/saigon/tiles32/` folders, and step 5 onward is unchanged. The isometric set (R3) will get its own `tiles_iso/` folder and a `Ultica_iso` compatibility entry.

## 3. What to restyle first: T1, in visual-impact order
1. **Street and walls (terrain):** `t_sidewalk` (square tiles), `t_pavement`, `t_pavement_y`, `t_concrete`, `t_brick_wall` (pastel stucco), `t_rdoor_c` (rolling shutter), `t_window_bars`, `t_concrete_roof`, `t_railing`, `t_door_c`, `t_stairs_up/down`, `t_thconc_floor` (patterned tiles).
2. **Vegetation:** `t_region_tree`, `t_region_grass`, `t_region_groundcover_urban`, `t_region_shrub_decorative` and their `_season_winter` variants. Also needs content: a tropical region `terrain_furniture` mapping (palms, banana, bougainvillea), owned by B8a.
3. **Street furniture:** `f_street_light`, `f_traffic_light`, `f_sign_stop` (Vietnamese road signs), `f_trashcan`, `f_bench`, `f_bike_rack`.
4. **Interiors:** `f_sgn_ban_tho`, `f_counter`, `f_table`, `f_stool` (red plastic), `f_bed`, `f_fridge`, `f_standing_tank` (stainless rooftop tank), `f_oven` (gas burner), `f_rack`, `f_sofa`, `f_toilet` (squat toilet), `f_sink`.
5. **Monsters:** `sgn_mon_zombie_xe_om`, `sgn_mon_zombie_vendor`, `sgn_mon_zombie_cong_an`, `sgn_mon_zombie_sot`, `mon_zombie`, `mon_zombie_fat`.
6. **Vehicles:** `vp_sgn_engine_110cc`, `vp_sgn_pillion`, `vp_wheel_motorbike`, `vp_basketsm`, `vp_xlframe`, … These are the 37 underbone, ba gác, xích lô and boat parts.
7. **Starting kit and overlays:** `sgn_non_la`, `sgn_non_bao_hiem`, `sgn_ao_mua_canh_doi`, `sgn_dep_to_ong` and their `overlay_worn_*` versions.
8. **Overmap (16×16):** the 24 `sgn_*` overmap terrains.
