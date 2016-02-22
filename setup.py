#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='PyGDX',
      version='2',
      author='Paul Natsuo Kishimoto',
      author_email='mail@paul.kishimoto.name',
      description='GAMS Data Exchange (GDX) file access',
      install_requires=['gdxcc >= 7', 'xray >= 0.4'],
      tests_require=['pytest'],
      url='https://github.com/khaeru/py-gdx',
      packages=find_packages(),
      )
