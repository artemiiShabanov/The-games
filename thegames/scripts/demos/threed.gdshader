shader_type spatial;
// Материал «продвинутых» (threed, #118): гладкий свет с мягкой границей, настоящие тени,
// контровой свет по краю, текстура с фильтром. Параметры зовутся как у `lowpoly_ps1.gdshader`,
// чтобы уровень и модели собирались одним кодом; чего здесь нет (`snap`, `affine`, дыры), то
// просто не используется.
render_mode diffuse_lambert_wrap, specular_schlick_ggx;

uniform sampler2D tex : source_color, filter_linear_mipmap, repeat_enable;
uniform vec4 tint : source_color = vec4(1.0);
uniform float hue_shift = 0.0;
uniform vec2 uv_scroll = vec2(0.0);
// Белая заливка на кадр попадания.
uniform float flash = 0.0;
// 0: без света, цвет как есть (вода, дым, ветер).
uniform float lit = 1.0;
uniform float rim = 0.35;
uniform float rough = 0.82;

vec3 shift_hue(vec3 c, float turns) {
	float a = turns * 6.2831853;
	vec3 k = vec3(0.57735);
	return c * cos(a) + cross(k, c) * sin(a) + k * dot(k, c) * (1.0 - cos(a));
}

void vertex() {
	UV += uv_scroll * TIME;
}

void fragment() {
	vec4 c = texture(tex, UV) * tint;
	if (c.a < 0.5) {
		discard;
	}
	vec3 rgb = c.rgb;
	if (hue_shift != 0.0) {
		rgb = clamp(shift_hue(rgb, hue_shift), 0.0, 1.0);
	}
	rgb = mix(rgb, vec3(1.0), flash);
	ALBEDO = rgb * lit;
	EMISSION = rgb * (1.0 - lit) + vec3(flash) * 0.5;
	ROUGHNESS = rough;
	SPECULAR = 0.25;
	RIM = rim * lit;
	RIM_TINT = 0.35;
}
