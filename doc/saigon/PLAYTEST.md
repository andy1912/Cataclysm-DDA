# Sài Gòn 2000s: guided playtest (F3)

This guide is for a person playing the mod to find bugs. Every check has an ID (`PT-xx`). Use that
ID in bug reports ([BUG_REPORT.md](BUG_REPORT.md)), so the lead can turn each report into a unit.

How to use it:
- Work through the areas in order, or pick one area per session.
- Each check says what to do, what "pass" looks like, and the fastest way to get there. The fastest
  way usually uses the playtest remote (the cheat mod) or the debug menu.
- A check passes only if everything in its "Pass" column is true.
- Anything else is a bug: a wrong result, an error popup, a crash, text that is broken or reads as
  American, or a slowdown. Report it even if you are not sure. "Probably fine" is a useful report too.

---

## 1. Before you start

### 1.1 Build and launch

| Step | What to do |
|---|---|
| Build | The lead builds the game. You need `cataclysm-tiles` (the graphical build) in the repo folder. If it is missing, ask the lead. The build command is in [PROGRESS.md](PROGRESS.md) (S0/tiles rows): `GLSLANG=<glslang> make -j2 TILES=1 FRAMEWORK=1 RELEASE=1 LOCALIZE=0 SOUND=0 BUILD_SHADER_FORMATS=spv cataclysm-tiles`. |
| Tileset | `gfx/UltimateCataclysm` must exist. `play_saigon.sh` warns if it does not. |
| Launch | From the repo folder, run `tools/saigon/play_saigon.sh`. The script starts `cataclysm-tiles` with the right settings. If `cataclysm-tiles` is not built yet, it starts the terminal build instead. |
| First launch | Expect a wait of about 2 minutes while the sprite atlases are baked. This is normal on an 8 GB Mac. |
| Game folder | The game keeps its files in the repo folder: `config/` (options, `debug.log`) and `save/` (worlds). |

### 1.2 Turn on the debug menu key (once)

The debug menu has no key by default.
1. Press `Esc` and choose **Keybindings**.
2. Find **Debug menu** (type `debug` to filter the list).
3. Add a key to it, for example `` ` `` or `F12`.

The debug menu then opens with that key, and it also appears in the `Esc` menu. In this guide, "Debug
> Map… > Change weather" means: open the debug menu, choose **Map…**, then **Change weather**.

Debug menu entries this guide uses:

| Need | Debug menu path |
|---|---|
| Teleport | Teleport… > Teleport - long range (pick a spot on the overmap) |
| Change time | Map… > Change time |
| Change weather | Map… > Change weather (for example `rain` or `thunder`) |
| Spawn an item | Spawning… > Spawn an item (search `sgn_`) |
| Spawn a monster | Spawning… > Spawn monster |
| Spawn an NPC | Spawning… > Spawn NPC |
| Spawn a vehicle | Spawning… > Spawn a vehicle (or Vehicle… > Spawn a vehicle; search `sgn_veh`) |
| Kill monsters | Map… > Kill all monsters |
| Skills | Player… > Change all skills |
| Edit a character | Player… > Edit player/NPC (heal, effects, needs) |
| Show hordes | Info… > Display hordes |
| Show weather | Info… > Display weather |
| Screenshot | Info… > Take screenshot |
| Game report | Info… > Generate game report (copies the version, mods and OS to the clipboard and to `debug.log`) |
| Run an EOC | Game… > Activate EOC (for example `SGN_EOC_intro`) |

### 1.3 Screenshots

- **macOS:** `Cmd+Shift+4` and drag over the game window, or `Cmd+Shift+4` then `Space` and click the
  window. The file goes to the Desktop. `Cmd+Shift+3` takes the whole screen.
- **In game:** Debug > Info… > Take screenshot. The file goes to `save/<world>/screenshots/`, and
  `tools/saigon/collect_bug_report.sh -w "<world>"` picks it up.
- Take the screenshot **before** you close a popup or move. If the bug is a message, scroll the
  message log first (`Shift+P`, or the sidebar).

### 1.4 Collecting files for a report

Run this after you notice a bug, before you start a new game:

```sh
tools/saigon/collect_bug_report.sh -w "<world name>" -t PT-xx
```

It gathers `debug.log`, the git commit, your system, the world's mod list and the newest character
save into one folder and one zip under `~/code/cdda-saigon-logs/bug_reports/`. Nothing is uploaded.
For a save the lead can load, first use **Esc > Export save archive for github bug report** in the
game: it saves the game and writes `save/<world>-trimmed.tar.gz`, which the script includes. Use
`-f` to pack the whole world instead (it can be large). Run the script with `-h` for all options.

---

## 2. The worlds

Make each world from the main menu (**World > Create World**). `play_saigon.sh` already selects
`saigon_2000s` for new worlds.

| World | Mods | Used for |
|---|---|---|
| **PT Vietmap** | dda, Sài Gòn 2000s, **Sài Gòn 2000s – playtest tools (cheats)** | most checks, scenario "Somewhere in Nam" |
| **PT Real** | dda, Sài Gòn 2000s, playtest tools | the 2009 real map, scenario "Saigon 2009" |
| **Real feel** | dda, Sài Gòn 2000s only | one honest session without cheats (difficulty, PT-90s) |

To add the playtest mod: in the world's **Mods** tab, find it under the category *Misc*, and add it
after Sài Gòn 2000s. It depends on Sài Gòn 2000s, so the game will not add it alone. Leave world
options at their defaults unless a check says otherwise.

A world can hold several characters. For each new start, use **New Game** on the same world.

### Starts to cover

| Scenario | Start locations |
|---|---|
| Somewhere in Nam (procedural Vietmap) | Nhà ống (shophouse home); Nhà ống, iron gate pulled shut; Chợ (wet market stall) |
| Saigon 2009 (real map) | the three above, plus Hẻm (a home deep in the alleys); Ga Sài Gòn (the station hall); Tân Sơn Nhất (departures hall) |

That makes nine starts. For most of them, the **Playtester (cheat)** profession is quickest. For each
scenario, do one start with a real Saigon profession (for example Xe ôm driver or Street vendor) so the
real kits get seen.

---

## 3. The playtest mod (cheats)

The mod `saigon_playtest` lives in `data/mods/saigon_playtest/`. It is a testing tool only. Never use
it for a real game, and leave it out of release builds.

### 3.1 The Playtester profession

The **Playtester (cheat)** profession is allowed in both Saigon scenarios. It costs 0 points and has
every useful skill at 6.

It starts with:
- **Clothes:** áo thun, cargo pants, socks, sneakers, a nón bảo hiểm, a watch and a backpack, plus a
  phone and a đồng wallet.
- **The playtest kit:**
  - the playtest remote;
  - a charged flashlight, a lighter, matches, a multitool, a hammer, a screwdriver set, a wrench, a
    hacksaw, duct tape and a dao phay;
  - an áo mưa cánh dơi and rubber flood boots;
  - 20 × 100,000 đ and 10 × 50,000 đ, 5 chỉ and 1 lượng of gold;
  - the cassette radio with a battery and 2 spare batteries;
  - 10 incense sticks;
  - a styrofoam cooler, 2 bags of tube ice and a block of ice;
  - a mini gas stove and a pot, mì gói, khô bò, bánh mì thịt, 2 canteens of clean water;
  - a ná thun with 40 bi sắt, a nỏ with 20 tên tre;
  - an điếu cày with thuốc lào;
  - bandages;
  - a jerrycan with 5 L of gasoline.

### 3.2 The playtest remote

Activate the remote (`a`, then pick it, or `Enter` and use) to open a menu.

| Menu | Option | What it does |
|---|---|---|
| Teleport to the nearest… | chợ, chợ tạm, đình, chùa, district police HQ, ward police post, army post, bia hơi, lò nước đá (ice works), nhà trọ, hẻm block, kênh, Chợ Bến Thành, Ga Sài Gòn, hospital | Jumps to the middle of the nearest such map square on the ground floor. It reveals the area around it. Only map that has already been generated is searched (on Vietmap, roughly the overmaps around you). If there is none, you get a message and stay put. Vietmap draws its landmarks from a pool, so a world may lack Bến Thành or the station. |
| Time… | Skip 1 hour / 1 day / 7 days | Moves the clock forward and rechecks the weather. Nothing is simulated in between, the same as Debug > Map… > Change time. |
| Time… | Jump to a wet-season afternoon | Jumps to early July (wet season) at about 14:00, the time when rain is most likely. |
| Spawn a test vehicle… | xe số, xích lô, xe đạp điện, ba gác máy, xe cứu thương | Puts an undamaged vehicle with a full tank in the middle of the nearest road square, and puts you 4 tiles north of it. |
| Spawn a test vehicle… | ghe máy, xà lan | Puts the boat on the nearest river (or lake: the real map's rivers) and puts you on it. If the game does not treat you as aboard, step off and back on. |
| Player… | Heal fully | Heals all body parts. Removes bleeding, bites, infection, poison, stun and pain. Resets thirst, tiredness and stamina, and tops up the stomach. |
| Player… | Protection on/off | Toggles the effect "Playtest protection": incoming damage is cancelled and you heal fast. Turn it off for combat checks. |
| Player… | Give the playtest kit again | The kit (with a new remote) appears in your hands or at your feet. |
| World… | Reveal the map around me | Reveals the overmap within 30 tiles. |
| World… | Kill all monsters within 30 tiles | Kills every monster on your level within 30 tiles, including pets. |
| World… | Spawn 3 zombies nearby | Spawns 3 monsters from the city's zombie group, 4 to 8 tiles away. |
| World… | Flood the streets now / Drain the flood now | Runs the mod's flood (or drain) transform around you, whatever the weather. |

**Not in the remote**, because the engine's effect_on_condition system cannot do it from JSON:

| Wanted | Why not | Use instead |
|---|---|---|
| Make it rain | Weather is recomputed from the weather generator at each change. EOCs can only ask for a recheck (`next_weather`); they cannot set the weather type. | Debug > Map… > Change weather (`rain`, `thunder`). Remote > Time > Jump to a wet-season afternoon makes rain likely by itself. |
| Spawn a vehicle on your own tile or facing a direction you choose | `mapgen_update` places vehicles at fixed spots inside a map square, not next to the player. | Debug > Spawning… > Spawn a vehicle (spawns next to you). |
| Teleport to an exact spot, or to places not generated yet | Searches only cover generated map. | Debug > Teleport… > Teleport - long range. |
| Spawn any item or monster by name | It would need one menu entry per id. | Debug > Spawning… > Spawn an item / Spawn monster. |

---

## 4. Checklist

### A. Launch, screen and mouse

| ID | Do | Pass looks like | Fast way |
|---|---|---|---|
| PT-01 | Launch with `tools/saigon/play_saigon.sh`. | The tiles window opens. The main menu works. No error popup. | — |
| PT-02 | Create World with the defaults. | Mods tab shows dda and Sài Gòn 2000s already selected. The playtest mod is listed under Misc. | — |
| PT-03 | Start any game and look at the map. | Saigon sprites appear: shophouses, red stools, teal shutters. There are no question-mark tiles and no American shop signs. | — |
| PT-04 | Click a tile a few steps away (mouse travel), then hover over tiles. | You walk to the tile you clicked. The hover cursor sits on the tile under the mouse (the A1 HiDPI fix). | — |
| PT-05 | Open the overmap (`m`) and zoom in and out. | The overmap shows Saigon symbols and landmark pictures (Larwick style). Nothing is drawn in the wrong place. | Remote > World > Reveal |
| PT-06 | Use the sidebar and the message log during a busy scene. | Vietnamese text (ă, ơ, ư, đ, tones) shows correctly in names, messages and menus. | — |

### B. Scenarios and starts

| ID | Do | Pass looks like | Fast way |
|---|---|---|---|
| PT-10 | New Game in PT Vietmap. Look at the scenario list. | Only the two Saigon scenarios are offered. "Somewhere in Nam" lists 3 starts; its description reads well. | — |
| PT-11 | Look at the profession list. | The 12 Saigon professions (and Playtester, with the cheat mod) are listed. There are no US professions. Hobbies have no baseball, golf or similar. | — |
| PT-12 | Start: Nhà ống. | You start inside a shophouse at ground level, at 6:00 on the morning of day 6 (about 4 days after the outbreak). A wake-up popup fits the start. About 5 minutes later, a loa phường broadcast is heard across the rooftops. | — |
| PT-13 | Start: Nhà ống, iron gate pulled shut. | As PT-12, but the cửa sắt kéo at the front is closed. | — |
| PT-14 | Start: Chợ. | You start at a stall in a wet market. The wake-up popup is the chợ one. | — |
| PT-15 | 2009 world: Hẻm. | You start in a home deep in hẻm alleys. The map around you is the real city: check with `m`, the river and District 1 should be where they belong. | — |
| PT-16 | 2009 world: Ga Sài Gòn. | You start in the station hall. The popup is the station one. | — |
| PT-17 | 2009 world: Tân Sơn Nhất. | You start in the departures hall, with its own popup. Runways and aprons are around it. | — |
| PT-18 | 2009 world: Nhà ống, gate shut, Chợ. | Same as PT-12 to PT-14 on the real map. About 40 map squares around the start are already visible. | — |
| PT-19 | Look at your starting kit with a real profession (`i`). | Kit items are Saigon items (đồng, not dollars). The clothing fits the job. Note in the report if the character has no usable weapon (see [DIFFICULTY.md](DIFFICULTY.md)). | — |

### C. Weather, heat and floods

| ID | Do | Pass looks like | Fast way |
|---|---|---|---|
| PT-20 | Wait a few hours outdoors in the dry-season start (`|` or `5`, or wait from the `Esc` menu). | Warm days (about 25-33 °C), no snow and no cold. Dry: rain is rare. | Remote > Time > Skip 1 day |
| PT-21 | Jump to the wet season and wait through an afternoon. | Afternoon rain or thunderstorms come often. | Remote > Time > Jump to a wet-season afternoon; then Debug > Map… > Change weather > `rain` |
| PT-22 | In the wet season, during heavy rain (rain or thunder), stand on a street for 20-40 minutes. | The message "Brown water is rising in the street…" appears once. Roads and alleys turn into flooded road and alley tiles; sidewalks are patchy. | Remote > World > Flood the streets now |
| PT-23 | Walk through the flood. | You can wade: it is slower (move cost 3-4), and you are not swimming. Vehicles still drive on flooded road. | — |
| PT-24 | Let the rain stop and wait 1-2 hours. | "The floodwater is draining away…" appears. The streets return to pavement, sidewalk and concrete alley. | Remote > World > Drain the flood now |
| PT-25 | Wear the áo mưa cánh dơi and the ủng cao su in rain and flood. | Rain wets you less. Feet stay dry in shallow flood. | — |
| PT-26 | Flood on the upper floor of a building. | Known limit: floods only act on your own level. Report anything else that looks wrong. | — |

### D. Food, cooking and ice

| ID | Do | Pass looks like | Fast way |
|---|---|---|---|
| PT-30 | Look at food in a chợ, street carts and kitchens. | Vietnamese street food, fruit and drinks (phở, bánh mì, cơm tấm, bún bò Huế, chè, mì gói, sầu riêng…). Names and descriptions read well. | Remote > Teleport > Chợ |
| PT-31 | Eat a few dishes and drink a few drinks. | Hunger and thirst go down. Morale effects make sense. Nothing is described as "imported" or American. | — |
| PT-32 | Hold a bag of tube ice and a block of ice, and wait. | Tube ice turns into clean water after about 4 hours, block ice into untreated water after about 10. Known limit: the cooler does not slow melting. | Remote > Time > Skip 1 hour (repeat) |
| PT-33 | Craft cà phê sữa đá or trà đá (`&`, search). | The recipe asks for ice, and the drink is made. Report any iced drink that does not need ice (an old recipe). | — |
| PT-34 | Cook with the mini gas stove (or a than tổ ong stove). | Cooking recipes for southern food show up and work. | — |
| PT-35 | Find an ice works (lò nước đá). | Block and tube ice (still melting on its timer) and hardware. A worker NPC may be there. It looks like an ice works. | Remote > Teleport > Lò nước đá |

### E. The city speaks: loudspeaker, radio, altars, intro

| ID | Do | Pass looks like | Fast way |
|---|---|---|---|
| PT-40 | Find a loa phường (a ward loudspeaker on a pole: on streets, on some shophouse rows, at the ward office) and examine it. | A popup with the ward's recorded notice (days 4-7). The sound carries far and draws nearby zombies. | — |
| PT-41 | Stand within about 18 tiles of a loa phường at 6:00 or 17:00. | A scheduled broadcast plays by itself: "A loa phường nearby crackles to life at its hour". Zombies come. | Remote > Time > Skip 1 hour, waiting near a pole |
| PT-42 | Examine the loudspeaker on day 8+ and day 15+, then day 30+. | Day 8-14: live evacuation calls. Day 15-29: a stretched looping tape. Day 30+: silence. | Remote > Time > Skip 7 days |
| PT-43 | Use the cassette radio: "Tune the radio". | Days 0-9: the city station. Days 10-20: emergency broadcasts. Days 21-44: survivors' voices. Later: static. Each use costs one battery charge (also when you cancel). | Remote > Time > Skip 7 days |
| PT-44 | Use the cassette radio: "Play the tape". | A tape plays (flavour text and morale). | — |
| PT-45 | Examine a home altar (bàn thờ) with incense and a lighter. | Flavour text. Lighting a stick gives a small morale bonus, at most once per 12 hours. Without a lighter you get "nothing to light it with". | Kit has incense and lighter |
| PT-46 | The same at a Thần Tài altar in a shop. | Its own text and morale ("Lit incense for Thần Tài"). | — |
| PT-47 | Read newspapers, ward notices and handwritten notes. | Snippets about the outbreak that fit the date and place. | — |

### F. Vehicles

| ID | Do | Pass looks like | Fast way |
|---|---|---|---|
| PT-50 | Find a parked xe số (underbone) or xe tay ga in the street, and drive it (`^`, or examine the controls). | It starts, it is fast and nimble, and it fits through a hẻm. Fuel use is plausible. | Remote > Vehicle > Xe số |
| PT-51 | Pedal a xích lô. | It moves with muscle power. The two front wheels and the seat in front work. This vehicle has not been driven before. | Remote > Vehicle > Xích lô |
| PT-52 | Ride a xe đạp điện (e-bike). | It runs on its battery, and you can pedal it when the battery is empty. | Remote > Vehicle > Xe đạp điện |
| PT-53 | Drive a ba gác máy (motor cart) with a load. | It is slow and strong. It is 3 tiles wide, so it fits streets but not hẻm. | Remote > Vehicle > Ba gác máy |
| PT-54 | Drive the xe cứu thương (ambulance). | It drives like a van. Medical parts work. | Remote > Vehicle > Xe cứu thương |
| PT-55 | Take the ghe máy (motor boat) on the river or a kênh. | It floats. The long-tail engine moves it, and its battery charges. It steers on the river. | Remote > Vehicle > Ghe máy |
| PT-56 | Take the xà lan (barge). | It floats and moves (slowly). Nothing breaks on spawn. | Remote > Vehicle > Xà lan |
| PT-57 | Look at street traffic in a few places. | Wrecked and parked vehicles are mostly two-wheelers (about 9 in 10), with the odd taxi, bus or truck. There are no American pickups or police cruisers. | Remote > World > Reveal, walk a main street |
| PT-58 | Try the moored xuồng and ghe on a kênh. | Small boats with oars or a long-tail engine; they float. | Remote > Teleport > Kênh |

### G. Places

| ID | Do | Pass looks like | Fast way |
|---|---|---|---|
| PT-60 | Walk a nhà ống row, all floors to the roof. | Narrow, deep shophouses with stairs paired between floors. There is a business at street level (barber, tailor, tiệm vàng, quán net, karaoke, bakery…), and an altar, kitchen and bedrooms above. Rooftops connect. | start there |
| PT-61 | Walk a hẻm block. | A maze of alleys, every one reachable from the street. Homes open onto the hẻm. | Remote > Teleport > Hẻm |
| PT-62 | Visit a chợ (2×2 market). | Stalls with produce, meat, fish, cloth and dry goods under a roof. Traders may be present. The roof is intact. | Remote > Teleport > Chợ |
| PT-63 | Visit a đình (communal house). | A communal hall with altars, incense and a courtyard. A caretaker and an elder may be there; talk to them. | Remote > Teleport > Đình |
| PT-64 | Visit a bia hơi. | Stools and tables on the pavement, beer, nhậu snacks and ice. A vendor NPC may be there. | Remote > Teleport > Bia hơi |
| PT-65 | Visit a district police HQ (trụ sở công an quận). | Holding cells, lockers and a **locked** armory of gun safes. Police zombies are about, some dormant in the cells. You need tools or a key to get into the safes. | Remote > Teleport > Police HQ |
| PT-66 | Visit a ward police post (công an phường). | An office, a desk and a cell. **No guns**, except what a guard NPC carries. | Remote > Teleport > Ward police post |
| PT-67 | Visit an army post (đồn quân sự). | A walled compound with a sandbagged gate post, barracks, a locked armory and a truck. Soldier zombies are present. | Remote > Teleport > Army post |
| PT-68 | Visit the other everyday places: chợ tạm, nhà trọ, cà phê võng, hớt tóc, điện thoại công cộng, giữ xe, trạm xe buýt, nhà thờ họ, lò nước đá. | Each one looks like what it is. Doors are reachable and the inside is roofed. | Remote > Teleport (some), or explore |
| PT-69 | Visit landmarks: Chợ Bến Thành, Ga Sài Gòn, Nhà thờ Đức Bà, Bưu điện, Dinh Độc Lập, Chợ Bình Tây, chùa Ngọc Hoàng (2009 map: all of them; Vietmap: whichever the world has). | Recognisable buildings with sprites on the overmap. You can move through every floor. NPC staff are present in some. | Remote > Teleport > Bến Thành / Ga |
| PT-70 | Visit a hospital, a Co.op-style supermarket, a petrol station and a cemetery. | They look right. The petrol pumps hold gasoline. | Remote > Teleport > Hospital |

### H. NPCs

| ID | Do | Pass looks like | Fast way |
|---|---|---|---|
| PT-75 | Meet random NPCs. | Vietnamese names (often with a nickname like "(Tư)"), with an odd foreigner about 3 % of the time. Saigon clothes. No firearms, except the công an guard. | Debug > Spawning… > Spawn NPC |
| PT-76 | Talk to place staff: monk, postal clerk, doctor, shopkeeper, đình keeper. | Each has something to say. Nobody ends the talk at once. | Remote > Teleport > Đình / Hospital |
| PT-77 | Trade with a chợ trader or the petrol attendant. | The trade screen opens. Prices are in đồng and gold. Your đồng notes and gold are accepted. The trader has stock and money. | Remote > Teleport > Chợ |
| PT-78 | Ask the NPC at your start for a job. | One of: oral rehydration salts for a sick child, bún bò Huế for the third floor, or "survive seven days and come back". Do one to the end; the reward arrives. | — |
| PT-79 | Do two more missions from any NPC (gold for the tiệm vàng, the ward notice, the zombie xe ôm, the grandmother's notebook…). | Targets appear on the map. Completing a mission is recognised. Text reads well. | Remote > Teleport to the target, Time skips |
| PT-80 | Start a three-step chain: the ward police (Đồng chí → Đại ca → Thằng Lộc), the hospital (Kháng sinh → Nhà thuốc → Ngọc Anh), or the chợ (Can nước → Gạo lên chùa → Chú Sáu). | Each step leads to the next. The last step gives you a companion who follows you. | Remote > Teleport > Ward police post / Hospital / Chợ |
| PT-81 | With a companion, give orders, fight, and ask them to guard a spot. | The companion follows orders and guards the spot. They do not pull out a gun they should not have. | — |
| PT-82 | Meet a gang (giang hồ row) or looters (broken nhà thuốc). | They are hostile and use melee only. | — |

### I. Zombies, hordes and encounters

| ID | Do | Pass looks like | Fast way |
|---|---|---|---|
| PT-85 | Look at the zombies you meet (`x` to look). | Saigon zombies: porter, schoolchild, rain-soaked, canal bloater, IV-pole patient, hard-hat, xe ôm with a helmet, market worker, police and soldier. Descriptions read well. | Remote > World > Spawn 3 zombies |
| PT-86 | Kill a few and look at what they drop. | Saigon clothes, đồng wallets, lighters, phones, vé số. Guns are very rare (police and army dead only). | — |
| PT-87 | Make noise (loudspeaker, gunshot) and watch for hordes. | Hordes move toward the sound. They are not a wall of zombies at the start. | Debug > Info… > Display hordes |
| PT-88 | Travel along roads outside the city. | Roadside encounters (crashed vehicles, abandoned checkpoints…) appear now and then, and look Saigon. | Remote > World > Reveal |
| PT-89 | Wait a few weeks. | Zombies evolve into the mod's later forms. Nothing is American. | Remote > Time > Skip 7 days |

### J. Weapons

| ID | Do | Pass looks like | Fast way |
|---|---|---|---|
| PT-90 | Fight with street weapons: dao phay, mã tấu, cuốc, đòn gánh, gậy tre, a U-lock. | They work as melee weapons with plausible damage. | Kit has a dao phay; Debug > Spawn an item |
| PT-91 | Smoke the điếu cày with thuốc lào. It is also a club. | Smoking works (morale and nicotine). As a melee weapon it bashes a little. | Kit |
| PT-92 | Shoot the ná thun with bi sắt and bi ve. | Loads, fires, can hit, ammo can be picked back up. | Kit |
| PT-93 | Shoot the nỏ with tên tre. | Loads, fires; bolts often survive, some break. | Kit |
| PT-94 | Look for firearms in homes, shops and on civilians. | **None.** Report any firearm found outside police and army sites, or on a civilian, as a bug. | — |
| PT-95 | Open the police HQ armory and an army post armory. | Period police and army firearms with their magazines and ammunition. Ammunition is named by cartridge (no "Makarov"). | Remote > Teleport > Police HQ / Army post |

### K. Books and reading

| ID | Do | Pass looks like | Fast way |
|---|---|---|---|
| PT-96 | Read skill books (motorbike repair, southern cooking, nursing, tailoring, fishing, TV repair, construction). | They train the skill. Cooking and repair books teach recipes. | Debug > Spawn an item `sgn_book_` |
| PT-97 | Read fiction and media: wuxia novels, the sutra, the almanac, the karaoke songbook, the comic, lịch bloc pages. | Morale or text that fits. No American books in Saigon loot. | — |

### L. Saving and loading

| ID | Do | Pass looks like | Fast way |
|---|---|---|---|
| PT-98 | Save (`S`), quit to the menu, and load again. Do it once in each world. | The game loads to the same place and time, with the same items, vehicles and companions. No error popup. | — |
| PT-99 | Save in a flood, on a boat, and with an active mission, then load. | The flood tiles, the boat and the mission are all still there. | — |
| PT-100 | After a few hours of play, quit and reopen the game, then load. | It loads in about the same time as before. No error lines in `config/debug.log` (check with `grep -E "ERROR\|WARNING" config/debug.log`). | — |

### M. Difficulty and feel (Real feel world, no cheats)

| ID | Do | Pass looks like |
|---|---|---|
| PT-101 | Play one character for an hour of real time with a real profession. | You survive the first day if you play carefully. Note what killed you, and when. |
| PT-102 | Note anything that felt wrong for Saigon in 2004/2009. | Free text. These become content units. |

### N. The playtest mod itself

| ID | Do | Pass looks like |
|---|---|---|
| PT-110 | Use every remote option once. | Each option does what section 3.2 says, or prints a clear message when it cannot. |
| PT-111 | Turn protection on, and let zombies hit you. Then turn it off. | No damage while it is on. Normal damage again once it is off. |

---

## 5. When something goes wrong

1. Take a screenshot (1.3).
2. Note the time on the in-game clock and what you did just before.
3. If the game shows an error popup, copy its text, or take a screenshot of it, before you press a key.
4. Save if you can, then run `tools/saigon/collect_bug_report.sh -w "<world>" -t PT-xx` (1.4).
5. Write the report from the template in [BUG_REPORT.md](BUG_REPORT.md), in
   `doc/saigon/playtest/PT-xx_short-name.md`, and add a row to the index in
   [playtest/README.md](playtest/README.md).

If the game crashes, run the collect script **before** you relaunch. Each launch starts a new
`config/debug.log` and keeps only one older log, as `config/debug.log.prev`. The script collects
both, so one relaunch is still safe; two are not.
