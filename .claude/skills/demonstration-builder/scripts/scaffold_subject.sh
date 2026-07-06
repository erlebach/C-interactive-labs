#!/usr/bin/env bash
# Scaffold a new cpp_labs demonstration subject from the skill templates.
#
# Why this exists: the scaffolding step (make the package dirs + __init__ markers +
# copy/rename the four templates, keeping topic-id/demo-file/layout references in
# sync) is deterministic, repetitive, and easy to get subtly wrong by hand. Running
# one tested command instead removes that whole class of path/name mistakes.
#
# Usage (run from anywhere inside the repo):
#   .claude/skills/demonstration-builder/scripts/scaffold_subject.sh <subject>
#
# Produces an immediately buildable, immediately green minimal page with ONE example
# (`<subject>_ex1`, printing `x = 42` under int/double tabs). Verify right away with:
#   ./build_labs.sh <subject> && pytest cpp_labs/<subject>/tests/ -q
# Then grow it: duplicate the example topic/demo per example, add a gotcha, and list
# each demo in layouts/<subject>.rail.yaml. See the skill's SKILL.md + reference/.
#
# Guard: refuses to overwrite an existing subject directory.
set -euo pipefail

SUBJECT="${1:-}"
if [ -z "$SUBJECT" ]; then
  echo "usage: scaffold_subject.sh <subject>" >&2
  exit 2
fi
# Keep ids/paths sane: letters, digits, underscore only.
if ! printf '%s' "$SUBJECT" | grep -Eq '^[A-Za-z][A-Za-z0-9_]*$'; then
  echo "invalid subject '$SUBJECT' (use letters/digits/underscore, starting with a letter)" >&2
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"          # .../demonstration-builder
ROOT="$(cd "$SKILL_DIR/../../.." && pwd)"           # repo root (.claude/skills/<skill>/../../..)
TEMPLATES="$SKILL_DIR/templates"
DEST="$ROOT/cpp_labs/$SUBJECT"
EX="${SUBJECT}_ex1"                                 # collision-free example id

if [ -e "$DEST" ]; then
  echo "refusing to overwrite existing $DEST" >&2
  exit 1
fi

mkdir -p "$DEST/topics" "$DEST/demos" "$DEST/layouts" "$DEST/tests"
: > "$DEST/__init__.py"
: > "$DEST/tests/__init__.py"

cp "$TEMPLATES/topic.topic.yaml" "$DEST/topics/$EX.topic.yaml"
cp "$TEMPLATES/demo.demo.yaml"   "$DEST/demos/$EX.demo.yaml"
cp "$TEMPLATES/layout.rail.yaml" "$DEST/layouts/$SUBJECT.rail.yaml"
cp "$TEMPLATES/test_subject.py"  "$DEST/tests/test_$SUBJECT.py"

# Rename the template's placeholder ids/paths so everything is internally consistent:
#   my_topic  -> <subject>_ex1   (topic id + demo bake + layout demo reference)
#   my_subject-> <subject>       (the test's LAYOUT filename)
perl -pi -e "s/\bmy_topic\b/$EX/g"      "$DEST/topics/$EX.topic.yaml" "$DEST/demos/$EX.demo.yaml" "$DEST/layouts/$SUBJECT.rail.yaml"
perl -pi -e "s/\bmy_subject\b/$SUBJECT/g" "$DEST/tests/test_$SUBJECT.py"

echo "scaffolded cpp_labs/$SUBJECT/  (example id: $EX)"
echo "verify now:  ./build_labs.sh $SUBJECT && pytest cpp_labs/$SUBJECT/tests/ -q"
echo "then grow it: add more topics/demos, wire them into layouts/$SUBJECT.rail.yaml, add a gotcha."
