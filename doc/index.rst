GDX file data access
====================

pyGDX is a Python 3 package for accessing data stored in *GAMS Data eXchange* (GDX) files. GDX is a proprietary, binary file format used by the General Algebraic Modelling System (GAMS_); pyGDX uses the Python bindings for the `GDX API`_.

pyGDX uses xray_ to provide labeled, multidimensional data structures for accessing data; a :class:`gdx.File` is a thinly-wrapped :class:`xray.Dataset`.

Documentation
-------------

.. toctree::
   :maxdepth: 2

   gdx
   file
   api
   todos

License
-------

PyGDX is available under the `MIT license`_.

History
-------

PyGDX was inspired by the similar package, also named `py-gdx, by Geoff Leyland`_.

.. Indices and tables
   ==================
   * :ref:`genindex`
   * :ref:`modindex`
   * :ref:`search`

.. _`MIT license`: https://github.com/khaeru/py-gdx/blob/master/LICENSE
.. _GAMS: http://www.gams.com
.. _`GDX API`: http://www.gams.com/dd/docs/api/expert-level/gdxqdrep.html
.. _xray: https://github.com/xray/xray
.. _`py-gdx, by Geoff Leyland`: https://github.com/geoffleyland/py-gdx
