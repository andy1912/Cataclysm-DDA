# Cataclysm Saigon

A zombie-survival roguelike set in Saigon in the 2000s. It is a standalone game built on
Cataclysm: Dark Days Ahead (CDDA): shophouses and alleys, wet markets, xe ôm and xích lô, the
monsoon, the ward loudspeakers, and a strange fever that did not stay in the hospitals.

## Two ways to play

- **Somewhere in Nam:** a generated Saigon-like city. Each new world is different, with real
  Saigon landmarks scattered through it.
- **Saigon 2009:** the real city, street by street, built from OpenStreetMap data as it stood
  in late 2009: the river, the canals, the bridges, the landmarks and the districts.

## Install

| System | Download | How to start |
|---|---|---|
| macOS (Apple Silicon and Intel) | `CataclysmSaigon-<version>-macos.dmg` | Open the dmg and drag **Cataclysm** to Applications. The first time, right-click the app and choose **Open**, because the app is not notarised. |
| Windows 10/11 (64-bit) | `CataclysmSaigon-<version>-windows-x64.zip` | Unzip anywhere and run `cataclysm-tiles.exe`. If SmartScreen warns, choose **More info → Run anyway**. |
| Linux (64-bit) | `CataclysmSaigon-<version>-linux-x64.tar.gz` | Unpack and run `./cataclysm-launcher`. |

## First game

1. **New Game → Create World.** The Saigon mod (Sài Gòn 2000s) is already selected. Keep it.
2. Pick a scenario: **Somewhere in Nam** or **Saigon 2009**.
3. Pick a profession and a start location, then survive.

Graphics and sound are included: the UltimateCataclysm tileset with the Saigon sprites, and the
CC-Sounds soundpack. To switch tilesets or the soundpack, go to **Options → Graphics**.
The Saigon sprites only show with UltimateCataclysm.

## Saves and settings

- **macOS:** `~/Library/Application Support/Cataclysm/`
- **Windows and Linux:** next to the game, in `save/` and `config/`

To update, install the new version over the old one. Your saves stay where they are.

## Credits and licences

- **Game engine and base content:** Cataclysm: Dark Days Ahead by CleverRaven and contributors,
  CC-BY-SA 3.0 (see `LICENSE.txt`).
- **Saigon mod, maps and code changes:** this fork (andy1912/Cataclysm-DDA), under the same
  licence.
- **Map data:** © OpenStreetMap contributors, available under the Open Database Licence (ODbL).
  The Saigon 2009 map is derived from it.
- **Tilesets:** their authors, CC-BY-SA (see each tileset's folder in `gfx/`).
- **Sound:** CC-Sounds (Fris0uman/CDDA-Soundpacks), CC-BY-SA 4.0; music by CO.AG.
- **Libraries:** SDL3, SDL3_image, SDL3_ttf, SDL3_mixer and their codecs (see the `LICENSE-*.txt`
  files).

Real brands in the game are fictionalised. Places are real and people are not.

## Reporting a bug

Open an issue on https://github.com/andy1912/Cataclysm-DDA with what happened and what you
expected, and attach `config/debug.log`.
