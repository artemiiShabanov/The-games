# The Games: рабочие заметки для Claude

Перед дизайном читай `docs/GDD.md`, перед планированием `docs/PLAN.md`. Решения, принятые в чате,
в тот же день попадают в журнал `docs/DESIGN.md`. Общий процесс всех проектов: gamedev-hub/WORKFLOW.md.

## Layout

- `thegames/` проект Godot: `scenes/`, `scripts/`, `resources/` (тюнинг-числа как Resource),
  `assets/`, `debug/` (дебаг-меню, тест-сцены; `debug/playtest/` в gitignore).
- `docs/` GDD, журнал решений, план (`plan.yaml` источник, `PLAN.md` генерируется), спеки.
- `tools/` скрипты: `sync_plan.py` зеркалит план в GitHub.

## Verification loop

- Godot: `/Applications/Godot.app/Contents/MacOS/Godot`. После добавления ассетов: `--headless --import`.
- Автотест: `Godot --path thegames -- --auto-test --screenshot=<dir>/x.png` должен печатать `END ok`
  (завести в первой же задаче: игра прогоняет N кадров с ботом, пишет скриншот, выходит).
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
