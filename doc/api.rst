Internals
=========

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
