class_name Style
extends RefCounted
## Единая точка визуального кода в коде: токены из `docs/STYLE.md`. Цвета, размеры шрифта,
## радиусы, отступы, геометрия, фабрики стилей и тема оболочки. Сцены и скрипты берут
## значения отсюда и не держат своих литералов. Правка STYLE.md тянет правку здесь.

# --- Палитра --------------------------------------------------------------------------------

const BG := Color("#F4F1EC")
const STUDIO_INK := Color("#1E2A4A")
const SURFACE := Color(1, 1, 1, 0.85)
const SURFACE_SOLID := Color("#FFFFFF")
const SURFACE_2 := Color("#ECE8E1")
const INK := Color("#1C1B19")
const INK_2 := Color("#6F6A62")
const INK_3 := Color("#A8A39A")
const FOCUS := Color("#2F5BFF")
const MONEY := Color("#1F8A4C")
const SUCCESS := Color("#2BB37A")
const DANGER := Color("#D93A2B")
const BUG := Color("#F07A1C")
const SHADOW := Color(0, 0, 0, 0.06)

## Акценты мини-игр a1..a4; палитру выбирает игрок в настройках, стартовая здесь.
static var accents: Array[Color] = [Color("#2F5BFF"), Color("#F07A1C"), Color("#2BB37A"), Color("#E0457B")]


static func accent(i: int) -> Color:
	return accents[wrapi(i, 0, accents.size())]


# --- Типографика, размеры при 1080p ----------------------------------------------------------

const FONT_VERB := 140
const FONT_H1 := 56
const FONT_H2 := 32
const FONT_BODY := 24
const FONT_CAPTION := 18
const LINE_HEIGHT_BODY := 1.4

# --- Геометрия -----------------------------------------------------------------------------

const SCREEN := Vector2i(1920, 1080)
const GRID := 8
const R_CARD := 24
const R_CTL := 16
const R_PILL := 999
const GAP_CARDS := 24
const PAD_CARD := 32
const EDGE := 96
const CARD_SIZE := Vector2(260, 190)
const CAROUSEL_WIDTH := 1200
const ESTIMATE_WIDTH := 500
const FEED_WIDTH := 880
const PEEK := 60
const BUTTON_HEIGHT := 72
const PILL_HEIGHT := 40

# --- Фокус и движение ------------------------------------------------------------------------

const FOCUS_WIDTH := 3
const FOCUS_OFFSET := 6
const FOCUS_SCALE := 1.06
const FOCUS_MOVE_SECONDS := 0.12
const SCREEN_SLIDE_PX := 24
const SHAKE_PX := 4
const DIM_LOCKED := 0.4


# --- Фабрики стилей ------------------------------------------------------------------------

## Плоская заливка с радиусом и, если задан цвет рамки, рамкой толщины `FOCUS_WIDTH` снаружи.
static func flat(color: Color, radius: int, border: Color = Color.TRANSPARENT, pad: int = 10) -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	sb.bg_color = color
	sb.set_corner_radius_all(radius)
	sb.set_content_margin_all(pad)
	if border.a > 0.0:
		sb.set_border_width_all(FOCUS_WIDTH)
		sb.border_color = border
		sb.set_expand_margin_all(FOCUS_WIDTH)
	return sb


## Рамка фокуса по STYLE: снаружи объекта, зазор `FOCUS_OFFSET`, радиус объекта плюс зазор.
static func focus_ring(object_radius: int) -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	sb.draw_center = false
	sb.set_border_width_all(FOCUS_WIDTH)
	sb.border_color = FOCUS
	sb.set_corner_radius_all(object_radius + FOCUS_OFFSET)
	sb.set_expand_margin_all(FOCUS_OFFSET + FOCUS_WIDTH)
	return sb


## Карточка: белая подложка с прозрачностью и мягкой тенью.
static func card(solid := false) -> StyleBoxFlat:
	var sb := flat(SURFACE_SOLID if solid else SURFACE, R_CARD, Color.TRANSPARENT, PAD_CARD)
	sb.shadow_color = SHADOW
	sb.shadow_size = 12
	sb.shadow_offset = Vector2(0, 2)
	return sb


## Тема оболочки: применяется к корневому окну автолоадом `UiTheme`, все Control наследуют.
## Ховера нет: hover равен normal. Пока без шрифта: гротеск выбирается отдельно.
static func make_theme() -> Theme:
	var t := Theme.new()
	t.default_font_size = FONT_BODY

	t.set_color("font_color", "Label", INK)
	t.set_color("font_color", "RichTextLabel", INK)
	t.set_color("default_color", "RichTextLabel", INK)

	var btn := flat(INK, R_CTL, Color.TRANSPARENT, 16)
	var btn_pressed := flat(INK_2, R_CTL, Color.TRANSPARENT, 16)
	var btn_disabled := flat(SURFACE_2, R_CTL, Color.TRANSPARENT, 16)
	t.set_stylebox("normal", "Button", btn)
	t.set_stylebox("hover", "Button", btn)
	t.set_stylebox("pressed", "Button", btn_pressed)
	t.set_stylebox("disabled", "Button", btn_disabled)
	t.set_stylebox("focus", "Button", focus_ring(R_CTL))
	t.set_color("font_color", "Button", SURFACE_SOLID)
	t.set_color("font_hover_color", "Button", SURFACE_SOLID)
	t.set_color("font_pressed_color", "Button", SURFACE_SOLID)
	t.set_color("font_focus_color", "Button", SURFACE_SOLID)
	t.set_color("font_disabled_color", "Button", INK_3)
	t.set_font_size("font_size", "Button", 28)

	t.set_stylebox("panel", "PanelContainer", card())
	t.set_stylebox("panel", "Panel", card())

	var field := flat(SURFACE_2, R_CTL, Color.TRANSPARENT, 12)
	t.set_stylebox("normal", "LineEdit", field)
	t.set_stylebox("focus", "LineEdit", focus_ring(R_CTL))
	t.set_color("font_color", "LineEdit", INK)
	t.set_color("font_placeholder_color", "LineEdit", INK_3)
	t.set_color("caret_color", "LineEdit", INK)

	t.set_stylebox("slider", "HSlider", flat(SURFACE_2, 4, Color.TRANSPARENT, 0))
	t.set_stylebox("grabber_area", "HSlider", flat(FOCUS, 4, Color.TRANSPARENT, 0))
	t.set_stylebox("grabber_area_highlight", "HSlider", flat(FOCUS, 4, Color.TRANSPARENT, 0))

	t.set_stylebox("panel", "PopupMenu", flat(SURFACE_SOLID, R_CTL, Color.TRANSPARENT, 8))
	t.set_stylebox("hover", "PopupMenu", flat(SURFACE_2, 8, Color.TRANSPARENT, 6))
	t.set_color("font_color", "PopupMenu", INK)
	t.set_color("font_hover_color", "PopupMenu", INK)
	return t
