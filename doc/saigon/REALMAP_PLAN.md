# Plan: a real-map Saigon (2004)

Goal: replace the procedural megacity with the real city layout. The Saigon River and its bends, the
canals, the real avenues, district by district, with every landmark at its real position, as the
city was in 2004.

## 1. What the engine already gives us

dda can load **pregenerated overmaps** instead of generating them:

- **The option.** The world option `OVERMAP_PREGENERATED_PATH` names a folder inside a mod
  (`src/overmap.cpp:931-955`). For overmap *(x, y)* the game reads `overmap_<x>_<y>.omap.gz`, a
  gzipped run-length list of overmap-terrain ids for one 180 × 180 layer (`overmap::unserialize_omap`,
  `src/savegame.cpp:886`).
- **What happens outside the data.** Overmaps with no file are filled with the
  `OUTSIDE_DEFINED_OMAP_OMT` terrain, then generated normally.
- **The model to copy.** dda's **MA mod** does exactly this for Massachusetts: 1,337 pregenerated
  overmaps (11 MB), built from a land-use database by a script (`data/mods/MA/MA_overmap.ps1`, `.sql`).
  A mod setting turns the option on (`game_balance.json`), and `"type": "city"` entries put real towns
  at real coordinates (`cities.json`).

So no new map engine is needed. What we need is **our own converter** and **two small engine
changes**:

| Gap | Fix |
|---|---|
| The loader reads one layer only (z = 0). Shophouses, landmarks and the tower have upper floors (z 1–10) and basements. | `unserialize_omap`: read every object in the file, one per z level (a ~15-line loop). Old single-layer files still load. |
| After loading, generation still runs rivers, lakes, forests, cities and megacity, which would overwrite the real layout. | A real-map region with those switched off: `overmap_river/lake/forest` false, `city_size` 0 (the city builder returns at once), `is_megacity` false. No C++ needed. |

## 2. Scale: true scale fits

One overmap tile is 24 m and one overmap is 180 tiles (≈ 4.3 km). The inner city is roughly 7 × 7 km:
Chợ Lớn to the river, District 4 to Phú Nhuận. That is **about 2 × 2 overmaps at true scale**.
The wider city adds Tân Sơn Nhất, Gò Vấp, Thủ Thiêm, Bình Thạnh and, in the north-east, Suối Tiên. That
is about 4 × 4 overmaps (≈ 17 km). Every landmark can sit at its real position, at real distances. All
figures here are approximate and will be measured from the data.

| Coverage option | Overmaps | Includes |
|---|---|---|
| **A. Inner city** | 2 × 2 | D1, D3, D4, D5, D10, Phú Nhuận, south Bình Thạnh; 16 of the 19 landmarks |
| **B. Greater city** (recommended) | 4 × 4 | also Tân Sơn Nhất, Gò Vấp, Thủ Thiêm, Bình Thạnh, D11 (Đầm Sen), Thủ Đức (Suối Tiên) |
| C. Whole province | ~8 × 10 | plus Củ Chi, Cần Giờ mangroves; mostly countryside |

Outside the covered area the game falls back to generated land: Mekong-delta countryside (rice
fields, canals, hamlets), not more city.

## 3. Where the layout comes from

| Option | Accuracy | Work | Notes |
|---|---|---|---|
| **OpenStreetMap** (recommended) | Street-level | a converter script | **Needs a download, which I will ask about first.** An Overpass query for the covered box (roads, waterways, land use, named places) is roughly 50–150 MB. The other route is Geofabrik's Vietnam extract, a few hundred MB. Licence: ODbL, which needs attribution ("© OpenStreetMap contributors"). Whether a coarse 24 m game grid is a "produced work" or a "derived database" decides if share-alike applies to the generated files. That is your call, maybe with advice. OSM shows today's city, so it needs the 2004 corrections in §5. |
| Hand-authored | Avenue-level | weeks of editing | Main roads, canals and district outlines traced from public maps. No data licence question, but much less accurate, and much slower to get right. |

## 4. How the converter works (`tools/saigon/realmap/`)

1. **Project.** Latitude/longitude to overmap tiles at 24 m per tile (local metric projection), with the
   origin chosen so District 1 sits mid-overmap.
2. **Water first.**
   - The Saigon River becomes `river` tiles with correct bank pieces.
   - The canals (Nhiêu Lộc–Thị Nghè, Tàu Hủ–Bến Nghé, Tân Hóa–Lò Gốm, Kênh Đôi) become `sgn_kenh` rows.
3. **Roads.**
   - Trunk, primary, secondary and tertiary streets, and named residential streets, become road tiles.
     The converter computes each tile's connections (`road_ns`, `road_nesw`…), bridges and bridgeheads.
   - The wide boulevards (Nguyễn Huệ, Lê Duẩn, Hai Bà Trưng, Trần Hưng Đạo) get a 2-tile-wide road
     variant.
   - Roundabouts (Quách Thị Trang at Bến Thành, Hồ Con Rùa, Cộng Hòa) become road junction pieces.
   - Alleys stay inside blocks: the hẻm mapgen already draws them within a tile.
4. **Blocks.** Every tile left between roads is a city block, filled by rules:
   - frontage tiles facing a road become nhà ống rows, rotated to face it;
   - interiors become hẻm blocks;
   - district character sets the mix. D1 is colonial and commercial, with more shops and offices. D3
     has villas, schools and churches. D5 (Chợ Lớn) has Hoa shophouses, temples and wholesale. D4 has
     the densest hẻm. Bình Thạnh has canal-side shacks.
5. **Places from the data.**

   | OSM tag | Becomes |
   |---|---|
   | `amenity=fuel` | cây xăng |
   | `amenity=marketplace` | chợ |
   | `amenity=place_of_worship` with religion buddhist / taoist / christian | chùa / temple / nhà thờ |
   | `school` | trường |
   | `hospital` | bệnh viện |
   | `police` | công an phường |
   | `shop=supermarket` | Co.op Mart |
   | `landuse=cemetery` | nghĩa trang |
   | parks | parks with sao trees |

   Each lands on the block tile nearest its real position, rotated to the nearest street.
6. **Landmarks at real coordinates.** Each of the 19 has an anchor point and a facing taken from the
   real building (Bến Thành's gate faces the roundabout; Đức Bà faces Đồng Khởi). They are placed as
   whole multi-tile buildings, and removed from the random pools in the real-map mod.
   With the user's image as the source (§8a), steps 2–6 read a class grid instead of OSM tags:
   `classify.py IMAGE POINTS.json OUT` fits the image onto real coordinates from its black reference
   marks (least squares, north-up fit preferred), samples every tile's footprint, lets thin linear
   classes (bridge, river, canal, roads, railway) win over area classes when they cover a quarter of the
   tile, and writes `OUT.grid.json` (one letter per tile, plus every landmark and place marker in tile
   coordinates) and `OUT.preview.png` (one pixel per tile). A full-size image takes a few minutes.
7. **Write** one `overmap_<x>_<y>.omap.gz` per overmap, every z level, plus a preview PNG through
   `render_overmap.py`, side by side with an OSM reference render.

## 5. Making it 2004, not today

OSM shows the city now. A small edits file (`tools/saigon/realmap/2004.json`) undoes what came after
2004. The candidates below are from memory, so **each one gets checked against a source before use**:

| Today | In 2004 |
|---|---|
| Võ Văn Kiệt boulevard along the Tàu Hủ canal (opened ~2010) | narrow canal-side streets and stilt-house slums over the water |
| Thủ Thiêm bridge (~2008), tunnel (~2011), the new urban area | marshes and villages reached by the Thủ Thiêm ferry |
| Phú Mỹ bridge (~2009) | no bridge |
| Nguyễn Huệ pedestrian street (~2015) | a boulevard with fountains and the Tết flower market |
| Bitexco tower (2010), Landmark 81 (2018), the metro line and stations | not there |
| The Nhiêu Lộc canal clean-up (~2003–2011) | still part-lined with shacks |

## 6. Delivery: a separate mod

**`saigon_2000s_realmap`** depends on `saigon_2000s` and contains:
- the pregenerated overmaps;
- the region switches from §1;
- the mod setting that turns on `OVERMAP_PREGENERATED_PATH`;
- `"type": "city"` entries naming the districts (Quận 1, Quận 3…);
- start locations at real places, for example a hẻm in Quận 3.

Players pick **real-map Saigon** or the **procedural megacity** when they create a world. The current
megacity stays as it is.

Generation also gets faster. Pregenerated overmaps skip the city builder, so the 5–17 s megacity pause
when reaching a new overmap goes away inside the covered area.

## 7. Units

| Unit | Work | Check |
|---|---|---|
| R0 | Decisions (§8). With your OK: download the OSM data for the covered box, add an attribution file. | — |
| R1 | Engine: multi-layer `.omap` loading; the real-map mod skeleton with region switches | test: a hand-written 3-layer test overmap loads with its upper floors; dda's MA mod still loads |
| R2 | Converter v1: water, roads, bridges, roundabouts | preview against the OSM render; road network connected (BFS); no road ends in a wall |
| R3 | Blocks: frontage rows facing streets, hẻm interiors, district rules | every building faces a road or hẻm; density per district within targets |
| R4 | Places from data (fuel, markets, temples, schools, hospitals, police, supermarkets, cemeteries, parks) | counts compared with the data; render review |
| R5 | Landmarks at real coordinates and facing | each landmark within ~1 tile of its real anchor; its door on its real street |
| R6 | 2004 corrections, including Thủ Thiêm marsh and ferry | each edit has a source, recorded in the file |
| R7 | Countryside outside the covered area (rice fields, canals, hamlets) | generated land looks like the delta, not the US |
| R8 | Start locations, district names, scenario option | new game starts in a real hẻm |
| R9 | QA: structure, connectivity and placement tests; generation time; a real-game load; a walk-through of the covered area | all green; a playtest by you |
| R10 | Docs: the map with a side-by-side reference, how to regenerate it, attribution | — |

Each unit is small and gets committed on its own. R1–R3 already give a playable real street plan.

## 8a. Second round of decisions (2026-10-05)

- **Names.** The world's map is chosen by scenario when the first character starts:
  - **"Vietmap"** is the current procedural megacity (the existing Sài Gòn scenario);
  - **"Saigon 2009"** is the real map.

  A world keeps the map its first game chose.
- **Year.** The real map shows **2009**, with the **Phú Mỹ bridge** (opened Sep 2009) and the Thủ Thiêm
  bridge (2008). The §5 corrections are re-cut for 2009. Still not there: the Võ Văn Kiệt boulevard (under
  construction), the Thủ Thiêm tunnel (2011), Bitexco (2010), Landmark 81 and the metro.
- **Source.** The user's **illustrated 2006–2009 map** (`tools/saigon/realmap/source/saigon_2009_illustrated.png`)
  is kept as the reference for 2009 features and district character. It is a poster, not to scale:
  measured scale runs from 3 to 15 m per pixel, and the airport is about 60° off. So its geometry is not
  traced. A Google Maps screenshot was also offered and is **not used** (its terms do not allow deriving
  map data). **The user is making a new, to-scale image to REALMAP_IMAGE_SPEC.md.**
- **Area.** 5 × 4 overmaps, so Đầm Sen and Suối Tiên both fit (REALMAP_IMAGE_SPEC.md §5).

## 8. Decisions (answered 2026-10-05)

| Question | Answer |
|---|---|
| Source of the layout | **A map image the user uploads.** The converter reads the image (colours for water, roads, parks, blocks) instead of OSM. Details are agreed before building (§9). |
| Coverage | **Greater city, 4 × 4 overmaps** (≈ 17 km) |
| Delivery | **A second map inside `saigon_2000s`, not a separate mod.** At world creation the player chooses the procedural megacity or the real map. Mechanism to be settled in R1: the engine's `OVERMAP_PREGENERATED_PATH` world option, pre-filled or offered as a choice, or a small option that switches the Saigon region to a real-map region. |
| Period | **Apply the 2004 corrections** (§5) |

## 9. What the converter needs from the map image

- **File:** the original, full-resolution file saved into the project, for example
  `tools/saigon/realmap/source/`. An image pasted into chat is shrunk before I see it, so it is not
  enough to measure from.
- **Resolution:** at least 1 pixel per 24 m over the covered area (≈ 720 px for 17 km). 2–4× that is
  better, so narrow roads and canals survive.
- **Georeference:** north up, plus a scale bar or the real distance between two marked points.
  Better still: 3–4 known points marked on the image (for example the Bến Thành gate, Đức Bà, the
  Independence Palace gate, Bến Nhà Rồng).
- **Colours:** a legend, or a style with flat distinct colours: water, major roads, minor streets,
  parks, cemeteries, built-up blocks. Labels make detection harder, so a no-labels version helps if the
  source has one.
- **Where it comes from:** the image's origin decides whether game data may be traced from it. Your own
  drawing, or an OSM-based render with attribution, is fine. Tracing Google Maps, other commercial map
  services, or a scanned published map may not be allowed by their terms or copyright.
- **Coverage split:** one image or several tiles both work. Several tiles need overlap, or marked
  points on each.

## 10. Original decision questions (kept for the record)

1. **Data source:** OpenStreetMap (accurate; needs a download and a licence decision) or hand-authored
   (no licence question, much coarser)?
2. **Coverage:** A (2 × 2 inner city), **B (4 × 4 greater city, recommended)** or C (whole province)?
3. **Delivery:** a **separate real-map mod next to the megacity (recommended)**, or replace the megacity?
4. **Period accuracy:** apply the 2004 corrections (recommended), or use today's layout for now and
   correct later?
