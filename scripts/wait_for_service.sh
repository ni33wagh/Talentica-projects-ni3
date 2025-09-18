#!/usr/bin/env bash

set -euo pipefail

# Usage:
#   scripts/wait_for_service.sh --url http://localhost:8080/login --timeout 120 --name "Jenkins"
#   scripts/wait_for_service.sh --cmd "docker compose restart jenkins" --url http://localhost:8080/login --timeout 180 --name "Jenkins restart"

URL=""
TIMEOUT=120
NAME="Service"
CMD=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --url)
      URL="$2"; shift 2;;
    --timeout)
      TIMEOUT="$2"; shift 2;;
    --name)
      NAME="$2"; shift 2;;
    --cmd)
      CMD="$2"; shift 2;;
    *) echo "Unknown arg: $1"; exit 1;;
  esac
done

if [[ -n "$CMD" ]]; then
  echo "▶ Starting: $CMD"
  bash -lc "$CMD" >/dev/null 2>&1 || true
fi

if [[ -z "$URL" ]]; then
  echo "--url is required"; exit 1
fi

echo "⏳ Waiting for $NAME at $URL (timeout: ${TIMEOUT}s)"

start_ts=$(date +%s)
end_ts=$((start_ts + TIMEOUT))
bar_width=40

progress_bar() {
  local percent=$1
  local filled=$(( percent * bar_width / 100 ))
  local empty=$(( bar_width - filled ))
  printf "["; printf "#%.0s" $(seq 1 $filled); printf "-%.0s" $(seq 1 $empty); printf "] %3d%%" "$percent"
}

until curl -fsS "$URL" >/dev/null 2>&1; do
  now=$(date +%s)
  if (( now >= end_ts )); then
    echo
    echo "❌ Timeout waiting for $NAME"
    exit 1
  fi
  elapsed=$(( now - start_ts ))
  percent=$(( elapsed * 100 / TIMEOUT ))
  printf "\r"
  progress_bar "$percent"
  printf "  elapsed: %2ds / %2ds" "$elapsed" "$TIMEOUT"
  sleep 1
done

printf "\r"
progress_bar 100
echo "  ✅ $NAME is up"

