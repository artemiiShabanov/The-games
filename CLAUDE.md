# The Games: рабочие заметки для Claude

Перед дизайном читай `docs/GDD.md`, перед планированием `docs/PLAN.md`, перед любым UI, мини-игрой
или экраном `docs/STYLE.md`. Решения, принятые в чате, в тот же день попадают в журнал
`docs/DESIGN.md`. Общий процесс всех проектов: gamedev-hub/WORKFLOW.md.

## Layout

- `thegames/` проект Godot: `scenes/`, `scripts/`, `resources/` (тюнинг-числа как Resource),
  `assets/`, `debug/` (дебаг-меню и тестовые сцены `debug/scenes/*_test.tscn`; продовые сцены
  на них не ссылаются; `debug/playtest/` в gitignore). Новая система регистрирует свои ручки
  в дебаг-меню через `Debug.add_*` в той же задаче, спека `docs/specs/debug.md`.
- `docs/` GDD, журнал решений, план (`plan.yaml` источник, `PLAN.md` генерируется), спеки,
  визуальный код `STYLE.md` и концепты к нему в `docs/concepts/` (правятся только после текста).
- `tools/` скрипты: `sync_plan.py` зеркалит план в GitHub.

## Verification loop

- Godot 4.7: `/Applications/Godot.app/Contents/MacOS/Godot`. После добавления ассетов:
  `--headless --path thegames --import`. Файлы `*.uid` и `*.import` коммитятся.
- Автотест: `sh tools/autotest.sh [--frames=N]` прогоняет игру ботом, пишет скриншот в
  `thegames/debug/playtest/autotest.png`, падает при `ERROR` в выводе или без `END ok`.
  `HEADLESS=1` без окна и скриншота. Внутри: `Godot --path thegames -- --auto-test
  --screenshot=debug/playtest/x.png`; автолоад `AutoTest`, бот `AutoTest.bot_mode` (OFF, WIN, LOSE),
  `AutoTest.fail(reason)` из любой системы. Дебаг-меню F1, `--debug`, `--scene=<id>`.
- Одна мини-игра ботом (WIN, затем LOSE): `sh tools/autotest.sh --scene=sprint_runner_test
  --minigame=<id> --frames=1500` (для `repeat` 2200). Демка: `--scene=demo_test --frames=3000`,
  скриншот паузы `--scene=demo_test --no-checks --pause --frames=240`. Уровень платформера по
  сиду текстом: `Godot --headless --path thegames -s debug/tools/dump_level.gd -- <seed> [from] [to]`. Весь план из 8 с проверкой багов: без `--minigame`,
  `--time-scale=4 --frames=3000`. Петля M0 целиком: `sh tools/autotest.sh --loop
  --time-scale=4 --frames=2600`. Кривые параметров и сцена в ресурс мини-игры:
  `Godot --headless --path thegames -s debug/tools/set_params.gd -- <id> tscn=res://... key=from:to`.
- Перед коммитом: автотест зелёный, нет ошибок в выводе Godot.

## Process

1. Взять issue. Нужно дизайн-решение: бриф в issue (вопрос, 2-3 варианта, рекомендация),
   метка `status: needs decision`, ждать Артемия.
2. Реализация на `main`, небольшие коммиты, сообщение ссылается на issue (`#12`). Пуш.
3. Играбельно: метка `status: needs playtest`, комментарий что пробовать. Артемий играет и закрывает.
4. Definition of done: автотест зелёный, скриншот или замер в issue, журнал решений обновлён.
5. Правка плана: `docs/plan.yaml`, затем `python3 tools/sync_plan.py --github`.

## Conventions

- GDScript со статической типизацией; `var x := f()` падает, если `f` возвращает Variant.
- `snake_case` функции и переменные, `PascalCase` классы и ноды, сигналы вверху скрипта.
- Тюнинг-числа только в `resources/*.tres`, не в коде сцен.
- Трейлер коммита: `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`.
