#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='PyGDX',
      version='2',
      author='Paul Natsuo Kishimoto',
      author_email='mail@paul.kishimoto.name',
      description='GAMS Data Exchange (GDX) file access',
      install_requires=[
        'gdxcc >= 7',
        'xarray >= 0.4',
        ],
      tests_require=['nose2 >= 0.5'],
      test_suite='nose2.collector.collector',
      url='https://github.com/khaeru/py-gdx',
      packages=find_packages(),
      )
