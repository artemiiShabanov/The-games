class_name LowpolyScreen
extends SubViewportContainer
## Экран демок low poly (#108, `docs/specs/demos_catalog.md`): своя 3D-сцена в `SubViewport` на
## всю область демки, в духе первой PlayStation (решение 2026-11-12). Картинка рисуется втрое
## мельче карточки (554×277) и увеличивается ближайшим соседом без сглаживания; все материалы
## на шейдере `lowpoly_ps1.gdshader`: вершины прилипают к сетке экрана и дрожат, текстуры низкого
## разрешения ложатся аффинно и плывут, свет и туман считаются по вершинам; поверх кадра
## 15-битный цвет с дизерингом. Теней от солнца нет, под героями тень-блин (`add_shadow`).
## Демка кладёт узлы в `world`, двигает `camera` (`LowpolyFollowCam`, `LowpolyFirstPerson`) и
## рисует HUD в колбэке `draw_hud` поверх сцены. Модели слотов собирает `model(def)`, уровень:
## неровная земля `LowpolyTerrain`, плоскости `add_plane`, ящики `add_box`, всё с текстурами
## сеттинга и разбито на мелкие грани, чтобы аффинное наложение не рвало картинку. Небо:
## панорама на цилиндре вокруг камеры. Общие баги: розовая заглушка это розовый ящик в шашку по
## габаритам модели (`pink_model`), чужая палитра сдвигает оттенок всех материалов мира
## (`set_alien`). Баг технологии «дыры в моделях» (#111, `set_holes`): грани пропадают и чернеют. Во встроенном режиме (стрим ленты) увеличение на ступень меньше.

## Роли цветов HUD сеттинга: земля, вода, дерево, светлое, кожа, опасность, бонус, тёмное.
enum { GROUND, GROUND_2, WALL, LIGHT, SKIN, DANGER, BONUS, DARK }
const ROLES := 8
## Предел треугольников на объект.
const MAX_TRIS := 300
const EMBED_SCALE := 1
## Грань уровня длиннее этого режется на части, метры.
const MAX_FACE := 2.5
## Плоскость шире этого считается дальним планом: баг «дыры в моделях» её не трогает.
const FAR_PLANE := 100.0
const PS1_SHADER := preload("res://scripts/demos/lowpoly_ps1.gdshader")
## Глубина цвета и дизеринг поверх кадра: матрица 4×4 по пикселям экрана демки.
const DITHER_SHADER := """
shader_type canvas_item;
uniform vec2 view = vec2(554.0, 277.0);
uniform float levels = 31.0;
uniform float dither = 1.0;
const float BAYER[16] = float[](0.0, 8.0, 2.0, 10.0, 12.0, 4.0, 14.0, 6.0, 3.0, 11.0, 1.0, 9.0, 15.0, 7.0, 13.0, 5.0);
void fragment() {
	vec4 c = texture(TEXTURE, UV);
	ivec2 p = ivec2(floor(UV * view));
	float b = (BAYER[(p.x % 4) + (p.y % 4) * 4] + 0.5) / 16.0 - 0.5;
	c.rgb = floor(c.rgb * levels + 0.5 + b * dither) / levels;
	COLOR = c;
}
"""
## Розовая заглушка: шашка в координатах модели, без света.
const PINK_SHADER := """
shader_type spatial;
render_mode unshaded;
uniform vec3 pink : source_color = vec3(1.0, 0.169, 0.839);
uniform float cell = 0.2;
varying vec3 local;
void vertex() {
	local = VERTEX;
}
void fragment() {
	vec3 c = floor(local / cell + 0.5);
	float k = mod(c.x + c.y + c.z, 2.0);
	ALBEDO = pink * mix(1.0, 0.72, k);
}
"""

## Виртуальный экран в пикселях демки.
var view := Vector2(554, 277)
var viewport: SubViewport
var world: Node3D
var camera: Camera3D
var environment: Environment
var sky_dome: MeshInstance3D
var hud: Node2D
var draw_hud := Callable()
var palette: Array[Color] = []
var sky := Color.WHITE
var tuning: LowpolyTuning
## Чужая палитра включена (проверки).
var alien := false
var hue_shift := 0.0
## Баг технологии «дыры в моделях» (#111): доля пропавших граней моделей, 0 выключен (проверки).
var holes := 0.0
var _holes_level := 0.0
var _flipped := 0.0
var _hole_rate := 1.4
## Сколько розовых заглушек создано (проверки).
var pink_count := 0
var _materials: Dictionary[String, ShaderMaterial] = {}
var _meshes: Dictionary[String, ArrayMesh] = {}
var _pink_material: ShaderMaterial
var _flash_material: ShaderMaterial
var _shadow_material: StandardMaterial3D
var _shadow_mesh: ArrayMesh


## Экран в области `area`: цвета HUD `palette_`, цвет тумана `sky_`, панорама неба `sky_texture`
## (без неё ровный цвет); `scale` 0 берёт увеличение из `LowpolyTuning`. Во встроенном режиме
## увеличение на ступень меньше.
static func make(area: Vector2, embedded: bool, palette_: Array[Color], sky_: Color, sky_texture: Texture2D = null,
		scale := 0) -> LowpolyScreen:
	var s := LowpolyScreen.new()
	s.tuning = LowpolyTuning.load_default()
	var full := scale if scale > 0 else s.tuning.screen_scale
	var shrink := maxi(full - 1, EMBED_SCALE) if embedded else full
	s.palette = palette_
	s.sky = sky_
	s.view = (area / shrink).floor()
	s.position = ((area - s.view * shrink) / 2.0).floor()
	s.size = s.view * shrink
	s.custom_minimum_size = s.size
	s.stretch = true
	s.stretch_shrink = shrink
	s.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	s.mouse_filter = Control.MOUSE_FILTER_IGNORE
	s.viewport = SubViewport.new()
	s.viewport.size = Vector2i(s.view)
	s.viewport.own_world_3d = true
	s.viewport.msaa_3d = Viewport.MSAA_DISABLED
	s.viewport.screen_space_aa = Viewport.SCREEN_SPACE_AA_DISABLED
	s.viewport.canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	s.viewport.snap_2d_transforms_to_pixel = true
	s.add_child(s.viewport)
	s._build_scene(sky_texture)
	return s


func _build_scene(sky_texture: Texture2D) -> void:
	environment = Environment.new()
	environment.background_mode = Environment.BG_COLOR
	environment.background_color = sky
	environment.tonemap_mode = Environment.TONE_MAPPER_LINEAR
	var env_node := WorldEnvironment.new()
	env_node.environment = environment
	viewport.add_child(env_node)
	camera = Camera3D.new()
	camera.fov = tuning.fov
	camera.far = tuning.far
	camera.near = 0.1
	camera.current = true
	viewport.add_child(camera)
	world = Node3D.new()
	viewport.add_child(world)
	hud = Node2D.new()
	hud.draw.connect(_draw_hud)
	viewport.add_child(hud)
	if tuning.dither > 0.0 or tuning.color_levels < 255.0:
		var shader := Shader.new()
		shader.code = DITHER_SHADER
		var post := ShaderMaterial.new()
		post.shader = shader
		post.set_shader_parameter("view", view)
		post.set_shader_parameter("levels", tuning.color_levels)
		post.set_shader_parameter("dither", tuning.dither)
		material = post
	var pink_shader := Shader.new()
	pink_shader.code = PINK_SHADER
	_pink_material = ShaderMaterial.new()
	_pink_material.shader = pink_shader
	_flash_material = _new_material(null, {"flash": 1.0, "lit": 0.0, "fog_amount": 0.0})
	if sky_texture != null:
		_build_sky(sky_texture)


func _process(_delta: float) -> void:
	if hud != null:
		hud.queue_redraw()
	if sky_dome != null and camera != null:
		sky_dome.position = Vector3(camera.position.x, camera.position.y, camera.position.z)


func _draw_hud() -> void:
	if draw_hud.is_valid():
		draw_hud.call(hud)


## Цвет роли HUD сеттинга.
func ink(role: int) -> Color:
	return palette[clampi(role, 0, palette.size() - 1)] if not palette.is_empty() else Color.WHITE


# --- Материалы ---------------------------------------------------------------------------------

func _new_material(tex: Texture2D, extra := {}) -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = PS1_SHADER
	if tex != null:
		m.set_shader_parameter("tex", tex)
	m.set_shader_parameter("snap", view / 2.0 / maxf(tuning.vertex_snap, 0.25))
	m.set_shader_parameter("affine", tuning.affine)
	var to_sun := Basis.from_euler(Vector3(deg_to_rad(tuning.sun_pitch), deg_to_rad(tuning.sun_yaw), 0.0)).z
	m.set_shader_parameter("light_dir", to_sun)
	m.set_shader_parameter("sun", Vector3.ONE * tuning.sun_energy)
	m.set_shader_parameter("ambient", Vector3.ONE * tuning.ambient_energy)
	m.set_shader_parameter("fog_color", sky)
	m.set_shader_parameter("fog_begin", tuning.fog_begin)
	m.set_shader_parameter("fog_end", tuning.fog_end)
	m.set_shader_parameter("hue_shift", hue_shift)
	_apply_holes(m)
	for key: String in extra:
		m.set_shader_parameter(key, extra[key])
	return m


## Материал мира с текстурой: один на текстуру и набор отличий (`extra`: `uv_scroll`, `affine`,
## `tint` и другие параметры шейдера).
func tex_material(tex: Texture2D, extra := {}) -> ShaderMaterial:
	var key := "%d:%s" % [tex.get_instance_id() if tex != null else 0, extra]
	if not _materials.has(key):
		_materials[key] = _new_material(tex, extra)
	return _materials[key]


## Чужая палитра (`alien_palette`): оттенок всех материалов мира сдвинут, небо и HUD прежние.
func set_alien(shift: float) -> void:
	alien = true
	hue_shift = shift
	for m: ShaderMaterial in _materials.values():
		m.set_shader_parameter("hue_shift", shift)


## Баг технологии low poly «дыры в моделях» (#111): у моделей пропадает доля граней `share`, у
## уровня `share_level`, ещё доля `flipped` у моделей вывернута и чернеет; набор меняется `rate`
## раз в секунду. Живёт в шейдере, поэтому работает в любой демке low poly; небо не трогает.
func set_holes(share: float, share_level: float, flipped: float, rate: float) -> void:
	holes = clampf(share, 0.0, 1.0)
	_holes_level = clampf(share_level, 0.0, 1.0)
	_flipped = clampf(flipped, 0.0, 1.0)
	_hole_rate = rate
	for m: ShaderMaterial in _materials.values():
		_apply_holes(m)


func _apply_holes(m: ShaderMaterial) -> void:
	m.set_shader_parameter("holes", holes)
	m.set_shader_parameter("holes_level", _holes_level)
	m.set_shader_parameter("flipped", _flipped)
	m.set_shader_parameter("hole_rate", _hole_rate)


# --- Модели ------------------------------------------------------------------------------------

## Модель слота: части узлами в точках вращения, один материал с атласом модели.
func model(def: LowpolyModelDef) -> LowpolyModel:
	var m := LowpolyModel.new()
	m.def = def
	m._flash = _flash_material
	if def == null:
		return m
	var nodes: Array[MeshInstance3D] = []
	var start := 0
	for i in def.part_names.size():
		var node := MeshInstance3D.new()
		node.name = def.part_names[i]
		node.mesh = _part_mesh(def, i, start)
		node.position = def.part_pivots[i]
		start += def.part_tris[i]
		nodes.append(node)
		m.parts[StringName(def.part_names[i])] = node
	for i in nodes.size():
		var parent := def.part_parents[i]
		if parent >= 0 and parent < nodes.size():
			nodes[parent].add_child(nodes[i])
		else:
			m.add_child(nodes[i])
	return m


## Розовая заглушка вместо модели: ящик в шашку в три четверти её габаритов.
func pink_model(def: LowpolyModelDef) -> LowpolyModel:
	var m := LowpolyModel.new()
	m.def = def
	m.pink = true
	m._flash = _flash_material
	var bounds := def.bounds() if def != null else AABB(Vector3(-0.4, 0.0, -0.4), Vector3(0.8, 0.8, 0.8))
	var node := MeshInstance3D.new()
	var mesh := BoxMesh.new()
	mesh.size = (bounds.size * 0.75).max(Vector3(0.3, 0.3, 0.3))
	mesh.material = _pink_material
	node.mesh = mesh
	node.position = Vector3(bounds.get_center().x, bounds.position.y + mesh.size.y / 2.0, bounds.get_center().z)
	m.add_child(node)
	pink_count += 1
	return m


func _part_mesh(def: LowpolyModelDef, part: int, start: int) -> ArrayMesh:
	var key := "%s:%d" % [def.resource_path, part]
	if _meshes.has(key):
		return _meshes[key]
	var verts := PackedVector3Array()
	var normals := PackedVector3Array()
	var uvs := PackedVector2Array()
	for t in range(start, start + def.part_tris[part]):
		# В файле против часовой стрелки наружу, у Godot лицевая сторона по часовой.
		for k: int in [0, 2, 1]:
			verts.append(def.vertices[t * 3 + k])
			normals.append(def.normals[t * 3 + k])
			uvs.append(def.uvs[t * 3 + k])
	var mesh := _commit(verts, normals, uvs, tex_material(def.texture), 0.0)
	_meshes[key] = mesh
	return mesh


# --- Уровень -----------------------------------------------------------------------------------

## Ящик уровня с текстурой: центр `at`, размеры `size`, `tile` метров на повтор текстуры. Грани
## режутся на куски не длиннее `MAX_FACE`.
func add_box(at: Vector3, size: Vector3, tex: Texture2D, tile := 2.0, parent: Node3D = null) -> MeshInstance3D:
	var h := size / 2.0
	var verts := PackedVector3Array()
	var normals := PackedVector3Array()
	var uvs := PackedVector2Array()
	var x := Vector3(size.x, 0, 0)
	var y := Vector3(0, size.y, 0)
	var z := Vector3(0, 0, size.z)
	_face(verts, normals, uvs, Vector3(-h.x, h.y, h.z), x, -z, tile)
	_face(verts, normals, uvs, Vector3(-h.x, -h.y, -h.z), x, z, tile)
	_face(verts, normals, uvs, Vector3(-h.x, -h.y, h.z), x, y, tile)
	_face(verts, normals, uvs, Vector3(h.x, -h.y, -h.z), -x, y, tile)
	_face(verts, normals, uvs, Vector3(h.x, -h.y, h.z), -z, y, tile)
	_face(verts, normals, uvs, Vector3(-h.x, -h.y, -h.z), z, y, tile)
	return _add_mesh(_commit(verts, normals, uvs, tex_material(tex)), at, parent)


## Горизонтальная плоскость (палуба, вода): центр `at`, размеры по x и z, `extra` отличия
## материала (у воды `uv_scroll`).
func add_plane(at: Vector3, size: Vector2, tex: Texture2D, tile := 2.0, extra := {}, parent: Node3D = null) -> MeshInstance3D:
	var verts := PackedVector3Array()
	var normals := PackedVector3Array()
	var uvs := PackedVector2Array()
	_face(verts, normals, uvs, Vector3(-size.x / 2.0, 0.0, size.y / 2.0), Vector3(size.x, 0, 0), Vector3(0, 0, -size.y), tile,
			maxf(MAX_FACE, maxf(size.x, size.y) / 24.0))
	# Плоскость до горизонта (море) режется на огромные клетки: дыра в ней закрыла бы пол-экрана.
	return _add_mesh(_commit(verts, normals, uvs, tex_material(tex, extra), 2.0 if maxf(size.x, size.y) > FAR_PLANE else 1.0), at, parent)


## Тень-блин под героем или вещью: тёмный полупрозрачный восьмиугольник, демка кладёт его на землю.
func add_shadow(radius := 0.45, parent: Node3D = null) -> MeshInstance3D:
	if _shadow_mesh == null:
		_shadow_material = StandardMaterial3D.new()
		_shadow_material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		_shadow_material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		_shadow_material.albedo_color = Color(0.0, 0.0, 0.0, tuning.shadow_alpha)
		var verts := PackedVector3Array()
		var normals := PackedVector3Array()
		var uvs := PackedVector2Array()
		for k in 8:
			var a := TAU * k / 8.0
			var b := TAU * (k + 1) / 8.0
			for p: Vector3 in [Vector3.ZERO, Vector3(sin(b), 0.0, cos(b)), Vector3(sin(a), 0.0, cos(a))]:
				verts.append(p)
				normals.append(Vector3.UP)
				uvs.append(Vector2.ZERO)
		_shadow_mesh = _commit(verts, normals, uvs, _shadow_material)
	var node := _add_mesh(_shadow_mesh, Vector3.ZERO, parent)
	node.scale = Vector3(radius, 1.0, radius)
	return node


func _build_sky(tex: Texture2D) -> void:
	var verts := PackedVector3Array()
	var normals := PackedVector3Array()
	var uvs := PackedVector2Array()
	var radius := tuning.far * 0.7
	var sides := 16
	for k in sides:
		var a := TAU * k / sides
		var b := TAU * (k + 1) / sides
		var lo_a := Vector3(sin(a) * radius, -radius * 0.12, cos(a) * radius)
		var lo_b := Vector3(sin(b) * radius, -radius * 0.12, cos(b) * radius)
		var up := Vector3(0.0, radius * 0.75, 0.0)
		var ua := 2.0 * k / sides
		var ub := 2.0 * (k + 1) / sides
		# Изнутри цилиндра: грани смотрят на камеру.
		for item: Array in [[lo_a, Vector2(ua, 1.0)], [lo_b + up, Vector2(ub, 0.0)], [lo_a + up, Vector2(ua, 0.0)],
				[lo_a, Vector2(ua, 1.0)], [lo_b, Vector2(ub, 1.0)], [lo_b + up, Vector2(ub, 0.0)]]:
			verts.append(item[0])
			normals.append(Vector3.UP)
			uvs.append(item[1])
		# Крышка: небо смыкается в зените цветом верхней строки панорамы (обе стороны грани).
		var top := Vector3(0.0, radius * 1.1, 0.0)
		for item: Array in [[lo_a + up, ua], [lo_b + up, ub], [top, (ua + ub) / 2.0], [lo_a + up, ua], [top, (ua + ub) / 2.0], [lo_b + up, ub]]:
			verts.append(item[0])
			normals.append(Vector3.UP)
			uvs.append(Vector2(item[1], 0.01))
	sky_dome = MeshInstance3D.new()
	sky_dome.mesh = _commit(verts, normals, uvs, _new_material(tex, {"lit": 0.0, "fog_amount": 0.0, "affine": 0.0}))
	viewport.add_child(sky_dome)
	viewport.move_child(sky_dome, world.get_index())


func _add_mesh(mesh: Mesh, at: Vector3, parent: Node3D) -> MeshInstance3D:
	var node := MeshInstance3D.new()
	node.mesh = mesh
	node.position = at
	(parent if parent != null else world).add_child(node)
	return node


## Грань из угла `o` по рёбрам `eu` и `ev` (нормаль `eu × ev`), сеткой с шагом не больше `step`.
static func _face(verts: PackedVector3Array, normals: PackedVector3Array, uvs: PackedVector2Array, o: Vector3, eu: Vector3,
		ev: Vector3, tile: float, step := MAX_FACE) -> void:
	var nu := maxi(ceili(eu.length() / step), 1)
	var nv := maxi(ceili(ev.length() / step), 1)
	var n := eu.cross(ev).normalized()
	for i in nu:
		for j in nv:
			var f := [Vector2(i, j) , Vector2(i + 1, j), Vector2(i + 1, j + 1), Vector2(i, j + 1)]
			for k: int in [0, 1, 2, 0, 2, 3]:
				var q: Vector2 = f[k]
				var uv := Vector2(q.x / nu, q.y / nv)
				push(verts, normals, uvs, o + eu * uv.x + ev * uv.y, n, Vector2(uv.x * eu.length(), -uv.y * ev.length()) / tile)
	# Тройки записаны против часовой стрелки; под Godot меняем вторую и третью вершину местами.
	flip_last(verts, normals, uvs, nu * nv * 2)


static func push(verts: PackedVector3Array, normals: PackedVector3Array, uvs: PackedVector2Array, p: Vector3, n: Vector3,
		uv: Vector2) -> void:
	verts.append(p)
	normals.append(n)
	uvs.append(uv)


## Последние `tris` треугольников из порядка против часовой стрелки в порядок Godot.
static func flip_last(verts: PackedVector3Array, normals: PackedVector3Array, uvs: PackedVector2Array, tris: int) -> void:
	for t in tris:
		var i := verts.size() - 3 * (t + 1)
		var v := verts[i + 1]
		verts[i + 1] = verts[i + 2]
		verts[i + 2] = v
		var n := normals[i + 1]
		normals[i + 1] = normals[i + 2]
		normals[i + 2] = n
		var u := uvs[i + 1]
		uvs[i + 1] = uvs[i + 2]
		uvs[i + 2] = u


## Меш из троек вершин. В цвет вершины кладётся номер грани (красный, 0..1, один на тройку) и
## `level` (0 модель, 1 геометрия уровня, 2 дальний план: зелёный и синий каналы): по ним шейдер выбирает грани для бага
## «дыры в моделях».
static func _commit(verts: PackedVector3Array, normals: PackedVector3Array, uvs: PackedVector2Array, mat: Material,
		level := 1.0) -> ArrayMesh:
	var colors := PackedColorArray()
	colors.resize(verts.size())
	for i in verts.size():
		# Цвет вершины хранится байтами 0..1, поэтому дальний план отдельным каналом.
		colors[i] = Color(fposmod((i / 3) * 0.6180339, 1.0), minf(level, 1.0), 1.0 if level > 1.5 else 0.0)
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = verts
	arrays[Mesh.ARRAY_NORMAL] = normals
	arrays[Mesh.ARRAY_TEX_UV] = uvs
	arrays[Mesh.ARRAY_COLOR] = colors
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	mesh.surface_set_material(0, mat)
	return mesh
