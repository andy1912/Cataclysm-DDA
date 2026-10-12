# Real-map Saigon: what to put in the map image

This is the spec for the map image(s) the real-map converter will trace (doc/saigon/REALMAP_PLAN.md).
One game map tile (OMT) is **24 m**. One overmap is 180 × 180 tiles (4.32 km).

## 1. What to trace

Draw **flat shapes in the exact colours of §3**. The converter classifies every pixel by its nearest
colour from that table:

1. **Water:** the Saigon River, canals, lakes and ponds.
2. **Roads:** boulevards, main streets, ordinary streets. Alleys (hẻm) are optional.
3. **Bridges** where a road crosses water, and the **railway** to Ga Sài Gòn.
4. **Land use:** every block filled with its kind (shophouse residential, downtown, Chợ Lớn,
   villas, industrial, government or military, park, cemetery, rice field, marsh).
5. **Landmarks:** one marker per landmark at its main entrance (§4).
6. **Places**, optional: markers for petrol stations, markets, pagodas, churches, schools,
   hospitals, police stations, supermarkets (§3). Anything you leave out is placed by rules.

**Leave out:** text labels, icons, building outlines, shadows, 3D buildings, satellite imagery,
gradients and hillshade. If your tool cannot turn labels off, give me a second copy without them.
Soft (anti-aliased) edges are fine; hard edges are better.

## 2. Size

| Pixels per tile | Metres per pixel | Whole area 5 × 4 overmaps | Whole area 4 × 4 overmaps | Verdict |
|---|---|---|---|---|
| 2 | 12 | 1440 × 1152 | 1440 × 1440 | minimum: a street is 2 px wide, alleys vanish |
| **4** | **6** | **3600 × 2880** | **2880 × 2880** | **best: streets 4 px, canals clear, small files** |
| 8 | 3 | 7200 × 5760 | 5760 × 5760 | more than needed; only if your tool draws alleys well |

**Recommended: 6 m per pixel (4 px per tile), PNG, north up, no rotation.**

## 3. Colour codes

| Layer | Hex | Notes |
|---|---|---|
| River (Saigon River, Đồng Nai) | `#1F4FB0` | full width as drawn |
| Canal (kênh, rạch) | `#3AA6F0` | at least 3 px wide at 6 m/px; narrower ones get widened |
| Lake / pond | `#2A7AD0` | Đầm Sen lake, Hồ Kỳ Hòa, palace pools are drawn by the landmark itself |
| Boulevard (≥ 30 m: Lê Duẩn, Nguyễn Huệ, Trần Hưng Đạo…) | `#E0302A` | becomes a 2-tile-wide road |
| Main street (arterial) | `#F28C1E` | |
| Street | `#FFFFFF` | |
| Hẻm (alley), optional | `#B4B4B4` | if left out, alleys are generated inside blocks |
| Bridge | `#9B3FC8` | the road's own width, over the water |
| Railway | `#3C3C3C` | the North–South line into Ga Sài Gòn |
| Shophouse residential (nhà ống, hẻm) | `#E6C89A` | most of the city |
| Downtown / commercial (D1 core) | `#E89AA0` | offices, hotels, the colonial centre |
| Chợ Lớn (Hoa quarter, D5–D6) | `#EBB54A` | Chinese shophouses, temples, wholesale |
| Villas / low density (D3, Thảo Điền) | `#C9DFA0` | |
| Apartment blocks (chung cư) | `#D8A0D8` | old collective housing |
| Industrial / port / warehouse | `#9A9A9A` | Khánh Hội port, Tân Thuận |
| Government / military / airport | `#6E80A8` | Tân Sơn Nhất, barracks |
| Park / green | `#3FA548` | Tao Đàn, 30/4 park, Lê Văn Tám |
| Cemetery | `#6B8A22` | |
| Rice field / farmland | `#D4EA9A` | the edges of the city |
| Marsh / mangrove (Thủ Thiêm in 2004) | `#7AB8A0` | |
| Open ground / construction | `#F2EDDC` | |
| **Landmark marker** | `#FF00FF` | 7 × 7 px square at the landmark's main entrance (§4) |
| Place: petrol station | `#FFF000` | 5 × 5 px square |
| Place: market (chợ) | `#FF7F00` | 5 × 5 px |
| Place: pagoda / temple | `#C00000` | 5 × 5 px |
| Place: church | `#FFB0C8` | 5 × 5 px |
| Place: school | `#0050FF` | 5 × 5 px |
| Place: hospital | `#00E0E0` | 5 × 5 px |
| Place: police | `#202080` | 5 × 5 px |
| Place: supermarket | `#00A050` | 5 × 5 px |

Keep the map's other colours away from these values. Within about ±12 per channel is read as the
listed colour.

## 4. Landmarks already in the game (19)

Footprint is in game tiles (24 m each); the street side is where the main gate or door is. Real
positions are approximate (from memory); **your image decides**. Put the magenta marker at the main
entrance, and I match each marker to the nearest landmark below.

| # | Landmark | District | Footprint | Main entrance faces | Approx. lat, lon |
|---|---|---|---|---|---|
| 1 | Chợ Bến Thành | D1 | 3 × 3 | the Quách Thị Trang roundabout (south gate, clock tower) | 10.772, 106.698 |
| 2 | Nhà thờ Đức Bà | D1 | 2 × 3 | Công xã Paris square | 10.780, 106.699 |
| 3 | Bưu điện Thành phố | D1 | 3 × 2 | Công xã Paris square | 10.780, 106.700 |
| 4 | Nhà hát Thành phố | D1 | 2 × 2 | Lam Sơn square / Đồng Khởi | 10.777, 106.703 |
| 5 | UBND Thành phố | D1 | 3 × 2 | the head of Nguyễn Huệ | 10.777, 106.701 |
| 6 | Dinh Độc Lập | D1 | 3 × 3 | Lê Duẩn (the gate) | 10.777, 106.695 |
| 7 | Chùa Bà Thiên Hậu | D5 | 2 × 2 | Nguyễn Trãi | 10.753, 106.661 |
| 8 | Chùa Ngọc Hoàng | D1 (Đa Kao) | 2 × 2 | Mai Thị Lựu | 10.792, 106.698 |
| 9 | Chợ Bình Tây | D6 | 3 × 3 | Tháp Mười (clock-tower gate) | 10.750, 106.652 |
| 10 | Ga Sài Gòn | D3 | 3 × 3 | Nguyễn Thông | 10.782, 106.677 |
| 11 | Bến xe Miền Đông (old site) | Bình Thạnh | 3 × 3 | Đinh Bộ Lĩnh | 10.815, 106.711 |
| 12 | Công viên Tao Đàn | D1 | 3 × 3 | Trương Định | 10.775, 106.693 |
| 13 | Hồ Con Rùa | D3 | 1 × 1 | the roundabout itself | 10.783, 106.696 |
| 14 | Saigon Trade Center | D1 | 1 × 1 | Tôn Đức Thắng | 10.781, 106.704 |
| 15 | Diamond Plaza | D1 | 2 × 2 | Lê Duẩn | 10.781, 106.698 |
| 16 | Phạm Ngũ Lão – Bùi Viện | D1 | 3 × 1 (street) | Bùi Viện (mark the middle of the block) | 10.768, 106.693 |
| 17 | Thảo Cầm Viên | D1 | 4 × 4 | Nguyễn Bỉnh Khiêm (main gate) | 10.788, 106.705 |
| 18 | Công viên Đầm Sen | D11 | 4 × 4 | Hòa Bình | 10.768, 106.642 |
| 19 | Suối Tiên | Thủ Đức | 4 × 4 | Xa lộ Hà Nội | 10.867, 106.802 |

The game also has generic places, placed by the colours above or by rules: nhà ống rows (15 shop
kinds), hẻm blocks, chợ, chùa, nhà thờ, trường, UBND phường, chung cư, canal rows with stilt
houses, petrol stations, Co.op Mart, district hospitals, ward police, cemeteries, bookstores,
motorbike dealers.

## 5. Area and tiling options

The area must hold Đầm Sen (west, ≈ 106.64 E) and Suối Tiên (north-east, ≈ 106.80 E, 10.87 N).
That is ≈ 17.5 km east–west, slightly more than 4 overmaps (17.28 km). Two areas:

| Area | Overmaps | Box (approx.) | Contains |
|---|---|---|---|
| **5 × 4 (recommended)** | 21.6 × 17.3 km | W 106.624, E 106.821, S 10.729, N 10.886 | all 19 landmarks at real positions |
| 4 × 4 (your earlier choice) | 17.3 × 17.3 km | W 106.630, E 106.788, S 10.735, N 10.891 | 18; Suối Tiên falls ~1.5 km outside and is moved to the east edge |

How to cut the image(s), at 6 m per pixel (any of these work; overlap is fine):

| Option | Files | Size each | Notes |
|---|---|---|---|
| **A. One image** | 1 | 3600 × 2880 (5 × 4) or 2880 × 2880 | simplest; needs 2–4 magenta-free reference marks (§6) |
| **B. One tile per overmap** | 20 (or 16) | 720 × 720 + 40 px overlap on each side = 800 × 800 | name `tile_<col>_<row>.png`, col 0 = west, row 0 = north |
| C. Four quadrants | 4 | half the area each + 80 px overlap | name `quad_nw.png`, `quad_ne.png`, `quad_sw.png`, `quad_se.png` |
| D. Free tiles by district | any | any | each tile needs its own 3 reference points (§6) |

## 6. Reference points (for positioning)

Mark 3–4 reference points in black `#000000` (a 5 × 5 square). Use places that are easy to find on
both your map and the real city, and list them with the image, for example:

- the Bến Thành clock tower;
- the front of Đức Bà;
- the Independence Palace gate;
- Bến Nhà Rồng (the Dragon House wharf);
- the Sài Gòn bridge (east end).

With tiles (options B and C), every tile needs at least 2 of these, or the export settings (exact
corner coordinates and metres per pixel) written next to it.

## 7. When you upload

Upload the image(s) in chat or point me at the files. I store them in
`tools/saigon/realmap/source/`, then show you a preview of how each colour was read before converting
the whole city.
