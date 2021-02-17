=======
History
=======

Pre-release
___________
* Soil now defines water mass density `wmd` and `liq_sg` instead of `liq_mass_density` to allow for not water liquids.
* Can retrieve the `unique_hash` from the ecp file for each object under the `loaded_unique_hash` parameter.
* Allow soil liquid mass to be changed.


0.9.31 (2021-01-28)
-------------------
* Improved saving and loading of `TwoDSystem`
* Allowed calculation of effective stress when soil under water and dry weight is not set
* Fixed issue where soil_profile.move_layer function would delete layer if new position was equal to previous position
* Fixed issue with mesh vary2DXY where mesh could not adjust near the surface
* Fixed issue with mesh vary2DY and vary2DXY when trimming mesh, where it could create a deformity
* Added `ip_axis` to foundation default outputs (`ip_axis` is in-plane axis)
* When using the `set_section_prop` on a `BeamColumnElement` the property is automatically added to the outputs list
* Can load `Material` object into `Building` as `Building.material`
* Can load `Material` object into `Section` as `Section.material` or `Section.mat`
* Added `sm.std.create_rc_beam()` function to create an RC beam element with RC sections.
* Added `override` option to the `Foundation` object to override pre-computed properties.

0.9.28 (2020-10-08)
--------------------
* Added in plane axis (`ip_axis`) and out-of-plane axis (`oop_axis`) parameters for foundation.
* Added new constructor to `sfsimodels.num.mesh` `FiniteElementVary2DMeshConstructor`,
  which constructs either `FiniteElementVaryY2DMesh` where x-coordinates remain unchanged with depth,
    but y-coordinates vary with x-distance, or `FiniteElementVaryXY2DMesh` where both x- and y-coordinates vary
    throughout the mesh.

0.9.27 (2020-09-03)
--------------------
* Improved handling of sections and materials
* Added `get_oop_axis` method to foundations to get the out-of-plane axis
* PadFoundation can now handle irregular spacing of footings
* Meshing can handle foundation out-of-plane input

0.9.25 (2020-08-17)
--------------------
* Fixed issue where SoilProfile split did not stop at soil profile height
* Added `material` to `Building` object
* Changed `Concrete` to `ReinforcedConcrete`
* Fixed bug with PadFoundation where `height` was returned when `depth` was requested
* For mesh the new class name is `FiniteElementOrth2DMesh` since the mesh is orthogonal. Also `active_nodes` is now cached

0.9.24 (2020-08-05)
--------------------
* Added `Coords` object, which defines coordinates in x, y, z directions
* Added `Units` and `GlobalUnits`
* Added `Load` and `LoadAtCoords` objects
* Better loading of ecp files - can now deal with non-defaults kwargs, e.g. changing `liq_mass_density` in a Soil object
* Added method for computing column vertical loads (`get_column_vert_loads`) to Frame object
* Added PadFooting object, and PadFoundation now as a PadFooting object to store pad footing attributes

0.9.23 (2020-4-19)
--------------------
* Added option to provide shear modulus at zero effective stress for stress dependent soil.
* Can load ecp file and if model not defined then can set flag to load the `base_type` model.
* Added mesh generation tool for creating meshes for finite-element analyses based on new TwoDSystem object.
* Added `NullBuilding` object to create a building with no attributes
* Added option for linking a building and a foundation using `building.set_foundation(foundation, two_way=True)` and `foundation.set_building(building)`, where if `two_way` is true then vice-versa link also created.
* Fixed issue were checking_tools would raise error for zero vs almost zero.

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
