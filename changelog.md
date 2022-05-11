# Changelog

Last change: 24-APR-2022, MTS

## 0.45
* Revision of how fractions are handled
* LFQ Acceleration @hugokitano
* Update of various packages 

## 0.4.4
* New maximum iterations for LFQ
* Auto-adjustment of settings for non-specific search

## 0.4.3
* LFQ Fix @hugokitano

## 0.4.2
* Better logging for LFQ
* Correct setting of cores when searching w/o saving database
* Fixed Docs

## 0.4.1
* Fixed a bug in LFQ

## 0.4.0
This version contains a lot of variable renaming to be more consistent with other Alpha*-packages.
This will probably lead to incompatibility with previous history modes.
* Optimized recalibration to be more memory efficient
* Fixed a bug where peptide_fdr was not accurately saved. This should affect reported protein / peptide ids.
* Included additional export of `identifications`, e.g. the best sequence for each recorded MS2-spectrum
* Usability improvements when starting AlphaPept multiple times
* Revised History Mode

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
