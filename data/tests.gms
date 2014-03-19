$onempty

set s0  'Example set'  /
  a  Aardvark
  b  'Blue whale'
  c  Chicken
  d  Dingo
  e  Elephant
  f  Frog
  g  Grasshopper
  /;

sets
  s1(s0)  'First subset of s0'   / a, b, c, d /
  s2(s0)  'Second subset of s0'  / e, f, g /
  ;

parameter  p0(s0)  'Example parameter'  / /;

p0('a') = 1;

execute_unload 'tests.gdx'
