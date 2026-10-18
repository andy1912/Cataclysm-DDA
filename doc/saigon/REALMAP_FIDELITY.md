# How closely the real map resembles Saigon (2009)

Unit R-fid. This file measures how far the generated real map (`data/mods/saigon_2000s/realmap_2009/`)
matches its OpenStreetMap source and the city as it was in late 2009. All numbers come from scripts,
not from looking at pictures. It lists the fixes made and what still differs.

- **Measure it again:** `python3 tools/saigon/realmap/audit_fidelity.py [FOLDER] [--json OUT.json]`.
  The folder defaults to the mod's `realmap_2009`. The script reads the written overmap files and
  the local OSM extract.
- **Tests:** `saigon_realmap_2009_fidelity` in `tests/saigon_realmap_test.cpp` checks:
  - landmark sites;
  - main streets drawn without breaks;
  - the 2009 corrections.
- **Pictures** (local, in `tools/saigon/realmap/build/`, rebuilt by `make_realmap.sh`):
  - the whole map: `realmap_2009.omap.png`;
  - before and after, side by side: `fidelity_*_before_after.png`.

"Before" means the map as of commit `ad88db5cc0`. "After" means the map built by this unit.

## 1. Scale, orientation, extent

| | Value |
|---|---|
| One overmap tile | 24 m (24 map squares of about 1 m each), the game's own scale |
| Projection | Equirectangular around 10.8° N (`classify.py`): 110,600 m per degree of latitude and 109,349 m per degree of longitude. WGS84 gives 110,613 m and 109,361 m. |
| Error over distance (map distance against great-circle distance) | Bến Thành to Suối Tiên (15.3 km): **−0.17 %**. Bến Thành to Đầm Sen (6.5 km): **+0.09 %**. Bến Thành to Tân Sơn Nhất (6.4 km): **−0.24 %**. Across the whole area (27.7 km): **−0.14 %**. |
| Orientation | North up. x grows east and y grows south, with no rotation. |
| Extent | 5 × 4 overmaps, 900 × 720 tiles = **21.6 × 17.3 km**. The box is N 10.8856, W 106.6237, S 10.7294, E 106.8212. These are game overmaps −1..3 × −2..1. |
| Inside the box | Districts 1, 3, 4, 5, 10, 11, Phú Nhuận, Bình Thạnh, Gò Vấp, Tân Bình and Quận 2. Also the east of Districts 6 and Tân Phú, the north of Districts 7 and 8, the south of Quận 9 and Thủ Đức, and the south of Quận 12. |
| Outside the box | The south of District 7: Phú Mỹ Hưng's centre lies on the box's south edge. Also the south of District 8, Bình Tân, the north of Thủ Đức, and Hóc Môn. Beyond the box the game generates delta countryside (R7). |

The scale is real (1:1 at 24 m per tile), so distances and walking times match the real city to
within 0.3 %.

## 2. Main streets

The audit takes 47 key streets, each by its OSM name. When several unrelated streets share a name, it
measures the one in the right district. For each street it records:
- **coverage**: the share of the street's OSM tiles that have a road within one tile;
- **continuity**: the share of the street's line that lies in the single linked road piece holding
  most of it;
- **breaks**: how many times the linked piece changes along the line;
- **gap**: the longest run of tiles with no road.

| 47 key streets | Before | After |
|---|---|---|
| Mean coverage | 99.0 % | **99.8 %** |
| Mean continuity | 89.0 % | **94.8 %** |
| Breaks, all streets | 357 | **69** |
| Streets with no break at all | 21 | **32** |
| Streets with a gap of more than 3 tiles | 2 | **0** |

Streets that changed most:

| Street | Before | After | Cause of the break, fix |
|---|---|---|---|
| Nguyễn Hữu Cảnh | 64.6 % coverage, gap 28 tiles | 100 %, gap 0 | The Tân Cảng (Vinhomes) and Ba Son correction zones removed it, and the Thủ Thiêm zone reached across the river and took it too. The street opened in 2003. |
| Điện Biên Phủ | gap 7, 12 breaks | gap 0, 5 breaks | The Tân Cảng zone removed the stretch to the Sài Gòn bridge. |
| Lê Lợi | 88 %, 2 breaks | 100 %, 0 breaks | The fountain at Lê Lợi and Nguyễn Huệ (Bùng binh Cây Liễu, built with the 2015 walking street) was drawn as a lake tile that cut the street. |
| Cách Mạng Tháng Tám | 43 %, 8 breaks | 100 %, 0 breaks | A diagonal avenue, broken into pieces that touched only at corners, or that ended one step short of each other. |
| Xô Viết Nghệ Tĩnh | 54.5 % | 100 % | Same as Cách Mạng Tháng Tám |
| Võ Văn Tần | 52 % | 100 % | Same as Cách Mạng Tháng Tám |
| Tôn Đức Thắng | 73 % | 100 % | Same as Cách Mạng Tháng Tám |
| Xa lộ Hà Nội / Võ Nguyên Giáp | 136 / 33 breaks | 8 / 14 breaks | The 2013–15 service roads (song hành) lay alongside the highway. |
| Võ Văn Kiệt | 72 breaks | 8 breaks | Carriageway pieces |

The end-to-end check in the test follows each street's simplified OSM line. It looks at the road tiles
within 3 tiles of that line and checks that they join the street's two ends. On the old map it fails for
Lê Lợi, Võ Văn Tần and Nguyễn Hữu Cảnh. On the new map it passes for all 13 streets: Lê Lợi, Nguyễn Huệ,
Đồng Khởi, Hai Bà Trưng, CMT8, Nam Kỳ Khởi Nghĩa, Võ Văn Tần, Lê Duẩn, Nguyễn Thị Minh Khai, Trần Hưng
Đạo, Nguyễn Văn Cừ, Nguyễn Hữu Cảnh and Xô Viết Nghệ Tĩnh.

**Street names cannot be shown on the overmap.** An overmap tile has no name, and the pregenerated
format (`overmap::unserialize_omap`) carries only terrain and the district "cities" (R11). Districts
therefore show their names, but streets do not. To show street names, the engine would need to change,
for example to read overmap notes or labels from the `.omap` file. This unit does not touch the engine.
The in-game tourist map item (RF1) reveals the streets but does not name them either.

## 3. River and canals

Each waterway is measured the same way as the streets. Water, bridge tiles and ferry docks count as
water.

| Waterway | Before: continuity, breaks | After: continuity, breaks |
|---|---|---|
| Sông Sài Gòn: all its bends, Thanh Đa loop, Thủ Thiêm, Nhà Bè | 100 %, 0 | 100 %, 0 |
| Rạch Bến Nghé | 100 %, 0 | 100 %, 0 |
| Kênh Tàu Hủ | 41.5 %, 3 | 52.3 %, 2 |
| Nhiêu Lộc – Thị Nghè | 19.3 %, 14 | **73.8 %, 5** |
| Tân Hóa – Lò Gốm | 34.5 %, 20 | 29.5 %, 22 (see §8) |
| Kênh Đôi, Kênh Tẻ, Kênh Thanh Đa | 100 % | 100 % |
| Rạch Văn Thánh | 53.9 %, 3 | **100 %, 0** |
| Rạch Chiếc | 95.4 %, 1 | 95.4 %, 1 |
| Mean of the 10 | 74.5 %, 41 breaks | **85.1 %, 30 breaks** |

Coverage of all waterways is 99.5–99.7 % before and after.

What changed:
- **Two-tile crossings are bridges now.**
  - Before, every road crossing a canal two tiles wide was made a culvert (plain road), which cut the
    canal. The game puts ramps on both end tiles of a bridge run of 2 or more, and keeps the water under
    them, so a crossing of two water tiles can be a bridge.
  - Bridge tiles went from 643 to 780 (162 straight runs). `check_realmap.py` finds 0 problems.
  - Only a crossing of a single water tile is still a culvert.
- **Canal-side streets no longer bury their canal.**
  - A canal drawn from its centre line is one tile wide. The street on its bank often fell on the same
    tiles and became a long "bridge" running down the canal (Lò Gốm, for example).
  - Where a street runs along a canal, the canal now moves one tile aside onto free land, and canal
    tiles that touch only at a corner are joined. 102 tiles were moved.

## 4. Bridges (late 2009)

Status of 24 river and canal bridges that stood in 2009:

| | Before | After |
|---|---|---|
| On the map (bridge or road across) | 23 | **24** |
| With real bridge tiles | 18 | **23** |

- **Cầu Thủ Thiêm** (opened January 2008) was missing. The Thủ Thiêm zone dropped it. It is back as a
  bridge from Bình Thạnh's ward 22 to the Thủ Thiêm marsh, joined to Lương Định Của.
- Cầu Bông, Cầu Kiệu, Cầu Lê Văn Sỹ and Cầu Văn Thánh were culverts. They are now bridges.
- Cầu Chà Và is still a culvert, because its canal is one tile wide there.
- **Cầu Phú Mỹ** opened on 2 September 2009 and is kept.
- The old Bình Lợi bridge (rail with a road lane) is represented by OSM's primary "Cầu Bình Lợi" road
  ways. The trunk ways (Phạm Văn Đồng's bridge, after 2009) are dropped. This is an assumption, see §8.

Bridges built after 2009 that must not appear:

| Bridge | Opened | Before | After |
|---|---|---|---|
| Cầu Sài Gòn 2 | 2021 | Merged into the 1961 bridge's crossing, so no second deck | Dropped by name |
| Cầu Ba Son (Thủ Thiêm 2) | 2022 | Absent | Absent |
| Cầu Mương Kênh, the expressway frontage bridge | 2015 | **16 bridge tiles** | Absent |
| Cầu Bà Dạt, Bà Hiện, Đỗ Xuân Hợp (expressway) | 2015 | Road drawn | Absent |
| Cầu Phú Hữu (ring road 2) | After 2015 | Road drawn | Absent |
| Cầu Thị Nghè 2 | About 2014 (from memory) | Road drawn | Dropped |

## 5. Landmarks and key places

Each placed landmark's centre is compared with its anchor and, where the extract has the feature,
with OSM. Distances are in metres.

| Landmark | Placed vs anchor | OSM vs anchor |
|---|---|---|
| Chợ Bến Thành | 57 | 6 |
| Nhà thờ Đức Bà | 81 | 13 |
| Bưu điện | 81 | — |
| Dinh Độc Lập | 11 | — |
| Nhà hát | 8 | — |
| UBND (City Hall) | 35 | — |
| Chợ Bình Tây (Chợ Lớn) | 36 | 5 |
| Chùa Bà Thiên Hậu | 22 | 27 (Hội quán Tuệ Thành) |
| Ga Sài Gòn | 73 | 235 (centre of the railway land) |
| Thảo Cầm Viên | 75 | 0 |
| Đầm Sen | 71 | 0 |
| Tao Đàn | 83 | 0 |
| Suối Tiên | 4 | — |
| **Tân Sơn Nhất terminal** | **43** (was 505 from the real terminal) | — |
| Chợ Rẫy hospital (a place, not a landmark) | nearest bệnh viện 57 m from the OSM site | |

All 28 landmarks stand 4–83 m from their anchors, which is within 3.5 tiles.

**Tân Sơn Nhất:** the remembered anchor put the 2007 international terminal on the apron, 430 m west
of the real building. It is now anchored on OSM's international departures and arrivals curb roads
("Ga đi Quốc tế", "Ga đến T2"). The test checks 11 landmarks and Chợ Rẫy within 4 tiles of their real
sites.

## 6. Districts and land use

**Whole map** (before → after, nearly unchanged):

| Land use | Share |
|---|---|
| Hẻm blocks | 32 % |
| Fields | 26 % |
| Street frontage nhà ống | 10.5 % |
| Roads | 13.7 % |
| Water | 9.8 % |
| Port and warehouses | 4 % |
| Parks | 1.2 % |
| Places | 1.3 % |
| Marsh | 1.3 % |

**By district.** Each tile counts for its nearest district centre, within 3 km; districts_2009.json has
no boundaries. Shares in % of tiles:

| District | nhà ống | hẻm | road | field | water | industrial | park | marsh |
|---|---|---|---|---|---|---|---|---|
| Quận 1 | 10.5 | 18.2 | 18.6 | 0.2 | 13.1 | 2.2 | 4.9 | 31.1 (Thủ Thiêm) |
| Quận 3 | 20.2 | 42.3 | 29.6 | 0.1 | 2.7 | 0.7 | 1.2 | — |
| Quận 5 (Chợ Lớn) | 26.3 | 31.2 | 33.4 | 0.4 | 4.0 | 0.4 | 0.7 | — |
| Quận 6 | 17.0 | 48.7 | 22.7 | 0.6 | 5.1 | 2.8 | 1.9 | — |
| Quận 4 (port) | 13.7 | 40.9 | 18.5 | 1.6 | 12.9 | 2.3 | 4.1 | 4.6 |
| Bình Thạnh | 12.4 | 49.7 | 14.4 | 3.3 | 14.5 | 3.9 | 0.8 | — |
| Quận 7 (north) | 14.9 | 36.5 | 18.7 | 4.5 | 13.2 | 8.8 (Tân Thuận EPZ) | 2.7 | — |
| Quận 2 | 8.8 | 18.3 | 14.3 | 34.4 | 13.1 | 4.7 | 1.4 | 4.5 |
| Quận 9 | 5.3 | 17.2 | 10.4 | 62.3 | 2.5 | 1.5 | 0.4 | — |
| Tân Bình | 14.0 | 29.8 | 16.0 | 30.5 (airport) | 0.6 | 0.4 | 0.2 | — |

How this compares with the real 2009 districts:
- **The character is right in kind.**
  - Chợ Lớn (D5) has the densest street frontage and roads (26 % nhà ống, 33 % road).
  - D3 and D10 are dense blocks with hẻm inside.
  - D4 is port and hẻm.
  - Thủ Thiêm is marsh.
  - D2 is a third fields with villages on the main roads.
  - D9 is two-thirds fields.
  - The Tân Thuận export zone is industrial.
  - Tân Cảng and Ba Son are port and shipyard.
- **What is wrong is mostly in the buildings available, not in the layout.**
  - The map has only nhà ống, hẻm blocks, the mod's places and landmarks.
  - It has no colonial villa blocks (D1, D3), Hoa shophouse rows (Chợ Lớn), cư xá apartment blocks
    (Thanh Đa, Nguyễn Thiện Thuật), or stilt houses over the canals (Tàu Hủ and Thị Nghè in 2009).

**This unit's land-use fixes:**
- **Bình Thạnh's ward 22** (Nguyễn Hữu Cảnh, the Thủ Thiêm bridge's west end) is city again: 291 marsh
  tiles became 0. The first versions of the Thủ Thiêm marsh zone reached across the river there. The
  zone's north and west edges now follow the middle of the river.
- **Today's building sites stay city.** OSM `landuse=construction` and `brownfield` (The One, Viet
  Capital Center, Phú Thọ sports area and others) became open fields in the middle of District 1. In
  2009 these sites were built up.
- **Small water polygons are ignored.** Fountains, pools and ponds smaller than one tile are not drawn
  as water.

## 7. Anachronisms removed

| Built after 2009 | Year | Before | After |
|---|---|---|---|
| HCMC – Long Thành – Dầu Giây expressway, ramps, frontage roads | 2015 | 672 of its 1,128 tiles drawn as road | 35 (only where an older road crosses its line) |
| Xa lộ Hà Nội / Võ Nguyên Giáp service roads ("song hành") | 2013–15 | 945 of 1,042 tiles | 269 (where they lie on the highway itself) |
| Tân Sơn Nhất terminal 3: aprons, flyover, curb roads | 2022–25 | 219 road tiles, 269 apron tiles | 8 road tiles (older streets at the box edge), 18 apron tiles; the land is air-force land again |
| Trần Quốc Hoàn – Cộng Hòa link and its underpass (Đường 18E, Phan Thúc Duyện west of Thăng Long) | 2024 | Drawn | Removed |
| Cầu Sài Gòn 2, Cầu Mương Kênh, Phú Hữu, Bà Dạt, Bà Hiện, Đỗ Xuân Hợp, Thị Nghè 2 | 2013–21 | See §4 | Removed |
| Phú Hữu roundabout, Cát Lái interchange ramps (Nhánh N3/N4/X4/X5) | After 2010 | Drawn | Removed |
| Phạm Văn Đồng's Bình Lợi bridge (trunk ways) | About 2013 | Drawn | Removed |

Already handled before this unit (R2a, R3, R6b, R7, RF2) and checked again:
- Mai Chí Thọ (2011), Phạm Văn Đồng (2013), Võ Chí Công (after 2015), Ba Son bridge (2022);
- Thủ Thiêm new town, Vinhomes Central Park and Landmark 81 (2015–18), Vinhomes Golden River,
  Diamond Island;
- Hi-Tech Park factories;
- the Thủ Thiêm ferry kept until the 2011 tunnel.

The audit's "post-2009 roads still drawn" line, for example Mai Chí Thọ 8 %, counts only tiles where an
older street crosses or follows the same line.

Other checks:
- **Metro line 1** (works from 2012): absent. The extract has `railway=rail` only, so no subway or light
  rail is drawn.
- **Bitexco Financial Tower** (2010, under construction in 2009): no landmark. The site is a shophouse
  block. A "tower under construction" building would be new mapgen.

## 8. What still differs, and why

1. **No street names on the map.** This needs an engine change (see §2).
2. **Diagonal streets are staircases.** The overmap links tiles north, east, south and west only. A
   diagonal avenue such as CMT8, Hai Bà Trưng or Nam Kỳ Khởi Nghĩa is drawn as a staircase. It is now
   unbroken, but it cannot be a straight diagonal.
3. **Some boulevards are drawn as two parallel strips.** Examples are Phạm Thế Hiển, parts of Nguyễn
   Hữu Cảnh and Nguyễn Tri Phương (continuity 50 %, 67 % and 43 %). These pairs are not tagged one-way
   in OSM, so they are not recognised as divided roads.
4. **One-tile canal crossings are culverts.** The game ramps only bridge runs of 2 or more tiles, so the
   canal shows a road tile at each crossing of a canal one tile wide.
5. **Kênh Tân Hóa – Lò Gốm** has streets on both banks along much of its length. Where both sides are
   taken, the canal cannot move aside and stays broken (continuity 29.5 %). A 2009 detail: the canal
   was then lined with shacks, and the embanked streets on both banks came with the 2010–2014 project.
   Removing those streets needs a dated source; OSM has none.
6. **District 7 east** (Phú Thuận, Phú Mỹ) and parts of District 2 (An Phú, An Khánh) were mostly
   fields, marsh and new estates in 2009. Today's dense OSM street grid makes them hẻm blocks. Drawing a
   correct 2009 zone needs a dated 2009 source we may use. The scans in `source/` are local reference
   only and must not be traced into committed data; tracing Google Maps is ruled out.
7. **Võ Văn Kiệt (Đại lộ Đông Tây)** was half built in 2009: it opened in full in November 2011. It
   follows the old canal-side streets (Bến Chương Dương, Hàm Tử, Trần Văn Kiểu), so a road there is
   right, but the map draws it at full boulevard rank.
8. **Buildings for district character are missing.** The map has no colonial villa or civic block
   (D1, D3, Thảo Điền), no Hoa shophouse row (Chợ Lớn), no cư xá apartment block, and no stilt houses
   over canals. These would be new mapgen and overmap terrain, which is outside this unit. They are
   reported for the lead.
9. **Unsure from memory, kept or changed with a note in corrections_2009.json:**
   - Cầu Thị Nghè 2: dropped as about 2014.
   - The old Bình Lợi bridge's road lane: kept as the primary ways.
   - GO! (ex-Big C) supermarkets: not placed, because the filter knows only the 2009 chain names.

**No download is needed for the fixes above.**

Two optional OSM extracts would help later. Each would be a request to the user; nothing has been
fetched.

- **Building footprints** in the box, to tell villas, shophouse rows and apartment blocks apart by
  footprint size and shape (fix 8):
  - Query: `way["building"](10.729,106.624,10.886,106.821); out tags geom qt;`
  - Source: https://overpass-api.de/api/interpreter
  - Expected size: roughly 150–300 MB of JSON. Today's buildings, so it needs the same 2009
    corrections.
- **Old district boundaries**, so the per-district numbers use real borders instead of nearest centres:
  - Query: `relation["boundary"="administrative"]["admin_level"="6"](10.729,106.624,10.886,106.821); out geom;`
  - Expected size: about 3–8 MB.
  - Vietnam abolished the district level in July 2025, so today's OSM may no longer hold these
    relations. The pre-2025 state would need an OSM history extract or a dated planet file.

## 9. Validation

- `tools/saigon/realmap/check_realmap.py` passes: 162 bridge runs straight and ramped; 2,501 hẻm
  networks, each with a way in; no dda American buildings.
- The largest road network holds 96.0 % of the 88,600 road tiles (95.8 % before).
- `tests/cata_test --mods=dda,saigon_2000s "saigon_realmap*,saigon_new_game_realmap_2009"` passes
  (9 test cases, 184 assertions). The routes test now targets the corrected Tân Sơn Nhất terminal site.
- The new `saigon_realmap_2009_fidelity` test's checks were run as Python equivalents on the old map,
  and they fail there: Lê Lợi, Võ Văn Tần and Nguyễn Hữu Cảnh broken, no Thủ Thiêm bridge, ward 22
  marsh, 219 road tiles on the T3 site. On the new map the test passes.
- `tools/saigon/check_mod.sh`: OK.
