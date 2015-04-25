#!/bin/sh

# before_install script

GAMS_URL="http://d37drm4t2jghv5.cloudfront.net/distributions/24.4.3/linux/linux_x64_64_sfx.exe"

before_install () {
  if ! python -m gdxcc; then
    curl -O $GAMS_URL
    unzip linux_x64_64_sfx.exe
    mv gams24.4_linux_x64_64_sfx $HOME/gams
    ls -l $HOME $HOME/gams
    cd $HOME/gams/apifiles/Python/api
    python gdxsetup.py install
  fi
}

script () {
  ls -l $HOME/gams
  which -a gams
  echo "$PATH"
  gams
  python setup.py test
}

case $1 in
  before_install) before_install;;
  script) script;;
  *) exit 1;;
esac
