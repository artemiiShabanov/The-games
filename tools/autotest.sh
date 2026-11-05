#!/bin/sh
# Автотест The Games: прогон N кадров ботом, скриншот, проверка вывода Godot на ошибки.
#   sh tools/autotest.sh                      # скриншот в thegames/debug/playtest/autotest.png
#   sh tools/autotest.sh --frames=300         # любые аргументы уходят в игру после `--`
#   sh tools/autotest.sh --scene=sprint_runner_test --minigame=fit_frame --frames=1500
#   HEADLESS=1 sh tools/autotest.sh           # без окна (скриншот будет пустым, проверка без него)
# Зелёный: в выводе есть `END ok` и нет `ERROR` / `SCRIPT ERROR`. Код выхода 0 или 1.
# `--fixed-fps 60`: игровое время идёт по кадрам, а не по часам, так что перекрытое или
# троттлящееся окно не ломает тайминги. Сторож: TIMEOUT секунд на весь прогон (по умолчанию 240),
# после `END` процессу даётся 5 секунд на выход, дальше он снимается.
set -u
ROOT=$(cd "$(dirname "$0")/.." && pwd)
GODOT=${GODOT:-/Applications/Godot.app/Contents/MacOS/Godot}
SHOT=${SHOT:-debug/playtest/autotest.png}
TIMEOUT=${TIMEOUT:-240}
LOG=$(mktemp)

HEAD=""
if [ "${HEADLESS:-0}" = "1" ]; then HEAD="--headless"; SHOT=""; fi

"$GODOT" $HEAD --fixed-fps 60 --path "$ROOT/thegames" -- --auto-test ${SHOT:+--screenshot=$SHOT} "$@" > "$LOG" 2>&1 &
PID=$!
waited=0
while kill -0 $PID 2>/dev/null; do
  if grep -q "^END" "$LOG"; then
    for i in 1 2 3 4 5; do kill -0 $PID 2>/dev/null || break; sleep 1; done
    kill -0 $PID 2>/dev/null && { echo "autotest: процесс не вышел после END, снимаю"; kill $PID 2>/dev/null; }
    break
  fi
  if [ $waited -ge $TIMEOUT ]; then
    echo "autotest: таймаут ${TIMEOUT}s, снимаю процесс"; kill $PID 2>/dev/null; break
  fi
  sleep 1; waited=$((waited + 1))
done
wait $PID 2>/dev/null
cat "$LOG"
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
