class_name Game
extends RefCounted
## Общие перечисления игры и их подписи. Порядок значений это порядок тюнинга:
## при равных весах аспекты идут в порядке `Aspect`.

enum Aspect { OPTIMIZATION, SOUND, CONTROLS, GRAPHICS, BALANCE }
enum Genre { PLATFORMER, RACING, SHOOTER, SPORT, FIGHTING }
enum Tech { ASCII, BIT8, BIT16, LOWPOLY, THREED }

const ASPECT_NAMES: Array[String] = ["оптимизация", "звук", "управление", "графика", "баланс"]
const GENRE_NAMES: Array[String] = ["платформер", "гонки", "шутер", "спорт", "файтинг"]
const TECH_NAMES: Array[String] = ["ASCII", "8-bit", "16/32-bit", "low poly 3D", "3D"]


static func aspect_name(a: Aspect) -> String:
	return ASPECT_NAMES[a]


static func genre_name(g: Genre) -> String:
	return GENRE_NAMES[g]


static func tech_name(t: Tech) -> String:
	return TECH_NAMES[t]
