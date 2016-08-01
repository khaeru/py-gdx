# PyGDX
[![Documentation Status](https://readthedocs.org/projects/pygdx/badge/?version=latest)](https://readthedocs.org/projects/pygdx/?badge=latest)
[![Build Status](https://travis-ci.org/khaeru/py-gdx.svg?branch=master)](https://travis-ci.org/khaeru/py-gdx)
[![Coverage Status](https://coveralls.io/repos/github/khaeru/py-gdx/badge.svg?branch=master)](https://coveralls.io/github/khaeru/py-gdx?branch=master)



PyGDX is a Python package for accessing data stored in *GAMS Data eXchange* (GDX) files. GDX is a proprietary, binary file format used by the [General Algebraic Modelling System](http://www.gams.com) (GAMS); pyGDX uses the Python bindings for the [GDX API](http://www.gams.com/dd/docs/api/expert-level/gdxqdrep.html).

Originally inspired by the similar package, also named [py-gdx, by Geoff Leyland](https://github.com/geoffleyland/py-gdx), this version makes use of [xarray](http://xarray.pydata.org) to provide labelled data structures which can be easily manipulated with [NumPy](http://www.numpy.org) for calculations and plotting.

**Documentation** is available at http://pygdx.readthedocs.org, built automatically from the contents of the Github repository.

PyGDX is provided under the **MIT License** (see `LICENSE`).

Example
-------

With the following GAMS program:
````
set  s  'Animals'  /
  a  Aardvark
  b  Blue whale
  c  Chicken
  d  Dingo
  e  Elephant
  f  Frog
  g  Grasshopper
  /;

set  t  'Colours'  /
  r  Red
  o  Orange
  y  Yellow
  g  Green
  b  Blue
  i  Indigo
  v  Violet
  /;

set  u  'Countries'  /
  CA  Canada
  US  United States
  CN  China
  JP  Japan
  /;

parameter p(s,t,u) 'Counts of nationalistic, colourful animals'
  / set.s.set.t.set.u 1 /;

execute_unload 'example.gdx'
````

The parameter `p` can be accessed via:
````python
>>> import gdx
>>> f = gdx.File('example.gdx')
>>> f.p[:,'y','CA']
a    1
b    1
c    1
d    1
e    1
f    1
g    1
dtype: float64
````
