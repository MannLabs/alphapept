Univeral Feature Finder command line
------------------------------------

This is a command line tool of the Bruker universal feature finder. For Bruker-internal use only. For technical questions, contact wiebke.timm@bruker.com

Call the exe with

uff-cmdline.exe --ff <dim> --readconfig <filename>

where <dim> is either 3d for lcms data in baf format or 4d for lc-tims-tof data in tdf format.
<filename> is a config file. There are two example config files in this directory. For peptide id/quant, use "proteomics.config", after changing the "input=" argument to the full path to the .d directory.

All parameters and descriptions can be output with uff-cmdline --help

You can also overwrite the input parameter on the command line with --input=<path-to-directory>. (You can overwrite any parameter that is in the config file with a command line parameter for use in scripts).

The resulting MGF and Feature sqlite files are put into the input .d directory.

Minimal RAM requirement for Proteomics data is 32 GB. Recommended 64 GB. Don't use on an acquisition machine, because I/O load is to be expected.



The "timstof" MGF format
------------------------
This explanation applies to the MGF format that is written with the parameter Mgf.mgfMode=timstof

Each BEGIN IONS/END IONS block corresponds to a group of PASEF scans, that are assigned to exactly one of the precursors found by the precursor selection. Its ID can be found after "SCANS" or in the TITLE line after "PASEFPRec./ScanNo". That ID references the one found in the tdf file. 'MSMSframes' lists the PASEF FrameIDs whose frames were summed to calculate the MSMS peaklist which was used to deduct the deisotoped peaklist within the BEGIN/END IONS block. 

There are two types of entries: Those with feature assignment and those without.

Example for an entry without feature assignment:

TITLE=No Feature, +MS2(1222.589747, 1+), 1.3484 1/k0, 42.00eV, 1.09 s, PASEFPrec./ScanNo 1, MS frame #1, MSMSframes <2/3/4/5/6/8/9/10/11/12>
PEPMASS=1221.986454
SCANS=1
RTINSECONDS=1.09
CHARGE=1+

"No Feature " means no appropriate feature was found by the feature finder. In that case, the PEPMASS and CHARGE correspond to the monoisotopic precursor mass and charge that were deduced by the precursor selection for PrecursorId 1 (SCANS=1). The mass "+MS2(1222.589747, 1+)" is the isolation mass used in fragmenting that precursor. The following values in the TITLE line are attributes of the precursor peak.


Example for an entry with a feature assignment:

TITLE=1 Features, +MS2(659.766018, 2+), 0.9272 1/k0, 42.00eV, 1981.65 s, PASEFPrec./ScanNo 52217, MS frame #16111, MSMSframes <16118>, Feature #22144 {mz 659.835800 Da | rt 1978.74 [1953.62,2007.96], FWHM rt 16.67 | mobility 0.9293 [0.8869,0.9591] | z 2 | I 514} 
PEPMASS=659.835800 514 2+
RTINSECONDS=1981.65
SCANS=52217

...and with multiple feature assignments:

TITLE=2 Features, +MS2(768.347458, 2+), 0.9839 1/k0, 42.00eV, 1556.24 s, PASEFPrec./ScanNo 35321, MS frame #12657, MSMSframes <12672/12673>, Feature #13708 {mz 767.343544 Da | rt 1568.62 [1547.61,1577.43], FWHM rt 13.56 | mobility 0.9701 [0.9474,1.0254] | z 2 | I 49} Feature #13709 {mz 767.833125 Da | rt 1557.78 [1547.61,1574.72], FWHM rt 24.26 | mobility 0.9798 [0.9542,1.0059] | z 2 | I 90} 
PEPMASS=767.343544 49 2+
PEPMASS=767.833125 90 2+
RTINSECONDS=1556.24
SCANS=35321

here, the attributes of the assigned features are printed after the precursor information and the isolation mass. The PEPMASS values are the monoisotopic masses of those features, in the same order as in the TITLE line. The intensity and charge of the features is also printed in the PEPMASS lines. 

Units: Da for m/z, seconds for retention time (rt), 1/k0 for mobility (inverse mobility). From the inverse mobility, the CCS value can be calculated if the charge, element of the gas, and temperature are known. We usually use N2 and 305 K. z is the charge, I is intensity. Values in square brackets show the bounding box limits of the feature. "FWHM rt" is the full width at half max peak width in seconds.
