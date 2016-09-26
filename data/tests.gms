$onempty

scalar  pi  'Circumference divided by diameter'  / 3.14 /;

set  s  'Example set of animals'  /
  a  Aardvark
  b  'Blue whale'
  c  Chicken
  d  Dingo
  e  Elephant
  f  Frog
  g  Grasshopper
  /;

set  t  'Example set of colors'  /
  r  Red
  o  Orange
  y  Yellow
  g  Green
  b  Blue
  i  Indigo
  v  Violet
  /;

set  u  'Example set of countries'  /
  CA  Canada
  US  United States
  CN  China
  JP  Japan
  /;

sets
  s1(s)      'First subset of s0'           / a, b, c, d /
  s2(s)      'Second subset of s0'          / e, f, g /
  s3(s,t)    'Two-dimensional set'          / set.s.set.t yes /
  s4(s,t,u)  'Three-dimensional set'        / a.set.t.set.u no /
  s5         'Set with unspecified parent'  / b, d, f /
  s6(*)      'Set under the universal set'  / b, d, f /
  s7(s,s)    'Set for testing sameas()'     / /
  ;

parameters
  p1(s)       'Example parameter with animal data'              / /
  p2(t)       'Example parameter with color data'               / set.t 0.1 /
  p3(s,t)     'Two-dimensional parameter'                       / set.s.y 1 /
  p4(s1)      'Parameter defined over a subset'                 / set.s1 1 /
  p5(*)       'Empty parameter defined over the universal set'
  p6(s,s1,t)  'Parameter defined over a set and its subset'     / /
  ;

parameter p7(*,*) 'Parameter defined over the universal set' /
  a.o   1
  r.US  2
  CA.b  3
  /;

equation  e1;
variables v1, v2;

e1.. v1 =e= v2;

p1('a') = 1;

alias (s, s_);
s7(s,s_)$sameas(s, s_) = yes;

execute_unload 'tests.gdx'
