=======
History
=======

0.9.2X (2020-2-XX)
--------------------
* Added `NullBuilding` object to create a building with no attributes
* Added option for linking a building and a foundation using `building.set_foundation(foundation, two_way=True)` and `foundation.set_building(building)`, where if `two_way` is true then vice-versa link also created.

0.9.22 (2020-2-17)
--------------------

* Can now pass `export_none` to ecp_object.add_to_dict() to turn on/off the export of null in ecp file.
* Can assign beam and column properties to frames using 'all' to assign to all beams or columns.

0.9.21 (2019-11-11)
--------------------

* Fixed issue with stack not working for overriding soil properties
* Switched to using wheel distributions on pypi for package

0.9.20 (2019-10-7)
--------------------

* Can now explicitly set gravity for soil (default=9.8) and liquid mass density `liquid_mass_density` (default=1000)
* `pw` is deprecated but still available and replaced with new name `uww` due to poor name
