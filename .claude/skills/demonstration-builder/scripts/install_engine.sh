#!/usr/bin/env bash
# Install the bundled demonstration engine into a target project.
#
# Why this exists: the skill carries its own copy of the `cpp_labs` engine (the
# shared Python that bakes real g++ output into HTML). To author demonstrations in
# ANY project — including a fresh one that has never seen cpp_labs — that engine
# must live as a `cpp_labs/` package at the project root, because the engine
# discovers subjects relative to its own physical location and `build_labs.sh`
# runs from the project root. This script copies the bundled engine into place.
#
# Usage (run from the target project root, or pass it explicitly):
#   .claude/skills/demonstration-builder/scripts/install_engine.sh          # into $PWD
#   .claude/skills/demonstration-builder/scripts/install_engine.sh /path/to/project
#   ~/.claude/skills/demonstration-builder/scripts/install_engine.sh        # global skill, into $PWD
#
# Safe to re-run: it MERGES the engine files in (overwriting only engine modules),
# and never touches your subject folders (cpp_labs/<subject>/). Re-run it to pull a
# newer engine after updating the skill.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"          # .../demonstration-builder
ENGINE="$SKILL_DIR/engine"

if [ ! -d "$ENGINE/cpp_labs" ]; then
  echo "bundled engine missing at $ENGINE/cpp_labs — is the skill installed intact?" >&2
  exit 1
fi

TARGET="${1:-$PWD}"
TARGET="$(cd "$TARGET" && pwd)"

mkdir -p "$TARGET/cpp_labs"
# Merge the engine modules in (trailing '/.' copies contents, not the dir itself).
# engine/cpp_labs holds ONLY shared modules — no subject dirs — so existing
# cpp_labs/<subject>/ folders in the target are left untouched.
cp -R "$ENGINE/cpp_labs/." "$TARGET/cpp_labs/"
cp "$ENGINE/build_labs.sh" "$TARGET/build_labs.sh"
chmod +x "$TARGET/build_labs.sh"

echo "installed engine into $TARGET/cpp_labs/  (+ build_labs.sh at project root)"
echo "dependency: pip install -r $ENGINE/requirements.txt   (PyYAML; pytest for tests)"
echo "next: scaffold_subject.sh <subject>  then  ./build_labs.sh <subject>"
