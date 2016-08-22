#!/bin/bash
[ "$1" = clean ] && {
    rm -fr py
}
[ ! -d py ] && {
    virtualenv -p $(which python3) py
    echo "$PWD/bin
" > py/lib/python3.5/site-packages/local.pth
    . py/bin/activate
    pip install --upgrade pip setuptools wheel
    pip install -r requirements.txt
    pip install -r turtles/requirements.txt
}
. py/bin/activate

