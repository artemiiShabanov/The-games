class_name CoverData
extends RefCounted
## Обложка коробки игры (`docs/specs/cover.md`) словарём из простых значений, чтобы пережить
## сохранение слота и профиля (`GameRecord.cover`, `GalleryEntry.cover`):
##
##   case: "#hex"                                  цвет пластика коробки
##   front, back: {color, color2: "#hex", fx: int, art: имя} фон стороны, эффект (`FX_NAMES`)
##                                                 и картинка из игры для эффекта «Из игры»
##   title: {font, color, style, x, y, size, rot}  название на лицевой, x и y в долях лица
##   stickers: [{id, side, x, y, size, rot, style}] стикеры: `id` из `CoverStickers.ids_for`
##   shots: [путь, путь]                           кадры плейтеста в двух окнах оборота
##
## На продажи обложка не влияет. Копирайт студии и окна кадров на обороте не убираются.

enum Side { FRONT, BACK }

const FX_NAMES: Array[String] = ["Цвет", "Градиент", "Полосы", "Точки", "Лучи", "Блёстки", "Голограмма", "Фольга", "Из игры"]
## Эффект «Из игры»: фоном картинка из ассетов игры, имя в `art` стороны (`CoverStickers.backgrounds`).
const FX_ART := 8
## Стиль стикера и названия.
const STYLE_NAMES: Array[String] = ["Без обводки", "Белая обводка", "Тёмная обводка", "Тень"]
const FONT_NAMES: Array[String] = ["Жирный", "Лёгкий", "Наклонный", "Узкий", "С засечками", "Машинка", "Плакат", "От руки"]
const SHOT_SLOTS := 2

static var _fonts: Dictionary[int, Font] = {}


static func tuning() -> CoverTuning:
	return CoverTuning.get_default()


static func palette() -> Array[Color]:
	return tuning().colors


static func hex(c: Color) -> String:
	return "#" + c.to_html(false)


static func color(d: Dictionary, key: String, fallback := Color.WHITE) -> Color:
	var v: Variant = d.get(key, null)
	return Color.from_string(v, fallback) if v is String else fallback


## Номер цвета в палитре, ближайший к `c`.
static func palette_index(c: Color) -> int:
	var best := 0
	var best_d := INF
	var colors := palette()
	for i in colors.size():
		var d := Vector3(colors[i].r - c.r, colors[i].g - c.g, colors[i].b - c.b).length_squared()
		if d < best_d:
			best_d = d
			best = i
	return best


static func side(cover: Dictionary, s: int) -> Dictionary:
	var key := "front" if s == Side.FRONT else "back"
	if not cover.get(key) is Dictionary:
		cover[key] = {"color": hex(palette()[10]), "color2": hex(palette()[8]), "fx": 0}
	return cover[key]


static func title(cover: Dictionary) -> Dictionary:
	if not cover.get("title") is Dictionary:
		cover["title"] = {"font": 0, "color": hex(Color.WHITE), "style": 2, "x": 0.5, "y": 0.2, "size": 1.0, "rot": 0.0}
	return cover["title"]


static func stickers(cover: Dictionary) -> Array:
	if not cover.get("stickers") is Array:
		cover["stickers"] = []
	return cover["stickers"]


static func shots(cover: Dictionary) -> Array:
	if not cover.get("shots") is Array:
		cover["shots"] = []
	var list: Array = cover["shots"]
	while list.size() < SHOT_SLOTS:
		list.append("")
	return list


## Шрифт названия по номеру из `FONT_NAMES`. Свой файл в проекте один (Nunito), остальное его
## начертания и системные шрифты с запасными именами.
static func font(i: int) -> Font:
	i = posmod(i, FONT_NAMES.size())
	if _fonts.has(i):
		return _fonts[i]
	var f: Font
	match i:
		0:
			f = Jelly.fun_font(900)
		1:
			var v := FontVariation.new()
			v.base_font = Jelly.fun_font(300)
			v.spacing_glyph = 3
			f = v
		2:
			var v := FontVariation.new()
			v.base_font = Jelly.fun_font(800)
			v.variation_transform = Transform2D(Vector2(1, 0), Vector2(0.24, 1), Vector2.ZERO)
			f = v
		3:
			var v := FontVariation.new()
			v.base_font = Jelly.fun_font(900)
			v.variation_transform = Transform2D(Vector2(0.68, 0), Vector2(0, 1), Vector2.ZERO)
			f = v
		4:
			f = _system(["Georgia", "Times New Roman", "DejaVu Serif", "serif"], 700)
		5:
			f = _system(["Courier New", "Menlo", "Consolas", "DejaVu Sans Mono", "monospace"], 700)
		6:
			f = _system(["Impact", "Arial Black", "Haettenschweiler", "sans-serif"], 400)
		_:
			f = _system(["Marker Felt", "Chalkboard SE", "Comic Sans MS", "Segoe Print", "cursive"], 700)
	_fonts[i] = f
	return f


## Шрифты 1 и 3 набираются заглавными: тонкий вразрядку и узкий плакатный.
static func font_caps(i: int) -> bool:
	i = posmod(i, FONT_NAMES.size())
	return i == 1 or i == 3 or i == 6


static func _system(names: Array, weight: int) -> Font:
	var f := SystemFont.new()
	f.font_names = PackedStringArray(names)
	f.font_weight = weight
	f.allow_system_fallback = true
	return f


static func _contrast(c: Color) -> Color:
	return Color("#1C1B19") if c.get_luminance() > 0.55 else Color.WHITE


## Случайная обложка: два цвета и эффект на сторону, название в верхней трети, крупный стикер
## и несколько мелких на лицевой, пара на обороте, первые кадры плейтеста в окнах. `ids` это
## стикеры игры (`CoverStickers.ids_for`), `shot_paths` снятые кадры, `arts` фоны из игры
## (`CoverStickers.backgrounds`): с ними среди эффектов выпадает и «Из игры».
static func random(rng: RandomNumberGenerator, ids: PackedStringArray, shot_paths: PackedStringArray,
		arts := PackedStringArray()) -> Dictionary:
	var colors := palette()
	var cover := {}
	var a := rng.randi_range(2, colors.size() - 1)
	var b := (a + rng.randi_range(1, 4)) % colors.size()
	cover["case"] = hex(colors[rng.randi_range(0, colors.size() - 1)])
	var fx_max := FX_ART if not arts.is_empty() else FX_ART - 1
	cover["front"] = {"color": hex(colors[a]), "color2": hex(colors[b]), "fx": rng.randi_range(0, fx_max)}
	cover["back"] = {"color": hex(colors[b]), "color2": hex(colors[a]), "fx": rng.randi_range(0, fx_max)}
	if not arts.is_empty():
		cover["front"]["art"] = arts[rng.randi_range(0, arts.size() - 1)]
		cover["back"]["art"] = arts[rng.randi_range(0, arts.size() - 1)]
	var ink := _contrast(colors[a])
	cover["title"] = {
		"font": rng.randi_range(0, FONT_NAMES.size() - 1),
		"color": hex(ink),
		# Обводка противоположного тона: название читается на любом эффекте.
		"style": 2 if ink.get_luminance() > 0.5 else 1,
		"x": 0.5, "y": rng.randf_range(0.14, 0.24),
		"size": rng.randf_range(0.9, 1.25), "rot": snappedf(rng.randf_range(-6.0, 6.0), 0.5),
	}
	var list: Array = []
	if not ids.is_empty():
		var style := rng.randi_range(0, STYLE_NAMES.size() - 1)
		list.append({"id": ids[0], "side": Side.FRONT, "x": 0.5, "y": rng.randf_range(0.56, 0.64),
				"size": rng.randf_range(1.7, 2.2), "rot": snappedf(rng.randf_range(-8.0, 8.0), 0.5), "style": style})
		var extra := rng.randi_range(1, 3)
		for k in extra:
			var id := ids[rng.randi_range(0, ids.size() - 1)]
			var left := k % 2 == 0
			list.append({"id": id, "side": Side.FRONT,
					"x": rng.randf_range(0.14, 0.3) if left else rng.randf_range(0.7, 0.86),
					"y": rng.randf_range(0.42, 0.9), "size": rng.randf_range(0.6, 1.0),
					"rot": snappedf(rng.randf_range(-20.0, 20.0), 0.5), "style": style})
		for k in rng.randi_range(1, 2):
			list.append({"id": ids[rng.randi_range(0, ids.size() - 1)], "side": Side.BACK,
					"x": rng.randf_range(0.14, 0.86), "y": rng.randf_range(0.7, 0.84),
					"size": rng.randf_range(0.6, 0.9), "rot": snappedf(rng.randf_range(-15.0, 15.0), 0.5), "style": style})
	cover["stickers"] = list
	var picked: Array = []
	for k in SHOT_SLOTS:
		picked.append(shot_paths[k % shot_paths.size()] if not shot_paths.is_empty() else "")
	cover["shots"] = picked
	return cover


## Обложка записи по умолчанию: случайная от сида игры, одна и та же при каждом вызове.
static func default_for(record: GameRecord) -> Dictionary:
	var rng := RandomNumberGenerator.new()
	rng.seed = hash([record.seed, record.title, "cover"])
	return random(rng, CoverStickers.ids_for(record.genre, record.tech), record.shots,
			CoverStickers.backgrounds(record.genre, record.tech))
