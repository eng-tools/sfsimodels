=======
History
=======

0.9.X (2019-X-X)
--------------------

* Can now pass `export_none` to ecp_object.add_to_dict() to turn on/off the export of null in ecp file.

0.9.21 (2019-11-11)
--------------------

* Fixed issue with stack not working for overriding soil properties
* Switched to using wheel distributions on pypi for package

0.9.20 (2019-10-7)
--------------------

* Can now explicitly set gravity for soil (default=9.8) and liquid mass density `liquid_mass_density` (default=1000)
* `pw` is deprecated but still available and replaced with new name `uww` due to poor name
