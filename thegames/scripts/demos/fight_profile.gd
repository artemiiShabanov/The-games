class_name FightProfile
extends Resource
## Профиль поведения соперника в файтинге × 8-bit (#54): из таких фаз сид собирает раунд
## (`FightPlanGen`). Лежат в `res://resources/demos/fighting_gen.tres`. Шаги боя при 60 в секунду.

## Короткое имя для дампа и заметок автотеста: «напор», «стена».
@export var title := ""
## Держит дистанцию, px; к удару подходит на его длину.
@export var gap := 20.0
## Пауза между своими ударами, шагов, от и до.
@export var attack_min := 30
@export var attack_max := 60
## Стойка, пока герой рядом: раз в `stance_min`..`stance_max` шагов выбирает блок, присед
## или стоять. Блок держит верхний, присед уходит от верхнего; нижний берёт обе.
@export var block_chance := 0.2
@export var crouch_chance := 0.1
@export var stance_min := 20
@export var stance_max := 40
## Увидев удар героя (через реакцию плана), бьёт в ответ, пока тот не восстановился.
@export var punish_chance := 0.3
## После своего удара отходит на `retreat_steps` шагов.
@export var retreat_chance := 0.0
@export var retreat_steps := 24
## Ждёт в приседе, а не стоя.
@export var crouch_idle := false
## Доля нижних в паттерне ударов фазы.
@export var low_share := 0.3
