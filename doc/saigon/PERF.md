# Turn-time measurements (I-B5perf)

Harness: `tests/saigon_perf_test.cpp`, a hidden test. It generates a Saigon overmap (megacity mode), then
puts the player in three places: a shophouse street, the Bến Thành downtown and a chợ. Each run is at
dusk in the wet season, in rain, with the player sealed in a concrete box so the run cannot end in death.
After 20 warm-up turns it times 300 whole game turns (`game::do_turn`: weather, fields, vehicles, map
caches, every monster's move). The test build has no tiles, so **rendering is not included**.
Machine: the 4-core MacBook Pro this fork is developed on.

```bash
tests/cata_test --mods=dda,saigon_2000s "[saigon_perf]"
```
```bash
SAIGON_PERF_WEATHER=clear tests/cata_test --mods=dda,saigon_2000s "[saigon_perf]"
```

## Results (2026-10-05)

Exit gate from integration §10.24 (tier a): p50 ≤ 40 ms with ≤ 100 awake monsters. **Passed with a wide
margin.** Monster counts vary between runs because the spawn rolls do.

| Site | Monsters in the bubble | p50 | p95 | Max (excluding the autosave) |
|---|---|---|---|---|
| Shophouse street | 53–260 | 3.2–21 ms | 5.6–30 ms | < 50 ms |
| Bến Thành downtown | 52–87 | 3.4–6.5 ms | 6–10 ms | < 45 ms |
| Chợ | 68–114 | 4.7–8.2 ms | 8–13 ms | < 50 ms |

Turn time grows roughly with the number of monsters (about 0.08 ms per monster). Even the worst run, with
260 monsters around a shophouse street, had a median of 21 ms. The macOS `sample` profile puts most of
an ordinary turn in `monmove()`.

## The one real stall: autosave

Every run has one turn of **4.2–5.0 s**. The profile shows it is `game::autosave()`, saving and
zstd-compressing the four overmaps that are loaded. With megacity off, the same autosave takes
**2.2 s**: megacity overmaps hold about three times as many buildings, so they take about twice as long to
compress.

Autosave is on by default (every 50 turns or 5 real minutes, whichever is longer), so in play this is a
pause of a few seconds about every 5 minutes. Options:

| Option | Effect | Cost |
|---|---|---|
| Leave it | 4–5 s pause every 5 real minutes | none |
| Players raise *Real minutes between autosaves* (Options → General) | rarer pauses | more progress lost on a crash |
| Engine: save only overmaps that changed since the last save | most autosaves skip the big overmaps entirely | a small C++ change in the fork (overmap dirty flag) |
| Engine: a faster zstd level for overmap saves | about 2–4× faster saves | slightly larger save files |
| Turn megacity off | 2.2 s pause | a sparser city |

## Engine change made for the harness

`game::do_turn()` called `gamemode->per_turn()` unconditionally. Tests that run turns without
`start_game()` have no game mode, and crashed there. It is now null-guarded (`src/do_turn.cpp`). A game
started normally always has a game mode, so nothing changes in play.
