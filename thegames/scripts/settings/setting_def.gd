class_name SettingDef
extends Resource
## Что сеттинг даёт демке (#46, `docs/specs/demos_catalog.md` «Набор ассетов сеттинга»): папку
## спрайтов 8-bit по слотам и цвета фона. Один ресурс на сеттинг в
## `res://resources/settings/<id>.tres`. Слова сеттинга (существительные для названий) живут в
## каталоге конструктора (`CatalogEntry.title_tags`), их уже знают генератор названий и лента.
## Пока у сеттинга нет своего спрайта, берётся пиратский: арт космоса и замков приходит
## отдельной задачей, а петля работает на любом сеттинге сразу.

const DIR := "res://resources/settings/"
const FALLBACK_SPRITES := "res://assets/settings/pirates/8bit/"
const IDS: Array[String] = ["pirates", "space", "castles"]

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
