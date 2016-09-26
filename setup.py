#!/usr/bin/env python

from setuptools import setup, find_packages

setup(name='gdx',
      version='3',
      author='Paul Natsuo Kishimoto',
      author_email='mail@paul.kishimoto.name',
      description='GAMS Data Exchange (GDX) file access',
      install_requires=[
        'backports.shutil_which',
        'future',
        'xarray',
        ],
      tests_require=['pytest'],
      url='https://github.com/khaeru/py-gdx',
      download_url='https://github.com/khaeru/py-gdx/tarball/3',
      packages=find_packages(),
      )
