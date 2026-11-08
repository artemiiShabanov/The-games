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
step "feed_test" sh tools/autotest.sh --scene=feed_test --frames=400
step "studio_test" sh tools/autotest.sh --scene=studio_test --frames=600
step "bugfix_test" sh tools/autotest.sh --scene=bugfix_test --time-scale=4 --frames=3000
step "sprint plan" sh tools/autotest.sh --scene=sprint_runner_test --time-scale=4 --frames=3000
step "demo bugs" sh tools/autotest.sh --scene=demo_test --bugs --frames=3000
step "loop M1" sh tools/autotest.sh --loop --time-scale=4 --frames=6500
[ $status -eq 0 ] && echo "ci: зелёный" || echo "ci: есть красные шаги"
exit $status
