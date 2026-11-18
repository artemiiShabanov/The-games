class_name UiPalette
extends Resource
## Палитра оболочки и мини-игр (2026-11-17): пять смысловых цветов и пять акцентов мини-игр.
## Игрок выбирает её в настройках, `Style.use_palette` раскладывает цвета по токенам. База
## (`bg`, `surface`, `ink`, студия) общая для всех палитр и здесь не живёт. Цвета взяты из
## «A Dictionary of Color Combinations» Санзо Вады, в комментариях ресурса имена по книге.

@export var id: StringName
## Название в настройках.
@export var title := ""
@export var focus := Color("#006EB8")
@export var money := Color("#1A7444")
@export var success := Color("#00B49B")
@export var danger := Color("#7E1E2A")
## Фирменный красный (2026-11-18): лампа логотипа, главная кнопка экрана, мелкие акценты.
## Опасность отдельно и темнее, чтобы не путалась с ним.
@export var accent := Color("#CB2F43")
@export var bug := Color("#C16B27")
## Акценты мини-игр a1..a5: a1 главный, a1 и a2 чаще всего рядом, поэтому сильно
## различаются светлотой; розового или фиолетового не больше одного (плейтест палитр
## 2026-11-17: мини-игры уходили в розово-фиолетовое).
@export var accents := PackedColorArray()
## Имена акцентов в среднем роде («синее»): правила «Реши» называют цвет словом.
@export var accent_names := PackedStringArray()
