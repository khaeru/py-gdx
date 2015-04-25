#!/bin/sh

# before_install script

GAMS_URL="http://d37drm4t2jghv5.cloudfront.net/distributions/24.4.3/linux/linux_x64_64_sfx.exe"

before_install () {
  if ! python -m gdxcc; then
    curl -O $GAMS_URL
    unzip linux_x64_64_sfx.exe
    mv gams*_linux_x64_64_sfx gams
    cd gams/apifiles/Python/api
    python gdxsetup.py install
  fi
}

script () {
  PATH=$HOME/gams:$PATH
  python setup.py test
}

case $1 in
  before_install) before_install;;
  script) script;;
esac
