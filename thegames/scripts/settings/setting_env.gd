class_name SettingEnv
extends Resource
## Окружение сеттинга в 3D (#147, `docs/specs/settings.md`): свет, небо, туман, картинка и
## основание мира, то, чем для пиратов служит море. У сеттинга два таких блока, для low poly и
## для «продвинутых» (`SettingDef.env_lowpoly`, `env_threed`); часть полей читает только одна из
## технологий, это помечено. Числа технологии, которые от сеттинга не зависят (дрожание вершин,
## тени, контровой край), остаются в `LowpolyTuning` и `ThreedTuning`.

## Основание мира: роль одна (среда вокруг уровня до горизонта), вид задаёт сеттинг.
enum Base {
	LIQUID,  ## Жидкость: море, лава, кислота. У «продвинутых» шейдер воды, у low poly текстура с прокруткой.
	VOID,  ## Пустота: ничего, небо со всех сторон.
	SOLID,  ## Твердь: плоскость с текстурой до горизонта.
}

@export_group("Свет")
## Солнце: наклон вниз и поворот, градусы; сила и цвет.
@export var sun_pitch := -45.0
@export var sun_yaw := 45.0
@export var sun_energy := 1.0
@export var sun_color := Color.WHITE
## Заполняющий свет: сколько видно на гранях, отвёрнутых от солнца, и его оттенок.
@export var ambient_energy := 0.5
@export var ambient_color := Color.WHITE
## «Продвинутые»: заполняющий свет берётся с неба; выключить для тёмного неба, тогда светит
## `ambient_color`, и герои читаются ночью.
@export var ambient_sky := true

@export_group("Небо")
## «Продвинутые»: зенит темнее цвета неба сеттинга, горизонт светлее (доли), когда `sky_colors`
## пуст.
@export var sky_top := 0.5
@export var sky_horizon := 1.12
## Свои цвета неба: зенит, горизонт, низ под горизонтом. Пусто: считаются из цвета неба сеттинга.
@export var sky_colors: Array[Color] = []
## Звёзды: сколько точек на небе, 0 нет. У low poly звёздный купол заменяет панораму `tex_sky`.
@export var stars := 0

@export_group("Туман")
## Low poly: с какого расстояния начинается и где закрывает всё, метры. Цвет это цвет неба.
@export var fog_begin := 30.0
@export var fog_end := 90.0
## «Продвинутые»: плотность и доля воздушной перспективы.
@export var fog_density := 0.002
@export var fog_aerial := 0.5

@export_group("Картинка «продвинутых»")
@export var glow_intensity := 0.4
@export var glow_bloom := 0.06
@export var glow_threshold := 0.95
@export var saturation := 1.0
@export var contrast := 1.0
@export var exposure := 1.0

@export_group("Основание мира")
@export var base := Base.LIQUID
## Текстура уровня для жидкости low poly и для тверди обеих технологий (`tex_<имя>`).
@export var base_texture := "water"
## Метров на повтор текстуры и скорость её прокрутки (жидкость low poly).
@export var base_tile := 6.0
@export var base_scroll := Vector2(0.02, 0.035)
## Жидкость «продвинутых»: цвет глубины и мелководья, прозрачность у берега (метры), высота волн.
@export var water_deep := Color(0.02, 0.15, 0.23)
@export var water_shallow := Color(0.13, 0.5, 0.53)
@export var water_clarity := 7.0
@export var water_waves := 1.0


## Небо в точках: прозрачная картинка `size` со `stars` белыми точками разной яркости; `back`
## непрозрачный фон сверху вниз (для купола low poly), пустой оставляет прозрачность.
func star_image(size: Vector2i, back: Array[Color] = []) -> Image:
	var img := Image.create(size.x, size.y, false, Image.FORMAT_RGBA8)
	for y in size.y:
		var c := Color(0, 0, 0, 0)
		if back.size() >= 2:
			c = back[0].lerp(back[1], float(y) / maxf(size.y - 1, 1.0))
		for x in size.x:
			img.set_pixel(x, y, c)
	var rng := RandomNumberGenerator.new()
	rng.seed = 7
	for i in stars:
		var bright := rng.randf_range(0.45, 1.0)
		img.set_pixel(rng.randi_range(0, size.x - 1), rng.randi_range(0, size.y - 1), Color(bright, bright, minf(bright * 1.1, 1.0), 1.0))
	return img
