class_name CoverBox
extends Control
## Трёхмерная коробка с диском (`docs/specs/cover.md`): пластик цвета `case`, вкладыши лицевой,
## оборота и корешка с фоном и эффектом, плёнка с глянцем поверх. Рисунок сторон приходит из
## трёх двумерных вьюпортов (`CoverFace`). Коробку крутят: `yaw` и `pitch`, в покое она слегка
## покачивается, чтобы блик и фольга жили. `pick` переводит точку экрана в сторону и доли лица.

const FACE_SHADER := preload("res://scripts/cover/cover_face.gdshader")
const FILM_SHADER := preload("res://scripts/cover/cover_film.gdshader")

var record: GameRecord
var studio := ""
var cover: Dictionary = {}
## Поворот коробки вокруг вертикали (0 лицевая, PI оборот) и наклон.
var yaw := 0.0
var pitch := 0.0
var sway := true

var _tune: CoverTuning
var _faces: Array[CoverFace] = []
var _face_viewports: Array[SubViewport] = []
var _materials: Array[ShaderMaterial] = []
var _case_material: StandardMaterial3D
var _view: TextureRect
var _viewport: SubViewport
var _camera: Camera3D
var _box: Node3D
var _time := 0.0
var _turn: Tween
var _face_size := Vector2.ONE


func setup(record_: GameRecord, studio_: String) -> void:
	record = record_
	studio = studio_
	_tune = CoverData.tuning()
	yaw = _tune.rest_yaw
	pitch = _tune.rest_pitch


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	if _tune == null:
		_tune = CoverData.tuning()
	_face_size = Vector2(_tune.face_px) / _tune.px_per_unit
	for kind: CoverFace.Kind in [CoverFace.Kind.FRONT, CoverFace.Kind.BACK, CoverFace.Kind.SPINE]:
		var vp := SubViewport.new()
		vp.transparent_bg = true
		vp.disable_3d = true
		vp.gui_disable_input = true
		vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
		var face := CoverFace.new()
		face.setup(kind, record, studio)
		vp.size = Vector2i(face.size)
		vp.add_child(face)
		add_child(vp)
		_faces.append(face)
		_face_viewports.append(vp)
	_viewport = SubViewport.new()
	_viewport.own_world_3d = true
	_viewport.transparent_bg = true
	_viewport.msaa_3d = Viewport.MSAA_4X
	_viewport.gui_disable_input = true
	_viewport.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	add_child(_viewport)
	_build_scene()
	_view = TextureRect.new()
	_view.texture = _viewport.get_texture()
	_view.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_view.stretch_mode = TextureRect.STRETCH_SCALE
	_view.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_view.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(_view)
	resized.connect(_fit)
	_fit()
	if not cover.is_empty():
		refresh()
	_apply_rotation()


func _build_scene() -> void:
	var env := Environment.new()
	env.background_mode = Environment.BG_CLEAR_COLOR
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color.WHITE
	env.ambient_light_energy = 0.7
	var world := WorldEnvironment.new()
	world.environment = env
	_viewport.add_child(world)
	var sun := DirectionalLight3D.new()
	sun.rotation = Vector3(-0.6, 0.5, 0.0)
	sun.light_energy = 0.8
	_viewport.add_child(sun)
	_camera = Camera3D.new()
	_camera.fov = _tune.camera_fov
	_camera.position = Vector3(0.0, 0.0, _tune.camera_distance)
	_viewport.add_child(_camera)
	_box = Node3D.new()
	_viewport.add_child(_box)
	var depth := _tune.case_depth
	var case_size := Vector3(_face_size.x + _tune.case_border * 2.0, _face_size.y + _tune.case_border * 2.0, depth)
	var body := MeshInstance3D.new()
	var body_mesh := BoxMesh.new()
	body_mesh.size = case_size
	_case_material = StandardMaterial3D.new()
	_case_material.roughness = 0.35
	_case_material.metallic_specular = 0.6
	body_mesh.material = _case_material
	body.mesh = body_mesh
	_box.add_child(body)
	var eps := 0.002
	# Лицевая смотрит на +Z, оборот развёрнут вокруг вертикали, корешок на левом ребре.
	var places: Array[Array] = [
		[_face_size, Vector3(0.0, 0.0, depth / 2.0 + eps), 0.0],
		[_face_size, Vector3(0.0, 0.0, -depth / 2.0 - eps), PI],
		[Vector2(depth * 0.86, _face_size.y), Vector3(-case_size.x / 2.0 - eps, 0.0, 0.0), -PI / 2.0],
	]
	for i in places.size():
		var quad := QuadMesh.new()
		quad.size = places[i][0]
		var mat := ShaderMaterial.new()
		mat.shader = FACE_SHADER
		mat.set_shader_parameter("overlay", _face_viewports[i].get_texture())
		mat.set_shader_parameter("aspect", quad.size.x / quad.size.y)
		quad.material = mat
		var node := MeshInstance3D.new()
		node.mesh = quad
		node.position = places[i][1]
		node.rotation.y = places[i][2]
		_box.add_child(node)
		_materials.append(mat)
	var film := MeshInstance3D.new()
	var film_mesh := BoxMesh.new()
	film_mesh.size = case_size + Vector3.ONE * 0.014
	var film_mat := ShaderMaterial.new()
	film_mat.shader = FILM_SHADER
	film_mat.set_shader_parameter("half_size", film_mesh.size / 2.0)
	film_mesh.material = film_mat
	film.mesh = film_mesh
	_box.add_child(film)


## Разрешение вьюпорта под реальные пиксели окна, чтобы коробка не мылилась в большом окне.
func _fit() -> void:
	if _viewport == null:
		return
	var k := 1.0
	var win := get_window()
	if win != null and win.content_scale_size.x > 0:
		k = clampf(float(win.size.x) / float(win.content_scale_size.x), 1.0, 3.0)
	_viewport.size = Vector2i((size * k).max(Vector2(16, 16)))


func _process(delta: float) -> void:
	_time += delta
	_apply_rotation()


func _apply_rotation() -> void:
	if _box == null:
		return
	var y := yaw
	var p := pitch
	if sway and _tune.sway_seconds > 0.0:
		var t := _time * TAU / _tune.sway_seconds
		y += sin(t) * _tune.sway_yaw
		p += cos(t * 0.7) * _tune.sway_pitch
	_box.rotation = Vector3(p, y, 0.0)


func set_cover(cover_: Dictionary) -> void:
	cover = cover_
	refresh()


## Пересобрать рисунок сторон и цвета по словарю обложки.
func refresh() -> void:
	if _faces.is_empty():
		return
	for face in _faces:
		face.set_cover(cover)
	var front := CoverData.side(cover, CoverData.Side.FRONT)
	var back := CoverData.side(cover, CoverData.Side.BACK)
	_set_background(0, front)
	_set_background(1, back)
	# Корешок продолжает лицевую, но ровным тоном её первого цвета.
	_set_background(2, {"color": front.get("color"), "color2": front.get("color2"), "fx": 0})
	_case_material.albedo_color = CoverData.color(cover, "case", Color("#1C1B19"))


func _set_background(i: int, d: Dictionary) -> void:
	_materials[i].set_shader_parameter("color_a", CoverData.color(d, "color", Color("#1C4286")))
	_materials[i].set_shader_parameter("color_b", CoverData.color(d, "color2", Color("#78CDD0")))
	var fx := int(d.get("fx", 0))
	if fx == CoverData.FX_ART:
		var arts := CoverStickers.backgrounds(record.genre, record.tech)
		var id := String(d.get("art", ""))
		if not arts.has(id):
			id = arts[0] if not arts.is_empty() else ""
		var found: Array = CoverStickers.background(record.setting, record.genre, record.tech, id) if id != "" else [null, 0]
		var tex: Texture2D = found[0]
		if tex == null:
			fx = 0
		else:
			var tiles: int = found[1]
			var face := float(_tune.face_px.x) / float(_tune.face_px.y)
			var shape := float(tex.get_width()) / float(tex.get_height())
			var scale := Vector2.ONE
			if tiles > 0:
				scale = Vector2(tiles, tiles / face * shape)
			elif shape > face:
				scale = Vector2(face / shape, 1.0)
			else:
				scale = Vector2(1.0, shape / face)
			var smooth := CoverStickers.smooth(record.tech)
			_materials[i].set_shader_parameter("art_smooth" if smooth else "art_near", tex)
			_materials[i].set_shader_parameter("art_is_smooth", smooth)
			_materials[i].set_shader_parameter("art_scale", scale)
	_materials[i].set_shader_parameter("fx", fx)


func face(side: int) -> CoverFace:
	return _faces[side] if side >= 0 and side < _faces.size() else null


## Какая большая сторона сейчас смотрит на игрока.
func facing() -> int:
	return CoverData.Side.FRONT if cos(yaw) >= 0.0 else CoverData.Side.BACK


## Повернуть коробку стороной `side` к игроку, с наклоном покоя.
func turn_to(side: int, instant := false) -> void:
	var target := (PI if side == CoverData.Side.BACK else 0.0) + _tune.rest_yaw
	# Кратчайшей дугой от текущего угла.
	target = yaw + wrapf(target - yaw, -PI, PI)
	if _turn != null:
		_turn.kill()
	if instant or not is_inside_tree():
		yaw = target
		pitch = _tune.rest_pitch
		return
	_turn = create_tween().set_parallel(true).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_BACK)
	_turn.tween_property(self, "yaw", target, _tune.turn_seconds)
	_turn.tween_property(self, "pitch", _tune.rest_pitch, _tune.turn_seconds)


## Полный оборот на месте: отклик на «Случайно».
func spin() -> void:
	if _turn != null:
		_turn.kill()
	if not is_inside_tree():
		return
	_turn = create_tween().set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
	_turn.tween_property(self, "yaw", yaw + TAU, _tune.turn_seconds * 1.4)


func drag(delta: Vector2) -> void:
	if _turn != null:
		_turn.kill()
	yaw += delta.x * _tune.drag_speed
	pitch = clampf(pitch + delta.y * _tune.drag_speed, -_tune.pitch_limit, _tune.pitch_limit)


## Точка экрана на большой стороне коробки: `{side, uv}` или пусто, если мимо.
func pick(point: Vector2) -> Dictionary:
	if _camera == null or _view == null or size.x <= 0.0 or size.y <= 0.0:
		return {}
	var local := get_global_transform().affine_inverse() * point
	var vp_point := local / size * Vector2(_viewport.size)
	var inv := _box.global_transform.affine_inverse()
	var origin := inv * _camera.project_ray_origin(vp_point)
	var dir := inv.basis * _camera.project_ray_normal(vp_point)
	if absf(dir.z) < 0.0001:
		return {}
	var front := dir.z < 0.0
	var plane := _tune.case_depth / 2.0 * (1.0 if front else -1.0)
	var hit := origin + dir * ((plane - origin.z) / dir.z)
	var uv := Vector2(hit.x / _face_size.x * (1.0 if front else -1.0) + 0.5, 0.5 - hit.y / _face_size.y)
	if uv.x < 0.0 or uv.x > 1.0 or uv.y < 0.0 or uv.y > 1.0:
		return {}
	return {"side": CoverData.Side.FRONT if front else CoverData.Side.BACK, "uv": uv}


## Картинка коробки в покое с прозрачным фоном, высотой `px.y`: для галереи и карточки игры.
## Без окна пустая.
func snapshot(px: Vector2i) -> Image:
	if DisplayServer.get_name() == "headless" or not is_inside_tree():
		return null
	var keep := [yaw, pitch, sway]
	if _turn != null:
		_turn.kill()
	for f in _faces:
		f.select(CoverFace.NONE)
	sway = false
	yaw = _tune.rest_yaw
	pitch = _tune.rest_pitch
	_apply_rotation()
	await RenderingServer.frame_post_draw
	await RenderingServer.frame_post_draw
	var img := _viewport.get_texture().get_image()
	yaw = keep[0]
	pitch = keep[1]
	sway = keep[2]
	if img == null or img.is_empty():
		return null
	img.convert(Image.FORMAT_RGBA8)
	var used := img.get_used_rect()
	if not used.has_area():
		return null
	img = img.get_region(used.grow(4).intersection(Rect2i(Vector2i.ZERO, img.get_size())))
	img.resize(maxi(roundi(px.y * float(img.get_width()) / img.get_height()), 1), px.y, Image.INTERPOLATE_LANCZOS)
	return img
