# Changelog

Last change: 15-Feb-2022, MTS


## 0.4.0
This version contains a lot of variable renaming to be more consistent with other Alpha*-packages.
* Optimized recalibration to be more memory efficient
*

## 0.3.33
* Versionbump for requirements

## 0.3.32
* Bugfixes for fragment calibration
* Bugfixes for matching
* Bugfix for duplicate hills in Thermo  #386
* Bugfix calling LFQ on MaxQuant files w/o calling delayed normalization

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
* Fixed a bug in how `fragments_int_ratio` is calculated in first_search
* Enabled handling of `mzML`-files in GUI / Core
* Improved Documentation
* Ion export for search parallel
* Moved loss_dict to constants.
