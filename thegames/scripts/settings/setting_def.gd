class_name SettingDef
extends Resource
## Что сеттинг даёт демке (#46, `docs/specs/demos_catalog.md` «Набор ассетов сеттинга»): папку
## спрайтов 8-bit по слотам и цвета фона. Один ресурс на сеттинг в
## `res://resources/settings/<id>.tres`. Слова сеттинга (существительные для названий) живут в
## каталоге конструктора (`CatalogEntry.title_tags`), их уже знают генератор названий и лента.
## Пока у сеттинга нет своего спрайта, берётся пиратский: арт космоса и замков приходит
## отдельной задачей, а петля работает на любом сеттинге сразу.

const DIR := "res://resources/settings/"
const PIRATES_DIR := "res://assets/settings/pirates/"
const FALLBACK_SPRITES := "res://assets/settings/pirates/8bit/"
const IDS: Array[String] = ["pirates", "space", "castles"]
const FALLBACK_SPRITES_16 := "res://assets/settings/pirates/16bit/"
const FALLBACK_MESHES := "res://assets/settings/pirates/lowpoly/"
## Слоты сеттинга в векторе (#88) и 8-bit спрайт, с силуэта которого снимается контур
## (`VectorShapes`); без своего спрайта сеттинга берётся пиратский, как в 8-bit.
const VECTOR_SLOTS: Dictionary[StringName, String] = {
	&"hero": "hero_run_0", &"enemy": "enemy_0", &"enemy_2": "parrot_0", &"rival": "rival_0",
	&"vehicle": "boat_0", &"shot": "shoot_shot", &"ball": "golf_ball", &"goal": "golf_cup",
	&"obstacle": "race_rock", &"bonus": "coin", &"finish": "flag", &"prop_a": "checkpoint",
	&"prop_b": "shoot_chest",
}
## Чернила слота в векторе: 1 луч (мир), 2 акцент (герой, своё, бонусы), 3 опасность (враги).
const VECTOR_INKS: Dictionary[StringName, int] = {
	&"hero": 2, &"vehicle": 2, &"bonus": 2, &"enemy": 3, &"enemy_2": 3, &"rival": 3, &"shot": 3,
}

@export var setting: Game.Setting = Game.Setting.PIRATES
@export var id: StringName = &"pirates"
## Набор готов целиком (#135, `docs/specs/settings.md`): ни одного слота у пиратов сеттинг не
## берёт. Готовые проверяет `tools/check_settings.py --check` и шаг ci.
@export var complete := false
## Папка спрайтов 8-bit: `hero_run_0.png`, `enemy_0.png`, `coin.png` и остальные слоты.
@export var sprites_8bit := "res://assets/settings/pirates/8bit/"
## Фон вида сбоку: полосы неба сверху вниз, светило, полоса горизонта с бликами, силуэты на
## горизонте (острова, кратеры, холмы) в двух тонах.
@export var sky_bands: Array[Color] = []
@export var sun := Color.WHITE
@export var horizon := Color.WHITE
@export var horizon_light := Color.WHITE
@export var silhouette := Color.WHITE
@export var silhouette_dark := Color.WHITE
## 16/32-bit (#95): папка лент кадров 32×32 (`hero_run.png` это шесть кадров подряд) и палитра из
## 16 цветов, индекс это роль (`Bit16Screen.K` … `PINE`). Нет своего файла или палитры: берутся
## пиратские, так что сеттинг подключается одной папкой и одной строкой палитры.
@export var sprites_16bit := "res://assets/settings/pirates/16bit/"
@export var bit16_colors: Array[Color] = []
## Low poly (#108): папка мешей слотов с атласами (`hero.tres`, `hero.png`) и текстур уровня
## (`tex_sand.png`), всё пишет `tools/lowpoly_meshes.py`; восемь цветов HUD (индекс это роль
## `LowpolyScreen.GROUND` … `DARK`) и цвет тумана у горизонта. Нет своего файла или цветов:
## берутся пиратские. 3D (#118) берёт те же меши.
@export var meshes_lowpoly := "res://assets/settings/pirates/lowpoly/"
@export var lowpoly_colors: Array[Color] = []
@export var lowpoly_sky := Color(0.61, 0.8, 0.91)
## Окружение в 3D (#147): свет, небо, туман и основание мира, отдельно для low poly и для
## «продвинутых». Нет своего: берётся пиратское.
@export var env_lowpoly: SettingEnv
@export var env_threed: SettingEnv
## Вектор (#88): фон `[0]` и чернила луча: 1 мир, 2 акцент, 3 опасность. На экран один-два
## цвета луча, третий только у врагов.
@export var vector_colors: Array[Color] = []
## Своя форма слота вместо снятой с силуэта, когда та не читается: замкнутые ломаные в
## пикселях спрайта от его центра.
@export var vector_shapes: Dictionary[StringName, Array] = {}

## Слова сеттинга заглавными для подписей HUD демок и штампов багов (#148): `hero` герой, `team`
## его команда, `enemies` рядовые враги во множественном, `boss` главный враг, `brute` здоровяк
## битемапа. Все мужского рода или множественного числа, как помечено: штампы согласуют с ними
## прилагательное.
@export var words: Dictionary[StringName, String] = {}

const WORD_KEYS: Array[StringName] = [&"hero", &"team", &"enemies", &"boss", &"brute"]

static var _cache: Dictionary[int, SettingDef] = {}
## Что сеттинг взял у пиратов с последнего `borrowed_reset` (#135): ключ «формат/имя».
static var _borrowed: Dictionary[String, bool] = {}


static func of(s: Game.Setting) -> SettingDef:
	if _cache.has(int(s)):
		return _cache[int(s)]
	var d := load(DIR + IDS[s] + ".tres") as SettingDef
	if d == null:
		d = load(DIR + "pirates.tres") as SettingDef
	_cache[int(s)] = d
	return d


## Подмены на пиратский набор с последнего сброса, по алфавиту. Демка под автотестом пишет
## их в лог, готовый сеттинг обязан дать пустой список.
static func borrowed() -> PackedStringArray:
	var out := PackedStringArray(_borrowed.keys())
	out.sort()
	return out


static func borrowed_reset() -> void:
	_borrowed.clear()


func _borrow(format: String, name: String) -> void:
	if setting != Game.Setting.PIRATES:
		_borrowed[format + "/" + name] = true


## Подмена по итоговому пути: файл нашёлся, но лежит в наборе пиратов. Ловит и сеттинг, у
## которого папка формата не задана и по умолчанию смотрит в пиратскую.
func _borrow_path(path: String, format: String, name: String) -> void:
	if path.begins_with(PIRATES_DIR) and ResourceLoader.exists(path):
		_borrow(format, name)


## Слово сеттинга по ключу; без своего пиратское, и это подмена.
func word(key: StringName) -> String:
	if words.has(key):
		return words[key]
	var base := of(Game.Setting.PIRATES)
	if base != self:
		_borrow("words", String(key))
	return base.words.get(key, String(key).to_upper())


## Текст с подстановкой слов сеттинга: «БЕССМЕРТНЫЙ {boss}».
func fill(text: String) -> String:
	if not text.contains("{"):
		return text
	var out := text
	for key: StringName in WORD_KEYS:
		var mark := "{%s}" % key
		if out.contains(mark):
			out = out.replace(mark, word(key))
	return out


## Спрайт слота `name` из папки сеттинга, без него пиратский.
func sprite(name: String) -> Texture2D:
	var path := sprites_8bit + name + ".png"
	if not ResourceLoader.exists(path):
		path = FALLBACK_SPRITES + name + ".png"
	_borrow_path(path, "8bit", name)
	return load(path) as Texture2D


## Лента кадров 16/32 по имени из папки сеттинга, без неё пиратская.
func sprite16(name: String) -> Texture2D:
	var path := sprites_16bit + name + ".png"
	if not ResourceLoader.exists(path):
		path = FALLBACK_SPRITES_16 + name + ".png"
	# Поле футбола `soccer_field_<id>` лежит в пиратской папке под именем сеттинга: это своё.
	if not name.ends_with("_" + String(id)):
		_borrow_path(path, "16bit", name)
	return load(path) as Texture2D if ResourceLoader.exists(path) else null


## Палитра 16/32 сеттинга, без своей пиратская.
func colors16() -> Array[Color]:
	if bit16_colors.size() >= 16:
		return bit16_colors
	_borrow("16bit", "палитра")
	return SettingDef.of(Game.Setting.PIRATES).bit16_colors if setting != Game.Setting.PIRATES else bit16_colors


## Меш слота low poly по имени из папки сеттинга, без него пиратский. `threed` берёт плотный
## набор «продвинутых» (#118) из соседней папки `threed`.
func model(name: String, threed := false) -> LowpolyModelDef:
	var path := _mesh_folder(meshes_lowpoly, threed) + name + ".tres"
	if not ResourceLoader.exists(path):
		path = _mesh_folder(FALLBACK_MESHES, threed) + name + ".tres"
	_borrow_path(path, "threed" if threed else "lowpoly", name)
	return load(path) as LowpolyModelDef if ResourceLoader.exists(path) else null


## Модель слота на скелете для «продвинутых» (#119, #130) из папки `rig` сеттинга, без неё
## пиратская; `null`, если у слота такой нет (реквизит остаётся жёстким).
func rig(name: String) -> RigModelDef:
	var path := meshes_lowpoly.replace("/lowpoly/", "/rig/") + name + ".tres"
	if not ResourceLoader.exists(path):
		path = FALLBACK_MESHES.replace("/lowpoly/", "/rig/") + name + ".tres"
	_borrow_path(path, "rig", name)
	return load(path) as RigModelDef if ResourceLoader.exists(path) else null


static func _mesh_folder(lowpoly_folder: String, threed: bool) -> String:
	return lowpoly_folder.replace("/lowpoly/", "/threed/") if threed else lowpoly_folder


## Текстура уровня low poly по имени (`sand`, `planks`, `water`, `rock`, `sail`, `sky`), без неё
## пиратская.
func texture_lowpoly(name: String, threed := false) -> Texture2D:
	var path := _mesh_folder(meshes_lowpoly, threed) + "tex_" + name + ".png"
	if not ResourceLoader.exists(path):
		path = _mesh_folder(FALLBACK_MESHES, threed) + "tex_" + name + ".png"
	_borrow_path(path, "threed" if threed else "lowpoly", "tex_" + name)
	return load(path) as Texture2D if ResourceLoader.exists(path) else null


## Цвета HUD low poly сеттинга, без своих пиратские; с ними и пиратский туман.
func colors_lowpoly() -> Array[Color]:
	if lowpoly_colors.size() >= LowpolyScreen.ROLES or setting == Game.Setting.PIRATES:
		return lowpoly_colors
	_borrow("lowpoly", "палитра")
	return SettingDef.of(Game.Setting.PIRATES).lowpoly_colors


## Окружение сеттинга для технологии, без своего пиратское.
func env(threed := false) -> SettingEnv:
	var e := env_threed if threed else env_lowpoly
	if e != null:
		return e
	_borrow("threed" if threed else "lowpoly", "окружение")
	var pirates := SettingDef.of(Game.Setting.PIRATES)
	e = pirates.env_threed if threed else pirates.env_lowpoly
	return e if e != null else SettingEnv.new()


## Цвет неба и тумана: свой, если у сеттинга свои цвета HUD или своё окружение.
func sky_lowpoly() -> Color:
	if lowpoly_colors.size() >= LowpolyScreen.ROLES or env_lowpoly != null or setting == Game.Setting.PIRATES:
		return lowpoly_sky
	return SettingDef.of(Game.Setting.PIRATES).lowpoly_sky


## Контуры слота в векторе: своя форма из ресурса или снятая с силуэта 8-bit спрайта.
func vector_contours(slot: StringName) -> Array[PackedVector2Array]:
	var out: Array[PackedVector2Array] = []
	if vector_shapes.has(slot):
		for c in vector_shapes[slot]:
			out.append(PackedVector2Array(c))
		return out
	return VectorShapes.of_texture(sprite(VECTOR_SLOTS.get(slot, "coin")))


func vector_ink(slot: StringName) -> int:
	return VECTOR_INKS.get(slot, 1)
