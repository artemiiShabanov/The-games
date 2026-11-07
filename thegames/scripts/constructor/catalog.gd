class_name Catalog
extends Resource
## Каталог карточек одного вида, ресурсы `res://resources/catalog/{genres,techs,settings}.tres`.
## Порядок записей это порядок карусели.

const DIR := "res://resources/catalog/"

@export var entries: Array[CatalogEntry] = []


static func load_kind(kind: CatalogEntry.Kind) -> Catalog:
	var file: String = ["genres", "techs", "settings"][kind]
	var c := load(DIR + file + ".tres") as Catalog
	return c if c != null else Catalog.new()


func by_value(value: int) -> CatalogEntry:
	for e in entries:
		if e.value == value:
			return e
	return null


func index_of(value: int) -> int:
	for i in entries.size():
		if entries[i].value == value:
			return i
	return -1
