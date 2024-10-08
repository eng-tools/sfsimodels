=======
History
=======

Pre-release
___________

0.9.46 (2024-06-20)
-------------------
* better handling on integers in loading system
* allow splitting of mesh at particular depths

0.9.45 (2022-11-22)
-------------------
* Added irregular section.
* Added in-plane axis for foundations.

0.9.43 (2022-04-08)
-------------------
* Added save_femesh
* Fixed issue with poissons ratio in soil stack

0.9.42 (2022-04-08)
-------------------
* Added `lshort` and `llong` parameters to foundations
* Minor changes to mesh algorithm to avoid divide by zero warnings

0.9.41 (2022-01-20)
-------------------
* Added `SingleWall`
* Foundation now has `.mass_density` to explicitly define it as the mass density
* Fixed bug with `StressDependentSoil.set_curr_m_eff_stress_from_g_mod()`

0.9.40 (2021-09-28)
-------------------
* In function `get_surface_node_indices` ordered surface node indices left to right
* Foundation object now accepts kwargs and adds them to object if already in `inputs`
* Added additional properties to RC section


0.9.38 (2021-07-28)
-------------------
* Fixed surface meshing issue
* Added `loop` to TwoDSystem for length out-of-plane.

0.9.37 (2021-07-15)
-------------------
* Added new `get_nearest_node_index_at_x` to ortho mesh.

0.9.35 (2021-07-15)
-------------------
* Soil now defines water mass density `wmd` and `liq_sg` instead of `liq_mass_density` to allow for not water liquids.
* Can retrieve the `unique_hash` from the ecp file for each object under the `loaded_unique_hash` parameter.
* Allow soil liquid mass to be changed.
* When loading an ecp file the loader does not fail when trying to set a non-settable attribute, instead it just does not set the attribute
* Fixed issue with meshing when adjusting for a smooth slope, when slope was going down to the right the top slope could be slightly wrong
* Improved meshing 2d vary xy - when multiple adjacent sloping surfaces on surface

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
