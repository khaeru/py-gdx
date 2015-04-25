#!/bin/sh

GAMS_URL="http://d37drm4t2jghv5.cloudfront.net/distributions/24.4.3/linux/linux_x64_64_sfx.exe"

before_install () {
  # Download GAMS and install the low-level gdcxx Python package
  if ! python -m gdxcc; then
    curl -O $GAMS_URL
    unzip linux_x64_64_sfx.exe
    # The command 'mv blah $HOME/gams' does not work here; because $HOME/gams is
    # cached, Travis creates an empty directory at that location when no cached
    # content exists, and 'mv' places the unzipped gams code one level too deep.
    # Move all the files instead.
    mv gams24.4_linux_x64_64_sfx/* $HOME/gams/
    cd $HOME/gams/apifiles/Python/api
    python gdxsetup.py install
    # Remove a bunch of stuff that doesn't need to be cached
    cd $HOME/gams
    rm -r apifiles docs *_ml
  fi
}

script () {
  # Prepare data
  cd data
  gams tests.gms
  cd ..
  # Run tests
  python setup.py test
}

case $1 in
  before_install) before_install;;
  script) script;;
  *) exit 1;;
esac
