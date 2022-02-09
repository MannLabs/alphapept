# AlphaPept



![CI](https://github.com/MannLabs/alphapept/workflows/CI/badge.svg)
![Quick Test](https://github.com/MannLabs/alphapept/workflows/Quick%20Test/badge.svg)
![Performance test](https://github.com/MannLabs/alphapept/workflows/Performance%20test/badge.svg)
![Windows Installer](https://github.com/MannLabs/alphapept/workflows/Windows%20Installer/badge.svg)

[![DOI:10.1101/2021.07.23.453379](http://img.shields.io/badge/DOI-10.1101/2021.07.23.453379-B31B1B.svg)](https://www.biorxiv.org/content/10.1101/2021.07.23.453379v1)

## Preprint

Our preprint **AlphaPept, a modern and open framework for MS-based proteomics** is now available [here.](https://www.biorxiv.org/content/10.1101/2021.07.23.453379v1)

Be sure to check out other packages of our ecosystem:
- [alphatims](https://github.com/MannLabs/alphatims): Fast access to TimsTOF data.
- [alphamap](https://github.com/MannLabs/alphamap): Peptide level MS data exploration.

## Windows Quickstart
![](https://i.imgur.com/UO64YPx.jpg)

1. Download the latest installer [here](https://github.com/MannLabs/alphapept/releases/latest), install and click the shortcut on the desktop. A browser window with the AlphaPept interface should open. In the case of Windows Firewall asking for network access for AlphaPept, please allow.
2. In the `New Experiment`, select a folder with raw files and FASTA files.
3. Specify additional settings such as modifications with `Settings`.
4. Click `Start` and run the analysis. 

See also below for more detailed instructions.

## Current functionality

| Feature         	| Implemented    	|
|-----------------	|----------------	|
| Type            	| DDA            	|
| Filetypes       	| Bruker, Thermo 	|
| Quantification  	| LFQ            	|
| Isobaric labels 	| None           	|
| Platform        	| Windows        	|

Linux and macOS should, in principle, work but are not heavily tested and might require additional work to set up (see detailed instructions below). To read Thermo files, we use Mono, which can be used on Mac and Linux. For Bruker files, we can use Linux but not yet macOS.

## Python Installation Instructions

### Requirements

We highly recommend the [Anaconda](https://www.anaconda.com) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html) Python distribution, which comes with a powerful package manager. See below for additional instructions for Linux and Mac as they require additional installation of Mono to use the RawFileReader.

AlphaPept can be used as an application as a whole or as a Python Package where individual modules are called. Depending on the use case, AlphaPept will need different requirements, and you might not want to install all of them.

Currently, we have the default `requirements.txt`, additional requirements to run the GUI `gui` and packages used for developing `develop`. 

Therefore, you can install AlphaPept in multiple ways:

- The default `alphapept`
- With GUI-packages `alphapept[gui]`
- With pacakges for development `alphapept[develop]` (`alphapept[develop,gui]` respectively

The requirements typically contain pinned versions and will be automatically upgraded and tested with `dependabot`. This `stable` version allows having a reproducible workflow. However, in order to avoid conflicts with package versions that are too strict, the requirements are not pinned when being installed. To use the strict version use the `-stable`-flag, e.g. `alphapept[stable]`.

For end-users that want to set up a processing environment in Python, the `"alphapept[stable,gui-stable]"` is the `batteries-included`-version that you want to use.

### Python

It is strongly recommended to install AlphaPept in its own environment.
1. Open the console and create a new conda environment: `conda create --name alphapept python=3.8`
2. Activate the environment: `conda activate alphapept`
3. Install AlphaPept via pip: `pip install "alphapept[stable,gui-stable]"`. If you want to use AlphaPept as a package without the GUI dependencies and without strict version dependencies, use `pip install alphapept`.

If AlphaPept is installed correctly, you should be able to import AlphaPept as a package within the environment; see below.

* * *
#### Linux
1. Install the build-essentials: `sudo apt-get install build-essential`.
2. Install AlphaPept via pip: `pip install "alphapept[stable,gui-stable]"`. If you want to use AlphaPept as a package withouth the GUI dependencies and strict version dependencies use `pip install alphapept`.
3. Install libgomp.1 with `sudo apt-get install libgomp1`.

##### Bruker Support
4. Copy-paste the Bruker library for feature finding to your /usr/lib folder with `sudo cp alphapept/ext/bruker/FF/linux64/alphapeptlibtbb.so.2 /usr/lib/libtbb.so.2`.

##### Thermo Support
5. Install Mono from mono-project website [Mono Linux](https://www.mono-project.com/download/stable/#download-lin). NOTE, the installed mono version should be at least 6.10, which requires you to add the ppa to your trusted sources!
6. Install pythonnet with `pip install pythonnet==2.5.2`

* * *
#### Mac

1. Install AlphaPept via pip: `pip install "alphapept[stable,gui-stable]"`. If you want to use AlphaPept as a package withouth the GUI dependencies and strict version dependencies use `pip install alphapept`.

##### Bruker Support
> Only supported for preprocessed files.

##### Thermo Support
2. Install [brew](https://brew.sh) and pkg-config: `brew install pkg-config`3. Intall Mono from mono-project website [Mono Mac](https://www.mono-project.com/download/stable/)
4. Register the Mono-Path to your system:
For macOS Catalina, open the configuration of zsh via the terminal:
* Type in `cd` to navigate to the home directory.
* Type `nano ~/.zshrc` to open the configuration of the terminal
* Add the path to your mono installation: `export PKG_CONFIG_PATH=/usr/local/lib/pkgconfig:/usr/lib/pkgconfig:/Library/Frameworks/Mono.framework/Versions/Current/lib/pkgconfig:$PKG_CONFIG_PATH`. Make sure that the Path matches to your version (Here 6.12.0)
* Save everything and execute `. ~/.zshrc` 
4. Install pythonnet with `pip install pythonnet==2.5.2`

* * *
#### Developer
1. Redirect to the folder of choice and clone the repository: `git clone https://github.com/MannLabs/alphapept.git`
2. Navigate to the alphapept folder with `cd alphapept` and install the package with `pip install .` (default users) or with `pip install -e .` to enable developers mode. Note that you can use the different requirements here aswell (e.g. `pip install ".[gui-stable]"`)

#### GPU Support
Some functionality of AlphaPept is GPU optimized that uses Nvidia's CUDA. To enable this, additional packages need to be installed. 

1. Make sure to have a working [CUDA toolkit](https://developer.nvidia.com/cuda-toolkit) installation that is compatible with CuPy. To check type `nvcc --version` in your terminal.
2. Install [cupy](https://cupy.dev). Make sure to install the cupy version matching your CUDA toolkit (e.g. `pip install cupy-cuda110` for CUDA toolkit 11.0.

### Additional Notes
> To access Thermo files, we have integrated [RawFileReader](https://planetorbitrap.com/rawfilereader) into AlphaPept. We rely on [Mono](https://www.mono-project.com/) for Linux/Mac systems.> To access Bruker files, we rely on the `timsdata`-library. Currently, only Windows is supported. For feature finding, we use the Bruker Feature Finder, which can be found in the `ext` folder of this repository.
 
#### Notes for NBDEV

* For developing with the notebooks, install the nbdev package (see the development requirements)
* To facilitate navigating the notebooks, use jupyter notebook extensions. They can be called from a running jupyter instance like so:`http://localhost:8888/nbextensions`. The extensions `collapsible headings` and `toc2` are very beneficial.
## Standalone Windows Installer
To use AlphaPept as a stand-alone program for end-users, it can be installed on Windows machines via a one-click installer. Download the latest version [here](https://github.com/MannLabs/alphapept/releases/latest).

## Additional Documentation

The documentation is automatically built based on the jupyter notebooks (nbs/index.ipynb) and can be found [here](https://mannlabs.github.io/alphapept/):

## Version Performance
An overview of the performance of different versions can be found [here](https://charts.mongodb.com/charts-alphapept-itfxv/public/dashboards/5f671dcf-bcd6-4d90-8494-8c7f724b727b).
We re-run multiple tests on datasets for different versions so that users can assess what changes from version to version. Feel free to [suggest](https://github.com/MannLabs/alphapept/discussions) a test set in case.

## How to use

AlphaPept is meant to be a framework to implement and test new ideas quickly but also to serve as a performant processing pipeline. In principle, there are three use-cases:

* GUI: Use the graphical user interface to select settings and process files manually.
* CMD: Use the command-line interface to process files. Useful when building automatic pipelines.
* Python: Use python modules to build individual workflows. Useful when building customized pipelines and using Python as a scripting language or when implementing new ideas. 

### Windows Standalone Installation

For the [windows installation](https://github.com/MannLabs/alphapept/releases/latest), simply click on the shortcut after installation. The windows installation also installs the command-line tool so that you can call alphapept via `alphapept` in the command line.

![](https://i.imgur.com/SQikLHQ.jpg)

### Python Package

Once AlphaPept is correctly installed, you can use it like any other python module.

```python
from alphapept.fasta import get_frag_dict, parse
from alphapept import constants

peptide = 'PEPT'

get_frag_dict(parse(peptide), constants.mass_dict)
```




    {'b1': 98.06004032687,
     'b2': 227.10263342687,
     'b3': 324.15539728686997,
     'y1': 120.06551965033,
     'y2': 217.11828351033,
     'y3': 346.16087661033}



### Using as a tool

If alphapept is installed an a conda or virtual environment, launch this environment first.

To launch the command line interface use:
* `alphapept`

This allows us to select different modules. To start the GUI use:
* `alphapept gui`

To run a workflow, use:
* `alphapept workflow your_own_workflow.yaml`
An example workflow is easily generated by running the GUI once and saving the settings which can be modified on a per-project basis.

### CMD / Python
1. Create a settings-file. This can be done by changing the `default_settings.yaml` in the repository or using the GUI.
2. Run the analysis with the new settings file. `alphapept run new_settings.yaml`

Within Python (i.e., Jupyter notebook) the following code would be required)
```
from alphapept.settings import load_settings
import alphapept.interface
settings = load_settings('new_settings.yaml')
r = alphapept.interface.run_complete_workflow(settings)
```

This also allows you to break the workflow down in indiviudal steps, e.g.:

```
settings = alphapept.interface.import_raw_data(settings)
settings = alphapept.interface.feature_finding(settings)
```

## Notebooks

Within the notebooks, we try to cover most aspects of a proteomics workflow:

* Settings: General settings to define a workflow
* Chem: Chemistry related functions, e.g., for calculating isotope distributions
* Input / Output: Everything related to importing and exporting and the file formats used
* FASTA: Generating theoretical databases from FASTA files
* Feature Finding: How to extract MS1 features for quantification
* Search: Comparing theoretical databases to experimental spectra and getting Peptide-Spectrum-Matches (PSMs)
* Score: Scoring PSMs
* Recalibration: Recalibration of data based on identified peptides
* Quantification: Functions for quantification, e.g., LFQ
* Matching: Functions for Match-between-runs
* Constants: A collection of constants
* Interface: Code that generates the command-line-interface (CLI) and makes workflow steps callable
* Performance: Helper functions to speed up code with CPU / GPU
* Export: Helper functions to make exports compatbile to other Software tools
* Label: Code for support isobaric label search
* Display: Code related to displaying in the streamlit gui
* Additional code: Overview of additional code not covered by the notebooks
* How to contribute: Contribution guidelines
* AlphaPept workflow and files: Overview of the worfklow, files and column names

## Contributing
If you have a feature request or a bug report, please post it either as an idea in the [discussions](https://github.com/MannLabs/alphapept/discussions) or as an issue on the [GitHub issue tracker](https://github.com/MannLabs/alphapept/issues). Upvoting features in the discussions page will help to prioritize what to implement next. If you want to contribute, put a PR for it. You can find more guidelines for contributing and how to get started [here](https://mannlabs.github.io/alphapept/contributing.html). We will gladly guide you through the codebase and credit you accordingly. Additionally, you can check out the Projects page on GitHub. You can also contact us via opensource@alphapept.com.

If you like the project, consider starring it!

## Cite us

```
@article {Strauss2021.07.23.453379,
	author = {Strauss, Maximilian T and Bludau, Isabell and Zeng, Wen-Feng and Voytik, Eugenia and Ammar, Constantin and Schessner, Julia and Ilango, Rajesh and Gill, Michelle and Meier, Florian and Willems, Sander and Mann, Matthias},
	title = {AlphaPept, a modern and open framework for MS-based proteomics},
	elocation-id = {2021.07.23.453379},
	year = {2021},
	doi = {10.1101/2021.07.23.453379},
	publisher = {Cold Spring Harbor Laboratory},
	URL = {https://www.biorxiv.org/content/early/2021/07/26/2021.07.23.453379},
	eprint = {https://www.biorxiv.org/content/early/2021/07/26/2021.07.23.453379.full.pdf},
	journal = {bioRxiv}
}
```
