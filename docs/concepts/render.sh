#!/bin/sh
# Рендер всех концептов в PNG 1920×1080 через headless Chrome.
# Использование: sh docs/concepts/render.sh [имя-без-расширения ...]
cd "$(dirname "$0")" || exit 1
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
if [ $# -eq 0 ]; then set -- $(ls [0-9]*.html | sed 's/\.html$//'); fi
for name in "$@"; do
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=1 \
    --window-size=1920,1080 --virtual-time-budget=2000 \
    --screenshot="$PWD/$name.png" "file://$PWD/$name.html" 2>/dev/null
  echo "$name.png"
done
