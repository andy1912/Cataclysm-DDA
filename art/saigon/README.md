# Saigon sprite sources

Drop one PNG per game id here, named `<id>.png`, then run `python3 tools/saigon/art/build_sprites.py`.
- `tiles32/`: 32×32 sprites for the UltimateCataclysm base tileset. Any sub-folders are fine.
- `overmap16/`: 16×16 overmap icons for the Larwick Overmap tileset.
- `_placeholder/` folders hold code-generated stand-ins that prove the pipeline works. Replace them with real art.

See `doc/saigon/art/UPDATING_SPRITES.md` for the full workflow.
