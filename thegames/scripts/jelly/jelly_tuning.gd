class_name JellyTuning
extends Resource
## Прототип желе (ветка proto/jelly): материал. Два ресурса: `resources/jelly.tres` мармелад
## (плотный, мало брызг, по умолчанию) и `resources/jelly_soft.tres` желе. Числа мягкого тела, брызг, следа, волн по поверхности и
## пружин мелких объектов. Ресурс `resources/jelly.tres`, ручки в разделе «Желе» дебаг-меню.

@export_group("Тело")
## Точек по контуру.
@export var blob_points := 28
## Жёсткость тяги точки к своему месту в форме, 1/с².
@export var blob_stiffness := 380.0
## Затухание скорости точки, 1/с.
@export var blob_damping := 7.0
## Сглаживание соседями: контур не мнётся углами.
@export var blob_neighbor := 160.0
## Давление: тело держит площадь, сплющиваясь, раздаётся вбок.
@export var blob_pressure := 1400.0
## Своя тяжесть точек: тело оседает на поверхности.
@export var blob_gravity := 1200.0
## Насколько центр формы утоплен в опору, доля радиуса: плоское пятно касания.
@export var blob_sit := 0.06
## Доля рывка центра, которую тело получает инерцией: сила шлепка и отрыва.
@export var blob_inertia := 0.3
## Трение о поверхность, 1/с: низ отстаёт, тело наклоняется вперёд.
@export var blob_friction := 7.0
## Вытягивание формы по вертикальной скорости, на 1 пиксель в секунду.
@export var blob_stretch := 0.00042
@export var blob_stretch_max := 0.5
## Дыхание в покое, доля радиуса.
@export var blob_breathe := 0.02

@export_group("Брызги и след")
@export var splash_scale := 1.0
@export var droplet_gravity := 2600.0
## Сколько живёт клякса на поверхности, с.
@export var blot_seconds := 1.8
## Сколько живёт след от скольжения, с.
@export var trail_seconds := 1.3
@export var trail_width := 7.0
@export var trail_alpha := 0.85

@export_group("Поверхность")
## Высота волны от удара на 1000 пикселей в секунду скорости падения.
@export var ripple_amp := 9.0
@export var ripple_speed := 900.0
@export var ripple_wavelength := 130.0
@export var ripple_decay := 3.2
@export var ripple_range := 460.0
## Прогиб поверхности под телом, пиксели.
@export var dent := 5.0

@export_group("Пружины предметов")
@export var spring_stiffness := 280.0
@export var spring_damping := 6.0

@export_group("Интерфейс")
## Пружины элементов интерфейса: жёсткость и затухание.
@export var ui_stiffness := 300.0
@export var ui_damping := 11.0
## Доля рывка скорости (пиксели в секунду), которая уходит в отставание элемента.
@export var ui_inertia := 0.018
## То же для роста: перелёт масштаба после увеличения.
@export var ui_scale_inertia := 0.05
## Насколько отставание вытягивает элемент и насколько гнёт середину.
@export var ui_stretch := 0.8
@export var ui_bend := 0.5
## Вздрог при фокусе, сжатие при нажатии.
@export var ui_poke := 0.5
@export var ui_press := 0.8
## Вмятина под курсором и наклон к нему (наклон выключен: карточка выглядела перекошенной).
@export var ui_hover_lens := 0.06
@export var ui_lean := 0.0

@export_group("Фокус толщиной")
## Подъём элемента в фокусе: высота бортика, вдавленный при нажатии, дыхание, затемнение.
@export var lift_px := 8.0
@export var lift_press := 1.5
@export var lift_breathe := 0.8
@export var lift_darken := 0.3
