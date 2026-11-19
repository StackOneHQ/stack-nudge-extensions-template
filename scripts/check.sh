#!/usr/bin/env bash
# Every check in the repo, one summary line per part, and a non-zero exit if any part fails. After
# agent-control's scripts/check.sh.
#
#   scripts/check.sh                    (or `pnpm check` from the repo root)
#   scripts/check.sh --base <ref>       the branch the extension version check compares with,
#                                       main by default
#   scripts/check.sh --list             names the parts that would run, one a line, and runs none
#
# Each part runs on its own; CI (.github/workflows/ci.yml) runs the extension parts. lint is Biome
# over the scripts and the JSON, so it needs `pnpm install` first. shellcheck and actionlint are
# skipped, saying so, when they aren't installed. A failing part prints the end of its log; the
# full logs are kept in the directory named at the end.
set -uo pipefail

BASE="main"
LIST=0
usage() {
  sed -n '2,13p' "$0" | sed 's/^# \{0,1\}//'
}
while (($# > 0)); do
  case "$1" in
    --base)
      BASE="${2:?--base needs a ref}"
      shift
      ;;
    --list) LIST=1 ;;
    -h | --help)
      usage
      exit 0
      ;;
    *)
      echo "check.sh: unknown option $1" >&2
      usage >&2
      exit 2
      ;;
  esac
  shift
done

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT" || exit 2

parts=(lint extensions-valid extensions-tests extensions-versions script-specs workflow-pins shellcheck actionlint)

if ((LIST == 1)); then
  printf '%s\n' "${parts[@]}"
  exit 0
fi

LOGS="$(mktemp -d "${TMPDIR:-/tmp}/extensions-check.XXXXXX")"
failed=()

run_part() {
  case "$1" in
    lint) pnpm exec biome ci . ;;
    extensions-valid) scripts/package-extensions.sh validate ;;
    extensions-tests)
      # test-extensions.sh is stack-nudge's, and fails when it finds no suites, which a catalogue
      # with no extensions yet has none of.
      if ! compgen -G 'extensions/*/manifest.json' >/dev/null; then
        echo "skipped: no extensions yet"
        return 0
      fi
      scripts/test-extensions.sh
      ;;
    extensions-versions)
      if ! git rev-parse --verify --quiet "$BASE^{commit}" >/dev/null; then
        echo "skipped: no $BASE to compare with"
        return 0
      fi
      scripts/check-extension-versions.sh "$BASE"
      ;;
    script-specs) pnpm exec vitest run --project workflow-pins ;;
    workflow-pins) node scripts/check-workflows.mjs ;;
    shellcheck)
      if ! command -v shellcheck >/dev/null 2>&1; then
        echo "skipped: shellcheck isn't installed"
        return 0
      fi
      shellcheck --severity=warning scripts/*.sh .githooks/*
      ;;
    actionlint)
      if ! command -v actionlint >/dev/null 2>&1; then
        echo "skipped: actionlint isn't installed"
        return 0
      fi
      actionlint
      ;;
  esac
}

for part in "${parts[@]}"; do
  log="$LOGS/$part.log"
  started=$SECONDS
  if run_part "$part" >"$log" 2>&1; then
    note=""
    if grep -q '^skipped:' "$log"; then
      note=" ($(grep -m1 '^skipped:' "$log"))"
    fi
    printf '  ok    %-22s %3ss%s\n' "$part" "$((SECONDS - started))" "$note"
  else
    printf '  FAIL  %-22s %3ss\n' "$part" "$((SECONDS - started))"
    tail -n 25 "$log" | sed 's/^/        /'
    failed+=("$part")
  fi
done

echo "logs: $LOGS"
if ((${#failed[@]} > 0)); then
  echo "failed: ${failed[*]}"
  exit 1
fi
echo "every part passed"
