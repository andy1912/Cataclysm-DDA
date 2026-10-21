# Building Cataclysm Saigon packages on your own machines

The GitHub workflow (`.github/workflows/saigon-release.yml`) is meant to build every platform. Until
it runs cleanly, you can build the same packages by hand on the machines you have. Each machine
builds a package for itself.

| Machine | Script | Output |
|---|---|---|
| Mac with Intel | `tools/saigon/package_macos.sh 0.1.0` | `CataclysmSaigon-0.1.0-macos-intel.dmg` |
| Mac with Apple Silicon | `tools/saigon/package_macos.sh 0.1.0` | `CataclysmSaigon-0.1.0-macos-apple-silicon.dmg` |
| Windows 10/11, 64-bit | `tools\saigon\package_windows.ps1 0.1.0` | `CataclysmSaigon-0.1.0-windows-x64.zip` |

Every package contains:
- the game with graphics and sound;
- every tileset in the repo, with the Saigon sprites;
- the CC-Sounds soundpack, if `sound/CC-Sounds` is present;
- both Saigon scenarios, with `dda` + `saigon_2000s` preselected for new worlds;
- the player README.

The playtest cheat mod is left out.

## Mac (Intel or Apple Silicon)

Do these steps once per Mac. Each download is from the official project page; check the version
numbers before you install.

1. **Apple's command line tools:** `xcode-select --install`
2. **Homebrew** (https://brew.sh), then: `brew install freetype pkg-config dylibbundler`
3. **SDL3 frameworks:** from the GitHub releases of libsdl-org (`SDL`, `SDL_image`, `SDL_ttf`,
   `SDL_mixer`), download the `.dmg` of each.
   - Versions: SDL3 3.4.x, SDL3_image 3.4.x, SDL3_ttf 3.2.x, SDL3_mixer 3.2.x.
   - Open each dmg and copy the `macos-arm64_x86_64/<name>.framework` folder (inside the
     `.xcframework`) into `~/Library/Frameworks/`.
4. **glslang** (shader compiler): https://github.com/KhronosGroup/glslang/releases. Put the
   `glslang` binary at `~/code/cdda-saigon-logs/tools/glslang/bin/glslang`, or set `GLSLANG=` to
   where it is.
5. **The SDL3_mixer pkg-config shim:** save this as
   `~/code/cdda-saigon-logs/tools/pkgconfig/sdl3-mixer.pc`:

   ```
   Name: SDL3_mixer
   Description: SDL3_mixer framework
   Version: 3.2.4
   Cflags: -F${HOME}/Library/Frameworks -Wno-error=old-style-cast
   Libs: -F${HOME}/Library/Frameworks -framework SDL3_mixer
   ```

   Write your real home path in place of `${HOME}`, because pkg-config does not expand it.
6. **Get the code** and, optionally, the soundpack:

   ```
   git clone https://github.com/andy1912/Cataclysm-DDA.git ~/code/cdda-saigon
   cd ~/code/cdda-saigon && git checkout saigon/pass1-vertical-slice
   ```

   For the soundpack, unpack CC-Sounds (https://github.com/Fris0uman/CDDA-Soundpacks/releases) into
   `sound/CC-Sounds`.
7. **Build and package:** `tools/saigon/package_macos.sh 0.1.0`
   - The first build takes 1–3 hours on a laptop.
   - The dmg is written to `~/code/cdda-saigon-logs/release/`.
   - Before signing, the script checks the finished app: it starts on its bundled libraries
     alone, nothing links outside it, and the curses build (if built) loads the Saigon mod from
     the app's data. The app is signed last and its signature verified.

**Notes**
- The app is signed ad hoc, not notarised, so players right-click → **Open** the first time.
- **Minimum macOS** is set by the oldest library inside. Homebrew's freetype is built for the Mac
  it is installed on, so an Intel build made on macOS 13 needs macOS 13 or newer.
- **Switching an existing build to sound:** `make` does not notice changed flags. If this checkout
  was built before with `SOUND=0`, first delete `obj/tiles/pch` and the `obj/tiles/*.o` files
  whose sources include `sdlsound.h`, `sound_backend.h` or `sounds.h`. The script refuses to
  package a binary without sound.

## Windows (64-bit)

1. **Visual Studio 2022** with the "Desktop development with C++" workload.
2. **vcpkg** at a path without spaces, for example `C:\dev\vcpkg`:

   ```
   git clone https://github.com/Microsoft/vcpkg.git C:\dev\vcpkg
   cd C:\dev\vcpkg
   git checkout f6672d8e480ccdecddfad3fd1b838ba369ffe6cd
   .\bootstrap-vcpkg.bat -disableMetrics
   .\vcpkg integrate install
   ```

   If CMake 4 is installed, use CMake 3.31 instead (see `doc/c++/COMPILING-VS-VCPKG.md`).
3. **Get the code:** clone it as on the Mac (Git for Windows), check out
   `saigon/pass1-vertical-slice`, and optionally unpack CC-Sounds into `sound\CC-Sounds`.
4. **Build:** open `msvc-full-features\Cataclysm-vcpkg-static.sln`, select **Release** and **x64**,
   then **Build → Build Solution**. The first build downloads and builds the libraries, which takes
   hours.
5. **Package** from the repo root in PowerShell:

   ```
   powershell -ExecutionPolicy Bypass -File tools\saigon\package_windows.ps1 0.1.0
   ```

   The zip is written next to the repo. Players unzip it and run `cataclysm-tiles.exe`.
   SmartScreen warns the first time (More info → Run anyway).

## Publishing

Attach the dmgs and the zip, with their `.sha256` files, to a GitHub Release on the fork by hand:
**Releases → Draft a new release**, tag `saigon-v0.1.0`. Nothing is uploaded by the scripts.
