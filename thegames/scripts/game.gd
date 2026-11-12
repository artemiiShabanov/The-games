class_name Game
extends RefCounted
## Общие перечисления игры и их подписи. Порядок значений это порядок тюнинга:
## при равных весах аспекты идут в порядке `Aspect`.

enum Aspect { OPTIMIZATION, SOUND, CONTROLS, GRAPHICS, BALANCE }
enum Genre { PLATFORMER, RACING, SHOOTER, SPORT, FIGHTING }
enum Tech { VECTOR, BIT8, BIT16, LOWPOLY, THREED }
## Стартовые сеттинги; открываемые достижениями приходят в M2+.
enum Setting { PIRATES, SPACE, CASTLES }

const ASPECT_NAMES: Array[String] = ["оптимизация", "звук", "управление", "графика", "баланс"]
const GENRE_NAMES: Array[String] = ["платформер", "гонки", "шутер", "спорт", "файтинг"]
## Названия для игрока (решение 2026-11-12); в коде и файлах прежние ключи: vector, bit8, bit16,
## lowpoly, threed.
const TECH_NAMES: Array[String] = ["примитив", "ретро", "2D", "3D", "продвинутые"]
const SETTING_NAMES: Array[String] = ["пираты", "космос", "замки"]


static func aspect_name(a: Aspect) -> String:
	return ASPECT_NAMES[a]


static func genre_name(g: Genre) -> String:
	return GENRE_NAMES[g]


static func tech_name(t: Tech) -> String:
	return TECH_NAMES[t]


static func setting_name(s: Setting) -> String:
	return SETTING_NAMES[s]
