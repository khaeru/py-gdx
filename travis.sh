#!/bin/sh

# before_install script

GAMS_URL="http://d37drm4t2jghv5.cloudfront.net/distributions/24.4.3/linux/linux_x64_64_sfx.exe"

if ! python -m gdxcc; then
  curl -O $GAMS_URL
  unzip linux_x64_64_sfx.exe
  ln -s gams*_linux_x64_64_sfx/gams
  cd gams*_linux_x64_64_sfx/apifiles/Python/api
  python gdxsetup.py install
fi
