# py-gdx

py-gdx is a Python 3 package for accessing data stored in GDX-formatted files, through the Python bindings for the [GAMS](http://www.gams.com) [GDX API](http://www.gams.com/dd/docs/api/expert-level/gdxqdrep.html).

Originally inspired by the similar package, also called py-gdx, by Geoff
Leyland (https://github.com/geoffleyland/py-gdx), this version makes use of [pandas](http://pandas.pydata.org/) to provide Pythonic data structures for access to GAMS data, which can be easily intergrated into [NumPy](http://www.numpy.org/)-based code.

Documentation is available at http://khaeru.github.io/py-gdx/

Example
-------

With the following GAMS program:
````
set  s  'Animals'  /
  a  Aardvark
  b  'Blue whale'
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
>>> f.p[:,'y',CA']
a    1
b    1
c    1
d    1
e    1
f    1
g    1
dtype: float64
````