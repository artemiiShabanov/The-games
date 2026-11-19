class_name CoverStickers
extends RefCounted
## Стикеры обложки (`docs/specs/cover.md`): картинки из ассетов самой игры по её жанру,
## технологии и сеттингу. Ретро и 2D берут спрайты (у 2D первый кадр ленты), примитив рисуется
## контурами слотов, а у 3D и «продвинутых» модель снимается в плоскую картинку (`CoverBaker`)
## при первом обращении: слепок всегда совпадает с текущим мешем, файлов на диске нет.
## Картинка стикера с прозрачным полем по краям, чтобы обводка шейдера не обрезалась.

## Стикеры жанра по технологиям; первый в списке главный герой игры.
const BIT8: Dictionary[int, Array] = {
	Game.Genre.PLATFORMER: ["hero_run_0", "hero_jump", "enemy_0", "parrot_0", "coin", "flag", "checkpoint", "cloud_big"],
	Game.Genre.RACING: ["boat_2", "rival_2", "boat_0", "race_buoy", "race_barrel", "race_rock", "race_finish", "coin"],
	Game.Genre.SHOOTER: ["shoot_hero_0", "shoot_gunner_0", "shoot_cannon", "shoot_chest", "shoot_barrel", "shoot_rum", "shoot_ball"],
	Game.Genre.SPORT: ["golf_hero_0", "golf_ball", "golf_flag", "golf_cannon", "golf_chest", "golf_cup", "golf_splash"],
	Game.Genre.FIGHTING: ["fight_hero_idle_0", "fight_hero_high_1", "fight_rival_idle_0", "fight_rival_high_1", "fight_guard", "fight_spark"],
}
## 2D: имя ленты и ширина кадра (0 картинка целиком).
const BIT16: Dictionary[int, Array] = {
	Game.Genre.PLATFORMER: [["hero_run", 32], ["hero_jump", 32], ["crab_walk", 32], ["enemy_walk", 32], ["parrot_fly", 32],
			["coin", 32], ["chest", 32], ["flag", 32], ["key", 32], ["heart", 32], ["palm", 0]],
	Game.Genre.RACING: [["cart_hero", 160], ["cart_0", 160], ["cart_1", 160], ["road_barrel", 0], ["road_rock", 0],
			["sign_left", 0], ["road_hut", 0], ["palm", 0]],
	Game.Genre.SHOOTER: [["skel_walk", 64], ["cut_walk", 64], ["skel_fire", 64], ["pistol", 128], ["medkit", 32],
			["key", 32], ["chest", 32], ["heart", 32]],
	Game.Genre.SPORT: [["soccer_hero", 24], ["soccer_keeper_rival", 24], ["soccer_rival_0", 24], ["soccer_ball", 8],
			["brawl_face_hero", 32], ["flag", 32]],
	Game.Genre.FIGHTING: [["brawl_hero", 96], ["brawl_thug", 96], ["brawl_knife", 96], ["brawl_boss", 96],
			["brawl_face_hero", 32], ["brawl_face_boss", 32], ["brawl_go", 0]],
}
## Примитив: слоты контуров сеттинга (`SettingDef.VECTOR_SLOTS`).
const VECTOR: Dictionary[int, Array] = {
	Game.Genre.PLATFORMER: ["hero", "enemy", "enemy_2", "bonus", "finish", "prop_a"],
	Game.Genre.RACING: ["vehicle", "rival", "obstacle", "bonus", "finish"],
	Game.Genre.SHOOTER: ["hero", "enemy", "enemy_2", "shot", "prop_b", "bonus"],
	Game.Genre.SPORT: ["hero", "rival", "ball", "goal", "finish"],
	Game.Genre.FIGHTING: ["hero", "rival", "enemy", "bonus"],
}
## 3D: модели слотов, которые ставит демка этой пары.
const MODELS: Dictionary[int, Array] = {
	Game.Genre.PLATFORMER: ["hero", "enemy", "coin", "chest", "lighthouse", "palm", "barrel", "crate", "cannon"],
	Game.Genre.RACING: ["cart", "cart_rival", "lighthouse", "flag", "palm", "rock", "barrel"],
	Game.Genre.SHOOTER: ["enemy", "captain", "pistol", "cannon", "keg", "bottle", "crate", "flag"],
	Game.Genre.SPORT: ["hero", "keg", "hoop", "ball", "lighthouse", "flag", "palm"],
	Game.Genre.FIGHTING: ["hero", "captain", "enemy", "bottle", "lighthouse", "flag"],
}
## «Продвинутые»: у этих демок свой набор (крюк-кошка, спринт, аванпост, дюна, один против всех);
## герой, враг и капитан снимаются с моделей на скелете.
const MODELS_THREED: Dictionary[int, Array] = {
	Game.Genre.PLATFORMER: ["hero", "lighthouse", "palm", "chest", "barrel", "crate", "rock"],
	Game.Genre.RACING: ["cart", "cart_rival", "lighthouse", "flag", "rock", "barrel", "chest"],
	Game.Genre.SHOOTER: ["enemy", "captain", "pistol", "keg", "bottle", "crate", "flag", "rock"],
	Game.Genre.SPORT: ["hero", "lighthouse", "rock", "barrel", "crate", "chest"],
	Game.Genre.FIGHTING: ["hero", "enemy", "cannon", "barrel", "crate", "chest", "keg"],
}
## Фоны из игры для обложки: имя и сколько раз картинка повторяется по ширине лица (0 это одна
## картинка во всё лицо). Ретро: плитки уровня; 2D: задники и плитки; 3D и «продвинутые»:
## текстуры уровня (`tex_<имя>`). У примитива фоновых картинок нет, там список пуст.
const BACK_BIT8: Dictionary[int, Array] = {
	Game.Genre.PLATFORMER: [["ground", 6], ["ground_inner", 6], ["platform", 6]],
	Game.Genre.RACING: [["race_water", 6], ["race_sand", 6], ["race_shallow", 6]],
	Game.Genre.SHOOTER: [["shoot_deck", 6], ["shoot_plank", 6]],
	Game.Genre.SPORT: [["golf_sea", 6], ["golf_sand", 6], ["golf_deck", 6]],
}
const BACK_BIT16: Dictionary[int, Array] = {
	Game.Genre.PLATFORMER: [["par3_back", 0], ["par3_trees", 0], ["trail_soil", 4]],
	Game.Genre.RACING: [["road_sky", 0]],
	Game.Genre.SHOOTER: [["wall_stone", 4], ["wall_planks", 4], ["wall_hull", 4], ["floor_planks", 4], ["floor_stone", 4]],
	Game.Genre.SPORT: [["soccer_grass", 4]],
	Game.Genre.FIGHTING: [["brawl_street", 0]],
}
const BACK_MODELS: Dictionary[int, Array] = {
	Game.Genre.PLATFORMER: [["sky", 0], ["sand", 3], ["water", 3], ["grass", 3]],
	Game.Genre.RACING: [["road", 3], ["sand", 3], ["grass", 3], ["sky", 0]],
	Game.Genre.SHOOTER: [["planks", 3], ["sky", 0], ["water", 3], ["sail", 3]],
	Game.Genre.SPORT: [["sand", 3], ["sky", 0], ["grass", 3]],
	Game.Genre.FIGHTING: [["planks", 3], ["sky", 0], ["sail", 3]],
}
## Сторона слепка модели в пикселях: 3D крупными пикселями, «продвинутые» гладко.
const BAKE_PX: Dictionary[int, int] = {Game.Tech.LOWPOLY: 96, Game.Tech.THREED: 320}

static var _textures: Dictionary[String, Texture2D] = {}
static var _baker: CoverBaker


## Имена стикеров игры: по жанру и технологии.
static func ids_for(genre: Game.Genre, tech: Game.Tech) -> PackedStringArray:
	var out := PackedStringArray()
	match tech:
		Game.Tech.VECTOR:
			out = PackedStringArray(VECTOR.get(genre, []))
		Game.Tech.BIT8:
			out = PackedStringArray(BIT8.get(genre, []))
		Game.Tech.BIT16:
			for item: Array in BIT16.get(genre, []):
				out.append(item[0])
		_:
			out = PackedStringArray((MODELS_THREED if tech == Game.Tech.THREED else MODELS).get(genre, []))
	return out


static func _back_table(tech: Game.Tech) -> Dictionary[int, Array]:
	match tech:
		Game.Tech.BIT8:
			return BACK_BIT8
		Game.Tech.BIT16:
			return BACK_BIT16
		Game.Tech.LOWPOLY, Game.Tech.THREED:
			return BACK_MODELS
	return {}


## Имена фонов из игры для пары; пусто, если у технологии их нет.
static func backgrounds(genre: Game.Genre, tech: Game.Tech) -> PackedStringArray:
	var out := PackedStringArray()
	for item: Array in _back_table(tech).get(genre, []):
		out.append(item[0])
	return out


## Картинка фона и число повторов по ширине лица (0 во всё лицо); `null`, если файла нет.
static func background(setting: Game.Setting, genre: Game.Genre, tech: Game.Tech, id: String) -> Array:
	var def := SettingDef.of(setting)
	var tiles := 0
	for item: Array in _back_table(tech).get(genre, []):
		if item[0] == id:
			tiles = item[1]
	var tex: Texture2D = null
	match tech:
		Game.Tech.BIT8:
			tex = def.sprite(id)
		Game.Tech.BIT16:
			tex = def.sprite16(id)
		Game.Tech.LOWPOLY, Game.Tech.THREED:
			tex = def.texture_lowpoly(id, tech == Game.Tech.THREED)
			# Плотная текстура «продвинутых» крупнее: меньше повторов.
			if tech == Game.Tech.THREED and tiles > 0:
				tiles = 2
	return [tex, tiles]


static func is_contour(tech: Game.Tech) -> bool:
	return tech == Game.Tech.VECTOR


## Гладкая ли картинка: всё, кроме «продвинутых», рисуется ближайшим соседом.
static func smooth(tech: Game.Tech) -> bool:
	return tech == Game.Tech.THREED


## Ширина обводки в текселях картинки стикера.
static func outline_texels(tech: Game.Tech) -> float:
	match tech:
		Game.Tech.BIT8:
			return 1.0
		Game.Tech.BIT16:
			return 1.5
		Game.Tech.LOWPOLY:
			return 2.5
		_:
			return 5.0


## Контуры слота примитива в пикселях спрайта от его центра.
static func contours(setting: Game.Setting, id: String) -> Array[PackedVector2Array]:
	return SettingDef.of(setting).vector_contours(StringName(id))


## Цвет луча слота примитива.
static func contour_color(setting: Game.Setting, id: String) -> Color:
	var def := SettingDef.of(setting)
	var colors := def.vector_colors if def.vector_colors.size() >= 4 else SettingDef.of(Game.Setting.PIRATES).vector_colors
	if colors.size() < 4:
		return Color.WHITE
	return colors[clampi(def.vector_ink(StringName(id)), 1, 3)]


## Картинка стикера с полем под обводку; у моделей сначала пустая, слепок приходит через
## несколько кадров и картинка обновляется на месте (сигнал `changed` текстуры).
static func texture(setting: Game.Setting, tech: Game.Tech, id: String) -> Texture2D:
	var key := "%d:%d:%s" % [setting, tech, id]
	if _textures.has(key):
		return _textures[key]
	var def := SettingDef.of(setting)
	var pad := ceili(outline_texels(tech)) + 1
	var tex: Texture2D = null
	match tech:
		Game.Tech.VECTOR:
			pass
		Game.Tech.BIT8:
			tex = _padded(_image(def.sprite(id)), pad)
		Game.Tech.BIT16:
			var img := _image(def.sprite16(id))
			var fw := _frame16(id)
			if img != null and fw > 0 and fw < img.get_width():
				img = img.get_region(Rect2i(0, 0, fw, img.get_height()))
			tex = _padded(img, pad)
		_:
			var holder := ImageTexture.create_from_image(Image.create_empty(8, 8, false, Image.FORMAT_RGBA8))
			tex = holder
			if DisplayServer.get_name() != "headless":
				# У «продвинутых» герои и враги в игре на скелете (#119): слепок с той же модели.
				var rig := def.rig(id) if tech == Game.Tech.THREED else null
				if rig != null:
					_baker_node().add_rig(rig, holder, BAKE_PX[tech], pad)
				else:
					var model := def.model(id, tech == Game.Tech.THREED)
					if model != null:
						_baker_node().add(model, holder, BAKE_PX[tech], pad, tech == Game.Tech.THREED)
	if tex != null:
		_textures[key] = tex
	return tex


static func _frame16(id: String) -> int:
	for list: Array in BIT16.values():
		for item: Array in list:
			if item[0] == id:
				return item[1]
	return 0


static func _image(tex: Texture2D) -> Image:
	if tex == null:
		return null
	var img := tex.get_image()
	if img == null or img.is_empty():
		return null
	if img.is_compressed():
		img.decompress()
	img.convert(Image.FORMAT_RGBA8)
	return img


## Обрезка по непрозрачному и прозрачное поле `pad` вокруг.
static func _padded(img: Image, pad: int) -> ImageTexture:
	if img == null:
		return null
	var used := img.get_used_rect()
	if not used.has_area():
		return null
	var out := Image.create_empty(used.size.x + pad * 2, used.size.y + pad * 2, false, Image.FORMAT_RGBA8)
	out.blit_rect(img, used, Vector2i(pad, pad))
	return ImageTexture.create_from_image(out)


static func _baker_node() -> CoverBaker:
	if _baker == null or not is_instance_valid(_baker):
		_baker = CoverBaker.new()
		var tree := Engine.get_main_loop() as SceneTree
		tree.root.add_child.call_deferred(_baker)
	return _baker
