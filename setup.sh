#!/bin/bash
[ "$1" = clean ] && {
    rm -fr py
}
[ -d py ] || {
    virtualenv -p $(which python3) py
    echo "$PWD/bin
" > py/lib/python3.5/site-packages/local.pth
    . py/bin/activate
    pip install -r requirements.txt
    pip install -r dev-requirements.txt
}
. py/bin/activate
pip install --upgrade -r requirements.txt
pip install --upgrade -r dev-requirements.txt
pip list -lo | cut -d\( -f1 | xargs pip install --upgrade
