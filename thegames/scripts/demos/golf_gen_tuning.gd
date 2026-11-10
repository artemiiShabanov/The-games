class_name GolfGenTuning
extends Resource
## Настройки генератора поля гольфа (спорт × 8-bit, #52), ресурс `res://resources/demos/sport_gen.tres`.
## Пиксели виртуального экрана (×4 в карточке), мир вида сбоку высотой в экран, y вниз.
## Лунка: ти (палуба-помост) слева, песчаный остров с холмами, иногда пролив с морем, грин на
## палубе выброшенного на берег корабля с люком-лункой, корма стеной справа.

const PATH := "res://resources/demos/sport_gen.tres"

## Лунок в демке, от и до (по сиду).
@export var holes_min := 2
@export var holes_max := 3
## Длина лунки в пикселях (кратна шагу высот), от и до.
@export var length_min := 640
@export var length_max := 1000
## Шаг карты высот, px: высота задана в точках через столько пикселей, между ними прямая.
@export var step := 8
## Поверхность острова по высоте: не выше `ground_top` и не ниже `ground_bottom` (y вниз).
@export var ground_top := 100.0
@export var ground_bottom := 172.0
## Холмы фарвея: опорных точек от и до, между ними косинусная кривая.
@export var hills_min := 3
@export var hills_max := 5
## Самый крутой перепад на шаг вне кромок (px на `step`), иначе мяч не катится, а скачет.
@export var max_rise := 10.0
## Ти: помост из палубы, ширина и отступ от левого края; мяч ставится в его середину.
@export var tee_from := 16
@export var tee_width := 40
## Грин: палуба корабля шириной от и до, приподнята над песком на `deck_lift` от и до; люк не
## ближе `cup_margin` к краям палубы. За грином корма стеной: ширина `stern_width`, высота
## `stern_height` над палубой.
@export var green_min := 112
@export var green_max := 152
@export var deck_lift_min := 4.0
@export var deck_lift_max := 12.0
@export var cup_margin := 28
@export var stern_width := 40
@export var stern_height := 72.0
## Пролив с морем поперёк фарвея: шанс, ширина от и до, не ближе `water_gap` к ти и грину.
@export var water_chance := 0.6
@export var water_min := 48
@export var water_max := 104
@export var water_gap := 96
## Уровень моря в проливе (y, вровень с горизонтом фона: 0,72 высоты экрана), дно пролива
## ниже экрана; берега пролива выше моря хотя бы на `bank_above`.
@export var sea_y := 150.0
@export var sea_floor := 260.0
@export var bank_above := 12.0
## Пар: 3, если от ти до лунки ближе `par4_from` px, иначе 4.
@export var par4_from := 640.0
## Ветер на лунку целыми делениями от −`wind_max` до `wind_max`.
@export var wind_max := 3
## Пропы на песке (пушка, сундук): штук от и до, не ближе `prop_gap` к ти, проливу и грину.
@export var props_min := 0
@export var props_max := 2
@export var prop_gap := 40


static func load_default() -> GolfGenTuning:
	var t := load(PATH) as GolfGenTuning
	return t if t != null else GolfGenTuning.new()
