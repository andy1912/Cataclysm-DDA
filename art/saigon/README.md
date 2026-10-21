# Saigon sprite sources

Three ways to make a Saigon sprite. In priority order, the first one that exists for an id wins:

1. **Hand-drawn:** `tiles/` holds one PNG per game id, named `<id>.png`, at the size of the original sprite (20×20 items, 32×32 terrain and furniture, 32×64 tall furniture, 32×36 worn overlays, 32×48 monsters). Any sub-folders are fine. `overmap16/` holds 16×16 overmap icons.
2. **Code-drawn:** each program in `drawn/` draws sprites with `tools/saigon/art/draw.py`. `python3 tools/saigon/art/draw_sprites.py` writes them to `generated/`, which is committed so changes show up in review.
3. **Derived:** `derive_recipes.json` and `derive_overmap_recipes.json` hold recolours of the original UltimateCataclysm and Larwick art, applied by `python3 tools/saigon/art/derive_sprites.py`.

Then run `python3 tools/saigon/art/build_sprites.py` to pack 1 and 2, and `python3 tools/saigon/art/validate_tileset.py` to check the result. `python3 tools/saigon/art/contact_sheet.py OUT.png <id> ...` shows the original next to the Saigon version.

`../examples/` holds the first code-generated placeholders. Licence: code-drawn and derived sprites are distributed under CC-BY-SA 3.0, like the UltimateCataclysm art they sit beside. Original art copied into a code-drawn sprite (the grass under trees and shrubs) is named in that program's docstring. See `doc/saigon/art/UPDATING_SPRITES.md` for the full workflow.
