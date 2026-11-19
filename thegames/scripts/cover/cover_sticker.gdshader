shader_type canvas_item;
// Стикер обложки: 0 как есть, 1 и 2 обводка цвета `line` шириной `width` текселей (вырубная
// наклейка), 3 мягкая тень со сдвигом. Картинка приходит с прозрачным полем под обводку.

uniform int mode = 0;
uniform float width = 1.0;
uniform vec4 line : source_color = vec4(1.0);

void fragment() {
	vec4 c = texture(TEXTURE, UV);
	if (mode == 1 || mode == 2) {
		float a = 0.0;
		for (int i = 0; i < 16; i++) {
			float ang = float(i) * 0.3926991;
			vec2 d = vec2(cos(ang), sin(ang)) * TEXTURE_PIXEL_SIZE * width;
			a = max(a, texture(TEXTURE, UV + d).a);
			a = max(a, texture(TEXTURE, UV + d * 0.5).a);
		}
		COLOR = vec4(mix(line.rgb, c.rgb, c.a), max(a, c.a));
	} else if (mode == 3) {
		float s = texture(TEXTURE, UV - TEXTURE_PIXEL_SIZE * width * vec2(0.8, 1.0)).a;
		COLOR = vec4(mix(vec3(0.0), c.rgb, c.a), max(s * 0.45, c.a));
	} else {
		COLOR = c;
	}
}
