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
  Ввод как от игрока (#82): `--bot=off "--input=200:key=space,300:move=960x936,310:click=960x936,
  320:wheel=2@300x500,330:pan=40@1500x500"` (кадр:действие, координаты экрана 1920×1080; заметка
  пишет Control под курсором: если там корень сцены, он съедает клики, нужен `MOUSE_FILTER_IGNORE`).
- Одна мини-игра ботом (WIN, затем LOSE): `sh tools/autotest.sh --scene=sprint_runner_test
  --minigame=<id> --frames=3500` (часть мини-игр не укладывается в 1500). Под автотестом `t` и сид
  не из дебаг-меню, а `--t=<0..1>` и `--seed=<n>` (по умолчанию 0 и 1); на высоком `t` бот
  «Наведи» застревает на призме. Демка: `--scene=demo_test --frames=3000` (гонки
  `--genre=racing --frames=4000`, `--seed=N`, `--setting=N`; трасса по сиду текстом
  `Godot --headless --path thegames -s debug/tools/dump_track.gd -- <seed>`; шутер
  `--genre=shooter --frames=6000`, арена и волны текстом `debug/tools/dump_arena.gd -- <seed>`;
  гольф `--genre=sport --frames=9000`, поле текстом `debug/tools/dump_course.gd -- <seed>`;
  кадр гольфа в нужный момент даёт и `--fixed-fps`: `SHOT=debug/playtest/x.png sh
  tools/autotest.sh --scene=demo_test --genre=sport --setting=0 --no-checks --frames=N`, без
  него окно крутит кадры быстрее 60 в секунду и `--frames` не равны времени); файтинг
  `--genre=fighting --frames=7000`, план соперника и бой ботами без окна текстом
  `debug/tools/dump_fight.gd -- <seed> [count]`; момент боя под скриншот `--no-checks
  --freeze=<с от запуска, с отсчётом>` (демка встаёт на этой секунде, работает у любой демки),
  скриншот паузы `--scene=demo_test --no-checks --pause --frames=240`. Уровень платформера по
  сиду текстом: `Godot --headless --path thegames -s debug/tools/dump_level.gd -- <seed> [from] [to]`. Весь план из 8 с проверкой багов: без `--minigame`,
  `--time-scale=4 --frames=4500` (с переигровками `--replays=2 --frames=4500`). Багфикс:
  `--scene=bugfix_test --time-scale=4 --frames=3000`. Вставки: `--scene=event_test --frames=600`; одна на скриншот
  `--no-checks --event=<id> [--mood=N]`; поверх фазы студии `--scene=studio_test --no-checks
  --past=4 --event=<id> --frames=20`. Настройки: `--scene=options_test --frames=30` (кадр `--no-checks`). Мышь в мини-играх:
  `--scene=mouse_test --frames=1500`.
  Главный экран забега: `--scene=hub_test --frames=60`, кадр `--no-checks
  [--past=N] [--pop=money|upgrades|release|offer]`. Галерея: `--scene=gallery_test --time-scale=4 --frames=2500`,
  кадр `--no-checks [--empty] [--studios]`; профиль `--scene=profile_test --frames=30`. Петля M1 целиком (три релиза ботом со сверкой денег): `sh tools/autotest.sh --loop
  --time-scale=4 --frames=6500` (`--releases=N` другое число, `--draw` разыгрывает стартовую пару как в игре, `--cap=N` свой кап, `--broke-at=N` банкротство перед фазой студии релиза N, `--refuse-events`
  бот отвечает на вставки последним вариантом; `--slot=N` сохранять в тестовый слот, `--resume`
  продолжить из него). Главная сцена проекта это меню (#71): под автотестом без `--menu` оно
  сразу открывает игру; меню кадром `--menu --frames=60`.. Студия на фоне (#80): `--scene=studio_backdrop_test --frames=600`
  (`--stage=0..3`, `--people=N --upgrades=a,b`, `--grid` четыре стадии сеткой, `--card`
  карточка поверх, `--static`, `--react=release|viral|broke`, `--sheet` лист спрайтов в
  `debug/playtest/studio_sheet.png`, `--daytime=0..1` сутки стоят (0 полночь, 0.5 полдень,
  0.75 золотой час, 0.96 ночь); кадр перетаскивания `--bot=off
  "--input=20:move=684x472,22:press=684x472,40:move=900x640" --stage=2` (с `50:release=900x640`
  и `--frames=53` падает), в `--input` есть `press=XxY` и `release=XxY`; телевизор посреди
  переключения `--stage=2 --bot=off --input=20:click=1508x198 --frames=28`, кулер `click=1204x204`). Фаза студии: `--scene=studio_test --frames=600`; скриншот
  состояния: `--scene=studio_test --no-checks --past=4 [--cash=-16000] [--rescued]
  [--all-bought] --frames=240` (под `--fixed-fps` снимок отстаёт от сцены, поэтому экран
  без `--animate` стоит с первого кадра). Кривые параметров и сцена в ресурс мини-игры:
  `Godot --headless --path thegames -s debug/tools/set_params.gd -- <id> tscn=res://... key=from:to`.
- Мармелад: лист кадров в движении `sh tools/autotest.sh --scene=jelly_test [--game=fit_frame]
  [--screen [--locked]] [--lose] --from=N --every=N --count=N [--crop=x,y,w,h]
  ["--actions=40:down,80:click=710x680"] ["--set=ui_press:0"] --frames=N`, лист в
  `debug/playtest/jelly_sheet.png`. Сцена без автотеста: `Godot --path thegames -- --scene=jelly_test`.
- Всё разом: `sh tools/ci.sh` (модель экономики `python3 tools/model_run.py --check` и
  автотесты систем без окна, пара минут).
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
