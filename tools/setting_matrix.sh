#!/bin/sh
# Все 25 демок на одном сеттинге без окна (#135): каждая пишет, что взяла у пиратов вместо своего
# набора, и с `--strict-setting` падает при любой подмене. Долго, около получаса.
#   sh tools/setting_matrix.sh 1            # космос, строгая проверка
#   STRICT=0 sh tools/setting_matrix.sh 1   # только сводка подмен по парам, код выхода 0
#   sh tools/setting_matrix.sh 1 bit16      # одна технология
set -u
ROOT=$(cd "$(dirname "$0")/.." && pwd)
N=${1:?номер сеттинга Game.Setting}
ONLY=${2:-}
STRICT=${STRICT:-1}
status=0
run() {
  genre=$1; tech=$2; frames=$3; timeout=$4
  if [ -n "$ONLY" ] && [ "$ONLY" != "$tech" ]; then return; fi
  strict=""; [ "$STRICT" = "1" ] && strict="--strict-setting"
  out=$(HEADLESS=1 TIMEOUT=$timeout sh "$ROOT/tools/autotest.sh" --scene=demo_test --genre=$genre --tech=$tech \
    --setting=$N $strict --frames=$frames 2>&1)
  line=$(echo "$out" | grep "AUTO-TEST note: сеттинг" | tail -1)
  if echo "$out" | grep -q "^autotest: зелёный"; then
    echo "ok   $genre × $tech: ${line#AUTO-TEST note: }"
  else
    echo "FAIL $genre × $tech: ${line#AUTO-TEST note: }"; status=1
  fi
}
# Кадры и таймауты как у шагов демок в ci.sh.
run platformer vector 5000 240;  run racing vector 7000 240;    run shooter vector 6000 240
run sport vector 7000 240;       run fighting vector 4000 240
run platformer bit8 3000 240;    run racing bit8 9000 240;      run shooter bit8 6000 240
run sport bit8 9000 240;         run fighting bit8 7000 240
run platformer bit16 5000 240;   run racing bit16 9000 240;     run shooter bit16 5000 240
run sport bit16 11000 300;        run fighting bit16 10000 240
run platformer lowpoly 7000 240; run racing lowpoly 17000 560;  run shooter lowpoly 6000 240
run sport lowpoly 6000 240;      run fighting lowpoly 7000 240
run platformer threed 7000 600;  run racing threed 10500 600;   run shooter threed 9000 600
run sport threed 13000 600;      run fighting threed 9000 600
exit $status
