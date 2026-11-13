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


## Экран в области `area`: цвета HUD `palette_`, цвет неба сеттинга `sky_`; `scale` 0 берёт
## размер HUD из `LowpolyTuning`.
static func make_threed(area: Vector2, embedded_: bool, palette_: Array[Color], sky_: Color, scale := 0) -> ThreedScreen:
	var s := ThreedScreen.new()
	s.look = ThreedTuning.load_default()
	s._setup(area, embedded_, palette_, sky_, null, scale)
	return s


func _render_shrink(_shrink: int) -> int:
	return 1


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
		if key in ["tint", "uv_scroll", "flash", "lit", "hue_shift", "rim", "rough"]:
			m.set_shader_parameter(key, extra[key])
	return m


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
