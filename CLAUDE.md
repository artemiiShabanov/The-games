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
  320:wheel=2@300x500,330:pan=40@1500x500"` (кадр:действие, клавиши
  `key=space|esc|up|down|left|right|r|ctrl|enter|del`, координаты экрана 1920×1080; заметка
  пишет Control под курсором: если там корень сцены, он съедает клики, нужен `MOUSE_FILTER_IGNORE`).
- Одна мини-игра ботом (WIN, затем LOSE): `sh tools/autotest.sh --scene=sprint_runner_test
  --minigame=<id> --frames=3500` (часть мини-игр не укладывается в 1500). Под автотестом `t` и сид
  не из дебаг-меню, а `--t=<0..1>` и `--seed=<n>` (по умолчанию 0 и 1). Прототипы
  мини-игр на пробу кладутся в `resources/minigames/proto/`: в планы не попадают, видны в
  дебаг-меню и `--minigame=<id>`. Демка: `--scene=demo_test --frames=3000` (гонки
  `--genre=racing --frames=9000`, `--seed=N`, `--setting=N`; трасса по сиду текстом
  `Godot --headless --path thegames -s debug/tools/dump_track.gd -- <seed>`; шутер
  `--genre=shooter --frames=6000`, арена и волны текстом `debug/tools/dump_arena.gd -- <seed>`;
  гольф `--genre=sport --frames=9000`, поле текстом `debug/tools/dump_course.gd -- <seed>`;
  кадр гольфа в нужный момент даёт и `--fixed-fps`: `SHOT=debug/playtest/x.png sh
  tools/autotest.sh --scene=demo_test --genre=sport --setting=0 --no-checks --frames=N`, без
  него окно крутит кадры быстрее 60 в секунду и `--frames` не равны времени); файтинг
  `--genre=fighting --frames=7000`, технология `--tech=vector|bit8` (по умолчанию 8-bit, так же
  у `feed_test`); векторная основа (#88): лист контуров `--scene=vector_test --frames=90`, пробная
  демка `--probe [--bugs|--bug=<id>] [--setting=N] --frames=2500`; план соперника и бой ботами без окна текстом
  `debug/tools/dump_fight.gd -- <seed> [count]`; момент боя под скриншот `--no-checks
  --freeze=<с от запуска, с отсчётом>` (демка встаёт на этой секунде, работает у любой демки),
  скриншот паузы `--scene=demo_test --no-checks --pause --frames=240`. Уровень платформера по
  сиду текстом: `Godot --headless --path thegames -s debug/tools/dump_level.gd -- <seed> [from] [to]`. Платформер ×
  вектор «этажи с дырами» (#90): `--scene=demo_test --tech=vector --frames=5000`, этажи по сиду и
  боты без окна текстом `debug/tools/dump_tower.gd -- <seed> [count] [wild,sneeze,coins]`. Гонки ×
  вектор «полосы» (#91): `--scene=demo_test --genre=racing --tech=vector --frames=7000`, заезд по
  сиду и боты без окна текстом `debug/tools/dump_lanes.gd -- <seed> [count] [ice,walls,sneeze]`. Шутер ×
  вектор «башня в центре» (#92): `--scene=demo_test --genre=shooter --tech=vector --frames=6000`,
  волны по сиду и боты без окна текстом
  `debug/tools/dump_turret.gd -- <seed> [count] [through,ice,endless,sneeze]`. Понг (спорт ×
  вектор, #93): `--scene=demo_test --genre=sport --tech=vector --frames=7000`, матч по сиду и
  боты без окна текстом `debug/tools/dump_pong.gd -- <seed> [count] [space,bouncy,wall,frail]`. Дуэль
  на реакцию (файтинг × вектор, #94): `--scene=demo_test --genre=fighting --tech=vector
  --frames=4000`, план по сиду и боты без окна текстом
  `debug/tools/dump_duel.gd -- <seed> [count] [ghost,float,immortal,frail]`. Основа 16/32-bit
  (#95): лист спрайтов и палитры `--scene=bit16_test --frames=120`, пробные демки `--probe=side`
  (вид сбоку с параллаксом) и `--probe=depth` (вид вглубь) `[--bugs|--bug=<id>] [--setting=N]
  --frames=2500`; спрайты рисует `python3 tools/pixel_sprites16.py [--preview out.png]`. Платформер ×
  16/32-bit «тропа» (#98): `--scene=demo_test --tech=bit16 --frames=5000` (хитбоксы поверх кадра
  `--hitboxes`), уровень по сиду и
  боты без окна текстом `debug/tools/dump_trail.gd -- <seed> [count] [wild,sneeze,coins]`. Гонки ×
  16/32-bit «псевдо-3D» (#99): `--scene=demo_test --genre=racing --tech=bit16 --frames=9000`,
  трасса по сиду и боты без окна текстом `debug/tools/dump_road.gd -- <seed> [count]
  [wild,sneeze,walls,finish,nonitro]`. Шутер × 16/32-bit «до выхода» (#100):
  `--scene=demo_test --genre=shooter --tech=bit16 --frames=5000`, карта по сиду и боты без окна
  текстом `debug/tools/dump_hold.gd -- <seed> [count] [wild,sneeze,pass,endless,walls]`. Футбол ×
  16/32-bit (#101): `--scene=demo_test --genre=sport --tech=bit16 --frames=9000`, план по сиду и
  боты без окна текстом `debug/tools/dump_soccer.gd -- <seed> [count] [wild,narrow,sneeze,space]`.
  Битемап × 16/32-bit (#102): `--scene=demo_test --genre=fighting --tech=bit16 --frames=10000`, волны
  по сиду и боты без окна текстом `debug/tools/dump_brawl.gd -- <seed> [count] [wild,immortal,sneeze,ghost]`. Основа low poly
  (#108): лист мешей и палитры `--scene=lowpoly_test --frames=200`, пробные демки `--probe=behind`
  (камера за спиной) и `--probe=first` (от первого лица) `[--bugs|--bug=<id>] [--setting=N]
  [--seed=N] [--bot=lose] --frames=5000`; меши пишет `python3 tools/lowpoly_meshes.py [--list]`. Основа
  «продвинутых» (threed, #118): то же с `--tech=threed` (лист плотных мешей `--frames=700`, пробы
  на `ThreedScreen`), сравнительный лист двух технологий `SHOT=debug/playtest/tech_compare.png
  sh tools/autotest.sh --scene=lowpoly_test --compare --frames=60`; генератор пишет оба набора.
  Модели на скелете и крупные текстуры «продвинутых» (#119, #130): `python3 tools/rig_models.py
  [--list] [--preview out.png]` (его же запускает `lowpoly_meshes.py`), ряд моделей
  `--scene=lowpoly_test --rig --frames=120` (`--rig=compare` рядом с прежней из кусков). Платформер ×
  low poly «тропа вглубь экрана» (#112): `--scene=demo_test --tech=lowpoly --frames=7000`, коса по
  сиду и боты без окна текстом `debug/tools/dump_spit.gd -- <seed> [count] [wild,sneeze,coins]`. Гонки × low poly «кольцо с дрифтом» (#113):
  `--scene=demo_test --genre=racing --tech=lowpoly --frames=17000` (`TIMEOUT=560`), трасса по сиду и
  заезд ботов без окна текстом `debug/tools/dump_ring.gd -- <seed> [count]`. Шутер × low poly «рельсовый тир» (#114):
  `--scene=demo_test --genre=shooter --tech=lowpoly --frames=6000`, маршрут по сиду и бой
  ботов без окна текстом `debug/tools/dump_rail.gd -- <seed> [count]`. Спорт × low poly «броски в кольцо» (#115):
  `--scene=demo_test --genre=sport --tech=lowpoly --frames=6000`, план по сиду и игра ботов без
  окна текстом `debug/tools/dump_hoop.gd -- <seed> [count]`. Файтинг × low poly «один на один сбоку
  в объёме» (#116): `--scene=demo_test --genre=fighting --tech=lowpoly --frames=7000`, план
  соперника по сиду и бой ботов без окна текстом `debug/tools/dump_spar.gd -- <seed> [count]`. Платформер ×
  «продвинутые» «крюк-кошка» (#121): `--scene=demo_test --tech=threed --frames=7000` (кадр в
  движении `--no-checks --fixed-fps --frames=760`), уровень по сиду и боты без окна текстом
  `debug/tools/dump_hook.gd -- <seed> [count]`. Гонки × «продвинутые» «спринт» (#122):
  `--scene=demo_test --genre=racing --tech=threed --frames=10500` (`TIMEOUT=580`, сто сидов идут
  около двух минут), трасса по сиду и заезд ботов без окна текстом
  `debug/tools/dump_sprint.gd -- <seed> [count]`. Шутер × «продвинутые» «оборона аванпоста»
  (#123): `--scene=demo_test --genre=shooter --tech=threed --frames=9000` (`TIMEOUT=560`), план
  волн по сиду и бой ботов без окна текстом `debug/tools/dump_outpost.gd -- <seed> [count]`. Спорт × «продвинутые» «спуск по дюне» (#124):
  `--scene=demo_test --genre=sport --tech=threed --frames=13000` (`TIMEOUT=580`), склон по сиду и спуск ботов без
  окна текстом `debug/tools/dump_dune.gd -- <seed> [count]`. Файтинг × «продвинутые» «один против всех» (#125):
  `--scene=demo_test --genre=fighting --tech=threed --frames=9000`, план волн по сиду и бой
  ботов без окна текстом `debug/tools/dump_fray.gd -- <seed> [count]`. Обзор
  мышью и стиком (#109): `--scene=lowpoly_test --look --frames=600`; движение захваченной мыши в
  `--input` это `кадр:look=DXxDY`. Весь план из 8 с проверкой багов: без `--minigame`,
  `--time-scale=4 --frames=6500`. Оценка мини-игр руками (баланс, 2026-11-18): `Godot --path
  thegames -- --scene=minigame_rating_test [--t=0.5] [--all] [--only=id,id]`, оценки в
  `thegames/debug/ratings/minigame_ratings.json`; ботом `--scene=minigame_rating_test --time-scale=4
  --frames=12000` (`TIMEOUT=600`, кадр карточки оценки `--only=<id> --hold`). Багфикс:
  `--scene=bugfix_test --time-scale=4 --frames=3000`. Вставки: `--scene=event_test --frames=600`; одна на скриншот
  `--no-checks --event=<id> [--mood=N]`; поверх фазы студии `--scene=studio_test --no-checks
  --past=4 --event=<id> --frames=20`. Настройки: `--scene=options_test --frames=30` (кадр `--no-checks`). Палитра смысловых цветов и
  акцентов мини-игр под автотестом `--palette=paper|fog|lacquer|contrast` у любой сцены. Мышь в мини-играх:
  `--scene=mouse_test --frames=1500`.
  Главный экран забега: `--scene=hub_test --frames=60`, кадр `--no-checks
  [--past=N] [--pop=money|upgrades|release|offer|stream|box|board|staff]` (`board` доска соискателей, `staff` штат); экран после релиза (#133) `--after`
  (`--after=all` все волны отклика сразу, `--pop=bet|wave`; `--pop=game` карточка игры с полки). Галерея: `--scene=gallery_test --time-scale=4 --frames=2500`,
  кадр `--no-checks [--empty] [--studios]`; профиль `--scene=profile_test --frames=30`. Петля M1 целиком (три релиза ботом со сверкой денег): `sh tools/autotest.sh --loop
  --time-scale=4 --frames=6500` (`--releases=N` другое число, `--draw` разыгрывает стартовую пару как в игре, `--cap=N` свой кап, `--broke-at=N` банкротство перед фазой студии релиза N, `--remake` студия с вектором и «Ремейками», бот берёт ремейк (`--remake=lowpoly` с 3D вместо вектора), `--techs` студия со всеми четырьмя купленными технологиями, `--start-tech=N` старт с технологии N, `--refuse-events`
  бот отвечает на вставки последним вариантом; `--after` бот идёт путём игрока после релиза: ставит на критиков, прокачка ждёт на главном экране; `--slot=N` сохранять в тестовый слот, `--resume`
  продолжить из него). Главная сцена проекта это меню (#71): под автотестом без `--menu` оно
  сразу открывает игру; меню кадром `--menu --frames=60` (`--settings` экран сеттингов поверх). Сеттинги и достижения (#139): на главном экране `--scene=hub_test --no-checks --pop=settings
  [--achieved=treasure,ten] [--buy-setting=ninja]`, пилюля достижения `--pop=toast`; условия и «новый сеттинг» проверяет `profile_test`; редкость
  достижений моделью `python3 tools/model_run.py --achievements`. Студия на фоне (#80): `--scene=studio_backdrop_test --frames=600`
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
- Сверка модели (#72): `sh tools/autotest.sh --loop --calm --hands=0.75 --refuse-events --cap=12
  --releases=12 --ledger=debug/playtest/ledger_m2.json --time-scale=4 --frames=40000` (долго,
  `TIMEOUT=1500`), затем `python3 tools/model_run.py --replay thegames/debug/playtest/ledger_m2.json`;
  таблица M2 `--m2 [--mid] [--events]`, M3 `--m3 [--start=vector|8bit|16bit|cheap] [--mid]` и сводка
  `--m3-summary [--events]`; M4 `--m4 [--events]` (ниши пяти технологий, старты × руки, вопросы) и `--m4 --start=vector|8bit|16bit|lowpoly|3d [--mid]`; сверка на трёх технологиях: та же петля с `--techs` (шаг ci
  `model M3 replay`).
- Полнота сеттингов (#135): `python3 tools/check_settings.py [<id>]` сводка и «чего не хватает» по
  семействам, `--check` для ci (сеттинги с `complete = true` в ресурсе). Любая демка на чужом
  сеттинге под автотестом пишет заметку «сеттинг …: подмен N» со списком взятого у пиратов,
  `--strict-setting` делает подмену провалом; все 25 демок: `sh tools/setting_matrix.sh <n>
  [tech]` (`STRICT=0` только сводка, около сорока минут; в ci для готовых сеттингов по
  `SETTINGS_MATRIX=1`).
- Набор low poly и «продвинутых» космоса (#136): модули `tools/space_mesh_*.py` и
  `tools/space_rig_*.py`, пишутся тем же `python3 tools/lowpoly_meshes.py`. Лист модуля без Godot:
  `python3 tools/space_mesh_big.py --preview out.png` (три вида и атлас, рендер
  `tools/mesh_preview.py`); в игре `--scene=lowpoly_test --setting=1 [--tech=threed]`.
- Набор 8-bit космоса (#136): модули `tools/space8_*.py`, пишутся тем же `python3
  tools/pixel_sprites.py`; лист `python3 tools/space8.py --preview out.png`.
- Набор 16/32 другого сеттинга (#136): модули `tools/space16.py` и `tools/space_*16.py`, пишутся
  тем же `python3 tools/pixel_sprites16.py`; лист одного модуля `python3 tools/space_road16.py
  --preview out.png`; проверка `sh tools/setting_matrix.sh 1 bit16`.
- Наборы остальных сеттингов (#137): модули-зеркала космоса `tools/<id>8*.py`, `<id>16.py`,
  `<id>_*16.py`, `<id>_mesh_*.py`, `<id>_rig_*.py`, список сеттингов в `tools/setting_sets.py`; пишут
  их те же три генератора. Номера `--setting=N`: 0 пираты, 1 космос, 2 замки, 3 зомби, 4
  супергерои, 5 фэнтези, 6 сладости, 7 ниндзя, 8 динозавры, 9 офис. Листы кадров сеттинга (шесть
  на технологию, `debug/playtest/shots/<id>_<tech>.jpg`): `sh tools/setting_shots.sh <n> [tech]`.
- Фоны карточек конструктора: `python3 tools/card_art.py` пишет `assets/cards/` из ассетов и
  кадров демок (`--capture` переснимает кадры, нужно окно; `--preview out.png` лист). У новых
  картинок в `.import` включить `mipmaps/generate=true`.
- Музыка (#87): `python3 tools/music.py --write` пишет темы и ударные в `assets/music/`
  (нужен sox), на слух вне игры `--themes <tech>` и `--pilot` (mp3 в `debug/playtest/music/`),
  `--one <сеттинг> <tech> <жанр> out.mp3`; в игре дебаг-меню «Музыка». Заглавная тема меню и главного экрана забега: `python3 tools/main_theme.py [--preview]` (`assets/music/main_theme.ogg`, с `--preview` mp3 на две петли в `debug/playtest/music/`).
- Иконка окна и приложения: `python3 tools/app_icon.py [--preview out.png]` пишет `thegames/icon.png`.
- Портреты внешних персонажей (#140): `python3 tools/portraits.py` пишет листы 24×24 в
  `assets/portraits/`, лист всех настроений `--preview out.png`; в игре вставка
  `--scene=event_test --no-checks --event=<id> [--mood=N]` и лента `--scene=feed_test` (`--summary` лента итогов релиза с первой неделей и оценкой студии).
- Окружение сеттинга в 3D (#147): свет, небо, туман и основание мира лежат в ресурсе сеттинга
  (`SettingEnv`), не в `lowpoly.tres` и `threed.tres`. Вид основания под кадр: `--base=liquid|void|solid`
  у любой 3D-демки (`--scene=demo_test --tech=threed --setting=1 --base=liquid --no-checks
  --frames=520`), в дебаг-меню «3D: основание мира».
- Язык (2026-11-18): переводы `thegames/locale/<id>.po`, ключ это русский текст, `Lang` в
  `scripts/menu/lang.gd`. Под автотестом `--lang=en` у любой сцены; экран выбора языка первого
  запуска `--menu --first-launch --frames=60`.
- Сборки (2026-11-18): `sh tools/build.sh [macos|windows]` пишет `builds/macos/Studio Running.zip`
  (universal arm64 + x86_64, ad-hoc подпись: на другом маке первый запуск через «Открыть» в
  контекстном меню) и `builds/windows/StudioRunning.exe` (x86_64, один файл). Пресеты
  `thegames/export_presets.cfg`, шаблоны экспорта Godot 4.7.2 в `~/Library/Application
  Support/Godot/export_templates/4.7.2.stable` (`macos.zip` из официального .tpz).
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

- Тексты (`STYLE.md`, «Тексты»): мета-тексты сухие и короткие, реплики персонажей живые. Игрок
  видит «игра», «продажи», «улучшения», «повтор спринта»; «демка», «хвост», «прокачка»,
  «переигровка» это рабочие слова кода и спек.

- Технологии для игрока: примитив, ретро, 2D, 3D, продвинутые; в коде, файлах, флагах и спеках
  рабочие названия vector (вектор), bit8 (8-bit), bit16 (16/32-bit), lowpoly, threed (3D).

- GDScript со статической типизацией; `var x := f()` падает, если `f` возвращает Variant.
- `snake_case` функции и переменные, `PascalCase` классы и ноды, сигналы вверху скрипта.
- Тюнинг-числа только в `resources/*.tres`, не в коде сцен.
- Трейлер коммита: `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`.
