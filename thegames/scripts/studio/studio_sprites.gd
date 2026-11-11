class_name StudioSprites
extends RefCounted
## Пиксель-арт студии на фоне (#80): текстовые карты, из которых собираются текстуры. Мебель в
## одном цвете `studio-ink` на фоне `bg` (STYLE «Студия»), тона это доли смешения фона с
## чернилами: `#` линия, `+` средний, `-` светлый, `o` фон (заслоняет то, что позади), `.`
## прозрачно. Человечки в своих приглушённых цветах (плейтест 2026-11-11), ключи ниже.
## Доли тонов в `resources/studio_backdrop.tres`. Карты правятся прямо здесь; лист всех
## спрайтов (`sheet`): `sh tools/autotest.sh --scene=studio_backdrop_test --sheet --frames=5`.
## Крупные рамки (стена, окна, доска, дверь) строятся функциями ниже, а не картами.

## Человечки 10 в ширину (с поднятыми руками 12), якорь посередине снизу, линии в два пикселя.
## Свои ключи цвета, у каждого человечка свои (`worker_colors`): `H` волосы, `S` кожа, `E` глаза,
## `B` рубашка, `b` её тень (руки), `P` брюки, `K` ботинки. Спереди с глазами, сидят спиной.
const MAPS := {
	"stand": [
		".HHHHHHHH.",
		".HHHHHHHH.",
		".HSSSSSSH.",
		".SSESSESS.",
		".SSSSSSSS.",
		".bBBBBBBb.",
		"bbBBBBBBbb",
		"bbBBBBBBbb",
		"SSBBBBBBSS",
		"..PPPPPP..",
		"..PP..PP..",
		"..PP..PP..",
		"..KK..KK..",
	],
	"walk0": [
		".HHHHHHHH.",
		".HHHHHHHH.",
		".HSSSSSSH.",
		".SSESSESS.",
		".SSSSSSSS.",
		".bBBBBBBb.",
		"bbBBBBBBbb",
		"bbBBBBBBbb",
		"SSBBBBBBSS",
		"..PPPPPP..",
		".PP....PP.",
		".PP....PP.",
		".KK....KK.",
	],
	"walk1": [
		"..........",
		".HHHHHHHH.",
		".HHHHHHHH.",
		".HSSSSSSH.",
		".SSESSESS.",
		".SSSSSSSS.",
		".bBBBBBBb.",
		"bbBBBBBBbb",
		"SSBBBBBBSS",
		"..PPPPPP..",
		"...PPPP...",
		"...PPPP...",
		"...KKKK...",
	],
	"hand_head": [
		".HHHHHHH..",
		".HHHHHHHSS",
		".HSSSSSHSS",
		".SSESSESbb",
		".SSSSSSSbb",
		".bBBBBBBbb",
		"bbBBBBBBb.",
		"bbBBBBBB..",
		"SSBBBBBB..",
		"..PPPPPP..",
		"..PP..PP..",
		"..PP..PP..",
		"..KK..KK..",
	],
	"wave0": [
		"SS........SS",
		"bb........bb",
		"bbHHHHHHHHbb",
		"bbHHHHHHHHbb",
		"bbHSSSSSSHbb",
		".bSSESSESSb.",
		"..SSSSSSSS..",
		"..bBBBBBBb..",
		"..BBBBBBBB..",
		"..BBBBBBBB..",
		"...PPPPPP...",
		"...PP..PP...",
		"...PP..PP...",
		"...KK..KK...",
	],
	"wave1": [
		"............",
		"............",
		"..HHHHHHHH..",
		"..HHHHHHHH..",
		"..HSSSSSSH..",
		"..SSESSESS..",
		"..SSSSSSSS..",
		"SSbBBBBBBbSS",
		"SSbBBBBBBbSS",
		"..BBBBBBBB..",
		"...PPPPPP...",
		"...PP..PP...",
		"...PP..PP...",
		"...KK..KK...",
	],
	"held0": [
		"SS........SS",
		"bb........bb",
		"bbHHHHHHHHbb",
		"bbHHHHHHHHbb",
		"bbHSSSSSSHbb",
		".bSSESSESSb.",
		"..SSSSSSSS..",
		"..bBBBBBBb..",
		"..BBBBBBBB..",
		"..BBBBBBBB..",
		"...PPPPPP...",
		"..PP....PP..",
		".PP......PP.",
		".KK......KK.",
	],
	"held1": [
		"SS........SS",
		"bb........bb",
		"bbHHHHHHHHbb",
		"bbHHHHHHHHbb",
		"bbHSSSSSSHbb",
		".bSSESSESSb.",
		"..SSSSSSSS..",
		"..bBBBBBBb..",
		"..BBBBBBBB..",
		"..BBBBBBBB..",
		"...PPPPPP...",
		"...PP..PP...",
		"...PP...PP..",
		"...KK...KK..",
	],
	"sit0": [
		".HHHHHHHH.",
		".HHHHHHHH.",
		"SHHHHHHHHS",
		".HHHHHHHH.",
		".bBBBBBBb.",
		"bbBBBBBBbb",
		"bbBBBBBBbb",
		".++++++++.",
		".++++++++.",
		".++....++.",
	],
	"sit1": [
		".HHHHHHHH.",
		".HHHHHHHH.",
		"SHHHHHHHHS",
		"bbHHHHHHH.",
		"bbBBBBBBb.",
		".bBBBBBBbb",
		".bBBBBBBbb",
		".++++++++.",
		".++++++++.",
		".++....++.",
	],
	"sit2": [
		".HHHHHHHH.",
		".HHHHHHHH.",
		"SHHHHHHHHS",
		".HHHHHHHbb",
		".bBBBBBBbb",
		"bbBBBBBBb.",
		"bbBBBBBBb.",
		".++++++++.",
		".++++++++.",
		".++....++.",
	],
	"stretch": [
		"SS........SS",
		"bb........bb",
		"bbHHHHHHHHbb",
		"bbHHHHHHHHbb",
		".SHHHHHHHHS.",
		"..HHHHHHHH..",
		"..bBBBBBBb..",
		"..BBBBBBBB..",
		"..BBBBBBBB..",
		"..++++++++..",
		"..++++++++..",
		"..++....++..",
	],
	"sleep": [
		"..........",
		"..........",
		".HHHHHHHH.",
		"SHHHHHHHHS",
		"bbHHHHHHbb",
		"bbBBBBBBbb",
		"bbBBBBBBbb",
		".++++++++.",
		".++++++++.",
		".++....++.",
	],
	# Приземлился после падения из рук: сплющен на кадр.
	"land": [
		".HHHHHHHH.",
		".HSSSSSSH.",
		".SSESSESS.",
		".SSSSSSSS.",
		"bbBBBBBBbb",
		"bbBBBBBBbb",
		"SSBBBBBBSS",
		"..PPPPPP..",
		".PP....PP.",
		"KKK....KKK",
	],
	"chair": [
		".++++++++.",
		".+oooooo+.",
		".++++++++.",
		".++++++++.",
		".++....++.",
	],
	"shadow": [
		"..++++++..",
		".++++++++.",
	],
	# Мелочь в руках и над головой.
	"cup": [
		"###",
		"#o#",
		"###",
	],
	"tablet": [
		"###",
		"#o#",
		"#o#",
		"###",
	],
	"phone": [
		"##",
		"##",
		"##",
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
	# Кулер с бутылью (плейтест 2026-11-11: «кулер»): вода средним тоном с бликом, краники, тумба.
	# По нажатию в бутыли всплывает пузырь (`StudioBackdrop`, вода `COOLER_WATER`).
	"coffee": [
		"...####...",
		"..#++++#..",
		".#-+++++#.",
		".#-+++++#.",
		".#++++++#.",
		"..######..",
		"##########",
		"#oooooooo#",
		"#o#oooo#o#",
		"#oooooooo#",
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
	# Часы без стрелок: стрелки рисует `StudioBackdrop` по времени суток, центр `CLOCK_CENTER`.
	"clock": [
		"..#####..",
		".#ooooo#.",
		"#ooooooo#",
		"#ooooooo#",
		"#ooooooo#",
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
## Окно: ширина и высота с подоконником (плейтест 2026-11-11: крупнее, за ними смена суток).
const WINDOW_SIZE := Vector2i(42, 34)
## Экран 8-bit телевизора (`tech_bit8`): левый верхний угол и размер; каналы ниже.
const TV_SCREEN := Rect2i(1, 4, 10, 5)
## Вода в бутыли кулера: левый верхний угол и размер; центр часов.
const COOLER_WATER := Rect2i(2, 1, 6, 4)
const CLOCK_CENTER := Vector2i(4, 4)
## Каналы телевизора 10×5 в тонах мебели; нулевой это картинка самого спрайта.
const TV_CHANNELS: Array = [
	[],
	[
		"oo#oooo#oo",
		"oooooooooo",
		"o#oooooo#o",
		"oo######oo",
		"oooooooooo",
	],
	[
		"ooooooo##o",
		"ooo#ooo##o",
		"oo###ooooo",
		"o#####o#oo",
		"##########",
	],
	[
		"##++--oo##",
		"##++--oo##",
		"##++--oo##",
		"##++--oo##",
		"oo--++##oo",
	],
	[
		"oo#oooo#oo",
		"oo######oo",
		"o##o##o##o",
		"o########o",
		"o#o#oo#o#o",
	],
	[
		"oo##oo##oo",
		"o########o",
		"oo######oo",
		"ooo####ooo",
		"oooo##oooo",
	],
	[
		"oooooooooo",
		"ooo##ooooo",
		"oo####oooo",
		"++++++++++",
		"o#o#o#oo#o",
	],
]

const HALO: Array[String] = ["stand", "walk0", "walk1", "hand_head", "wave0", "wave1", "held0", "held1",
		"land", "sit0", "sit1", "sit2", "stretch", "sleep"]

static var _cache := {}


## Цвета мебели: доли смешения фона с чернилами, `o` чистый фон.
static func tone_colors(tones: Vector3, strength := 1.0) -> Dictionary:
	var bg := Style.BG
	var ink := Style.STUDIO_INK
	return {
		"#": bg.lerp(ink, tones.x * strength),
		"+": bg.lerp(ink, tones.y * strength),
		"-": bg.lerp(ink, tones.z * strength),
		"o": bg,
	}


## Цвета человечка: мебельные тона плюс свои ключи. Рубашка, кожа и волосы приглушены к фону на
## `mix`; глаза и брюки долями чернил. Тень рубашки (руки) на четверть темнее к чернилам.
static func worker_colors(base: Dictionary, shirt: Color, skin: Color, hair: Color, mix: float,
		pants: float, eyes: float, strength := 1.0) -> Dictionary:
	var bg := Style.BG
	var ink := Style.STUDIO_INK
	var k := mix * strength
	var c := base.duplicate()
	c["B"] = bg.lerp(shirt, k)
	c["b"] = bg.lerp(shirt.lerp(ink, 0.25), k)
	c["S"] = bg.lerp(skin, k)
	c["H"] = bg.lerp(hair, k)
	c["E"] = bg.lerp(ink, eyes * strength)
	c["P"] = bg.lerp(ink, pants * strength)
	c["K"] = bg.lerp(ink, eyes * 0.8 * strength)
	return c


## Картинка карты; `halo` обводит фигуру пикселем фона (картинка шире на пиксель с каждой стороны).
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
		var ring: Array[Vector2i] = []
		for y in img.get_height():
			for x in img.get_width():
				if img.get_pixel(x, y).a > 0.0:
					continue
				for d in [Vector2i.LEFT, Vector2i.RIGHT, Vector2i.UP, Vector2i.DOWN]:
					var q: Vector2i = Vector2i(x, y) + d
					if q.x >= 0 and q.y >= 0 and q.x < img.get_width() and q.y < img.get_height() \
							and img.get_pixelv(q).a > 0.0:
						ring.append(Vector2i(x, y))
						break
		for q in ring:
			img.set_pixelv(q, colors["o"])
	return img


## Сдвиг рисования: у спрайтов с ореолом картинка начинается на пиксель левее и выше.
static func offset(name: String) -> Vector2:
	return Vector2(-1, -1) if HALO.has(name) else Vector2.ZERO


## Текстура по имени карты или построенной рамки в цветах `colors`; кешируется по `key`
## (набор цветов: мебель или облик человечка при данной силе чернил).
static func texture(name: String, colors: Dictionary, key: String) -> Texture2D:
	var k := name + "|" + key
	if _cache.has(k):
		return _cache[k]
	var tex := ImageTexture.create_from_image(image_from(rows_of(name), colors, HALO.has(name)))
	_cache[k] = tex
	return tex


static func rows_of(name: String) -> Array:
	if MAPS.has(name):
		return MAPS[name]
	match name:
		"window":
			return window_rows(WINDOW_SIZE.x, WINDOW_SIZE.y)
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


## Превью-лист: все спрайты (человечки в первом облике), ниже ряды «стоит», «идёт» и «сидит»
## во всех обликах `looks`; строки шириной `row_w` пикселей арта, ×`scale`.
static func sheet(furniture: Dictionary, looks: Array[Dictionary], scale := 6, row_w := 300, pad := 6) -> Image:
	var images: Array[Image] = []
	var breaks: Array[int] = []
	for n in names():
		images.append(image_from(rows_of(n), looks[0] if HALO.has(n) or n == "chair" else furniture, HALO.has(n)))
	for pose in ["stand", "walk0", "sit1"]:
		breaks.append(images.size())
		for look in looks:
			images.append(image_from(rows_of(pose), look, true))
	var places: Array[Vector2i] = []
	var x := pad
	var y := pad
	var row_h := 0
	for i in images.size():
		var img := images[i]
		if x + img.get_width() + pad > row_w or breaks.has(i):
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


## Окно: рама, переплёт крестом, подоконник средним. Стёкла прозрачные: за ними небо, которое
## рисует `StudioBackdrop` по времени суток (плейтест 2026-11-11).
static func window_rows(w: int, h: int) -> Array:
	var rows: Array = []
	var mid_x := w / 2
	var mid_y := (h - 3) / 2
	for y in h - 2:
		var line := ""
		for x in w:
			var c := "."
			if y == 0 or y == h - 3 or x == 0 or x == w - 1 or x == mid_x or y == mid_y:
				c = "#"
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
