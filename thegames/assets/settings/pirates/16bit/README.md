# Пираты, формат 16/32-bit

Ленты кадров 32×32 рисуются заново в `tools/pixel_sprites16.py` (не из 8-bit, решение
2026-11-12): фигуры из примитивов, потом тень по нижнему и правому краю и чёрная обводка.
Править там, затем `python3 tools/pixel_sprites16.py` и `Godot --headless --path thegames --import`.

Палитра из 16 цветов, индекс это роль (`Bit16Screen.K` … `PINE`, та же в
`resources/settings/pirates.tres`, поле `bit16_colors`): обводка `#161412`, тёмное море
`#1B2A4A`, море `#2F6FB5`, блик воды `#6FB4E8`, небо у горизонта `#BFE3F5`, белый `#F4EFE6`, тень
белого `#C9C2B4`, кожа `#F2C89A`, тень кожи `#C98F5E`, золото `#F2C85A`, тень золота `#C08A2A`,
дерево `#A85A2A`, тень дерева `#6E3418`, красный `#D9432F`, зелень `#3E9B5A`, тень зелени `#1F5F3A`.

Стартовый набор основы (#95): герой сбоку `hero_run` (6 кадров), `hero_jump`; герой со спины
`hero_back` (6); скелет сбоку `enemy_walk` (6) и лицом `enemy_front` (6); дублон `coin` (6);
флаг `flag` (6); палуба `ground` и `ground_inner`; камень `rock`; сундук `chest`; слои фона
`par_sky` (облака 256×48), `par_far` (острова 256×48), `par_mid` (волны 256×32), стыкуются по
краям. Платформер «тропа» (#98) добавил в палитре спрайтов: стойка `hero_idle` (2 кадра), прыжок
`hero_leap` (4), слайд `hero_slide` (2), присед `hero_crouch` (2), вис на лиане `hero_hang` (2), краб `crab_walk`
(4) и попугай `parrot_fly` (4) с красной обводкой опасности, сердце `heart`. В своих палитрах из `tools/pixel_trail16.py`: фон
`par3_back`, `par3_trees`, `par3_bushes` (512×277 и 512×120, без неба), листва над кадром
`canopy_front`; передний план `trail_soil` (булыжный грунт 64×64), `trail_edge` (травяная
кромка), `arch_bark` (ствол-арка), украшения `dec_*`. Гонка «псевдо-3D» (#99) из
`tools/pixel_road16.py`: повозки 160×104 со спины `cart_hero` и `cart_0`..`cart_3` (вымпел
своего цвета; шесть кадров: три крена по два кадра колёс), пальмы `palm` и `palm_b`, камень
`road_rock`, бочка `road_barrel`, знаки `sign_left` и `sign_right`, хижина `road_hut`; горизонт в
своей палитре: `road_sky`, `road_islands`, `road_sea`; цвета дороги лентой `road_colors` (8×1:
светлая и тёмная дорога, бордюр, разметка, песок двумя тонами, дымка). Шутер «до выхода» (#100) из
`tools/pixel_hold16.py`: текстуры 64×64 `wall_planks`, `wall_stone`, `wall_pillar`, `wall_exit`,
`wall_cabin`, `wall_hull`, `wall_cargo`, `floor_planks`, `floor_stone`, `floor_carpet`,
`ceiling_beams`; скелет с мушкетом `skel_walk` (5 ракурсов по 2 кадра), `skel_fire` (2),
`skel_die` (3), с саблей `cut_walk`, `cut_slash`, `cut_die`; ориентиры залов `hold_decor` (6:
бочки, ящики, фонарь, пушка, сундук, штурвал); пистоль `pistol` 128×96 (2), лицо `face` (5
выражений), `key`, `medkit`, пули `shot` (скелета) и `bullet` (героя). Футбол (#101) из `tools/pixel_soccer16.py`: игроки 16×16
`soccer_hero`, `soccer_rival_0`..`2`, `soccer_keeper_hero`, `soccer_keeper_rival` (8 направлений
по 3 кадра бега, 8 подкатов, 8 лежит), мяч `soccer_ball` 8×8 (2, пятиугольник и пятна попиксельно), трава `soccer_grass` 64×64. Битемап (#102) из `tools/pixel_brawl16.py`:
бойцы 96×112 `brawl_hero` (37 кадров), `brawl_thug`, `brawl_knife` (по 23), боцман 128×136
`brawl_boss` (27), лица для HUD `brawl_face_hero`, `_thug`, `_knife`, `_boss` 32×32; улица
`brawl_street` 1664×416 (первые этажи, тротуар, мостовая); эффекты `brawl_fx_hit` 40×40 (4),
`brawl_fx_heavy` 80×64 (5), `brawl_fx_whoosh` 64×40 (3), `brawl_fx_dust` 56×28 (5), стрелка
`brawl_go` 72×44 (2). Ленты битемапа в своих палитрах (у бойца рампы по четыре тона).
Футбол по сеттингу (#96): поле `soccer_field_pirates` (песок), `_castles` (трава), `_space`
(реголит) 64×64 и аут `soccer_out_<сеттинг>` 256×64 (4 кадра: море, брусчатка, звёзды).
Эффекты `tools/pixel_fx16.py`: `fx16_dust` 24×12 (5), `fx16_spark` и `fx16_star` 24×24 (4),
`fx16_flash` 32×32 (3). Все силуэты в палитре сеттинга (кроме слоёв дали и футболистов)
записываются в своей палитре с рампами по четыре тона (`reshade` в `pixel_sprites16.py`). Остальное под пять демок приходит с #96. У космоса и замков своих лент пока нет,
берутся пиратские: сеттинг подключается папкой `assets/settings/<id>/16bit/` и строкой палитры.
