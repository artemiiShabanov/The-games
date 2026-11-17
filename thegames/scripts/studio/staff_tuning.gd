class_name StaffTuning
extends Resource
## Числа штата и доски соискателей (`resources/staff.tres`), спека `docs/specs/staff.md`.
## Массивы по ролям идут в порядке `Staff.Role`, внутри три числа по грейдам: джуниор, мидл,
## сеньор, подряд (роль × 3 + грейд).

const PATH := "res://resources/staff.tres"

## Сила эффекта: доля (упрощение мини-игр аспекта, скидка на спринт, скидка на багфикс) или
## штуки (повторы спринта у тимлида). У продюсера и аналитика эффект задаёт сам грейд.
@export var effect: Array[float] = []
## Цена найма и зарплата за релиз.
@export var price: Array[int] = []
@export var salary: Array[int] = []
## Доска: сколько соискателей на старте забега, сколько приходит после релиза, сколько
## релизов соискатель ждёт, шансы грейдов.
@export var board_start := 3
@export var board_add := 2
@export var board_stay := 3
@export var grade_weights: Array[float] = [0.55, 0.32, 0.13]
## Повторов спринта за релиз не больше.
@export var max_replays := 3
## Скидка сеньора-продюсера на разработку сиквелов и ремейков.
@export var producer_discount := 0.1
## Спрос выше этого аналитик-сеньор помечает в конструкторе.
@export var demand_tag_from := 1.05
## Разработчики для картинки студии: один каждые столько релизов.
@export var developer_every := 2

static var _cache: StaffTuning


static func load_default() -> StaffTuning:
	if _cache == null:
		_cache = load(PATH) as StaffTuning
		if _cache == null:
			_cache = StaffTuning.new()
	return _cache


func value(role: Staff.Role, grade: Staff.Grade) -> float:
	var i := int(role) * 3 + int(grade)
	return effect[i] if i < effect.size() else 0.0


func price_of(role: Staff.Role, grade: Staff.Grade) -> int:
	var i := int(role) * 3 + int(grade)
	return price[i] if i < price.size() else 0


func salary_of(role: Staff.Role, grade: Staff.Grade) -> int:
	var i := int(role) * 3 + int(grade)
	return salary[i] if i < salary.size() else 0
