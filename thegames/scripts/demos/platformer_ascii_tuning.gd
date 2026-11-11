class_name PlatformerAsciiTuning
extends Resource
## Числа демки платформер × ASCII (#90), ресурс `res://resources/demos/platformer_ascii.tres`.
## Всё по клеткам: герой делает шаг вбок раз в `step_seconds`, по вертикали раз в `vtick`.
## Прыжок: `jump_rows` клеток вверх, `hang_ticks` тиков на вершине, затем падение. Генератор
## уровня (`platformer_ascii_gen.tres`) считает с прыжком на 4 колонки вровень и 3 вверх; эти
## числа должны давать не меньше.

const PATH := "res://resources/demos/platformer_ascii.tres"
const GEN_PATH := "res://resources/demos/platformer_ascii_gen.tres"

@export var lives := 2
@export var step_seconds := 0.08
@export var vtick := 0.06
@export var jump_rows := 2
@export var hang_ticks := 4
## Шаг врага-ходока.
@export var enemy_step := 0.3
## Неуязвимость после возрождения и пауза на смерти.
@export var invulnerable_seconds := 1.2
@export var death_pause := 0.6
## Декор: доля колонок земли с пропом.
@export var prop_chance := 0.03
@export var music_db := -10.0
@export var sfx_db := -8.0


static func load_default() -> PlatformerAsciiTuning:
	var t := load(PATH) as PlatformerAsciiTuning
	return t if t != null else PlatformerAsciiTuning.new()


static func gen() -> PlatformerGenTuning:
	var t := load(GEN_PATH) as PlatformerGenTuning
	return t if t != null else PlatformerGenTuning.new()
