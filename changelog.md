# Changelog

Last change: 12-Jan-2021, MTS

## 0.3.32
* Bugfixes for fragment calibration

## 0.3.30
* Improved fragment calibration, this increases performance
* Support for fractionated data (Note the performance is not yet satisfactory)
* Basic scaffold for TMT quantification
* Community contributions by @mgleeming (Coverage Map) and @romanzenka (Typo)
* Multiple small bugs and improvements

## 0.3.29
* Stability improvements
* support of running multiple `mzML`-files #316
* Auto-refresh of Status page #203
* Moved custom plots to home directory

## 0.3.28

* Automatic fragment tolerance estimation for better support of MS2=Iontrap Thermo runs #305
* Updated error message handling
* consistent renaming of o_mass to prec_offset
* Fixed a bug in how `int_ratio` is calculated in first_search
* Enabled handling of `mzML`-files in GUI / Core
* Improved Documentation
* Ion export for search parallel
* Moved loss_dict to constants.
