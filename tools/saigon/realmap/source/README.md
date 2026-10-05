# Real-map source images

Uploaded maps, kept **on this machine only** (`.gitignore`): they are third-party printed maps and
screenshots. Only what the converter derives from them is committed.

| File | What | Used for |
|---|---|---|
| `tourist_map_hcmc_caravelle.*` | Caravelle Hotel tourist map of HCMC, 2000s (Miền Đông at Đinh Bộ Lĩnh, Thủ Thiêm undeveloped) | the 2009 reference: checking corrections, Thủ Thiêm creeks. Georeferenced in `../georef/` (5.56 m/px, residuals 10–160 m) |
| `tourist_map_d1_d3_d10.*` | the same map's inset, Districts 1, 3, 10, 4, 5 | 2009 reference for the core |
| `osm_d1_core_screenshot.*` | OpenStreetMap render of District 1 (today) | none: the OSM data itself is used (`../osm/`) |
| `ai_map_spec_colours.*` | AI-generated city map in the spec colours | none: invented geography |
| `saigon_2009_illustrated.png` | AI-illustrated Saigon poster | mood reference only; not to scale |

For drawing a map in the converter's own colours, see `doc/saigon/REALMAP_IMAGE_SPEC.md`.
