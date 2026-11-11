class_name SettingDef
extends Resource
## Что сеттинг даёт демке (#46, `docs/specs/demos_catalog.md` «Набор ассетов сеттинга»): папку
## спрайтов 8-bit по слотам и цвета фона. Один ресурс на сеттинг в
## `res://resources/settings/<id>.tres`. Слова сеттинга (существительные для названий) живут в
## каталоге конструктора (`CatalogEntry.title_tags`), их уже знают генератор названий и лента.
## Пока у сеттинга нет своего спрайта, берётся пиратский: арт космоса и замков приходит
## отдельной задачей, а петля работает на любом сеттинге сразу.
## ASCII-формат слотов (#88) строкой, не рисунком: глиф, номер чернил в `ascii_palette` и
## слово для легенды на каждый слот `ASCII_SLOTS`. Правила читаемости (проверяет `ascii_test`):
## глифы одного сеттинга попарно различимы, герой самый плотный из не-земли, земля, стена и
## платформа только из `ASCII_TERRAIN_GLYPHS`.

const DIR := "res://resources/settings/"
const FALLBACK_SPRITES := "res://assets/settings/pirates/8bit/"
const IDS: Array[String] = ["pirates", "space", "castles"]
## Слоты сеттинга в ASCII (`demos_catalog.md` «Набор ассетов сеттинга»): `enemy_2` второй боец
## файтинга, `platform` платформа платформера.
const ASCII_SLOTS: Array[StringName] = [&"hero", &"enemy", &"enemy_2", &"rival", &"vehicle", &"shot", &"ball",
		&"goal", &"obstacle", &"bonus", &"finish", &"ground", &"wall", &"platform", &"prop_a", &"prop_b"]
const ASCII_TERRAIN: Array[StringName] = [&"ground", &"wall", &"platform"]
const ASCII_TERRAIN_GLYPHS := ".#=░▒█"

@export var setting: Game.Setting = Game.Setting.PIRATES
@export var id: StringName = &"pirates"
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
## ASCII: фон `[0]` и чернила; на экран один-два цвета, остальные для мелочей.
@export var ascii_palette: Array[Color] = []
@export var ascii_glyphs: Dictionary[StringName, String] = {}
@export var ascii_inks: Dictionary[StringName, int] = {}
@export var ascii_names: Dictionary[StringName, String] = {}

static var _cache: Dictionary[int, SettingDef] = {}


static func of(s: Game.Setting) -> SettingDef:
	if _cache.has(int(s)):
		return _cache[int(s)]
	var d := load(DIR + IDS[s] + ".tres") as SettingDef
	if d == null:
		d = load(DIR + "pirates.tres") as SettingDef
	_cache[int(s)] = d
	return d


## Спрайт слота `name` из папки сеттинга, без него пиратский.
func sprite(name: String) -> Texture2D:
	var path := sprites_8bit + name + ".png"
	if not ResourceLoader.exists(path):
		path = FALLBACK_SPRITES + name + ".png"
	return load(path) as Texture2D


## Глиф слота в ASCII, «?» если слота нет.
func ascii_glyph(slot: StringName) -> String:
	return ascii_glyphs.get(slot, "?")


func ascii_ink(slot: StringName) -> int:
	return ascii_inks.get(slot, 1)


## Строка-легенда под экраном: «☠ матрос · † скелет · $ дублон».
func ascii_legend(slots: Array[StringName]) -> String:
	var parts: Array[String] = []
	for slot in slots:
		parts.append("%s %s" % [ascii_glyph(slot), ascii_names.get(slot, String(slot))])
	return " · ".join(parts)
