class_name PlatformerBit16Tuning
extends Resource
## Физика и правила демки платформер × 16/32-bit «тропа» (#98), ресурс
## `res://resources/demos/platformer_bit16.tres`. Пиксели мира, секунды; мир шагает 60 раз в
## секунду.

const PATH := "res://resources/demos/platformer_bit16.tres"

@export var lives := 3
@export var gravity := 980.0
## Прыжок: скорость вверх (высота v²/2g ≈ 59 пикселей), запас после края и нажатие заранее.
@export var jump_speed := 340.0
@export var coyote := 0.08
@export var jump_buffer := 0.12
## Бег с инерцией: разгон, торможение без стрелки, разворот, наибольшая скорость; в воздухе
## разгон слабее.
@export var run_max := 150.0
@export var run_accel := 420.0
@export var run_friction := 520.0
@export var run_turn := 900.0
@export var air_accel := 300.0
## Склон тянет вниз долей тяжести; в гору наибольшая скорость меньше на долю наклона.
@export var slope_pull := 0.55
@export var uphill_slow := 0.5
## Присед на B: медленный шаг в приседе (разгон и предел), рост ниже. Слайд: B на скорости не
## ниже `slide_min`, прибавка `slide_boost`, трение; когда скорость падает ниже `slide_to_crouch`,
## герой переходит в присед (или встаёт, если B уже отпущена и над ним нет потолка).
@export var crouch_max := 55.0
@export var crouch_accel := 400.0
@export var slide_min := 110.0
@export var slide_boost := 40.0
@export var slide_max := 280.0
@export var slide_friction := 150.0
@export var slide_to_crouch := 60.0
## Лиана: хват за нижние доли длины, раскачка стрелкой, затухание, прибавка вверх при отпуске,
## сколько нельзя схватить ту же лиану снова.
@export var vine_grab_from := 0.35
@export var vine_grab_radius := 11.0
@export var vine_pump := 260.0
@export var vine_damping := 0.15
@export var vine_max_deg := 72.0
@export var vine_release_up := 150.0
@export var vine_regrab := 0.35
## Удар врага: отброс, неуязвимость; падение в воду, потом возврат.
@export var hurt_knock := 140.0
@export var hurt_up := 200.0
@export var invulnerable_seconds := 1.4
@export var drown_seconds := 0.7
## Бот WIN: решение раз в столько секунд, горизонт прогона вариантов и добор до приземления.
@export var bot_every := 0.1
@export var bot_horizon := 1.1
@export var bot_land_extra := 1.2
@export var music_db := -12.0
@export var sfx_db := -6.0


static func load_default() -> PlatformerBit16Tuning:
	var t := load(PATH) as PlatformerBit16Tuning
	return t if t != null else PlatformerBit16Tuning.new()
