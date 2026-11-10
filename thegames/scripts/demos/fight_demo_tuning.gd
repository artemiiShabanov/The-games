class_name FightDemoTuning
extends Resource
## Бой, темп и боты демки файтинг × 8-bit (#54), ресурс `res://resources/demos/fighting_bit8.tres`.
## Пиксели виртуального экрана (×6 в карточке), скорости в пикселях в секунду. Бой идёт ровным
## шагом `1 / physics_hz`, длительности приёмов в шагах (при 60 это кадры), так что бой
## детерминирован и проверка в `demo_test` гоняет его без окна тем же кодом (`FightSim`).
## Прямоугольники ударов и тела от точки между ступнями бойца, x вперёд по взгляду, y вверх
## отрицательный.

const PATH := "res://resources/demos/fighting_bit8.tres"

## Шаг боя, раз в секунду.
@export var physics_hz := 60
## Здоровье бойца в начале раунда.
@export var health := 100
## Раунд один: кто больше здоровья через `round_seconds`, тот победил; нокаут раньше.
@export var round_seconds := 60.0
## Отсчёт 3-2-1 до боя и пауза на «KO» или «ВРЕМЯ» перед итогом, секунды.
@export var countdown := 2.4
@export var end_pause := 1.8
## Палуба между бортами, px, и расстояние между бойцами на старте.
@export var arena_width := 240.0
@export var start_gap := 80.0
## Шаг вперёд и назад, px/с.
@export var walk_forward := 48.0
@export var walk_back := 36.0
## Полуширина тела для расталкивания: ближе `2 * push_half` бойцы не сходятся.
@export var push_half := 6.0
## Тело стоя и в приседе. Присед ниже верхнего удара: верхний проходит над головой.
@export var stand_hurt := Rect2(-5, -31, 10, 31)
@export var crouch_hurt := Rect2(-5, -19, 10, 19)
## Верхний удар (A стоя): замах, активные шаги, восстановление; урон, оглушение при попадании
## и в блоке; кулак на уровне лица. Блок стоя держит, присед уходит.
@export var high_startup := 6
@export var high_active := 3
@export var high_recovery := 16
@export var high_damage := 7
@export var high_hitstun := 16
@export var high_blockstun := 9
@export var high_hit := Rect2(4, -26, 14, 6)
## Нижний удар (A в приседе): подсечка у палубы, медленнее и короче верхнего, слабее; блок
## стоя не держит, присед тоже. Защита: отойти за его длину или опередить.
@export var low_startup := 9
@export var low_active := 3
@export var low_recovery := 20
@export var low_damage := 6
@export var low_hitstun := 14
@export var low_hit := Rect2(4, -5, 11, 5)
## Отброс при попадании и в блоке, px; упёрся в борт: отъезжает бьющий. Нокаут отбрасывает дальше.
@export var hit_push := 10.0
@export var block_push := 7.0
@export var ko_push := 24.0
## Стоп-кадр на попадание и блок, шагов.
@export var hitstop := 4
## Нажатая A ждёт, пока боец освободится, столько шагов.
@export var buffer := 6
## Рисование: кадр вытянутой руки или ноги держится ещё столько шагов восстановления.
@export var strike_hold := 5
## Бот WIN читает соперника через `bot_react` шагов: под верхний приседает, от нижнего
## отходит, бьёт в восстановление (стоящего верхним, присевшего нижним), оглушённого добивает.
## Сам бьёт стоящего верхним с полосы, где нижний соперника не достаёт, блок нижним, а
## присевшего ждёт `bot_crouch_wait` шагов. После своего удара выжидает
## `bot_pause_min`..`bot_pause_max` шагов на дистанции `bot_gap` (защищается и в паузе).
@export var bot_react := 2
@export var bot_gap := 24.0
@export var bot_crouch_wait := 50
@export var bot_pause_min := 50
@export var bot_pause_max := 130
## Бот LOSE идёт к сопернику и машет верхним раз в `bot_lose_every` шагов только издалека
## (дальше `bot_lose_far`): не попадает, не блокирует.
@export var bot_lose_every := 40
@export var bot_lose_far := 34.0
@export var music_db := -14.0
@export var sfx_db := -8.0


## Длина удара: от ступней бьющего до дальнего края тела стоящего соперника.
func reach(low: bool) -> float:
	var hit := low_hit if low else high_hit
	return hit.position.x + hit.size.x - stand_hurt.position.x


static func load_default() -> FightDemoTuning:
	var t := load(PATH) as FightDemoTuning
	return t if t != null else FightDemoTuning.new()
