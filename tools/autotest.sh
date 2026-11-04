#!/bin/sh
# Автотест The Games: прогон N кадров ботом, скриншот, проверка вывода Godot на ошибки.
#   sh tools/autotest.sh                      # скриншот в thegames/debug/playtest/autotest.png
#   sh tools/autotest.sh --frames=300         # любые аргументы уходят в игру после `--`
#   HEADLESS=1 sh tools/autotest.sh           # без окна (скриншот будет пустым, проверка без него)
# Зелёный: в выводе есть `END ok` и нет `ERROR` / `SCRIPT ERROR`. Код выхода 0 или 1.
set -u
ROOT=$(cd "$(dirname "$0")/.." && pwd)
GODOT=${GODOT:-/Applications/Godot.app/Contents/MacOS/Godot}
SHOT=${SHOT:-debug/playtest/autotest.png}
LOG=$(mktemp)

HEAD=""
if [ "${HEADLESS:-0}" = "1" ]; then HEAD="--headless"; SHOT=""; fi

"$GODOT" $HEAD --path "$ROOT/thegames" -- --auto-test ${SHOT:+--screenshot=$SHOT} "$@" 2>&1 | tee "$LOG"
status=0
if ! grep -q "^END ok" "$LOG"; then
  echo "autotest: нет END ok"; status=1
fi
if grep -qE "ERROR|SCRIPT ERROR" "$LOG"; then
  echo "autotest: в выводе есть ошибки"; status=1
fi
rm -f "$LOG"
[ $status -eq 0 ] && echo "autotest: зелёный"
exit $status
