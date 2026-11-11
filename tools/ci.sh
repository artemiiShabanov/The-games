#!/bin/sh
# Проверки The Games одним прогоном (#39): модель экономики против тюнинга и автотесты систем
# без окна. Зелёный, когда все шаги зелёные; код выхода 1 при первом красном шаге не
# прерывает остальные, итог в конце.
#   sh tools/ci.sh
set -u
ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT" || exit 1
status=0
step() {
  name=$1; shift
  if "$@" > /tmp/thegames_ci.log 2>&1; then
    echo "ok   $name"
  else
    echo "FAIL $name"; tail -20 /tmp/thegames_ci.log; status=1
  fi
}
step "model_run --check" python3 tools/model_run.py --check
export HEADLESS=1
step "economy_test" sh tools/autotest.sh --scene=economy_test --frames=200
step "success_test" sh tools/autotest.sh --scene=success_test --frames=200
step "constructor_test" sh tools/autotest.sh --scene=constructor_test --frames=400
step "mouse_test" sh tools/autotest.sh --scene=mouse_test --frames=1500
step "feed_test" sh tools/autotest.sh --scene=feed_test --frames=400
step "event_test" sh tools/autotest.sh --scene=event_test --frames=600
step "profile_test" sh tools/autotest.sh --scene=profile_test --frames=30
step "gallery_test" sh tools/autotest.sh --scene=gallery_test --time-scale=4 --frames=2500
step "hub_test" sh tools/autotest.sh --scene=hub_test --frames=60
step "options_test" sh tools/autotest.sh --scene=options_test --frames=30
step "studio_test" sh tools/autotest.sh --scene=studio_test --frames=600
step "studio_backdrop_test" sh tools/autotest.sh --scene=studio_backdrop_test --frames=30
step "bugfix_test" sh tools/autotest.sh --scene=bugfix_test --time-scale=4 --frames=3000
step "sprint plan" sh tools/autotest.sh --scene=sprint_runner_test --time-scale=4 --frames=4500
step "demo bugs" sh tools/autotest.sh --scene=demo_test --bugs --frames=3000
step "ascii sheet" sh tools/autotest.sh --scene=ascii_test --frames=120
step "minigame mash" sh tools/autotest.sh --scene=sprint_runner_test --minigame=mash --frames=1500
step "ascii probe bugs" sh tools/autotest.sh --scene=ascii_test --probe --bugs --frames=1500
step "demo racing" sh tools/autotest.sh --scene=demo_test --genre=racing --frames=5000
step "demo racing bugs" sh tools/autotest.sh --scene=demo_test --genre=racing --bugs --frames=5000
step "feed racing" sh tools/autotest.sh --scene=feed_test --genre=racing --frames=400
step "demo shooter" sh tools/autotest.sh --scene=demo_test --genre=shooter --frames=6000
step "demo shooter bugs" sh tools/autotest.sh --scene=demo_test --genre=shooter --bugs --frames=9000
step "feed shooter" sh tools/autotest.sh --scene=feed_test --genre=shooter --frames=400
step "demo sport" sh tools/autotest.sh --scene=demo_test --genre=sport --frames=9000
step "demo sport bugs" sh tools/autotest.sh --scene=demo_test --genre=sport --bugs --frames=18000
step "feed sport" sh tools/autotest.sh --scene=feed_test --genre=sport --frames=400
step "demo fighting" sh tools/autotest.sh --scene=demo_test --genre=fighting --frames=7000
step "demo fighting bugs" sh tools/autotest.sh --scene=demo_test --genre=fighting --bugs --frames=9000
step "feed fighting" sh tools/autotest.sh --scene=feed_test --genre=fighting --frames=400
step "loop M1" sh tools/autotest.sh --loop --time-scale=4 --frames=6500
# Сверка модели (#72): игра на спокойном рынке с руками 0.75 пишет ведомость, модель её пересчитывает.
step "model M2 replay" sh -c 'sh tools/autotest.sh --loop --calm --hands=0.75 --refuse-events --cap=12 --releases=4 --ledger=debug/playtest/ledger_ci.json --time-scale=4 --frames=12000 && python3 tools/model_run.py --replay thegames/debug/playtest/ledger_ci.json'
step "loop rescue" sh tools/autotest.sh --loop --broke-at=2 --releases=3 --time-scale=4 --frames=9000
step "slot save" sh tools/autotest.sh --slot=3 --refuse-events --time-scale=4 --frames=2600
step "slot resume" sh tools/autotest.sh --slot=3 --resume --loop --releases=3 --refuse-events --time-scale=4 --frames=8000
step "menu" sh tools/autotest.sh --menu --frames=60
step "loop refuse rescue" sh tools/autotest.sh --loop --broke-at=2 --refuse-events --releases=3 --time-scale=4 --frames=9000
[ $status -eq 0 ] && echo "ci: зелёный" || echo "ci: есть красные шаги"
exit $status
