shader_type spatial;
render_mode unshaded, cull_back;
// Вкладыш обложки на грани коробки: фон с эффектом и рисунок стороны поверх. Эффекты
// коллекционных карточек (блёстки, голограмма, фольга) зависят от угла взгляда и живут, пока
// коробку крутят. fx: 0 цвет, 1 градиент, 2 полосы, 3 точки, 4 лучи, 5 блёстки, 6 голограмма,
// 7 фольга, 8 картинка из игры (`art`: плиткой или во всё лицо, поверх первого цвета).

uniform sampler2D overlay : source_color, filter_linear, repeat_disable;
uniform vec4 color_a : source_color = vec4(0.1, 0.3, 0.6, 1.0);
uniform vec4 color_b : source_color = vec4(0.5, 0.8, 0.8, 1.0);
uniform int fx = 0;
// Отношение ширины лица к высоте: узоры в квадратных клетках.
uniform float aspect = 0.7;
// Фон из игры: пиксельная картинка ближайшим соседом, гладкая со сглаживанием. Точка картинки
// это (uv − 0.5) × art_scale + 0.5.
uniform sampler2D art_near : source_color, filter_nearest, repeat_enable;
uniform sampler2D art_smooth : source_color, filter_linear_mipmap, repeat_enable;
uniform bool art_is_smooth = false;
uniform vec2 art_scale = vec2(1.0);

float hash(vec2 p) {
	p = fract(p * vec2(123.34, 456.21));
	p += dot(p, p + 45.32);
	return fract(p.x * p.y);
}

vec3 rainbow(float h) {
	return clamp(abs(fract(h + vec3(0.0, 0.6667, 0.3333)) * 6.0 - 3.0) - 1.0, 0.0, 1.0);
}

void fragment() {
	vec2 uv = UV;
	vec2 sq = vec2(uv.x * aspect, uv.y);
	vec3 v = normalize(VIEW);
	// Наклон взгляда в плоскости грани: ноль, когда смотрим прямо.
	vec2 tilt = vec2(dot(v, normalize(TANGENT)), dot(v, normalize(BINORMAL)));
	vec3 a = color_a.rgb;
	vec3 b = color_b.rgb;
	vec3 col = a;
	if (fx == 1) {
		col = mix(a, b, smoothstep(0.05, 0.95, uv.y));
	} else if (fx == 2) {
		float s = fract((sq.x + sq.y) * 7.0);
		col = mix(a, b, smoothstep(0.48, 0.52, s));
	} else if (fx == 3) {
		vec2 cell = fract(sq * 16.0) - 0.5;
		float r = mix(0.1, 0.46, uv.y);
		col = mix(b, a, smoothstep(r - 0.03, r + 0.03, length(cell)));
	} else if (fx == 4) {
		vec2 d = sq - vec2(0.5 * aspect, 0.42);
		float ang = atan(d.y, d.x);
		float ray = smoothstep(-0.08, 0.08, sin(ang * 14.0));
		col = mix(a, b, ray * smoothstep(0.02, 0.1, length(d)));
	} else if (fx == 5) {
		col = mix(a, b, uv.y * 0.6);
		// Блёстки: у каждой чешуйки свой наклон, вспыхивает, когда взгляд с ним совпал.
		for (int layer = 0; layer < 2; layer++) {
			float scale = layer == 0 ? 46.0 : 90.0;
			vec2 g = sq * scale;
			vec2 id = floor(g);
			vec2 f = fract(g) - 0.5;
			float seed = hash(id + float(layer) * 17.0);
			if (seed > 0.55) {
				vec2 facet = vec2(hash(id + 3.1), hash(id + 7.7)) - 0.5;
				float hit = 1.0 - smoothstep(0.0, 0.2, length(facet - tilt * 1.6));
				float dotm = 1.0 - smoothstep(0.12, 0.34, length(f));
				col += (0.12 + 2.4 * hit) * dotm * mix(vec3(1.0), rainbow(seed * 3.0), 0.35) * 0.5;
			}
		}
	} else if (fx == 6) {
		float phase = sq.x * 1.3 + sq.y * 0.9 + tilt.x * 2.4 + tilt.y * 1.7;
		vec3 holo = rainbow(phase);
		float band = 0.5 + 0.5 * sin((sq.x - sq.y) * 26.0 + tilt.x * 22.0);
		float fine = 0.5 + 0.5 * sin(sq.y * 380.0);
		col = mix(a, holo, 0.42 + 0.3 * band);
		col = mix(col, b, 0.18);
		col += holo * fine * 0.1 + vec3(band * band) * 0.12;
	} else if (fx == 7) {
		// Фольга: шлифованный металл, вертикальный блик едет по грани за взглядом.
		float grain = hash(vec2(floor(uv.x * 620.0), 1.0)) * 0.16 + hash(vec2(floor(uv.x * 90.0), 5.0)) * 0.1;
		float sweep = uv.x - 0.5 + tilt.x * 2.2;
		float shine = exp(-sweep * sweep * 18.0) + 0.45 * exp(-(sweep - 0.42) * (sweep - 0.42) * 60.0);
		col = a * (0.55 + grain) + mix(a, b, 0.6) * shine * 0.9 + vec3(shine * shine) * 0.35;
	}
	if (fx == 8) {
		vec2 auv = (uv - 0.5) * art_scale + 0.5;
		vec4 t = art_is_smooth ? texture(art_smooth, auv) : texture(art_near, auv);
		col = mix(a, t.rgb, t.a);
	}
	vec4 o = texture(overlay, uv);
	// Вьюпорт рисунка с прозрачным фоном отдаёт цвет, уже умноженный на альфу.
	ALBEDO = col * (1.0 - o.a) + o.rgb;
}
