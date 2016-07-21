#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='PyGDX',
      version='2',
      author='Paul Natsuo Kishimoto',
      author_email='mail@paul.kishimoto.name',
      description='GAMS Data Exchange (GDX) file access',
      install_requires=[
        'backports.shutil_which',
        'gdxcc >= 7',
        'future',
        'xarray >= 0.4',
        ],
      tests_require=[
        'coveralls',
        'pytest',
        'pytest-cov',
        ],
      url='https://github.com/khaeru/py-gdx',
      packages=find_packages(),
      )
