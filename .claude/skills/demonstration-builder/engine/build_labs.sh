#!/usr/bin/env bash
#
# build_labs.sh — regenerate every HTML page in dist_labs/ from its YAML spec.
#
# Auto-discovers all buildable specs under cpp_labs/ (no list to maintain):
#   - cpp_labs/*/layouts/*.yaml   (multi-demo layout pages: rail / tabs / page)
#   - cpp_labs/*/*.page.yaml      (older standalone single-subject pages)
# and bakes each with the engine (real g++ output baked at build time).
#
# Usage:
#   ./build_labs.sh              # rebuild everything into dist_labs/
#   ./build_labs.sh <filter>     # only specs whose path contains <filter>
#                                #   e.g. ./build_labs.sh class_structure
#   OUT=other_dir ./build_labs.sh   # write into a different output dir
#
# Exits non-zero if any page fails to build.

set -u
cd "$(dirname "$0")"                       # always run from the repo root

OUT="${OUT:-dist_labs}"
FILTER="${1:-}"

shopt -s nullglob
specs=( cpp_labs/*/layouts/*.yaml cpp_labs/*/*.page.yaml )
shopt -u nullglob

built=0 failed=0 skipped=0
echo "Rebuilding lab pages into ${OUT}/ ..."
for spec in "${specs[@]}"; do
    if [ -n "$FILTER" ] && [[ "$spec" != *"$FILTER"* ]]; then
        skipped=$((skipped + 1))
        continue
    fi
    # print the exact command executed, so it can be copied and rerun by hand
    echo "  \$ python -m cpp_labs.yaml_engine.render_page $spec $OUT"
    if python -m cpp_labs.yaml_engine.render_page "$spec" "$OUT" >/dev/null 2>/tmp/build_labs_err; then
        echo "    ok"
        built=$((built + 1))
    else
        echo "    FAIL"
        sed 's/^/        /' /tmp/build_labs_err       # indent the error
        failed=$((failed + 1))
    fi
done
rm -f /tmp/build_labs_err

echo "---"
echo "built ${built}, failed ${failed}${FILTER:+, skipped ${skipped} (filter: ${FILTER})}"
[ "$failed" -eq 0 ]
