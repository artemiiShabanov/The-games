class_name StaffMember
extends Resource
## Человек штата или соискатель на доске (полировка 2026-11-17, спека `docs/specs/staff.md`):
## роль и грейд. У соискателя `until` это последний релиз, после которого он уходит с доски;
## у нанятого `hired` релиз найма.

@export var role: Staff.Role = Staff.Role.PROGRAMMER
@export var grade: Staff.Grade = Staff.Grade.JUNIOR
@export var until := 0
@export var hired := 0


static func make(role_: Staff.Role, grade_: Staff.Grade, until_ := 0) -> StaffMember:
	var m := StaffMember.new()
	m.role = role_
	m.grade = grade_
	m.until = until_
	return m


func _to_string() -> String:
	return "%s %s" % [Staff.GRADE_NAMES[grade], Staff.title(role)]
