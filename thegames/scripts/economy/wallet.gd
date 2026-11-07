class_name Wallet
extends RefCounted
## Деньги студии, спека `docs/specs/economy.md`. Единственное место, где меняется `cash`:
## `earn` и `spend` шлют `money_changed` с причиной (`&"release"`, `&"upkeep"`, `&"tail"`,
## `&"upgrade"`, `&"bugfix"`, `&"rescue"`), по нему оболочка крутит счётчик. В минус уходить
## можно: содержание списывается всегда, банкротство проверяет экономика.

signal money_changed(amount: int, delta: int, reason: StringName)

var cash := 0


func _init(start := 0) -> void:
	cash = start


func can_afford(amount: int) -> bool:
	return cash >= amount


func earn(amount: int, reason: StringName) -> void:
	if amount == 0:
		return
	cash += amount
	money_changed.emit(cash, amount, reason)


func spend(amount: int, reason: StringName) -> void:
	if amount == 0:
		return
	cash -= amount
	money_changed.emit(cash, -amount, reason)


func _to_string() -> String:
	return "%d" % cash
