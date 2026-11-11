class_name StudioSprites
extends RefCounted
## Пиксель-арт студии на фоне (#80): текстовые карты, из которых собираются текстуры. Один цвет
## `studio-ink` на фоне `bg` (STYLE «Студия»), тона это доли смешения фона с чернилами:
## `#` линия, `+` средний, `-` светлый, `o` фон (заслоняет то, что позади), `.` прозрачно.
## Доли тонов в `resources/studio_backdrop.tres`. Карты правятся прямо здесь; лист всех
## спрайтов (`sheet`): `sh tools/autotest.sh --scene=studio_backdrop_test --sheet --frames=5`.
## Крупные рамки (стена, окна, доска, дверь) строятся функциями ниже, а не картами.

## Человечки 8 в ширину, якорь посередине снизу. Безликие: со спины и спереди одинаковы.
const MAPS := {
	"stand": [
		"...##...",
		"..####..",
		"..####..",
		"...##...",
		".######.",
		".######.",
		"..####..",
		"..#..#..",
		"..#..#..",
	],
	"walk0": [
		"...##...",
		"..####..",
		"..####..",
		"...##...",
		".######.",
		".######.",
		"..####..",
		"..#..#..",
		".#....#.",
	],
	"walk1": [
		"........",
		"...##...",
		"..####..",
		"..####..",
		"...##...",
		".######.",
		".######.",
		"..####..",
		"...##...",
	],
	"hand_head": [
		"...##.#.",
		"..#####.",
		"..####..",
		"...##...",
		".#####..",
		".#####..",
		"..####..",
		"..#..#..",
		"..#..#..",
	],
	"wave0": [
		"#..##..#",
		"#.####.#",
		"#.####.#",
		".#.##.#.",
		"..####..",
		"..####..",
		"..####..",
		"..#..#..",
		"..#..#..",
	],
	"wave1": [
		"...##...",
		"..####..",
		"#.####.#",
		"##.##.##",
		"..####..",
		"..####..",
		"..####..",
		"..#..#..",
		"..#..#..",
	],
	"sit0": [
		"...##...",
		"..####..",
		"..####..",
		"...##...",
		".######.",
		".######.",
		".++++++.",
		".+....+.",
	],
	"sit1": [
		"...##...",
		"..####..",
		"..####..",
		"...##...",
		"#######.",
		".######.",
		".++++++.",
		".+....+.",
	],
	"sit2": [
		"...##...",
		"..####..",
		"..####..",
		"...##...",
		".#######",
		".######.",
		".++++++.",
		".+....+.",
	],
	"stretch": [
		"#..##..#",
		"#.####.#",
		"#.####.#",
		".#.##.#.",
		"..####..",
		".######.",
		".++++++.",
		".+....+.",
	],
	"sleep": [
		"........",
		"..####..",
		".######.",
		".######.",
		".++++++.",
		".+....+.",
	],
	"chair": [
		".++++++.",
		".+oooo+.",
		".++++++.",
		".+....+.",
	],
	# Мелочь в руках и над головой.
	"cup": [
		"##",
		"##",
	],
	"tablet": [
		"###",
		"#o#",
		"#o#",
		"###",
	],
	"phone": [
		"#",
		"#",
	],
	"bubble": [
		".####.",
		"#oooo#",
		"#oooo#",
		".####.",
		".#....",
	],
	"zz": [
		"###",
		".#.",
		"###",
	],
	# Стол в три четверти: столешница сверху, перед, ножки.
	"desk": [
		"######################",
		"#--------------------#",
		"#--------------------#",
		"#--------------------#",
		"######################",
		"#++++++++++++++++++++#",
		"######################",
		".#..................#.",
		".#..................#.",
	],
	"monitor": [
		"##########",
		"#oooooooo#",
		"#oooooooo#",
		"#oooooooo#",
		"##########",
		"....##....",
		"..######..",
	],
	"monitor_a": [
		"##########",
		"#o+++o++o#",
		"#oo++++oo#",
		"#o++oooo##",
		"##########",
		"....##....",
		"..######..",
	],
	"monitor_b": [
		"##########",
		"#o++o+++o#",
		"#oo+++ooo#",
		"#o+++++oo#",
		"##########",
		"....##....",
		"..######..",
	],
	"monitor_off": [
		"##########",
		"#++++++++#",
		"#++++++++#",
		"#++++++++#",
		"##########",
		"....##....",
		"..######..",
	],
	# Монитор тестировщика: человечек прыгает по платформе.
	"monitor_game_a": [
		"##########",
		"#oooooooo#",
		"#ooo#oooo#",
		"#+++++ooo#",
		"##########",
		"....##....",
		"..######..",
	],
	"monitor_game_b": [
		"##########",
		"#oooo#ooo#",
		"#oooooooo#",
		"#+++++o++#",
		"##########",
		"....##....",
		"..######..",
	],
	# Боковые мониторы переигровок, повёрнуты к сидящему.
	"monitor_side_l": [
		"#####.",
		"#ooo##",
		"#ooo##",
		"#ooo##",
		"#####.",
		"..##..",
		".####.",
	],
	"monitor_side_r": [
		".#####",
		"##ooo#",
		"##ooo#",
		"##ooo#",
		".#####",
		"..##..",
		".####.",
	],
	# Мелочь на столе.
	"mug": [
		"##.",
		"#o#",
		"##.",
	],
	"papers": [
		".###",
		"#oo#",
		"###.",
	],
	"lamp": [
		".##.",
		"#oo#",
		"..#.",
		".##.",
	],
	"plant_mini": [
		"#.#",
		".#.",
		"###",
		"###",
	],
	"gamepad": [
		".####.",
		"#o##o#",
		"##..##",
	],
	"coffee": [
		"..######..",
		"..#oooo#..",
		"..#o++o#..",
		"..#oooo#..",
		"..######..",
		"..#+..+#..",
		"..#+..+#..",
		"..######..",
		"##########",
		"#--------#",
		"##########",
		"#++++++++#",
		"#++++++++#",
		"##########",
	],
	"plant": [
		"..#..#..",
		".#.#.#..",
		"#.###.#.",
		".#.#.#.#",
		"..###.#.",
		"...#....",
		"..####..",
		"..#oo#..",
		"..#oo#..",
		"..####..",
	],
	"plant_tall": [
		"...#....",
		"..#.#.#.",
		".#.#.#..",
		"#.###.#.",
		".#.#.#.#",
		"..###.#.",
		".#.#.#..",
		"..###...",
		"...#....",
		"...#....",
		"..####..",
		".#oooo#.",
		".#oooo#.",
		"..####..",
	],
	"boxes": [
		"..######....",
		"..#oooo#....",
		"..#o##o#....",
		"..######....",
		"##########..",
		"#oooo#oooo#.",
		"#o##o#o##o#.",
		"###########.",
	],
	"sofa": [
		"..################..",
		".#oooooooooooooooo#.",
		".#oooooooooooooooo#.",
		"####################",
		"#+#--------------#+#",
		"#+#--------------#+#",
		"#+################+#",
		"####################",
		".#................#.",
	],
	"clock": [
		"..#####..",
		".#ooooo#.",
		"#ooo#ooo#",
		"#ooo#ooo#",
		"#ooo##oo#",
		"#ooooooo#",
		".#ooooo#.",
		"..#####..",
	],
	# Сиквелы: полка с коробками игр.
	"shelf": [
		"##################",
		"#oooooooooooooooo#",
		"#o#+#+#+#oooooooo#",
		"#o#+#+#+#o#+#oooo#",
		"#o#+#+#+#o#+#oooo#",
		"##################",
		"#oooooooooooooooo#",
		"#ooo#+#+#+#+#+ooo#",
		"#ooo#+#+#+#+#+ooo#",
		"#ooo#+#+#+#+#+ooo#",
		"##################",
		"#oooooooooooooooo#",
		"#o#+#+#oooo#+#+#o#",
		"#o#+#+#oooo#+#+#o#",
		"#o#+#+#oooo#+#+#o#",
		"##################",
		"#++++++++++++++++#",
		"##################",
		"#................#",
	],
	# Ремейки: архивный шкаф с ящиками.
	"cabinet": [
		"##############",
		"#------------#",
		"##############",
		"#oooooooooooo#",
		"#oooo####oooo#",
		"#oooooooooooo#",
		"##############",
		"#oooooooooooo#",
		"#oooo####oooo#",
		"#oooooooooooo#",
		"##############",
		"#oooooooooooo#",
		"#oooo####oooo#",
		"#oooooooooooo#",
		"##############",
		"#............#",
	],
	# Техника на стойке у стены: от ASCII до 3D.
	"tech_ascii": [
		"############",
		"#++++++++++#",
		"#+o+++++++##",
		"#++o++++++##",
		"#+o+ooo+++##",
		"#++++++++++#",
		"############",
		".#--------#.",
		"############",
	],
	"tech_bit8": [
		"#.......#.....",
		".#.....#......",
		"..#...#.......",
		"##############",
		"#oooooooooo#+#",
		"#oo#ooooooo#o#",
		"#o###oooooo#+#",
		"#oooooo##oo#o#",
		"#oooooooooo#+#",
		"##############",
		".#..........#.",
	],
	"tech_bit16": [
		"....##########....",
		"....#oooooooo#....",
		"###.#o++oooo+#.###",
		"#o#.#oooo+ooo#.#o#",
		"###.#o+++o+oo#.###",
		"#o#.##########.#o#",
		"###.....##.....###",
		"......######......",
	],
	"tech_lowpoly": [
		"..........#####.",
		"##########+o+o+#",
		"#oooo#ooo##+++++#",
		"#ooo#o#oo##ooooo#",
		"#oo#ooo#o##ooooo#",
		"#o#######o##+++++#",
		"##########.#ooooo#",
		"....##.....#ooooo#",
		"..######...#######",
	],
	"tech_server": [
		"############",
		"#+o++++++++#",
		"#++++++++++#",
		"############",
		"#+o++++++++#",
		"#++++++++++#",
		"############",
		"#+o++++++++#",
		"#++++++++++#",
		"############",
		"#+o++++++++#",
		"#++++++++++#",
		"############",
		"#++++++++++#",
		"#++++++++++#",
		"############",
		".#........#.",
	],
	"tech_server_b": [
		"############",
		"#++o+++++++#",
		"#++++++++++#",
		"############",
		"#+o+o++++++#",
		"#++++++++++#",
		"############",
		"#++++++++++#",
		"#++++++++++#",
		"############",
		"#+o+o++++++#",
		"#++++++++++#",
		"############",
		"#++++++++++#",
		"#++++++++++#",
		"############",
		".#........#.",
	],
	# Плакаты жанров: рамка и значок внутри, по `Game.Genre`.
	"poster_platformer": [
		"############",
		"#oooooooooo#",
		"#oooooo##oo#",
		"#oooooo##oo#",
		"#oooo#ooooo#",
		"#ooo###oooo#",
		"#oooo#ooooo#",
		"#ooo#o#oooo#",
		"#oooooooooo#",
		"#o########o#",
		"#oooooooooo#",
		"#oooooooooo#",
		"############",
	],
	"poster_racing": [
		"############",
		"#oooooooooo#",
		"#o#ooooooo##",
		"#o#++##++oo#",
		"#o#++##++oo#",
		"#o###++##oo#",
		"#o###++##oo#",
		"#o#ooooooo##",
		"#o#oooooooo#",
		"#o#oooooooo#",
		"#o#oooooooo#",
		"#oooooooooo#",
		"############",
	],
	"poster_shooter": [
		"############",
		"#oooooooooo#",
		"#oooo#ooooo#",
		"#oo#####ooo#",
		"#o#oo#oo#oo#",
		"#o#ooooo#oo#",
		"######o#####",
		"#o#ooooo#oo#",
		"#o#oo#oo#oo#",
		"#oo#####ooo#",
		"#oooo#ooooo#",
		"#oooooooooo#",
		"############",
	],
	"poster_sport": [
		"############",
		"#oooooooooo#",
		"#oooooooooo#",
		"#ooo####ooo#",
		"#oo#++++#oo#",
		"#o#+#++#+#o#",
		"#o#++##++#o#",
		"#o#+#++#+#o#",
		"#oo#++++#oo#",
		"#ooo####ooo#",
		"#oooooooooo#",
		"#oooooooooo#",
		"############",
	],
	"poster_fighting": [
		"############",
		"#oooooooooo#",
		"#oooo#ooooo#",
		"#o#oo#oo#oo#",
		"#oo#o#o#ooo#",
		"#ooo###oooo#",
		"#######o####",
		"#ooo###oooo#",
		"#oo#o#o#ooo#",
		"#o#oo#oo#oo#",
		"#oooo#ooooo#",
		"#oooooooooo#",
		"############",
	],
	"poster_any": [
		"############",
		"#oooooooooo#",
		"#oo+++++ooo#",
		"#oo+ooo+ooo#",
		"#oo+ooo++++#",
		"#oo+++++oo+#",
		"#ooooo+ooo+#",
		"#ooooo+++++#",
		"#oooooooooo#",
		"#o######ooo#",
		"#o####oooo##",
		"#oooooooooo#",
		"############",
	],
}

## Человечки с ореолом фона в пиксель: не сливаются со столами и друг с другом.
const HALO: Array[String] = ["stand", "walk0", "walk1", "hand_head", "wave0", "wave1", "sit0", "sit1",
		"sit2", "stretch", "sleep"]

static var _cache := {}


## Цвета тонов; `@` для человечков, на долю `people` (они чуть темнее мебели, чтобы копошение
## читалось боковым зрением).
static func tone_colors(tones: Vector3, strength := 1.0, people := 0.55) -> Dictionary:
	var bg := Style.BG
	var ink := Style.STUDIO_INK
	return {
		"@": bg.lerp(ink, people * strength),
		"#": bg.lerp(ink, tones.x * strength),
		"+": bg.lerp(ink, tones.y * strength),
		"-": bg.lerp(ink, tones.z * strength),
		"o": bg,
	}


## Картинка карты; `halo` обводит линии пикселем фона (картинка шире на пиксель с каждой стороны).
static func image_from(rows: Array, colors: Dictionary, halo := false) -> Image:
	var h := rows.size()
	var w := 0
	for r in rows:
		w = maxi(w, (r as String).length())
	var m := 1 if halo else 0
	var img := Image.create_empty(maxi(w, 1) + 2 * m, maxi(h, 1) + 2 * m, false, Image.FORMAT_RGBA8)
	img.fill(Color(0, 0, 0, 0))
	for y in h:
		var row: String = rows[y]
		for x in row.length():
			var c := row[x]
			if colors.has(c):
				img.set_pixel(x + m, y + m, colors[c])
	if halo:
		var line: Color = colors["#"]
		var ring: Array[Vector2i] = []
		for y in img.get_height():
			for x in img.get_width():
				if img.get_pixel(x, y).a > 0.0:
					continue
				for d in [Vector2i.LEFT, Vector2i.RIGHT, Vector2i.UP, Vector2i.DOWN]:
					var q: Vector2i = Vector2i(x, y) + d
					if q.x >= 0 and q.y >= 0 and q.x < img.get_width() and q.y < img.get_height() \
							and img.get_pixelv(q).is_equal_approx(line):
						ring.append(Vector2i(x, y))
						break
		for q in ring:
			img.set_pixelv(q, colors["o"])
	return img


## Человечки рисуются тоном `@` вместо линии.
static func _colors_for(name: String, colors: Dictionary) -> Dictionary:
	if not HALO.has(name):
		return colors
	var c := colors.duplicate()
	c["#"] = colors["@"]
	return c


## Сдвиг рисования: у спрайтов с ореолом картинка начинается на пиксель левее и выше.
static func offset(name: String) -> Vector2:
	return Vector2(-1, -1) if HALO.has(name) else Vector2.ZERO


## Текстура по имени карты или построенной рамки; кешируется на набор тонов.
static func texture(name: String, tones: Vector3, strength := 1.0, people := 0.55) -> Texture2D:
	var key := "%s|%s|%.3f|%.3f" % [name, tones, strength, people]
	if _cache.has(key):
		return _cache[key]
	var rows := rows_of(name)
	var tex := ImageTexture.create_from_image(image_from(rows, _colors_for(name, tone_colors(tones, strength, people)), HALO.has(name)))
	_cache[key] = tex
	return tex


static func rows_of(name: String) -> Array:
	if MAPS.has(name):
		return MAPS[name]
	match name:
		"window":
			return window_rows(30, 22)
		"whiteboard":
			return whiteboard_rows(38, 20)
		"door":
			return door_rows(20, 34)
		"counter":
			return counter_rows(60, 8)
	if name.begins_with("counter:"):
		return counter_rows(int(name.get_slice(":", 1)), 8)
	push_error("StudioSprites: нет карты " + name)
	return ["#"]


## Все имена, которые знает лист: карты и построенные рамки.
static func names() -> PackedStringArray:
	var out := PackedStringArray(MAPS.keys())
	out.append_array(["window", "whiteboard", "door", "counter"])
	return out


## Превью-лист: все спрайты в тонах `tones` строками шириной `row_w` пикселей арта, ×`scale`.
static func sheet(tones: Vector3, people := 0.55, scale := 6, row_w := 300, pad := 6) -> Image:
	var colors := tone_colors(tones, 1.0, people)
	var images: Array[Image] = []
	for n in names():
		images.append(image_from(rows_of(n), _colors_for(n, colors), HALO.has(n)))
	var places: Array[Vector2i] = []
	var x := pad
	var y := pad
	var row_h := 0
	for img in images:
		if x + img.get_width() + pad > row_w:
			x = pad
			y += row_h + pad
			row_h = 0
		places.append(Vector2i(x, y))
		x += img.get_width() + pad
		row_h = maxi(row_h, img.get_height())
	var out := Image.create_empty(row_w, y + row_h + pad, false, Image.FORMAT_RGBA8)
	out.fill(Style.BG)
	for i in images.size():
		out.blend_rect(images[i], Rect2i(Vector2i.ZERO, images[i].get_size()), places[i])
	out.resize(out.get_width() * scale, out.get_height() * scale, Image.INTERPOLATE_NEAREST)
	return out


# --- Построенные рамки ------------------------------------------------------------------------

static func _row(w: int, edge: String, fill: String) -> String:
	return edge + fill.repeat(w - 2) + edge


## Окно: рама, переплёт крестом, блик по диагонали светлым, подоконник средним.
static func window_rows(w: int, h: int) -> Array:
	var rows: Array = []
	var mid_x := w / 2
	var mid_y := (h - 3) / 2
	for y in h - 2:
		var line := ""
		for x in w:
			var c := "o"
			if y == 0 or y == h - 3 or x == 0 or x == w - 1 or x == mid_x or y == mid_y:
				c = "#"
			elif (x + y) % 9 == 0 and y < mid_y and x < mid_x:
				c = "-"
			line += c
		rows.append(line)
	rows.append("#".repeat(w))
	rows.append(_row(w, "+", "+"))
	return rows


## Доска с каракулями средним тоном и полочкой для маркеров.
static func whiteboard_rows(w: int, h: int) -> Array:
	var rows: Array = []
	var scribbles := [
		[3, 4, 14], [5, 4, 10], [5, 18, 26], [8, 6, 20], [10, 4, 9], [10, 24, 33],
		[13, 14, 22], [15, 4, 12],
	]
	for y in h - 2:
		var line := ""
		for x in w:
			var c := "o"
			if y == 0 or y == h - 3 or x == 0 or x == w - 1:
				c = "#"
			else:
				for s in scribbles:
					if y == s[0] and x >= s[1] and x <= s[2]:
						c = "+"
			line += c
		rows.append(line)
	rows.append(".." + "+".repeat(w - 4) + "..")
	rows.append("." + "#" + ".".repeat(w - 4) + "#" + ".")
	return rows


## Дверь: косяк, две филёнки, ручка.
static func door_rows(w: int, h: int) -> Array:
	var rows: Array = []
	for y in h:
		var line := ""
		for x in w:
			var c := "-"
			if x == 0 or x == w - 1 or y == 0:
				c = "#"
			elif x == 1 or x == w - 2 or y == 1:
				c = "+"
			elif (x == 4 or x == w - 5) and ((y >= 4 and y <= 14) or (y >= 18 and y <= h - 4)):
				c = "+"
			elif (y == 4 or y == 14 or y == 18 or y == h - 4) and x >= 4 and x <= w - 5:
				c = "+"
			elif x == w - 4 and (y == 16 or y == 17):
				c = "#"
			line += c
		rows.append(line)
	return rows


## Низкая стойка под техникой вдоль стены.
static func counter_rows(w: int, h: int) -> Array:
	var rows: Array = ["#".repeat(w), _row(w, "#", "-"), "#".repeat(w)]
	for y in h - 5:
		rows.append(_row(w, "#", "+"))
	rows.append("#".repeat(w))
	rows.append(".#" + ".".repeat(w - 4) + "#.")
	return rows
