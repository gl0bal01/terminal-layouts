#!/usr/bin/env bash
# test-idempotence.sh — generators must produce byte-identical output on re-run.
set -euo pipefail
cd "$(dirname "$0")/.."

PYTHON="${PYTHON:-python3}"
WORKFLOWS_DIR="manifest/workflows"

fail() { echo "IDEMPOTENCE FAIL: $*" >&2; exit 1; }

for wf_yaml in "$WORKFLOWS_DIR"/*.yaml; do
    wf_id="$(basename "$wf_yaml" .yaml)"

    "$PYTHON" generators/gen-tmux.py "$wf_id" > /tmp/tl-tmux-1.yaml
    "$PYTHON" generators/gen-tmux.py "$wf_id" > /tmp/tl-tmux-2.yaml
    diff -q /tmp/tl-tmux-1.yaml /tmp/tl-tmux-2.yaml >/dev/null || fail "tmux $wf_id not idempotent"

    "$PYTHON" generators/gen-zellij.py "$wf_id" > /tmp/tl-zellij-1.kdl
    "$PYTHON" generators/gen-zellij.py "$wf_id" > /tmp/tl-zellij-2.kdl
    diff -q /tmp/tl-zellij-1.kdl /tmp/tl-zellij-2.kdl >/dev/null || fail "zellij $wf_id not idempotent"

    echo "  OK: $wf_id idempotent"
done

rm -f /tmp/tl-tmux-*.yaml /tmp/tl-zellij-*.kdl
echo "Idempotence check passed."
