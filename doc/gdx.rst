GDX data terminology
====================

Objects in GDX files are termed **Symbols**, and are of several types:

- **Sets** are ordered collections of labels.
- **Parameters** contain numerical data.
- **Variables** are scalar values.
- **Aliases** are alternate names for other Symbols.
- **Equations**, not currently supported by PyGDX.

For clarity (e.g., Python has a built-in class :class:`python.set`), these terms are capitalized throughout this documentation.

Both Sets and Parameters may be declared with one-dimensional Sets for each dimension. An example:

.. code-block:: none

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

   set v(s,t) 'Valid animal colours'
     / set.s.set.t yes /;

   parameter p(s,t,u) 'Counts of nationalistic, colourful animals'
     / set.s.set.t.set.u 5 /;

   parameter total(s) 'Total populations of each type of animal';
   total(s) = sum((t, u), p(s, t, u));

   execute_unload 'example.gdx';

In the resulting file `example.gdx`:

- ``s``, ``t`` and ``u`` are 1-dimensional Sets.
- ``v`` is a 2-dimensional Set, defined over the *parent* Sets ``s`` and ``t``. Any Set defined with reference to others, in this way, may include or exclude each element of the parent set. For instance, the following GAMS code defines a subset of ``u``:

  .. code-block:: none

     set na(u)  'North American countries' / CA, US /;

- ``p`` and ``total`` are Parameters containing numerical data.

Other concepts
--------------

The **universal Set**, ``*``, contains every element appearing in any Set in the GDX file.

- In the above example, ``*`` would contain: ``a b c d e f g r o y b i v CA US CN JP``.
- GAMS allows defining Sets and Parameters over the universal set:

  .. code-block:: none

     parameter new(*)  'More data';
     new('L') = 3;

  This would add ``L`` to the universal Set.

The **descriptive text** provided on declaration of Symbols or Set elements is stored in GDX files along with the data contained in those variables.

- For Set ``v``, the string ``"Valid animal colours"``.
- For Set element ``o``, the string ``"Orange"``.
