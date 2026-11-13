class_name ThreedScreen
extends LowpolyScreen
## Экран демок «продвинутых» (threed, #118, решение 2026-11-13: стилизованное современное 3D).
## Наследует сборку сцены, моделей и уровня у `LowpolyScreen`, поэтому демки пользуются им так
## же (`world`, `camera`, `model`, `add_box`, `add_plane`, HUD в `draw_hud`), а картинка другая:
## сцена рисуется в полном разрешении, меши плотные (набор `threed` из `tools/lowpoly_meshes.py`),
## текстуры 256×256 с фильтром, материал `threed.gdshader` с гладким светом и контровым краем,
## солнце с мягкими тенями, небо градиентом, туман с воздушной перспективой, свечение,
## цветокоррекция. Дрожания вершин, аффинных текстур и дизеринга нет. HUD рисуется в том же
## виртуальном экране и растягивается до полного разрешения. Тень-блин не нужна: тени настоящие.
## Общие баги: розовая заглушка это ящик в розово-чёрную шашку, чужая палитра сдвигает оттенок
## материалов. Во встроенном режиме (стрим ленты) затенение в углах и сглаживание выключены.

const SHADER := preload("res://scripts/demos/threed.gdshader")
const WATER_SHADER := preload("res://scripts/demos/threed_water.gdshader")
const CHECKER_SHADER := """
shader_type spatial;
uniform float cell = 0.2;
varying vec3 local;
void vertex() {
	local = VERTEX;
}
void fragment() {
	vec3 c = floor(local / cell + 0.5);
	float k = mod(c.x + c.y + c.z, 2.0);
	ALBEDO = mix(vec3(1.0, 0.169, 0.839), vec3(0.03), k);
	EMISSION = ALBEDO * 0.35;
	ROUGHNESS = 0.6;
}
"""

var look: ThreedTuning
var sun_light: DirectionalLight3D
## Баг технологии «камера в стене» (#120): раз в `clip_period` секунд на `clip_seconds` ближняя
## граница кадра уезжает на `clip_depth` метров, и всё, что ближе (герой, стена, оружие в руке),
## пропадает: камера смотрит сквозь. 0 выключено.
var clip_period := 0.0
var clip_seconds := 1.3
var clip_depth := 7.0
## Камера сейчас «в стене» (проверки и HUD демок).
var clipping := false
var _clip_time := 0.0


## Экран в области `area`: цвета HUD `palette_`, цвет неба сеттинга `sky_`; `scale` 0 берёт
## размер HUD из `LowpolyTuning`.
static func make_threed(area: Vector2, embedded_: bool, palette_: Array[Color], sky_: Color, scale := 0) -> ThreedScreen:
	var s := ThreedScreen.new()
	s.look = ThreedTuning.load_default()
	s._setup(area, embedded_, palette_, sky_, null, scale)
	return s


func _render_shrink(_shrink: int) -> int:
	return 1


## Прогрев (#130): материалы «продвинутых» собираются при первом показе, и кадр на секунду
## замирает. Крошечный экран за краем окна с моделью на скелете, реквизитом, заглушкой и белой
## заливкой рисуется несколько кадров и исчезает: сборка проходит в меню, а не в демке.
static var warmed := false


static func prewarm(host: Node) -> void:
	if warmed or DisplayServer.get_name() == "headless":
		return
	warmed = true
	var set := SettingDef.of(Game.Setting.PIRATES)
	var screen := ThreedScreen.make_threed(Vector2(192, 96), false, set.colors_lowpoly(), set.sky_lowpoly())
	screen.position = Vector2(-400, -400)
	host.add_child(screen)
	screen.add_plane(Vector3.ZERO, Vector2(6, 6), set.texture_lowpoly("sand", true), 3.0)
	screen.add_plane(Vector3(0, -0.2, 0), Vector2(8, 8), set.texture_lowpoly("water", true), 6.0, {"uv_scroll": Vector2(0.02, 0.03)})
	var at := -1.0
	for item: LowpolyModel in [screen.model(set.model("barrel", true)), screen.pink_model(set.model("crate", true)),
			RigModel.make(set.rig("hero"), screen.look), RigModel.make(set.rig("enemy"), screen.look)]:
		item.position = Vector3(at, 0.0, 0.0)
		at += 0.7
		screen.world.add_child(item)
		if item is RigModel:
			item.flash(at > 0.8)
	screen.camera.transform = Transform3D(Basis.IDENTITY, Vector3(0.0, 1.2, 4.0)).looking_at(Vector3(0.0, 0.8, 0.0))
	for i in 6:
		await host.get_tree().process_frame
	if is_instance_valid(screen):
		screen.queue_free()


func _build_scene(_sky_texture: Texture2D) -> void:
	LowpolyScreen.with_tangents = true
	super._build_scene(null)
	# Без дизеринга и ближайшего соседа: кадр как есть.
	material = null
	texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	if look.msaa and not embedded:
		viewport.msaa_3d = Viewport.MSAA_2X
	# Небо градиентом от цвета сеттинга.
	var sky_material := ProceduralSkyMaterial.new()
	var top := sky.darkened(1.0 - look.sky_top)
	top.s = minf(top.s * 2.6, 0.75)
	sky_material.sky_top_color = top
	sky_material.sky_horizon_color = sky.lightened(look.sky_horizon - 1.0)
	sky_material.ground_horizon_color = sky.lightened(look.sky_horizon - 1.0)
	sky_material.ground_bottom_color = sky.darkened(0.35)
	sky_material.sun_angle_max = 12.0
	var sky_resource := Sky.new()
	sky_resource.sky_material = sky_material
	environment.background_mode = Environment.BG_SKY
	environment.sky = sky_resource
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	environment.ambient_light_energy = look.ambient_energy
	environment.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	environment.tonemap_exposure = look.exposure
	environment.fog_enabled = true
	environment.fog_light_color = sky
	environment.fog_density = look.fog_density
	environment.fog_aerial_perspective = look.fog_aerial
	environment.fog_sky_affect = 0.0
	environment.glow_enabled = true
	environment.glow_intensity = look.glow_intensity
	environment.glow_bloom = look.glow_bloom
	environment.glow_hdr_threshold = look.glow_threshold
	environment.adjustment_enabled = true
	environment.adjustment_saturation = look.saturation
	environment.adjustment_contrast = look.contrast
	environment.ssao_enabled = look.ssao and not embedded
	# Солнце с мягкими тенями.
	sun_light = DirectionalLight3D.new()
	sun_light.rotation = Vector3(deg_to_rad(look.sun_pitch), deg_to_rad(look.sun_yaw), 0.0)
	sun_light.light_energy = look.sun_energy
	sun_light.light_color = look.sun_color
	sun_light.shadow_enabled = true
	sun_light.shadow_blur = look.shadow_blur
	sun_light.shadow_bias = 0.04
	sun_light.shadow_normal_bias = 1.0
	sun_light.directional_shadow_max_distance = look.shadow_distance
	sun_light.directional_shadow_mode = DirectionalLight3D.SHADOW_ORTHOGONAL if embedded else DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS
	viewport.add_child(sun_light)
	var checker := Shader.new()
	checker.code = CHECKER_SHADER
	_pink_material = ShaderMaterial.new()
	_pink_material.shader = checker


func _new_material(tex: Texture2D, extra := {}) -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = SHADER
	if tex != null:
		m.set_shader_parameter("tex", tex)
		# Карта рельефа лежит рядом с текстурой: `<имя>_n.png` (пишет генератор).
		var bump := tex.resource_path.replace(".png", "_n.png")
		if tex.resource_path.ends_with(".png") and ResourceLoader.exists(bump):
			m.set_shader_parameter("normal_tex", load(bump))
			m.set_shader_parameter("normal_strength", look.normal_strength)
	m.set_shader_parameter("hue_shift", hue_shift)
	m.set_shader_parameter("rim", look.rim)
	m.set_shader_parameter("rough", look.rough)
	for key: String in extra:
		# Параметры шейдера PS1, которых тут нет, пропускаются.
		if key in ["tint", "uv_scroll", "uv_scale", "flash", "lit", "hue_shift", "rim", "rough"]:
			m.set_shader_parameter(key, extra[key])
	return m


## Включить баг «камера в стене»: живёт на экране, поэтому работает в любой демке «продвинутых».
func set_clip(period: float, seconds: float, depth: float) -> void:
	clip_period = maxf(period, 0.0)
	clip_seconds = seconds
	clip_depth = depth
	# Первый провал скоро: баг виден в первые секунды демки.
	_clip_time = maxf(clip_period - 2.0, 0.0)


func _process(delta: float) -> void:
	super._process(delta)
	if clip_period <= 0.0 or camera == null:
		return
	_clip_time += delta
	clipping = fmod(_clip_time, clip_period) < clip_seconds
	camera.near = clip_depth if clipping else 0.1


## Вода с волнами, глубиной и пеной (`threed_water.gdshader`): плоскость `size` метров с
## серединой `at`, уровень воды это `at.y`. Сетка частая у середины хватает на волны; мелкая
## рябь и пена идут по шумовым текстурам.
func add_water(at: Vector3, size: float) -> MeshInstance3D:
	var plane := PlaneMesh.new()
	plane.size = Vector2(size, size)
	var cells := 90 if embedded else 260
	plane.subdivide_width = cells
	plane.subdivide_depth = cells
	var m := ShaderMaterial.new()
	m.shader = WATER_SHADER
	var bumps := FastNoiseLite.new()
	bumps.noise_type = FastNoiseLite.TYPE_SIMPLEX_SMOOTH
	bumps.frequency = 0.035
	bumps.fractal_octaves = 4
	var ripple := NoiseTexture2D.new()
	ripple.width = 256
	ripple.height = 256
	ripple.seamless = true
	ripple.as_normal_map = true
	ripple.bump_strength = 7.0
	ripple.noise = bumps
	var spots := FastNoiseLite.new()
	spots.noise_type = FastNoiseLite.TYPE_CELLULAR
	spots.frequency = 0.05
	var foam := NoiseTexture2D.new()
	foam.width = 256
	foam.height = 256
	foam.seamless = true
	foam.noise = spots
	m.set_shader_parameter("ripple", ripple)
	m.set_shader_parameter("foam_noise", foam)
	m.set_shader_parameter("deep_color", look.water_deep)
	m.set_shader_parameter("shallow_color", look.water_shallow)
	m.set_shader_parameter("clarity", look.water_clarity)
	m.set_shader_parameter("wave_height", look.water_waves)
	m.set_shader_parameter("hue_shift", hue_shift)
	plane.material = m
	var node := MeshInstance3D.new()
	node.mesh = plane
	node.position = at
	node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	world.add_child(node)
	return node


## Пальма (#121, плейтест 2026-11-13: листья объёмные, свисают и качаются): изогнутый ствол
## трубой и крона из листьев-лент. Лист растёт из верхушки ствола, сначала вверх и в сторону,
## потом провисает; в сечении он сложен вдоль жилки, обе стороны видны. Доля качания едет во
## второй развёртке (к концу листа больше), качает шейдер. `tex` это атлас пальмы: слева кора,
## справа лист.
func add_palm(tex: Texture2D, at: Vector3, yaw: float, height: float, rng: RandomNumberGenerator) -> MeshInstance3D:
	var tool := SurfaceTool.new()
	tool.begin(Mesh.PRIMITIVE_TRIANGLES)
	# Ствол: дуга в сторону `lean`, к верхушке тоньше.
	var lean := Vector3(sin(rng.randf_range(0.0, TAU)), 0.0, cos(rng.randf_range(0.0, TAU))).normalized() * rng.randf_range(0.35, 0.8)
	var spine: Array[Vector3] = []
	var rows := 9
	for i in rows:
		var k := float(i) / (rows - 1)
		spine.append(Vector3(0.0, height * k, 0.0) + lean * k * k)
	var sides := 8
	for i in rows - 1:
		for j in sides:
			var quad: Array = []
			for corner: Vector2i in [Vector2i(i, j), Vector2i(i + 1, j), Vector2i(i + 1, j + 1), Vector2i(i, j + 1)]:
				var k := float(corner.x) / (rows - 1)
				var a := TAU * corner.y / sides
				var r := lerpf(0.21, 0.11, k) * (1.18 if corner.x == 0 else 1.0)
				quad.append([spine[corner.x] + Vector3(cos(a), 0.0, sin(a)) * r, Vector3(cos(a), 0.15, sin(a)).normalized(),
						Vector2(0.02 + 0.46 * corner.y / sides, height * k / 2.2)])
			for id: int in [0, 1, 2, 0, 2, 3]:
				tool.set_normal(quad[id][1])
				tool.set_uv(quad[id][2])
				tool.set_uv2(Vector2.ZERO)
				tool.add_vertex(quad[id][0])
	# Крона: большие листья по кругу и короткие молодые вверх.
	var top := spine[rows - 1] - Vector3(0.0, 0.05, 0.0)
	var count := rng.randi_range(9, 11)
	for n in count + 4:
		var young := n >= count
		var around := TAU * n / count + rng.randf_range(-0.2, 0.2) if not young else TAU * (n - count) / 4.0 + 0.6
		var out := Vector3(sin(around), 0.0, cos(around))
		var across := Vector3(out.z, 0.0, -out.x)
		var length := rng.randf_range(2.5, 3.2) if not young else rng.randf_range(1.2, 1.6)
		var rise := deg_to_rad(rng.randf_range(28.0, 48.0) if not young else rng.randf_range(62.0, 78.0))
		var droop := deg_to_rad(rng.randf_range(95.0, 125.0) if not young else 50.0)
		var half := (0.5 if not young else 0.3) * length / 2.9
		var steps := 7
		var mids: Array[Vector3] = [top]
		var dirs: Array[Vector3] = []
		for i in steps:
			var k := (i + 0.5) / steps
			var pitch := rise - droop * pow(k, 1.25)
			var dir := (out * cos(pitch) + Vector3.UP * sin(pitch)).normalized()
			dirs.append(dir)
			mids.append(mids[i] + dir * length / steps)
		dirs.append(dirs[steps - 1])
		for i in steps:
			for flank: float in [-1.0, 1.0]:
				var quad: Array = []
				for row: int in [i, i + 1]:
					var k := float(row) / steps
					# Сложен вдоль жилки: края ниже середины.
					var up := dirs[row].cross(across).normalized() * (-1.0 if dirs[row].cross(across).y < 0.0 else 1.0)
					var edge := mids[row] + (across * flank * 0.9 - up * 0.42).normalized() * half
					var sway := k * k * 7.0
					quad.append([mids[row], Vector2(0.75, 0.02 + 0.96 * k), sway, up])
					quad.append([edge, Vector2(0.75 + flank * 0.245, 0.02 + 0.96 * k), sway * 1.15, (up + across * flank * 0.45).normalized()])
				# Обе стороны листа.
				for order: Array in [[0, 1, 3], [0, 3, 2], [0, 3, 1], [0, 2, 3]]:
					var pa: Vector3 = quad[order[0]][0]
					var pb: Vector3 = quad[order[1]][0]
					var pc: Vector3 = quad[order[2]][0]
					# Лицевая сторона у Godot по часовой: нормаль вершины смотрит туда же, куда грань.
					var face := (pc - pa).cross(pb - pa)
					for id: int in order:
						var normal: Vector3 = quad[id][3]
						var bend: float = quad[id][2]
						tool.set_normal(normal if normal.dot(face) >= 0.0 else -normal)
						tool.set_uv(quad[id][1])
						tool.set_uv2(Vector2(bend, 0.0))
						tool.add_vertex(quad[id][0])
	tool.generate_tangents()
	var mesh := tool.commit()
	var m := _new_material(tex)
	m.set_shader_parameter("cloth_sway", look.palm_sway)
	mesh.surface_set_material(0, m)
	var node := MeshInstance3D.new()
	node.mesh = mesh
	node.position = at
	node.rotation.y = yaw
	world.add_child(node)
	return node


## Тени настоящие: вместо тени-блина пустой узел, чтобы демки ставили его как обычно.
func add_shadow(_radius := 0.45, parent: Node3D = null) -> MeshInstance3D:
	var node := MeshInstance3D.new()
	(parent if parent != null else world).add_child(node)
	return node


## Дыры в моделях это баг low poly; у «продвинутых» свой (#120).
func set_holes(_share: float, _share_level: float, _flipped: float, _rate: float) -> void:
	pass


func _apply_holes(_m: ShaderMaterial) -> void:
	pass
