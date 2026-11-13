shader_type spatial;
// Вода «продвинутых» (#121, плейтест 2026-11-13: «объёмная, насколько можем»). Сетка качается
// суммой четырёх бегущих волн, мелкая рябь идёт двумя картами нормалей навстречу друг другу.
// Цвет по толщине воды до дна или берега за ней (глубина кадра): у берега прозрачная и
// светлая, дальше густая; дно видно с преломлением. Небо и блик солнца отражаются сами
// (гладкая поверхность, зеркальность по Френелю). Пена у берега и на гребнях.
render_mode specular_schlick_ggx, depth_draw_always, cull_back;

uniform vec3 deep_color : source_color = vec3(0.02, 0.16, 0.24);
uniform vec3 shallow_color : source_color = vec3(0.12, 0.52, 0.56);
uniform vec3 foam_color : source_color = vec3(0.92, 0.97, 0.98);
// На какой толщине вода становится непрозрачной и на какой кончается пена берега.
uniform float clarity = 7.0;
uniform float foam_width = 0.9;
uniform float wave_height = 1.0;
uniform float ripple_strength = 0.6;
uniform float refraction = 0.03;
uniform float hue_shift = 0.0;
uniform sampler2D ripple : hint_normal, filter_linear_mipmap, repeat_enable;
uniform sampler2D foam_noise : filter_linear_mipmap, repeat_enable;
uniform sampler2D depth_tex : hint_depth_texture, filter_linear, repeat_disable;
uniform sampler2D screen_tex : hint_screen_texture, filter_linear, repeat_disable;

varying vec3 world_pos;
varying float crest;

vec3 shift_hue(vec3 c, float turns) {
	float a = turns * 6.2831853;
	vec3 k = vec3(0.57735);
	return c * cos(a) + cross(k, c) * sin(a) + k * dot(k, c) * (1.0 - cos(a));
}

// Волна: направление, длина, высота, скорость. Возвращает высоту и копит наклон.
float wave(vec2 p, vec2 dir, float len, float amp, float speed, inout vec2 slope) {
	float k = 6.2831853 / len;
	float ph = dot(normalize(dir), p) * k + TIME * speed;
	slope += normalize(dir) * k * amp * cos(ph);
	return amp * sin(ph);
}

void vertex() {
	vec3 w = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
	vec2 slope = vec2(0.0);
	float h = 0.0;
	h += wave(w.xz, vec2(1.0, 0.35), 31.0, 0.22, 1.1, slope);
	h += wave(w.xz, vec2(-0.45, 1.0), 19.0, 0.14, 1.5, slope);
	h += wave(w.xz, vec2(0.8, -0.7), 11.0, 0.075, 2.1, slope);
	h += wave(w.xz, vec2(-0.9, -0.25), 6.5, 0.04, 2.8, slope);
	h *= wave_height;
	slope *= wave_height;
	VERTEX.y += h;
	NORMAL = normalize(vec3(-slope.x, 1.0, -slope.y));
	TANGENT = normalize(vec3(1.0, slope.x, 0.0));
	BINORMAL = normalize(cross(NORMAL, TANGENT));
	world_pos = w;
	crest = h / max(wave_height * 0.48, 0.001);
}

void fragment() {
	// Рябь: две карты навстречу, разного масштаба.
	vec2 uv1 = world_pos.xz * 0.11 + vec2(TIME * 0.035, TIME * 0.02);
	vec2 uv2 = world_pos.xz * 0.27 - vec2(TIME * 0.03, -TIME * 0.045);
	vec3 n = mix(texture(ripple, uv1).rgb, texture(ripple, uv2).rgb, 0.5);
	NORMAL_MAP = n;
	NORMAL_MAP_DEPTH = ripple_strength;
	// Толщина воды до того, что за ней.
	vec2 bend = (n.xy - 0.5) * refraction;
	float depth = texture(depth_tex, SCREEN_UV + bend).r;
	vec4 behind = INV_PROJECTION_MATRIX * vec4((SCREEN_UV + bend) * 2.0 - 1.0, depth, 1.0);
	float thick = -behind.z / behind.w + VERTEX.z;
	if (thick < 0.0) {
		// Преломлённая точка оказалась перед водой: берём без сдвига.
		bend = vec2(0.0);
		depth = texture(depth_tex, SCREEN_UV).r;
		behind = INV_PROJECTION_MATRIX * vec4(SCREEN_UV * 2.0 - 1.0, depth, 1.0);
		thick = -behind.z / behind.w + VERTEX.z;
	}
	float murk = 1.0 - exp(-max(thick, 0.0) / clarity * 3.0);
	vec3 body = mix(shallow_color, deep_color, smoothstep(0.0, 1.0, murk));
	vec3 bottom = texture(screen_tex, SCREEN_UV + bend).rgb;
	// Пена: полоса у берега, рваная по шуму, и барашки на гребнях.
	float noise = texture(foam_noise, world_pos.xz * 0.16 + vec2(TIME * 0.02, -TIME * 0.015)).r;
	float shore = 1.0 - smoothstep(0.0, foam_width, thick + (noise - 0.5) * foam_width * 0.9);
	float lace = smoothstep(0.55, 0.9, sin(thick * 7.0 - TIME * 2.2) * 0.5 + 0.5) * (1.0 - smoothstep(0.0, foam_width * 2.2, thick)) * noise;
	float caps = smoothstep(0.86, 1.1, crest * 0.62 + noise * 0.7) * 0.4;
	float foam = clamp(shore + lace + caps, 0.0, 1.0);
	if (hue_shift != 0.0) {
		body = clamp(shift_hue(body, hue_shift), 0.0, 1.0);
	}
	// Дно просвечивает как свет из-под воды, сама вода освещается солнцем.
	ALBEDO = mix(body * murk, foam_color, foam);
	EMISSION = bottom * mix(vec3(1.0), shallow_color * 1.6, clamp(murk * 1.5, 0.0, 1.0)) * (1.0 - murk) * (1.0 - foam);
	ROUGHNESS = mix(0.07, 0.6, foam);
	SPECULAR = 0.65;
	METALLIC = 0.0;
}
