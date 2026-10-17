# Saigon sprite plan: what to make next

This plan comes after the G17 peer review ([`../review/G_art_review.md`](../review/G_art_review.md)), as of 2026-10-03. Current coverage is in [`SPRITE_REVISION_SUMMARY.md`](SPRITE_REVISION_SUMMARY.md). Every on-screen (T1) and common-loot (T2) sprite already has Saigon or deliberately kept art. This plan covers the next layer:
- review fix-ups;
- **new usable items**;
- **environment** (terrain and furniture that make streets, hẻm, chợ and canals read as Saigon);
- creatures, vehicles, effects and map icons.

Most entries need **new game content as well as a sprite**. Where an entry says "copy-from", the base id has been checked to exist in dda.

## 0. Rules for every new sprite
| Rule | Detail |
|---|---|
| Content first | Only draw for ids that exist, or that land in the same unit. Each unit adds the JSON (copy-from a dda base), the sprite and an item-group or palette entry, so the art is reachable. |
| UltimateCataclysm budget | Items: a **20×20 canvas with the object about 11×9 px** (median), at most about 14×12, 3–4 tones per material, a soft dark outline and a 1 px shadow. Furniture and terrain: 32×32, or 32×64 for tall objects. Monsters: 32×48. Trees: 96×96. Worn clothing: 32×36, male + female. Map icons: 16×16. |
| Connected and rotating sprites | Walls, fences and floors that connect need `multitile` with all subtiles: `center`, `corner`, `edge`, `t_connection`, `end_piece`, `unconnected` (+`broken`/`open` where they apply). Rotating furniture needs 4 facings or `"rotates": true`. Vehicle parts always set `"rotates": true`. |
| Route | **D** = code-drawn (`art/saigon/drawn/`), **R** = derived recolour, **H** = hand art recommended. Characters and organic shapes go to H; a D placeholder ships until H exists. |
| Gates per unit | `draw_sprites.py`, `build_sprites.py`, `validate_tileset.py` (0 problems), `check_mod.sh`, `[saigon]` tests, a `[saigon_scene]` render of the affected area viewed before committing, then `revision_list.py`. |
| In-game check | Load a **new world** with `tools/saigon/play_saigon.sh` and look at: a shophouse front, a tree, a parked motorbike turning, an item on the floor and the character in a nón lá. This closes R9 in the review. |

## 1. Fix-ups from the review (do first)
| Unit | Work | Count | Route |
|---|---|---:|---|
| **G18** | **Redraw the 20×20 icons to the UltimateCataclysm budget (R5).** Draw them smaller rather than downscaling: books become about 10×8 plus a page edge, and boxes and packets about 12×9. Add a size gate to `validate_tileset.py` that warns when a 20×20 sprite's opaque area exceeds about 120 px. Draw the 4 Saigon-referenced gaps (R8): `hot_sauce`, `noodles_fast`, `pickle`, `ring_wedding`. Wire the validator into `check_mod.sh` (R12). | 45 + 4 | D |
| **G19** | **Flora content (R6, R7).** Make banana and papaya non-log plants (no `TREE`, no treetop roof; they bash into leaves and fibre). Give Saigon versions of the forest-edge mixes: `t_region_shrub_forest*` and `t_region_shrub_plains` → bamboo, cassava, lantana, wild banana; `f_region_flower`/`weed` → periwinkle, mimosa (cây xấu hổ), wild morning glory. Add 3 sprites. | 3 | D |
| G-tools | Cache decoded base sheets in `pngio` (raw RGBA next to the PNG, keyed by mtime) to cut the 1–2 min runs (R11). | – | – |

## 2. Usable items (new content + 20×20 icons)
Priority **A** = seen in every house or shop, or part of a core loop (cooking, water, light, heat, trade). **B** = flavour loot with a use. **C** = morale and collectibles.

### 2a. Kitchen, food prep and drink
| Id (proposed) | Vietnamese | Use (copy-from) | Pri |
|---|---|---|---|
| `sgn_noi_com_dien` | nồi cơm điện | Electric rice cooker; cooks rice and keeps it warm on grid power (copy-from `hotplate`, `pot` pocket) | A |
| `sgn_bep_than_to_ong` + `sgn_than_to_ong` | bếp than tổ ong, than tổ ong | Honeycomb-briquette stove and briquettes, the poor household's stove (copy-from `f_brazier` as furniture + `charcoal` fuel) | A |
| `sgn_phin` | phin cà phê | Coffee drip filter, a tool quality for the cà phê sữa đá recipe | A |
| `sgn_ca_phe_bot` | cà phê bột | Ground robusta, a recipe input | A |
| `sgn_sua_dac` | sữa đặc (fictional "Ông Thọ"-style tin) | Condensed milk tin (copy-from `con_milk`) | A |
| `sgn_da_cay` | đá cây | Block of ice from an ice factory; melts, cools food (needs a temperature-carrier design) | A |
| `sgn_bich_nuoc` | bịch nylon | Tied plastic bag of iced drink, the street container (copy-from `bag_plastic`, liquid pocket) | A |
| `sgn_ly_nhua` | ly nhựa | Plastic cup with a straw (copy-from `cup_plastic`) | B |
| `sgn_chai_nuoc_mam` | chai nước mắm | Fish-sauce bottle, so the condiment shows as a bottle not a puddle (copy-from `bottle_plastic`) | B |
| `sgn_lu_nuoc` | lu nước | Glazed water jar: rain catchment and storage, as furniture (see §3b) | A |
| `sgn_gao_bao` | bao gạo | 25 kg rice sack (`dry_rice` container variant) | B |
| Street dishes | hủ tiếu, bánh xèo, gỏi cuốn, xôi, bánh bao | Recipes + icons | B |
| Dried goods | khô mực, bánh tráng, tôm khô | Long-keeping loot | B |
| Fruit | dừa trái (coconut to drink), chuối nải (banana hand), xoài | Drops from the G12 trees (drink, eat) | A |

### 2b. Household, electronics, light and power
| Id | Vietnamese | Use (copy-from) | Pri |
|---|---|---|---|
| `sgn_quat_may` | quạt máy | Stand fan; a heat-relief morale buff on grid power (copy-from `fan`) | A |
| `sgn_den_dau` | đèn dầu | Kerosene wick lamp, the power-cut light (copy-from `oil_lamp`) | A |
| `sgn_nen` | nến | Altar candle (copy-from `candle`) | B |
| `sgn_dien_thoai_nokia` | "cục gạch" phone | 2G brick phone, fictional brand (copy-from `cell_phone`) | B |
| `sgn_the_cao` | thẻ cào | Prepaid card, trade value | C |
| `sgn_radio_cassette` | radio cassette | Radio + tapes for morale (copy-from `radio` or the dda tool) | B |
| `sgn_vcd` | đĩa VCD | Karaoke and film discs, trade/morale | C |
| `sgn_ac_quy` | bình ắc quy | Motorbike battery as a power source (exists as a vehicle part; icon only) | B |
| `sgn_mung` | mùng | Mosquito net; a sleep comfort bonus against mosquitoes (wearable/bedding, copy-from `hammock`-style bedding) | A |
| `sgn_vong` | võng | Hammock (copy-from `hammock`) + furniture `f_sgn_vong` (§3b) | A |
| `sgn_chieu` | chiếu | Woven sleeping mat, portable bedding | B |

### 2c. Medicine and hygiene
| Id | Vietnamese | Use (copy-from) | Pri |
|---|---|---|---|
| `sgn_dau_gio` | dầu gió | Green medicated oil; pain and nausea relief (copy-from `aspirin`-style) | A |
| `sgn_cao_sao_vang` | balm tin (fictionalised) | Balm for aches | B |
| `sgn_oresol` | oresol | Rehydration salts against heat and diarrhoea | A |
| `sgn_khau_trang` | khẩu trang vải | Cloth face mask, ubiquitous on motorbikes (copy-from `mask_dust`) + worn overlay | A |
| `sgn_xa_bong_cuc` | xà bông cục | Bar soap | C |

### 2d. Tools, weapons and work gear
| Id | Vietnamese | Use (copy-from) | Pri |
|---|---|---|---|
| `sgn_xa_beng` | xà beng | Crowbar-class pry bar for cửa sắt kéo gates | A |
| `sgn_dao_phay` | dao phay | Kitchen cleaver (`knife_cleaver` now has an icon; a Saigon variant is optional) | C |
| `sgn_dao_thai` | dao Thái Lan | Small paring knife | B |
| `sgn_ong_bom` | ống bơm xe | Tyre pump for vehicles | B |
| `sgn_quang_ganh` | đòn gánh + thúng | Shoulder pole with two baskets: big carry capacity, slow (wearable container) + worn overlay | A |
| `sgn_ro_nhua` | rổ / thau nhựa | Plastic basket and basin (containers) | B |
| `sgn_luoi_chai` | lưới chài | Cast net for fishing in canals | B |
| `sgn_can_nhua` | can nhựa 20 L | Fuel and water jerrycan in Saigon blue/white (an R recolour of `jerrycan`) | A |
| `sgn_binh_gas` | bình gas 12 kg | Household LPG cylinder (copy-from `medium_propane_tank`) | A |

### 2e. Clothing (icon + male/female worn overlays)
| Id | Vietnamese | Pri | Route |
|---|---|---|---|
| `sgn_ao_dai` | áo dài (white schoolgirl, coloured festive) | B | D icon / H overlay |
| `sgn_ao_thun` | áo thun | Plain tees in Saigon colours (R of `tshirt`) | B |
| `sgn_quan_tay` | quần tây | Slacks (R of `pants`) | B |
| `sgn_ao_khoac_chong_nang` | áo khoác chống nắng | Sun jacket with hood and gloves | A |
| `sgn_non_ket` | nón kết | Baseball cap (R) | C |
| `sgn_dep_lao` | dép lào | Rubber flip-flops (D, the dép tổ ong shape) | B |
| `sgn_uniform_cong_an` | công an uniform | Khaki uniform + cap (NPC and zombie source) | B |
| `sgn_ao_trang_hoc_sinh` | áo trắng học sinh | White school shirt + red scarf | C |

### 2f. Documents, trade and paper
| Id | Vietnamese | Use | Pri |
|---|---|---|---|
| `sgn_cmnd` | CMND | National ID card (lore, NPC trust) | C |
| `sgn_so_ho_khau` | sổ hộ khẩu | Household registration book (lore key for some doors and NPCs) | C |
| `sgn_ve_so` | vé số | Lottery tickets, trade and morale | B |
| `sgn_thuoc_la` | fictional cigarette brand | Cigarettes (copy-from `cig`) | B |
| `sgn_lich_to` | lịch bloc | Tear-off wall calendar (furniture decor or item) | C |
| `sgn_vang_luong` | lượng vàng | Gold tael, 10 chỉ (variant of `sgn_vang_chi`) | B |

**Section total:** about 55 items. That's about 55 icons plus about 16 worn overlays (8 garments × 2).

## 3. Environment
### 3a. Terrain (32×32; connected ones are multitile)
| Id | Vietnamese | Where | Pri | Route |
|---|---|---|---|---|
| `t_sgn_gach_bong` | gạch bông | Patterned encaustic floor tiles, the signature nhà ống floor. 4 patterns as weighted variants | **A** | D |
| `t_sgn_gach_men` | gạch men | Glazed 2000s floor tile, mid-range homes (R of `t_linoleum_white`) | A | R |
| `t_sgn_tuong_bong_gio` | tường bông gió | Breeze-block wall: decorative, see-through, connects | **A** | D (multitile) |
| `t_sgn_mai_ton` | mái tôn | Corrugated metal roof, blue or rust (R of `t_metal_roof`) | A | R |
| `t_sgn_mai_ngoi` | mái ngói | Terracotta tile roof for pagodas and old houses | B | D |
| `t_sgn_hem_xi_mang` | hẻm xi măng | Cracked concrete alley paving with a centre drain line | A | D |
| `t_sgn_cua_sat_keo_c/o` | cửa sắt kéo | Accordion iron gate, closed and open: the iconic loud, slow entry (copy-from `t_door_metal_c`) | **A** | D (+open) |
| `t_sgn_cua_cuon_o` | cửa cuốn (open) | Rolled-up shutter state (the closed one exists) | A | D |
| `t_sgn_kenh` + `t_sgn_bo_ke` | nước kênh, bờ kè | Murky green canal water and a stone embankment (needs B8f canal content) | A | D/R |
| `t_sgn_ngap_*` | nước ngập | **Done (G30):** flooded road, sidewalk and alley, raised and drained by wet-season rain (region/flood.json) | B | D |
| `t_sgn_cong` | nắp cống | Sidewalk drain grate (R of `t_grate`) | C | R |

### 3b. Furniture (32×32 or 32×64)
| Id | Vietnamese | Use / where | Pri | Route |
|---|---|---|---|---|
| `f_sgn_cot_dien` | cột điện + dây | Concrete power pole with tangled cables, *the* Saigon street icon (32×64, copy-from `f_utility_pole`) | **A** | D |
| `f_sgn_ban_inox` + `f_sgn_ghe_nhua_set` | bàn inox, ghế nhựa | Steel street-food table with red and blue stools (stools exist) | **A** | D |
| `f_sgn_xe_banh_mi` | xe bánh mì | Glass-cased bánh mì cart, lootable (container) | **A** | D |
| `f_sgn_xe_hu_tieu` | xe hủ tiếu | Noodle cart with a pot and stove | B | D |
| `f_sgn_du` | dù / ô | Big sidewalk umbrella, shade (32×64) | A | D |
| `f_sgn_ban_tho_than_tai` | bàn thờ Thần Tài | Small floor altar at shop entrances, offerings (container) | **A** | D |
| `f_sgn_may_lanh` | cục nóng máy lạnh | Wall AC outdoor unit, scrap and dripping (R of `f_air_conditioner`) | A | R |
| `f_sgn_bang_hieu` | bảng hiệu | Shop sign boards, textless colour panels, several variants | A | D |
| `f_sgn_loa_phuong` | loa phường | Ward loudspeaker on a pole; ties into broadcast lore (32×64) | A | D |
| `f_sgn_lu_nuoc` | lu nước | Water jar (furniture, rain collection) | A | D |
| `f_sgn_chau_kieng` | chậu kiểng | Potted bonsai and kumquat (copy-from `f_planter`) | B | D |
| `f_sgn_long_chim` | lồng chim | Hanging bird cage (café décor) | C | D |
| `f_sgn_day_phoi` | dây phơi | Clothesline with laundry: hẻm texture, cloth source | A | D |
| `f_sgn_vong` | võng | Hung hammock: café and porch seat, sleep | A | D |
| `f_sgn_giuong_mung` | giường + mùng | Bed under a mosquito net (a variant of the chiếu bed) | B | D |
| `f_sgn_tivi_crt` | tivi CRT | CRT TV on a cabinet: new furniture (dda only has the `television` item), deconstructs into it | B | D |
| `f_sgn_dan_karaoke` | dàn karaoke | Karaoke set: TV, speakers, mic (karaoke bar landmark) | B | D |
| `f_sgn_quay_vang` | quầy vàng | Gold-shop glass counter (copy-from `f_glass_cabinet`) | B | D |
| `f_sgn_tu_thuoc` | tủ thuốc | Pharmacy shelf (nhà thuốc lots) | B | D |
| `f_sgn_may_net` | máy tính net | Internet-café PC booth | C | D |
| `f_sgn_xe_dap_dung` | xe đạp dựng | Parked bicycle as décor where a vehicle won't fit | C | D |
| `f_sgn_thung_rac_xanh` | – | Done in G11 (green bin) | – | – |

### 3c. Region and map extras
- **Hẻm texture extra:** scatter laundry lines, potted plants, parked bicycles and small altars along hẻm spines, as a `map_extra` or nested chunks in `gen_hem.py`.
- **Wet-season puddles:** a map extra on roads in May–Nov.

## 4. Creatures and people
| Id | What | Size | Pri | Route |
|---|---|---|---|---|
| Saigon zombies ×4 + common | Proper Saigon clothes: short-sleeved shirts, slacks, dép, conical hats, uniforms, aprons | 32×48 | A | **H** (D recolours ship today) |
| `sgn_mon_zombie_hoc_sinh` | Schoolchild zombie in áo trắng (new content: copy-from `mon_zombie_child`) | 32×32 | B | H |
| `sgn_mon_cho_ta` | Street dog (cho ta), a variant of `mon_dog` | 32×32 | A | R/H |
| `sgn_mon_meo` / `sgn_mon_ga` | Alley cat and yard chicken (`mon_cat`, `mon_chicken`), flu-carrier lore | 32×32 | B | R |
| `sgn_mon_chuot_cong` | Sewer rat | 32×32 | B | D |
| `sgn_mon_ran_nuoc` / `sgn_mon_ky_da` | Canal snake and monitor lizard (content from bible §10) | 32×32 | C | H |
| NPC clothing | Công an, vendor, monk robes (áo nâu / áo vàng) as worn overlays | 32×36 | B | H |

## 5. Vehicles (32×32 top-down parts, `"rotates": true`)
| Content | Parts needing sprites | Pri |
|---|---|---|
| Underbone colour variants (red, blue, black) | `vp_sgn_frame_underbone` with `_var_` colours, front fairing and leg shield | A |
| Xe buýt (city bus, period livery: fictional colours) | Bus body panels, windows and door (copy-from bus parts) | B |
| Xe tải nhẹ (light truck) and taxi (fictional livery) | Recolour variants | C |
| Ghe extras | `vp_sgn_mui_ghe` (curved bamboo canopy), painted bow eyes on the front frame | B |
| Ba gác load | Strapped cargo look for the bed (variant) | C |

## 6. Fields, effects and weather
| Id | What | Pri | Route |
|---|---|---|---|
| `fd_sgn_khoi_nhang` | Incense smoke wisps near altars (cosmetic field) | C | D |
| Rain and flood | Heavier rain overlay for the wet season; flood-water terrain (§3a) | B | D |
| `fd_sgn_mui_hoi` | Market stench visual (cosmetic) | C | D |

## 7. Overmap icons (16×16, Larwick)
For new building content: church (nhà thờ), school, ward office (UBND phường), internet café, karaoke bar, motorbike repair (tiệm sửa xe), nhà thuốc, gold shop, ice factory (nhà máy đá), canal (kênh) segments, bus station. These are 11 icons, **R** from Larwick originals like G7, with **D** for the canal.

## 8. Later: isometric
Ultica_iso equivalents of everything, once renderer phase R3 starts. Out of scope for this plan.

## Schedule (small resumable units, as in `PROGRESS.md`)
| Unit | Contents | New ids | New sprites (approx.) | Mostly | Status (2026-10-04) |
|---|---|---:|---:|---|---|
| G18 | Icon rescale, 4 gap items, size gate, validator in `check_mod.sh` | 4 | 49 | D | done |
| G19 | Flora content fixes + forest-edge species | 3–6 | 3 | content + D | done |
| G20 | **Street kit:** cột điện, bàn inox + ghế set, xe bánh mì, dù, bảng hiệu, loa phường, cục nóng máy lạnh | 7 | ~14 | D/R | done |
| G21 | **Shophouse interior:** gạch bông ×4, gạch men, Thần Tài altar, lu nước, võng, CRT TV, chậu kiểng | 9 | ~16 | D/R | done |
| G22 | **Gates and hẻm:** cửa sắt kéo c/o, cửa cuốn open, hẻm paving, tường bông gió (multitile), dây phơi + hẻm extra | 6 | ~30 | D | done |
| G23 | **Kitchen and drink items:** nồi cơm điện, bếp than tổ ong + briquettes, phin, cà phê bột, sữa đặc, bịch nylon, ly nhựa, chai nước mắm, bình gas, can nhựa | 11 | 11 | D + recipes | done |
| G24 | **Household and medicine items:** quạt máy, đèn dầu, nến, Nokia, radio, mùng, chiếu, dầu gió, oresol, khẩu trang (+overlay) | 10 | 12 | D | done |
| G25 | **Work gear and trade:** xà beng, quang gánh (+overlay), rổ/thau, lưới chài, vé số, thuốc lá, lượng vàng, street dishes ×5, dried goods ×3 | 16 | 18 | D | done |
| G26 | **Clothing:** áo dài, áo thun, quần tây, áo khoác chống nắng, nón kết, dép lào, uniform, áo trắng (icons + 16 overlays) | 8 | 24 | D/R/H | done |
| G27 | **Canal:** kênh water + embankment, ghe canopy, flood water (with B8f canal content) | 3–4 | ~20 | D | done with B8f (canal water, embankment, tin roofs, icons); flood water done in G30; ghe canopy left |
| G28 | **Animals:** chó ta, mèo, gà, chuột cống (+ snake and lizard) | 4–6 | ~8 | R/D/H | done |
| G29 | **Map icons** for new landmarks | 11 | 11 | R/D | done for the church, ward office and school (B8h-2); gold shop, net café and karaoke are shophouse lots (B8h-1) |
| H1 | **Hand-art pass (artist):** Saigon zombies ×5, NPC outfits, áo dài overlay, iconic street objects polish | – | ~40 | **H** | for an artist |

**Total:** about 100 new game ids and about 260 new sprites. About 80% can be code-drawn or derived (G18–G29). The hand-art pass H1 is where a pixel artist adds the most.

**Suggested order:** G18 → G19 → G20 → G22 → G21 → G23 → G24, then the rest. Fix-ups go first. The street and hẻm kits come next because they're on screen everywhere. Items follow, since each needs its own gameplay hook.
