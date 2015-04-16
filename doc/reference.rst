API reference
=============

GDX data terminology
--------------------

Objects in GDX files are named **Symbols**, of several types:

- **Sets** are ordered collections of labels.
- **Parameters** contain numerical data.
- **Variables** are scalar values.
- **Aliases** are alternate names for other Symbols.
- **Equations**, not currently supported by PyGDX.

For clarity, these terms are capitalized throughout this documentation.

Both Sets and Parameters may be declared with one-dimensional Sets for each dimension. An example helps illustrate:

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

``v`` is a 2-dimensional Set, defined over the 'parent' Sets `s` and `t`. Any
Set defined with reference to others, in this way, can have individual elements
of the parent sets included, or excluded.

``p`` and ``total`` contain numerical data.

The comments, or **descriptive text**, provided on declaration of Symbols (e.g.
for `v`, the string "Valid animal colours") or Set elements (e.g. for `o`, the
string "Orange") are stored in GDX files along with the data contained in those
variables.

GDX data sets
-------------

.. autoclass:: gdx.File
   :members:

   :class:`File` is a subclass of :class:`xray.Dataset`. The GDX data is
   represented as follows:

   - One-dimensional GDX Sets are stored as xray *coordinates*.
   - GDX Parameters and multi-dimensional GDX Sets are stored as
     :class:`xray.DataArray` variables within the :class:`xray.Dataset`.
   - Other information and metadata on GDX Symbols is stored as attributes of
     the :class:`File`, or attributes of individual data variables or
     coordinates.

   Individual Symbols are thus available in one of three ways:

   1. As dict-like members of the :class:`xray.Dataset`; see
      http://xray.readthedocs.org/en/stable/data-structures.html#dataset:

      >>> f = File('example.gdx')
      >>> f['myparam']

   2. As attributes of the :class:`File`:

      >>> f.myparam

   3. Using :func:`get_symbol_by_index`, using the index of the Symbol within
      the GDX file.

Internals
---------

.. automodule:: gdx.api
   :members:
   :private-members:

   Most methods in the GDX API have similar semantics:

   - Names are in CamelCase, e.g. gdxMethodName.
   - A list is returned; the first element is a return code.

   :class:`GDX` hides these details, allowing for simpler code. Methods can be
   accessed using :func:`call`. For instance, the following code calls the API
   method gdxFileVersion_:

   >>> g = GDX()
   >>> g.call('FileVersion')

   Alternately, methods can be accessed as members of :class:`GDX` objects,
   where the CamelCase API names are replaced by lowercase, with underscores
   separating words:

   >>> g.file_version()  # same as above

   See :py:attr:`GDX.__valid` for the list of supported methods.

.. _`GDX API`: http://www.gams.com/dd/docs/api/expert-level/gdxqdrep.html
.. _gdxFileVersion:
   http://www.gams.com/dd/docs/api/expert-level/gdxqdrep.html#gdxFileVersion
