#!/usr/bin/env bash
# ci-local.sh [REV] — run every CI job locally, 1:1 and in the same order as
# .github/workflows/*.yml. Keep in sync: a new CI step lands here in the same commit.
#
# Like actions/checkout, each job runs on a clean export of a commit (REV,
# default HEAD; the pre-push hook passes each pushed commit), so uncommitted
# changes are not tested. Fresh venv per Python version. All jobs run; a
# summary lists failures and log paths. HERDR_BIN=/path/to/herdr is forwarded
# to e2e-herdr (needed off linux-x86_64, where no pinned download exists).
set -uo pipefail
REV="${1:-HEAD}"

REPO="$(cd "$(dirname "$0")/.." && pwd)"
LOGS="$REPO/.cache/ci-local"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
mkdir -p "$LOGS" "$REPO/.cache"
command -v uv >/dev/null || { echo "ci-local: uv is required (https://docs.astral.sh/uv/)" >&2; exit 1; }
# CI installs zsh with apt (shell helper tests run under bash AND zsh); locally it must exist.
command -v zsh >/dev/null || { echo "ci-local: zsh is required (CI installs it with apt)" >&2; exit 1; }

checkout() {  # $1 = dir: committed tree only, shared download cache
    mkdir -p "$1" && git -C "$REPO" archive "$REV" | tar -x -C "$1" && ln -s "$REPO/.cache" "$1/.cache"
}

venv() {  # $1 = python version, $2 = dir  (mirrors setup-python + pip install)
    uv venv -q --python "$1" "$2/.venv" && uv pip install -q --python "$2/.venv/bin/python" pyyaml jsonschema
}

job_test() {  # test.yml: test (matrix python-version)
    local dir="$WORK/test-$1"
    checkout "$dir" && venv "$1" "$dir" && make -C "$dir" test PYTHON="$dir/.venv/bin/python"
}

job_e2e_herdr() {  # test.yml: e2e-herdr
    local dir="$WORK/e2e-herdr"
    checkout "$dir" && venv 3.12 "$dir" &&
        make -C "$dir" e2e-herdr PYTHON="$dir/.venv/bin/python" ${HERDR_BIN:+HERDR_BIN="$HERDR_BIN"}
}

job_publish_build() {  # publish.yml: uv build (the PyPI upload itself cannot run locally)
    local dir="$WORK/publish"
    checkout "$dir" && (cd "$dir" && uv build -q --out-dir "$dir/out")
}

git -C "$REPO" rev-parse --verify -q "$REV^{commit}" >/dev/null || { echo "ci-local: unknown revision $REV" >&2; exit 1; }
echo "ci-local: $(git -C "$REPO" log -1 --format='%h %s' "$REV")"
JOBS=("test 3.10" "test 3.12" "e2e_herdr" "publish_build")
failed=()
for job in "${JOBS[@]}"; do
    read -r fn arg <<<"$job"
    name="${job// /-}"
    log="$LOGS/$name.log"
    printf '%-16s ' "$name"
    # shellcheck disable=SC2086  # $arg is empty or one word
    if "job_$fn" $arg >"$log" 2>&1 </dev/null; then echo "PASS"; else echo "FAIL  ($log)"; failed+=("$name"); fi
done
echo "note: publish.yml 'uv publish' (PyPI upload) is not run locally."
if ((${#failed[@]})); then echo "ci-local: ${#failed[@]} job(s) failed: ${failed[*]}"; exit 1; fi
echo "ci-local: all jobs passed (logs in $LOGS)"
