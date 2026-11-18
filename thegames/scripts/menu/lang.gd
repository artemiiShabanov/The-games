class_name Lang
extends RefCounted
## Язык интерфейса (2026-11-18). Исходный язык игры русский: ключ перевода это сам русский
## текст, переводы лежат в `res://locale/<id>.po` и подключены в `project.godot`
## (`internationalization/locale/translations`). Нет перевода строки: остаётся русский текст.
## Резервный язык движка `ru`, иначе русская игра брала бы строки из английского файла.
## Подписи `Label` движок переводит сам; текст с подстановкой (`"Слот %d" % n`) переводится
## до подстановки: `tr("Слот %d") % n` в нодах, `Lang.t(...)` в статических функциях.

const IDS: Array[String] = ["ru", "en"]
## Название языка на нём самом: так его узнает игрок, который ещё не выбрал язык.
const NAMES: Array[String] = ["Русский", "English"]
## Языки системы, на которых по умолчанию предлагается русский.
const RU_LIKE: Array[String] = ["ru", "uk", "be", "kk"]


## Язык из настроек; до выбора на первом запуске русский.
static func current() -> String:
	return Options.language if IDS.has(Options.language) else IDS[0]


static func use(id: String) -> void:
	var lang := id if IDS.has(id) else IDS[0]
	if TranslationServer.get_locale() != lang:
		TranslationServer.set_locale(lang)


## Язык, который экран выбора предлагает первым: по языку системы.
static func system_default() -> String:
	return "ru" if RU_LIKE.has(OS.get_locale_language()) else "en"


## Перевод вне нод (статические функции, ресурсы).
static func t(text: String) -> String:
	return String(TranslationServer.translate(text))


static func name_of(id: String) -> String:
	var i := IDS.find(id)
	return NAMES[i] if i >= 0 else id
