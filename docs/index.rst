.. sfsimodels documentation master file, created by
   sphinx-quickstart on Wed May 23 10:38:42 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to sfsimodels's documentation!
======================================

.. toctree::
   :maxdepth: 2

   sfsimodels
   sfsimodels.models
   sfsimodels.methods

..
   .. note::

      If you use sfsimodels in your own project or package then please let me
      know at `maxim.millen@canterbury.ac.nz <maxim.millen@canterbury.ac.nz>`_ and I can keep you
      up-to date with planned updates.

==========
sfsimodels
==========

A set of python objects to represent physical objects for assessing structural and geotechnical problems

Attempting to solve the `Liskov Substitution Principle <https://en.wikipedia.org/wiki/Liskov_substitution_principle>`_
problem for combining independently developed source
code in the fields of structural and geotechnical engineering.

Models represent states of physical objects, currently can not represent dynamic/changing states.

Model inheritance system
========================

Every object contains a ``type``, a ``base_type`` and a list of ``ancestor_types``.

 - ``type`` is the current type of the class or instance of the class
 - ``base_type`` is what class should be considered as for standard operations such as saving and loading.
 - ``ancestor_types`` is a list of the ``type`` of the ancestors of the class


Generation of new custom models
===============================

It is easiest to create a new object by inheriting from ``sm.CustomObject``, as this contains the default parameters
needed for loading and saving the model.

If you chose not to use the default custom object, you must set the object ``base_type`` parameter to ``"custom_object"``.

Loading a custom object
=======================

pass a dictionary to the ``custom_object`` parameter in the ``sm.load_json`` function, where the dictionary contains:
`custom={"<base_type>-<type>": Object}`.


Installation
============

.. code:: bash

    pip install sfsimodels

Saving and loading models
=========================

Check out a full set of examples [on github](https://github.com/eng-tools/sfsimodels/blob/master/examples/saving_and_loading_objects.ipynb)

.. code-block:: python

    structure = models.Structure()  # Create a structure object
    structure.id = 1  # Assign it an id
    structure.name = "sample building"  # Assign it a name and other parameters
    structure.h_eff = 10.0
    structure.t_fixed = 1.0
    structure.mass_eff = 80000.
    structure.mass_ratio = 1.0  # Set vertical and horizontal masses are equal

    ecp_output = files.Output()  # Create an output object
    ecp_output.add_to_dict(structure)  # Add the structure to the output object
    ecp_output.name = "test data"
    ecp_output.units = "N, kg, m, s"  # Set the units
    ecp_output.comments = ""

    p_str = json.dumps(ecp_output.to_dict(), skipkeys=["__repr__"], indent=4)  # Assign it to a json string
    objs = files.loads_json(p_str)  # Load a json string and convert to a dictionary of objects
    assert ct.isclose(structure.mass_eff, objs['buildings'][1].mass_eff)  # Access the object



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`



Contributing
============

 * All properties that require exterior parameters should be named ``get_<property>``,
 * Parameters that vary with depth in the soil profile should be named ``get_<property>_at_depth``
 * Properties in the stress dependent soil should use ``get_<property>_at_v_eff_stress`` to obtain the property
 * Functions that set properties on objects should start with 'set' then the property the citation, i.e. ``set_<property>_<author-year>``
 * Methods that generate properties on the object should have the prefix ``gen_`` then property i.e. ``gen_<property`` e.g. ``soil_profile.gen_split()``


Citing
======

Please use the following citation:

Millen M. D. L. (2019) Sfsimodels <version-number> - A set of standard models for assessing structural and geotechnical problems,
https://pypi.org/project/sfsimodels/, doi: 10.5281/zenodo.2596721

