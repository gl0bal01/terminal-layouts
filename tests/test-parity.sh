#!/usr/bin/env bash
# test-parity.sh — check that tmux and zellij generated layouts are structurally equivalent.
#
# For each workflow, compares:
#   - tab count (excluding tmux_only / zellij_only tabs)
#   - leaf pane count per tab (in order)
#   - leaf pane names per tab (in order)
#
# Exits non-zero on any mismatch.
set -euo pipefail

cd "$(dirname "$0")/.."

PYTHON="${PYTHON:-python3}"
WORKFLOWS_DIR="terminal_layouts/manifest/workflows"
TMUX_DIR="dist/tmux"
ZELLIJ_DIR="dist/zellij"

fail() { echo "PARITY FAIL: $*" >&2; exit 1; }

for wf_yaml in "$WORKFLOWS_DIR"/*.yaml; do
    wf_id="$(basename "$wf_yaml" .yaml)"
    wf_path="$(pwd)/$wf_yaml"
    tmux_path="$(pwd)/$TMUX_DIR/$wf_id.yaml"
    zellij_path="$(pwd)/$ZELLIJ_DIR/$wf_id.kdl"
    repo_root="$(pwd)"

    echo "Checking parity: $wf_id"

    [ -f "$tmux_path" ] || fail "missing $tmux_path"
    [ -f "$zellij_path" ] || fail "missing $zellij_path"

    "$PYTHON" "$repo_root/tests/parity-check.py" "$wf_path" "$tmux_path" "$zellij_path" \
        || fail "parity mismatch for $wf_id"
done

echo "Parity check passed for all workflows."
