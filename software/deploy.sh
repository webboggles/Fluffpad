#!/bin/zsh
# Push a game to the Pico. Packages are precompiled to .mpy; main.py goes to the board root.
# Usage: ./deploy.sh <game> [--no-main]    e.g. ./deploy.sh jade_sun
set -e
cd "$(dirname "$0")"
GAME=${1:?usage: ./deploy.sh <game> [--no-main]}
SRC=games/$GAME
[[ -f $SRC/main.py ]] || { echo "no game at $SRC" >&2; exit 1; }
PORT=${PORT:-$(ls /dev/cu.usbmodem* 2>/dev/null | head -1)}
[[ -n $PORT ]] || { echo "no Pico found on /dev/cu.usbmodem*; set PORT=" >&2; exit 1; }
MP=(.venv/bin/mpremote connect "$PORT")
BUILD=build/$GAME
rm -rf $BUILD && mkdir -p $BUILD

for pkg in $SRC/*/__init__.py(N); do
  dir=${pkg:h}
  name=${dir:t}
  mkdir -p $BUILD/$name
  for f in $dir/*.py; do
    b=${f:t:r}
    if [[ $b == __init__ ]]; then cp $f $BUILD/$name/; else .venv/bin/mpy-cross -O2 -o $BUILD/$name/$b.mpy $f; fi
  done
  $MP exec "import os
try:
    os.mkdir('$name')
except OSError:
    pass
for f in os.listdir('$name'):
    if f.endswith('.py') and f != '__init__.py':
        os.remove('$name/' + f)"
  $MP cp $BUILD/$name/* :$name/ > /dev/null
  $MP ls :$name
done

if [[ $2 != --no-main ]]; then $MP cp $SRC/main.py :main.py > /dev/null && echo "main.py <- $SRC/main.py"; fi
