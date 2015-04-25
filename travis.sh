#!/bin/sh

# before_install script

GAMS_URL="http://d37drm4t2jghv5.cloudfront.net/distributions/24.4.3/linux/linux_x64_64_sfx.exe"

curl -O $GAMS_URL
unzip linux_x64_64_sfx.exe
cd gams*_linux_x64_64_sfx/apifiles/Python
python gdxsetup.py install
