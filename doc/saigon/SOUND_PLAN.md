# Sound plan: a Saigon soundtrack and sound effects

Written 2026-10-19 after the playtester found the game silent. It records why the game is
silent, what the base soundpack contains, how the engine picks sounds, and what a Saigon
soundpack needs.

## Why the game is silent

1. **Every build so far used `SOUND=0`.** SDL3_mixer was not installed. It is now installed:
   `SDL3_mixer.framework` 3.2.4 is in `~/Library/Frameworks`, from the official
   `SDL3_mixer-3.2.4.dmg` (libsdl-org/SDL_mixer, release-3.2.4, sha256 `78a12346…69ac`).
2. **The Makefile's macOS framework path does not add SDL3_mixer.** Its `SOUND=1` block asks
   pkg-config for `sdl3-mixer`. A local shim at
   `~/code/cdda-saigon-logs/tools/pkgconfig/sdl3-mixer.pc` answers that without editing the
   Makefile, which is an upstream file. The shim also passes `-Wno-error=old-style-cast`: SDL's
   `SDL_AUDIO_DEVICE_DEFAULT_PLAYBACK` macro is a C cast, and the FRAMEWORK build includes SDL as a
   user header, so `-Werror -Wold-style-cast` stopped `sound_backend_sdl3.cpp`. Switching from
   `SOUND=0` to `SOUND=1` also needs the objects that test `SDL_SOUND` deleted first (make does
   not track flags): every `obj/tiles/*.o` whose source includes `sdlsound.h`, `sound_backend.h`
   or `sounds.h`, plus `obj/tiles/pch`. Build command:

       GLSLANG=~/code/cdda-saigon-logs/tools/glslang/bin/glslang \
       PKG_CONFIG_PATH=~/code/cdda-saigon-logs/tools/pkgconfig \
       make -j2 TILES=1 FRAMEWORK=1 RELEASE=1 LOCALIZE=0 SOUND=1 BUILD_SHADER_FORMATS=spv cataclysm-tiles

3. **Only a test pack ships with the repo.** `data/sound/Menu_Sound_Test` has two menu beeps and
   an empty playlist. CC-Sounds (Fris0uman/CDDA-Soundpacks, release 2025-11-15, CC-BY-SA-4.0,
   138 MB, sha256 `adf73063…f2ee`) is downloaded and unpacked in
   `~/code/cdda-saigon-logs/downloads/cc_sounds/unz/CC-Sounds`. The game finds user soundpacks in
   `<userdir>/sound/`; `play_saigon.sh` runs with the repo root as the userdir, and `/sound/` is
   gitignored, so `./sound/CC-Sounds` is the place.

## What CC-Sounds contains

- 459 ogg files in 33 effect ids with 1,702 variants, plus one playlist.
- **Music:** one playlist, `title`, of 62 CO.AG tracks (dark ambient, CC-BY-SA-4.0).
- **Effects with the most files:** smash_fail 2252, smash_success 1024, speech 656, fire_gun 473,
  plmove 375, reload 165.
- **environment** (ambience), 29 variants:
  - WEATHER_CLEAR, WEATHER_CLOUDY and WEATHER_SUNNY, each per season;
  - drizzle, rainy, rainstorm, thunder, thunder_far and thunder_near;
  - snow, snowstorm and flurries;
  - indoors, indoors_rain, nighttime and underground;
  - alarm, church_bells and police_siren.
- **Engines:** `combustion`, `electric` and `engine_v8` only. **vehicle:** car_alarm, gear_shift,
  horn_medium and rear_beeper.
- **speech:** 83 variants, all dda monster ids (zombies, ferals). **radio:** static and inaudible_chatter.

## How the engine chooses a sound (and what that means for the mod)

- **Music plays in only four situations**, the `music_id` values in `src/music.h`:
  - `title`, the main menu;
  - `mp3`, a music player item in use;
  - `instrument`, playing an instrument;
  - `sound`, set from `sounds.cpp`.

  CDDA has no background score during play. A Saigon soundtrack therefore means:
  - a `title` playlist;
  - an `mp3` playlist, heard when the player uses a music player. The mod's cassette radio
    could become one: it would need the MP3 use action, which is in addition to its V3 EOC
    radio.
  - instrument tunes, if the mod adds instruments such as a đàn bầu, đàn tranh or guitar.
- **Ambience is the "environment" id.** Its variant is chosen by weather and season, indoors or
  out, day or night, and underground. Saigon's character fits here: rain on tin roofs, cicadas
  in the dry season, geckos at night, distant traffic. Seasons use the game's four; the
  mod's monsoon is expressed through weather, which suits the WEATHER_* variants.
- **Fallbacks:**
  - A missing variant falls back to `default` (`find_random_effect`, `src/sdlsound.cpp:637`).
  - Engines fall back to `combustion` (`src/sounds.cpp:950`).
  - Guns fall back to `fire_gun` `default` (`src/sounds.cpp:1382`).

  So every `sgn_` engine, gun and zombie already makes a generic sound; nothing is silent once
  a pack is installed. A Saigon pack adds variants named by the mod's ids, for example
  `engine_working_internal` / `sgn_engine_110cc` or `speech` / `sgn_mon_zombie_xe_om`.

## What a Saigon soundpack needs

The pack is a separate soundpack (`sound/Saigon/`). It starts from CC-Sounds and adds or
overrides; CC-BY-SA requires the result to stay CC-BY-SA with credits. Units, in order of what
the player hears most:

1. **SND1 Street ambience** (environment):
   - day traffic of motorbikes, horns and vendors' calls (rao);
   - night with geckos (tắc kè), dogs and a distant karaoke;
   - rain on tôn roofs (indoors_rain), monsoon downpour (WEATHER_RAINSTORM);
   - dry-season cicadas;
   - the chợ crowd.
2. **SND2 Vehicles:** small-engine variants for the 50/100/110/125 cc engines, the tay ga, the
   xe lam's two-stroke, the long-tail and outboard; a motorbike horn (the review's open
   horn nit; needs a horn part too).
3. **SND3 Voices of the city:**
   - the loa phường (a PA voice behind a crackle) and the cassette radio's stations, keyed to
     the V3 phases if the engine can be told which;
   - temple bells, the mõ (wooden fish) and church bells;
   - zombie `speech` variants for the sgn_ zombies.
4. **SND4 Soundtrack:**
   - a `title` playlist, and an `mp3` playlist for the cassette radio;
   - in the mod's world, the cassette plays the 2000s Saigon sound: bolero, nhạc vàng, cải
     lương, V-pop and Hoa ballads, and the radio plays news jingles.
5. **SND5 Weapons:** variants for the five period firearms, the ná and the nỏ (twang, release).

## Sourcing rules (no exceptions)

- **Only audio we may redistribute:**
  - our own recordings or compositions;
  - CC0 or CC-BY / CC-BY-SA (for example freesound.org, with each licence checked per file);
  - public-domain recordings.

  Record the licence and source of every file in the pack's `credits.md`.
- **Traditional melodies may be public domain, but recordings are not.** Most bolero, nhạc
  vàng and V-pop songs are copyrighted (Vietnam: life + 50 years). Use new performances of
  traditional or folk tunes, or commission originals in the style. Never rip from YouTube,
  CDs or radio.
- No trademarks: no real radio jingles or brand slogans.
- Downloads need the user's OK each time: file, source and size.

## Status

- SDL3_mixer is installed. CC-Sounds is downloaded and analysed.
- Not done yet, both waiting for the user's go-ahead:
  - copying CC-Sounds into `./sound/`;
  - building `cataclysm-tiles` with `SOUND=1`.
