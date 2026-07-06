#!/usr/bin/env bash
# Refresh the skill's vendored engine bundle from a live source engine.
#
# This is the MAINTAINER inverse of install_engine.sh: install copies the bundle
# OUT into a project; sync copies the live engine IN, re-vendoring `engine/cpp_labs`
# so the skill ships the latest code. Run it in the source repo whenever you change
# the engine, then commit the refreshed bundle.
#
# The drift guard `test_bundled_engine_matches_source` fails when the bundle lags the
# source — that failure is your signal to run this.
#
# Usage:
#   .claude/skills/demonstration-builder/scripts/sync_engine.sh          # source = repo root
#   .claude/skills/demonstration-builder/scripts/sync_engine.sh /path/to/source_repo
#   SOURCE_ROOT=/path/to/source_repo  sync_engine.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"          # .../demonstration-builder
ENGINE="$SKILL_DIR/engine"

# Source project root = arg > SOURCE_ROOT env > the repo containing this skill
# (skills/<skill>/scripts -> up 4 = repo root).
SOURCE="${1:-${SOURCE_ROOT:-$(cd "$SKILL_DIR/../../.." && pwd)}}"
SOURCE="$(cd "$SOURCE" && pwd)"
SRC_PKG="$SOURCE/cpp_labs"

if [ ! -d "$SRC_PKG" ] || [ ! -f "$SOURCE/build_labs.sh" ]; then
  echo "no source engine found in $SOURCE (need cpp_labs/ + build_labs.sh)" >&2
  exit 1
fi

# The exact bundle file set — must stay in sync with test_bundled_engine_matches_source.
MODULES=(
  __init__.py build_html.py code_generator.py compiler_runner.py
  components.py html_renderer.py topic_yaml.py
  yaml_engine/__init__.py yaml_engine/render_page.py yaml_engine/interface_catalog.py
)
ASSETS=(
  vendor/highlightjs/highlight.min.js
  vendor/highlightjs/atom-one-dark.min.css
  vendor/highlightjs/README.md
)

mkdir -p "$ENGINE/cpp_labs/yaml_engine" "$ENGINE/cpp_labs/vendor/highlightjs"
for rel in "${MODULES[@]}" "${ASSETS[@]}"; do
  if [ ! -f "$SRC_PKG/$rel" ]; then
    echo "source missing cpp_labs/$rel — aborting" >&2
    exit 1
  fi
  cp "$SRC_PKG/$rel" "$ENGINE/cpp_labs/$rel"
done
cp "$SOURCE/build_labs.sh" "$ENGINE/build_labs.sh"
chmod +x "$ENGINE/build_labs.sh"

# Never vendor bytecode.
find "$ENGINE" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

echo "synced bundle in $ENGINE/cpp_labs/ from $SRC_PKG"
echo "verify: pytest cpp_labs/tests/test_demonstration_skill.py -q"
