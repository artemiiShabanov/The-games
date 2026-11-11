class_name Wallet
extends RefCounted
## Деньги студии, спека `docs/specs/economy.md`. Единственное место, где меняется `cash`:
## `earn` и `spend` шлют `money_changed` с причиной (`&"release"`, `&"upkeep"`, `&"tail"`,
## `&"upgrade"`, `&"bugfix"`, `&"rescue"`), по нему оболочка крутит счётчик. В минус уходить
## можно: содержание списывается всегда, банкротство проверяет экономика. История (#77): каждая
## операция строкой `{release, delta, reason, note}` в `history`, релиз ставит хозяин (`release`),
## подпись (название игры, прокачки, вставки) передаёт тот, кто платит. Окно денег главного экрана
## забега показывает её по релизам; сохраняется в слот.

signal money_changed(amount: int, delta: int, reason: StringName)

var cash := 0
## Номер релиза для новых строк истории.
var release := 1
var history: Array[Dictionary] = []


func _init(start := 0) -> void:
	cash = start


func can_afford(amount: int) -> bool:
	return cash >= amount


func earn(amount: int, reason: StringName, note := "") -> void:
	if amount == 0:
		return
	cash += amount
	_log(amount, reason, note)
	money_changed.emit(cash, amount, reason)


func spend(amount: int, reason: StringName, note := "") -> void:
	if amount == 0:
		return
	cash -= amount
	_log(-amount, reason, note)
	money_changed.emit(cash, -amount, reason)


func _log(delta: int, reason: StringName, note: String) -> void:
	history.append({"release": release, "delta": delta, "reason": String(reason), "note": note})


func _to_string() -> String:
	return "%d" % cash
