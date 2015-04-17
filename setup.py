#!/usr/bin/env python

from distutils.core import setup

setup(name='PyGDX',
      version='2',
      description='GAMS Data Exchange (GDX) file access',
      author='Paul Natsuo Kishimoto',
      author_email='mail@paul.kishimoto.name',
      install_requires=['numpy', 'pandas', 'xray'],
      url='https://github.com/khaeru/py-gdx',
      packages=['gdx'],
      )
