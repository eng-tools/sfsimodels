.. image:: https://travis-ci.org/eng-tools/sfsimodels.svg?branch=master
   :target: https://travis-ci.org/eng-tools/sfsimodels
   :alt: Testing Status

.. image:: https://img.shields.io/pypi/v/sfsimodels.svg
   :target: https://pypi.python.org/pypi/sfsimodels
   :alt: PyPi version
   
.. image:: https://coveralls.io/repos/github/eng-tools/sfsimodels/badge.svg
   :target: https://coveralls.io/github/eng-tools/sfsimodels

.. image:: https://img.shields.io/badge/license-MIT-blue.svg
    :target: https://github.com/eng-tools/sfsimodels/blob/master/LICENSE
    :alt: License

**********
sfsimodels
**********

A set of standard python models for assessing structural and geotechnical problems

Liskov Substitution Principle


Installation
============

.. code:: bash
    pip install sfsimodels

Saving and loading models
=========================

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


How do I get set up?
====================

1. Run ``pip install -r requirements.txt``

Testing
=======

Tests are run with pytest

* Locally run: ``pytest`` on the command line.

* Tests are run on every push using travis, see the ``.travis.yml`` file


Deployment
==========

To deploy the package to pypi.com you need to:

 1. Push to the *pypi* branch. This executes the tests on circleci.com

 2. Create a git tag and push to github, run: ``trigger_deploy.py`` or manually:

 .. code:: bash
    git tag 0.5.2 -m "version 0.5.2"
    git push --tags origin pypi