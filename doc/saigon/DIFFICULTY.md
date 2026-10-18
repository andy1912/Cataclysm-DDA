# Difficulty assessment — sgn_saigon_2004/2009

Written 2026-10-18 after the playtester reported the game is too hard. Every number below
was read out of the game's own code and JSON; none is estimated from memory.

## Where the fear of "too many zombies" is wrong

The obvious suspect is the monster count, and the arithmetic does not support it.

| | dda default | sgn_city | delta |
|---|---|---|---|
| `city_size` | 8 | 12 | 1.5x |
| `desired_zombies` = size x 80 x 1.0 | 640 | 960 | 1.5x |
| placement radius = size x 1.5 | 12 OMT | 18 OMT | 1.5x |
| **zombies per OMT** | **1.41** | **0.94** | **-33%** |

(`src/overmap.cpp:3474`, `SPAWN_CITY_HORDE_SCALAR`=80, `SPAWN_CITY_HORDE_SPREAD`=1.5,
`SPAWN_DENSITY`=1.0 from `data/core/external_options.json`.)

The mod's horde layer is **sparser per tile than vanilla** because the spread scales with
city size. Monster speed is also at baseline: `mon_zombie` 70, `sgn_mon_zombie_sot` 70,
`sgn_mon_zombie_xe_om` 70, `sgn_mon_zombie_vendor` 55. Only the schoolchild variant
(`sgn_mon_zombie_hoc_sinh`, speed 95) is quicker, at 3.6% of awake-group weight.

**Do not tune `city_size` or the SPAWN_* options. It will not fix this.**

## What is actually making it hard

### 1. The start. Unarmed, in armourless clothes. (dominant)
`professions/professions.json`, field `items.both.entries`:

| weapon | professions |
|---|---|
| none at all | `sgn_survivor`, `sgn_xe_om`, `sgn_market_trader`, `sgn_student`, `sgn_nurse`, `sgn_monk`, `sgn_veteran` (walking cane) |
| improvised melee | `sgn_street_vendor` (cleaver), `sgn_cong_an` (baton), `sgn_construction` (hammer), `sgn_fisherman` (folding knife), `sgn_mechanic` (wrench) |

**7 of 12 professions start with no usable weapon.** Armoured: only `sgn_cong_an`
(`sgn_non_bao_hiem`, a bulletproof vest) and `sgn_construction` (steel boots, work
gloves). Everyone else: tshirt, pants, sandals.

This compounds with a deliberate, documented design rule — *2009 Saigon civilians carry
no firearms* — so there is no gun to find early and nothing to buy one with.

### 2. The clock starts 4 days late
`scenario/scenarios.json`: `start_of_cataclysm` year 1 day 1 hour 22;
`start_of_game` **year 1 day 6 hour 6**. That is **4 days 8 hours** of elapsed collapse
before the player gains control. `CONTENT_BIBLE.md` says the intent is "the player starts
in the first days of the collapse" — day 6 is the far end of the first week.

### 3. A second zombie layer on top of the hordes
`tools/saigon/gen_saigon_landmarks.py`, `MONSTERS`, applied per map tile: `sgn_GROUP_SAIGON_AWAKE`
chance 35, `sgn_GROUP_ZOMBIE_DORMANT` chance 40 repeat [1,3]. Mean **~1.15 zombies per
map tile** — a 4x4 park is ~18 zombies on top of the horde layer. Players spend their time
in landmarks, so this is where they meet them.

### 4. No escape route (2004 scenario)
`sgn_city` has `is_megacity: true`, `city_spacing: 1` — the whole overmap is one continuous
city. There is no countryside to fall back to. (The 2009 real-map scenario does have one:
`sgn_saigon_delta`, city_size 3, spacing 5.)

### 5. Gold is dead
All 10 `MISSION_SGN_*` have `value: 0` and `has_generic_rewards: false`. Two of nineteen
staff templates are `SHOPKEEP`. So a player who loots gold cannot convert it into a knife
through the mission system, which locks lever 1 in place.

### 6. Year-round heat
`region/weather.json`: `base_temperature` 27.5 C, monthly 25.9-29.2, water 27-30. No
cold-season relief from the bible's own "heat stress and thirst matter more than cold".

## Triage (Jev `jev-1.13.0`, calibrated, evidence = the measurements above)

- **Difficulty now: 5.9 / 10**, confidence 0.70. 66% probability of landing at 6-7
  ("very hard… most die in days" through to "brutal… likely die within hours").
- **Dominant lever: unarmed start, p=0.67.** Elapsed time 0.06, landmark monsters 0.09,
  escape valve 0.04, heat 0.01, horde count 0.00. Note `unarmed_start` was second in the
  option list, so this is not simple first-position bias.
- **Whether three fixes alone suffice: p=0.50.** Genuinely uncertain. Treat a difficulty
  pass as something to measure and re-run, not a one-shot.
- **Whether day 6 contradicts the written intent: p=0.35.** Jev is not persuaded it is a
  clear contradiction of "the first days". I think it is still wrong on the player's
  behalf, but it is a judgement call, not a demonstrated defect.

## Proposed pass, in leverage order

1. **Every profession starts able to fight back.** A melee weapon for all 12: keep the
   thematic ones, and give the bare-handed ones something period-correct — a `nắm` (kitchen
   knife), a `gậy` (bamboo stick), the monk's `côn`, the veteran's `cane` as a blunt.
   Cost: one file, ~30 min. Biggest measured effect.
2. **Start armour on everyone**: at minimum `sgn_ao_khoac` / `sgn_quan_tay` and something on
   the feet instead of sandals. Cost: same file.
3. **Move the start to day 1-2.** `start_of_game` day 6 hour 6 → day 2 hour 6. Cost: one line.
4. **Restore an escape route** for the 2004 scenario: non-megacity, or lower city_size/spacing,
   so the delta is reachable. Cost: one region setting. Touches the A2 megacity perf work —
   check `doc/saigon/PERF.md` before changing `is_megacity`.
5. **Landmark monster layer**: drop `sgn_GROUP_SAIGON_AWAKE` chance 35 → 20 and
   `ZOMBIE_DORMANT` repeat [1,3] → [1,2]. Cost: two numbers.
6. **Make gold spendable**: give missions a small `value`, or flip the vendor and petrol
   attendant templates to `SHOPKEEP` so a market can actually sell to you. Cost: small.

Items 1-3 are cheap and evidence-backed. 4 needs care because megacity was a deliberate
perf decision. 5 and 6 are optional and I would hold them until after 1-3 are retested.

## Method

Re-test by running the suite plus one real new game. If the playtester still dies early,
the next lever is 4/5, not more professions — do not raise zombie counts, they are already
below vanilla.