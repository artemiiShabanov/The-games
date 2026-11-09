# Сеттинг «Космос», 8-bit

Заглушечный арт до M5 (#47): спрайты 16×16 по слотам платформера, палитра 4 цвета плюс чёрный.
Генерируются `tools/pixel_sprites.py` из карт в `tools/pixel_sets_extra.py`, руками не править:

    python3 tools/pixel_sprites.py --preview thegames/debug/playtest/sprites.png
    Godot --headless --path thegames --import
