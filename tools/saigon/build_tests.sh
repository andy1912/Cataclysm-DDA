#!/usr/bin/env bash
# Build tests/cata_test (curses, the suite's flags) under a lock, so several sessions sharing
# this tree never run two builds at once (8 GB machine: one make -j2 at a time).
#   tools/saigon/build_tests.sh            build cataclysm + tests
#   tools/saigon/build_tests.sh --check F  syntax-check one tests/*.cpp file only (no lock, no output)
set -u
cd "$(dirname "$0")/../.."

if [ "${1:-}" = "--check" ]; then
    f=$(basename "$2")
    cd tests
    exec clang++ -I. -I../src -isystem ../src/third-party -DNO_STALE_DATA_WARN -DRELEASE \
        -DZSTD_STATIC_LINKING_ONLY -DZSTD_DISABLE_ASM -DFMT_USE_LOCALE=0 -DMACOSX -DGIT_VERSION \
        -DBACKTRACE -DIMTUI -DCATCH_CONFIG_ENABLE_BENCHMARKING -D_XOPEN_SOURCE_EXTENDED -Os -Wodr \
        -Werror -Wall -Wextra -Wformat-signedness -Wlogical-op -Wmissing-declarations \
        -Wmissing-noreturn -Wpedantic -Wunused-macros -Wno-unknown-warning-option -Wredundant-decls \
        -g -fsigned-char -stdlib=libc++ -mmacosx-version-min=10.15 -std=c++17 -Wnon-virtual-dtor \
        -Wold-style-cast -Woverloaded-virtual -Wsuggest-override -Wzero-as-null-pointer-constant \
        -Wno-dangling-reference -Wno-c++20-compat -Wno-unknown-warning-option -fvisibility=hidden \
        -Wno-unused-variable -Wno-sign-compare -Wno-unknown-pragmas -Wno-parentheses -Wall -Wextra \
        -Wno-unused-macros -Winvalid-pch -include-pch obj/pch/tests-pch.hpp.pch -DCATA_CATCH_PCH \
        -fsyntax-only "../tests/$f"
fi

lock=/tmp/cdda-saigon-build.lock
waited=0
until mkdir "$lock" 2>/dev/null; do
    if [ $waited -eq 0 ]; then echo "waiting for another build ($(cat "$lock/who" 2>/dev/null))"; fi
    waited=1
    sleep 10
done
echo "$$ $(date +%T)" > "$lock/who"
trap 'rm -rf "$lock"' EXIT
CXXFLAGS=-D_XOPEN_SOURCE_EXTENDED nice make -j2 RELEASE=1 DEBUG_SYMBOLS=1 LOCALIZE=0 TILES=0 SOUND=0 \
    NCURSES_PREFIX=ncurses cataclysm tests > "$HOME/code/cdda-saigon-logs/build_tests.txt" 2>&1
rc=$?
if [ $rc -ne 0 ]; then
    grep -E 'error:|Error ' "$HOME/code/cdda-saigon-logs/build_tests.txt" | head -20
fi
echo "build exit $rc"
exit $rc
