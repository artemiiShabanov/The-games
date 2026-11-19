class_name SalesFigure
extends Control
## Число продаж игры, оформленное по ступени `SalesGrade`: цвет, размер и жирность в статике,
## а `play()` прокручивает число от нуля и отыгрывает итог. Пока число крутится, из цифр летят
## частицы цвета самого числа, в конце залп; частиц тем больше, чем выше ступень (`DROPS`,
## множитель `drops_gain`). С «неплохо» число вздувается и пружинит, у суперхита второй залп и
## блик по цифрам раз в несколько секунд. Провал: число проседает и остаётся чуть накренённым. Число живёт внутри `Control`, а не в контейнере: контейнер сбрасывает масштаб и
## поворот детей при раскладке.

const ROLL_SECONDS := 0.4
const POP_SECONDS := 0.32
const POP_SCALES: Array[float] = [1.0, 1.0, 1.06, 1.18, 1.3]
## Частиц на ступень: треть летит из цифр за время прокрутки, остальное залпом в конце.
const DROPS: Array[int] = [2, 5, 10, 18, 28]
const DROP_SECONDS := 0.8
const FLOP_TILT := -0.035
const FLOP_DROP := 3.0
const SHEEN_EVERY := 4.0
const SHEEN_SECONDS := 0.7
const ON_DARK_MIX := 0.6
const SHEEN_SHADER := "shader_type canvas_item;
uniform float at = -1.0;
uniform float width = 40.0;
uniform vec4 glow : source_color = vec4(1.0);
varying vec2 local;
void vertex() { local = VERTEX; }
void fragment() {
	float d = abs(local.x - local.y * 0.5 - at) / width;
	COLOR.rgb = mix(COLOR.rgb, glow.rgb, (1.0 - smoothstep(0.0, 1.0, d)) * 0.75);
}"

class Drop:
	var pos := Vector2.ZERO
	var vel := Vector2.ZERO
	var r := 4.0
	var age := 0.0
	var life := DROP_SECONDS

var value := 0
var grade := SalesGrade.FINE
var prefix := ""
## Множитель числа частиц: экран после релиза сыплет щедрее.
var drops_gain := 1.0
## Число стоит на тёмной подложке (строка в фокусе): цвет ступени высветлен.
var on_dark := false:
	set(v):
		on_dark = v
		if _label != null:
			var c := SalesGrade.color(grade)
			_label.add_theme_color_override("font_color", c.lerp(Color.WHITE, ON_DARK_MIX) if v else c)

var _label: Label
var _drops: Array[Drop] = []
var _rng := RandomNumberGenerator.new()
var _sheen: ShaderMaterial
var _sheen_timer := SHEEN_EVERY * 0.5
var _played := false


## `prefix_`: знак перед числом в ведомостях («+ »).
static func make(value_: int, grade_: int, base_size: int, prefix_ := "") -> SalesFigure:
	var f := SalesFigure.new()
	f.prefix = prefix_
	f.value = value_
	f.grade = grade_
	f.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var l := Label.new()
	l.text = prefix_ + Style.format_money(value_)
	l.add_theme_font_override("font", SalesGrade.font(grade_))
	l.add_theme_font_size_override("font_size", SalesGrade.font_size(grade_, base_size))
	l.add_theme_color_override("font_color", SalesGrade.color(grade_))
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	f._label = l
	f.add_child(l)
	f._rng.seed = value_
	if grade_ == SalesGrade.FLOP:
		f._settle_flop.call_deferred()
	f.set_process(grade_ == SalesGrade.SMASH)
	return f


## Место под число считается в дереве, с темой, по итоговому тексту: прокрутка его не дёргает.
func _ready() -> void:
	custom_minimum_size = _label.get_minimum_size()


## Провал в статике: число чуть накренено и просело.
func _settle_flop() -> void:
	_label.pivot_offset = _label.size / 2.0
	_label.rotation = FLOP_TILT
	_label.position.y = FLOP_DROP


## Появление: прокрутка от нуля, затем отыгрыш ступени.
func play() -> void:
	if _played or Debug.skip_cards:
		return
	_played = true
	_label.pivot_offset = Vector2(0.0, _label.size.y / 2.0) if grade != SalesGrade.FLOP else _label.size / 2.0
	_label.rotation = 0.0
	_label.position.y = 0.0
	var tw := create_tween()
	tw.tween_method(func(v: float) -> void:
		_label.text = prefix + Style.format_money(int(round(v))), 0.0, float(value), ROLL_SECONDS) \
		.set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_CUBIC)
	tw.tween_callback(_land)
	# Пока число крутится, цифры искрят: треть частиц по одной.
	var early := int(round(DROPS[grade] * drops_gain / 3.0))
	if early > 0:
		var drip := create_tween().set_loops(early)
		drip.tween_callback(_burst.bind(1, 0.7))
		drip.tween_interval(ROLL_SECONDS / early)


func _land() -> void:
	_label.text = prefix + Style.format_money(value)
	match grade:
		SalesGrade.FLOP:
			_burst(_late(), 0.6)
			var tw := create_tween().set_parallel(true).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_BACK)
			tw.tween_property(_label, "rotation", FLOP_TILT, POP_SECONDS)
			tw.tween_property(_label, "position:y", FLOP_DROP, POP_SECONDS)
		SalesGrade.WEAK:
			_burst(_late(), 0.7)
		_:
			_pop(POP_SCALES[grade])
			if grade >= SalesGrade.HIT:
				ShellSounds.play(&"done")
			if grade == SalesGrade.SMASH:
				_burst(_late() / 2, 1.0)
				var tw := create_tween()
				tw.tween_interval(0.18)
				tw.tween_callback(func() -> void:
					_pop(1.12)
					_burst(_late() - _late() / 2, 1.5)
					_sheen_timer = 0.0)
			else:
				_burst(_late(), 1.0)


## Частицы залпа: всё, что не вылетело за прокрутку.
func _late() -> int:
	var all := int(round(DROPS[grade] * drops_gain))
	return all - int(round(DROPS[grade] * drops_gain / 3.0))


func _pop(to: float) -> void:
	_label.scale = Vector2.ONE * to
	create_tween().tween_property(_label, "scale", Vector2.ONE, POP_SECONDS) \
		.set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_BACK)


## Частицы вылетают из цифр во все стороны, вверх охотнее, и гаснут.
func _burst(count: int, power: float) -> void:
	# Число частиц это смысл (ступень продаж), поэтому общий множитель брызг мармелада его не режет.
	var n := count if Jelly.on() else 0
	var box := _label.size
	for i in n:
		var d := Drop.new()
		var a := _rng.randf_range(-PI, PI)
		d.pos = Vector2(_rng.randf_range(0.05, 0.95) * box.x, _rng.randf_range(0.3, 0.7) * box.y)
		d.vel = Vector2(cos(a), sin(a) - 0.5) * _rng.randf_range(200.0, 520.0) * power
		d.r = _rng.randf_range(3.0, 7.5)
		d.life = DROP_SECONDS * _rng.randf_range(0.7, 1.0)
		_drops.append(d)
	set_process(true)


func _process(delta: float) -> void:
	for d in _drops:
		d.age += delta
		d.vel.y += 620.0 * delta
		d.vel *= 1.0 - 1.8 * delta
		d.pos += d.vel * delta
	_drops = _drops.filter(func(d: Drop) -> bool: return d.age < d.life)
	queue_redraw()
	if grade == SalesGrade.SMASH and Jelly.on():
		_step_sheen(delta)
	elif _drops.is_empty():
		set_process(false)


## Блик: светлая полоса проходит по цифрам слева направо.
func _step_sheen(delta: float) -> void:
	if _sheen == null:
		var sh := Shader.new()
		sh.code = SHEEN_SHADER
		_sheen = ShaderMaterial.new()
		_sheen.shader = sh
		_sheen.set_shader_parameter("glow", Style.MONEY.lerp(Color.WHITE, 0.8))
		_label.material = _sheen
	_sheen_timer -= delta
	var span := _label.size.x + 120.0
	var t := 1.0 - (_sheen_timer + SHEEN_SECONDS) / SHEEN_SECONDS
	_sheen.set_shader_parameter("at", -60.0 + span * t if t >= 0.0 and t <= 1.0 else -1000.0)
	if _sheen_timer < -SHEEN_SECONDS:
		_sheen_timer = SHEEN_EVERY


func _draw() -> void:
	var c := SalesGrade.color(grade)
	for d in _drops:
		var k := 1.0 - d.age / d.life
		draw_circle(d.pos, d.r * (0.5 + 0.5 * k), Color(c, minf(1.0, k * 1.6)))
