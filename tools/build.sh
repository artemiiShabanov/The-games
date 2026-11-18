#!/bin/sh
# Сборки Studio Running: macOS (universal: arm64 и x86_64, ad-hoc подпись, zip с .app) и Windows (x86_64, один exe).
#   sh tools/build.sh            # обе
#   sh tools/build.sh macos      # одна: macos | windows
# Пресеты в thegames/export_presets.cfg, результат в builds/ (в .gitignore). Нужны шаблоны
# экспорта Godot той же версии в ~/Library/Application Support/Godot/export_templates/<версия>.
set -eu
ROOT=$(cd "$(dirname "$0")/.." && pwd)
GODOT=${GODOT:-/Applications/Godot.app/Contents/MacOS/Godot}
WHICH=${1:-all}

build() {
  preset=$1; out=$2
  mkdir -p "$(dirname "$ROOT/builds/$out")"
  rm -f "$ROOT/builds/$out"
  echo "build: $preset -> builds/$out"
  "$GODOT" --headless --path "$ROOT/thegames" --export-release "$preset" "$ROOT/builds/$out" 2>&1 | grep -vE "^\[ *[0-9]+% \]" || true
  if [ ! -s "$ROOT/builds/$out" ]; then
    echo "build: $preset не собрался"; exit 1
  fi
  echo "build: $(du -h "$ROOT/builds/$out" | cut -f1) builds/$out"
}

"$GODOT" --headless --path "$ROOT/thegames" --import > /dev/null 2>&1 || true
case "$WHICH" in
  macos) build "macOS" "macos/Studio Running.zip" ;;
  windows) build "Windows" "windows/StudioRunning.exe" ;;
  *) build "Windows" "windows/StudioRunning.exe"; build "macOS" "macos/Studio Running.zip" ;;
esac
