class_name PersonDef
extends Resource
## Постоянный персонаж отклика: критик или стример, спека `docs/specs/success.md`. Имя,
## издание или канал, характер (сдвиг оценки или охвата), цвет акцента портрета. Портреты
## пиксельные приходят в M5, пока буква в круге цвета акцента.

enum Role { CRITIC, STREAMER }
## Любитель ретро: плюс за ASCII и 8-bit; ненавистник багов: минус за каждый баг; охотник за
## новизной: плюс за новую пару; любитель багов: охват больше при зрелищном баге; любитель 3D:
## охват больше на low poly и 3D.
enum Nature { RETRO, BUG_HATER, NOVELTY, BUG_LOVER, LOVER_3D }

@export var id: StringName = &""
@export var name := ""
@export var role: Role = Role.CRITIC
@export var nature: Nature = Nature.RETRO
## Издание критика или размер канала стримера.
@export var subtitle := ""
@export var accent := Color.WHITE
