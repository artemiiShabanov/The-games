shader_type spatial;
render_mode unshaded, cull_back, blend_mix, depth_draw_never;
// Плёнка поверх коробки: глянец. Блик окна полосой, точечный блик лампы, свечение на скользящих
// углах и шов по кромке. Только добавляет белое поверх обложки и пластика.

uniform float strength = 1.0;
// Половины размеров коробки в метрах: складки считаются от краёв грани.
uniform vec3 half_size = vec3(0.7, 0.98, 0.08);

varying vec3 local_pos;
varying vec3 local_normal;

void vertex() {
	local_pos = VERTEX;
	local_normal = NORMAL;
}

void fragment() {
	vec3 n = normalize(NORMAL);
	vec3 v = normalize(VIEW);
	vec3 r = reflect(-v, n);
	vec3 lamp = normalize(vec3(-0.35, 0.55, 0.75));
	float spot = pow(max(dot(r, lamp), 0.0), 90.0) * 0.85;
	// Окно: широкая наклонная полоса и узкая рядом. Сдвиг по грани даёт полосе наклон на
	// плоской стороне, а поворот коробки ведёт её поперёк.
	vec2 p = local_pos.xy / half_size.xy;
	float w = r.x * 1.7 + r.y * 0.6 + p.x * 0.3 - p.y * 0.16;
	// Полосы повторяются по углу: блик есть и в покое, и на любом повороте коробки.
	float window = smoothstep(0.8, 1.0, sin(w * 4.5 + 2.14)) * 0.26 + smoothstep(0.985, 1.0, sin(w * 4.5 + 3.3)) * 0.2;
	float fres = pow(1.0 - max(dot(n, v), 0.0), 3.0) * 0.4;
	// Сварной шов плёнки: тонкая светлая кромка по периметру больших граней.
	float seam = 0.0;
	if (abs(local_normal.z) > 0.5) {
		float edge = max(abs(p.x), abs(p.y));
		seam = smoothstep(0.955, 0.975, edge) * (1.0 - smoothstep(0.985, 1.0, edge)) * 0.16;
	}
	ALBEDO = vec3(1.0);
	ALPHA = clamp((spot + window + fres + seam) * strength, 0.0, 0.9);
}
