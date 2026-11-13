shader_type spatial;
// Сыпучая земля «продвинутых» (#124, плейтест 2026-11-13: у песка виден узор). Песок, а в
// других сеттингах снег: текстура кладётся по координатам мира тремя слоями разного масштаба
// и поворота, слои мешаются по шуму, поэтому повтор плитки не читается; крупный шум даёт
// светлые и тёмные поля, рельеф идёт от двух слоёв карты нормалей, отдельные зёрна блестят.
render_mode diffuse_lambert_wrap, specular_schlick_ggx;

uniform sampler2D tex : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D normal_tex : hint_normal, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D noise_tex : filter_linear_mipmap, repeat_enable;
uniform float normal_strength = 0.8;
uniform float hue_shift = 0.0;
// Насколько приглушён рисунок текстуры (0 как есть, 1 ровный цвет) и сила блеска зёрен.
uniform float flatten = 0.45;
uniform float glint = 0.7;
uniform vec4 tint : source_color = vec4(1.0);

varying vec3 world_pos;

vec3 shift_hue(vec3 c, float turns) {
	float a = turns * 6.2831853;
	vec3 k = vec3(0.57735);
	return c * cos(a) + cross(k, c) * sin(a) + k * dot(k, c) * (1.0 - cos(a));
}

void vertex() {
	world_pos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz;
}

void fragment() {
	vec2 p = world_pos.xz;
	vec2 uv_a = p * 0.21;
	vec2 uv_b = mat2(vec2(0.8, 0.6), vec2(-0.6, 0.8)) * p * 0.083 + vec2(0.37, 0.11);
	vec2 uv_c = mat2(vec2(0.28, -0.96), vec2(0.96, 0.28)) * p * 0.47 + vec2(0.6, 0.2);
	float fields = texture(noise_tex, p * 0.0045).r;
	float patches = texture(noise_tex, p * 0.027 + vec2(0.5, 0.3)).r;
	float blend = smoothstep(0.35, 0.65, patches);
	vec3 a = texture(tex, uv_a).rgb;
	vec3 b = texture(tex, uv_b).rgb;
	vec3 c = texture(tex, uv_c).rgb;
	vec3 color = mix(mix(a, b, blend), c, 0.3);
	// Рисунок приглушён к среднему тону: остаётся зерно, а не полосы.
	vec3 mean = textureLod(tex, uv_b, 6.0).rgb;
	color = mix(color, mean, flatten) * tint.rgb;
	color *= 0.86 + 0.26 * fields;
	if (hue_shift != 0.0) {
		color = clamp(shift_hue(color, hue_shift), 0.0, 1.0);
	}
	ALBEDO = color;
	NORMAL_MAP = mix(texture(normal_tex, uv_a).rgb, texture(normal_tex, uv_b).rgb, blend);
	NORMAL_MAP_DEPTH = normal_strength;
	float grain = texture(noise_tex, p * 1.7).r * texture(noise_tex, p * 2.9 + vec2(0.3, 0.7)).r;
	float spark = smoothstep(0.42, 0.55, grain) * glint;
	ROUGHNESS = mix(0.94, 0.3, spark);
	SPECULAR = 0.3 + 0.4 * spark;
}
