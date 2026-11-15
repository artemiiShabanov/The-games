#!/bin/sh
# Листы кадров сеттинга (#136): на каждую технологию шесть кадров сеткой 3×2: пять демок в
# движении и лист ассетов технологии. Пишет `thegames/debug/playtest/shots/<id>_<tech>.jpg`.
#   sh tools/setting_shots.sh 1            # космос, пять листов
#   sh tools/setting_shots.sh 1 bit16      # одна технология
set -u
ROOT=$(cd "$(dirname "$0")/.." && pwd)
N=${1:?номер сеттинга Game.Setting}
ONLY=${2:-}
ID=$(python3 -c "import sys; sys.path.insert(0, '$ROOT/tools'); import setting_sets as s; print((('pirates',) + s.IDS)[$N])")
DIR=debug/playtest/shots
mkdir -p "$ROOT/thegames/$DIR"
shot() {
  name=$1; shift
  SHOT=$DIR/${ID}_$name.png sh "$ROOT/tools/autotest.sh" "$@" --setting=$N --no-checks --fixed-fps >/dev/null 2>&1
}
for tech in vector bit8 bit16 lowpoly threed; do
  if [ -n "$ONLY" ] && [ "$ONLY" != "$tech" ]; then continue; fi
  for genre in platformer racing shooter sport fighting; do
    frames=700; [ "$genre" = "racing" ] && frames=900
    shot ${tech}_$genre --scene=demo_test --genre=$genre --tech=$tech --frames=$frames
  done
  case $tech in
    vector) shot ${tech}_sheet --scene=vector_test --frames=90 ;;
    bit8) shot ${tech}_sheet --scene=demo_test --genre=platformer --tech=bit8 --frames=1300 ;;
    bit16) shot ${tech}_sheet --scene=bit16_test --frames=120 ;;
    lowpoly) shot ${tech}_sheet --scene=lowpoly_test --frames=200 ;;
    threed) shot ${tech}_sheet --scene=lowpoly_test --tech=threed --frames=700 ;;
  esac
  python3 "$ROOT/tools/shots_sheet.py" "$ROOT/thegames/$DIR/${ID}_${tech}.jpg" \
    "$ROOT/thegames/$DIR/${ID}_${tech}_platformer.png" "$ROOT/thegames/$DIR/${ID}_${tech}_racing.png" \
    "$ROOT/thegames/$DIR/${ID}_${tech}_shooter.png" "$ROOT/thegames/$DIR/${ID}_${tech}_sport.png" \
    "$ROOT/thegames/$DIR/${ID}_${tech}_fighting.png" "$ROOT/thegames/$DIR/${ID}_${tech}_sheet.png"
done
