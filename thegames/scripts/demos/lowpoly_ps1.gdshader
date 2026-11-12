shader_type spatial;
render_mode unshaded;
// Материал low poly в духе первой PlayStation (#108). Вершины прилипают к сетке экрана и
// дрожат при движении, текстура ложится аффинно и плывёт на крупных гранях, свет считается по
// вершинам, туман тоже. Текстура без сглаживания и без мипов, прозрачные пиксели вырезаются.
// Числа ставит `LowpolyScreen` из `LowpolyTuning`.

uniform sampler2D tex : source_color, filter_nearest, repeat_enable;
uniform vec4 tint : source_color = vec4(1.0);
// Сетка прилипания в долях экрана: половина разрешения на шаг в пикселях.
uniform vec2 snap = vec2(138.0, 69.0);
// 1 полностью аффинное наложение, 0 правильная перспектива.
uniform float affine = 1.0;
uniform vec3 light_dir = vec3(0.4, 0.8, 0.4);
uniform vec3 sun = vec3(0.8);
uniform vec3 ambient = vec3(0.45);
uniform vec3 fog_color : source_color = vec3(0.6, 0.8, 0.9);
uniform float fog_begin = 28.0;
uniform float fog_end = 85.0;
// Сколько тумана ложится на материал: у неба 0.
uniform float fog_amount = 1.0;
// Сколько света берёт материал: у неба 0 (текстура как есть).
uniform float lit = 1.0;
uniform float hue_shift = 0.0;
uniform vec2 uv_scroll = vec2(0.0);
// Белая заливка на кадр попадания.
uniform float flash = 0.0;
// Баг технологии «дыры в моделях» (#111): доля пропавших граней у моделей и у уровня, доля
// вывернутых (чернеют), сколько раз в секунду набор меняется. Номер грани в COLOR.r, в COLOR.g
// метка: 0 модель, 1 геометрия уровня; в COLOR.b единица у дальнего плана без дыр.
uniform float holes = 0.0;
uniform float holes_level = 0.0;
uniform float flipped = 0.0;
uniform float hole_rate = 1.4;

varying vec3 uvw;
varying vec3 light;
varying float fog;

vec3 shift_hue(vec3 c, float shift) {
	const vec3 k = vec3(0.57735);
	float a = shift * 6.2831853;
	return c * cos(a) + cross(k, c) * sin(a) + k * dot(k, c) * (1.0 - cos(a));
}

void vertex() {
	vec3 n = normalize((MODEL_MATRIX * vec4(NORMAL, 0.0)).xyz);
	light = mix(vec3(1.0), ambient + sun * max(dot(n, normalize(light_dir)), 0.0), lit);
	vec4 view = MODELVIEW_MATRIX * vec4(VERTEX, 1.0);
	vec4 clip = PROJECTION_MATRIX * view;
	clip.xy = floor(clip.xy / clip.w * snap + 0.5) / snap * clip.w;
	POSITION = clip;
	float w = mix(1.0, max(clip.w, 0.001), affine);
	uvw = vec3((UV + uv_scroll * TIME) * w, w);
	fog = clamp((-view.z - fog_begin) / max(fog_end - fog_begin, 0.001), 0.0, 1.0) * fog_amount;
	if (holes > 0.0 || holes_level > 0.0) {
		float roll = fract(sin((COLOR.r * 97.0 + floor(TIME * hole_rate) * 0.37) * 91.7) * 43758.5453);
		// Синий канал: дальний план (море), его баг не трогает.
		float share = COLOR.b > 0.5 ? 0.0 : mix(holes, holes_level, COLOR.g);
		if (roll < share) {
			// Все три вершины грани уходят в одну точку за экраном: грань пропадает.
			POSITION = vec4(2.0, 2.0, 2.0, 1.0);
		} else if (COLOR.g < 0.5 && roll < share + flipped) {
			light *= 0.22;
		}
	}
}

void fragment() {
	vec4 c = texture(tex, uvw.xy / uvw.z) * tint;
	if (c.a < 0.5) {
		discard;
	}
	vec3 rgb = c.rgb * light;
	if (hue_shift != 0.0) {
		rgb = clamp(shift_hue(rgb, hue_shift), 0.0, 1.0);
	}
	rgb = mix(rgb, vec3(1.0), flash);
	ALBEDO = mix(rgb, fog_color, fog);
}
