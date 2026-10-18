#!/usr/bin/env bash
# Run the Saigon test suite and keep the whole output, so an intermittent failure leaves its
# evidence: the seed to replay it, the test it was in, and the backtrace.  QA2: a SIGSEGV seen
# once in saigon_new_game_realmap_2009 was lost because the run's output was filtered away.
# Usage: tools/saigon/run_suite.sh [seed] ["test spec"]   (default: a random seed, "[saigon]")
# Replay a failure with the seed it printed:  tools/saigon/run_suite.sh <seed>
set -u
cd "$(dirname "$0")/../.."
seed="${1:-$RANDOM$RANDOM}"
spec="${2:-[saigon]}"
logs="${SAIGON_LOGS:-$HOME/code/cdda-saigon-logs}/suite"
mkdir -p "$logs"
log="$logs/$(date +%Y%m%d-%H%M%S)-seed$seed.txt"
tests/cata_test --mods=dda,saigon_2000s --rng-seed "$seed" "$spec" > "$log" 2>&1
rc=$?
grep -E "test cases|All tests|Treating result" "$log"
if [ $rc -ne 0 ] || grep -qE "SIGSEGV|SIGABRT|fatal error|Treating result as failure" "$log"; then
    echo "FAIL (exit $rc, seed $seed): $log"
    grep -nE "SIGSEGV|SIGABRT|fatal error" "$log" | head -5
    exit 1
fi
echo "OK (seed $seed): $log"
