![CI](https://github.com/MannLabs/alphapept/workflows/CI/badge.svg)
![HeLa Thermo Win](https://github.com/MannLabs/alphapept/workflows/HeLa%20Thermo%20Win/badge.svg)
![HeLa Bruker Win](https://github.com/MannLabs/alphapept/workflows/HeLa%20Bruker%20Win/badge.svg)
![Windows Installer](https://github.com/MannLabs/alphapept/workflows/Windows%20Installer/badge.svg)

# AlphaPept
<img src="nbs/images/alphapept_logo.png" align="center">
> A modular, python-based framework to analyze mass spectrometry data. Powered by nbdev. Supercharged with numba.


## Documentation

The documentation is automatically built based on the jupyter notebooks and can be found [here](https://mannlabs.github.io/alphapept/):

## Installation Instructions

> To access Thermo files, we have integrated [RawFileReader](https://planetorbitrap.com/rawfilereader) into AlphaPept. We rely on [Mono](https://www.mono-project.com/) for Linux/Mac systems.
> To access Bruker files, we rely on the `timsdata`-library. Currently only Windows is supported. For feature finding, we use the Bruker Feature Finder, which can be found in the `ext` folder of this repository.
> ### Installation on Windows 10
> `pip install alphapept`
>  `or` `pip install .` in downloaded local AlphaPept repository
> ### Installation on Ubuntu for RawFileReader (Other Linux systems should be similar)
> 1. `sudo apt-get install build-essential`
> 2. Intall Mono from mono-project website [Mono Linux](https://www.mono-project.com/download/stable/#download-lin)
> 3. `pip install alphapept`
>  `or` `pip install .` from downloaded local AlphaPept repository
> ### Installation on Mac for RawFileReader
> 1. `brew install pkg-config`
> 2. Intall Mono from mono-project website [Mono Mac](https://www.mono-project.com/download/stable/)
> 3. `export PKG_CONFIG_PATH=/usr/local/lib/pkgconfig:/usr/lib/pkgconfig:/Library/Frameworks/Mono.framework/Versions/6.12.0/lib/pkgconfig:$PKG_CONFIG_PATH`
>   (`or` add above `PKG_CONFIG_PATH=/usr/......:$PKG_CONFIG_PATH` into ~./bash_profile, and run `source ~/bash_profile`.) Here 6.12.0 is developers' Mono version
> 4. `pip install alphapept`
>  `or` `pip install .` in downloaded local AlphaPept repository

### Standalone Windows Installer
To use AlphaPept as a stand-alone program for end-users, it can be installed on Windows machines via a one-click installer. Download the latest version [here](http://alphapept.org).

### Python

We highly recommend the [Anaconda](https://www.anaconda.com) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html) Python distribution which comes with a powerful package manager.

It is strongly recommended to install AlphaPept in its own environment.
1. Open the console and create a new conda environment: `conda create --name alphapept python`
2. Activate the environment: `source activate alphapept` for Linux / Mac Os X or `activate alphapept` for Windows
2. Redirect to the folder of choice and clone the repository: `git clone https://github.com/MannLabs/alphapept.git`
3. Install the packages with `pip install -r requirements.txt`
4. Install the package with `python setup.py install`
5. Install pytables with `conda install pytables`
{% include note.html content='If you would like to use alphapept in your jupyter notebook environment, additionally install nb_conda: `conda install nb_conda`. This also installs the juper notebook extensions. They can be called from a running jupyter instance like so: `http://localhost:8888/nbextensions`. For navigating the notebooks, the exension `collapsible headings` and `toc2` are very beneficial. For developing with the notebooks see the `nbev` section below.' %}
If AlphaPept is installed correctly, you should be able to import Alphapept as a package within the environment; see below.

## How to use

AlphaPept is meant to be a framework to implement and test new ideas quickly but also to serve as a performant processing pipeline. In principle, there are three use-cases:

* GUI: Use the graphical user interface to select settings and process files manually.
* CMD: Use the command-line interface to process files. Useful when building automatic pipelines.
* Python: Use python modules to build individual workflows. Useful when building customized pipelines and using Python as a scripting language or when implementing new ideas.

### Windows Installation

For the windows installation, simply click on the shortcut after installation. The windows installation also installs the command-line tool so that you can call alphapept via `alphapept` in the command line.

### Python Package

Once AlphaPept is correctly installed, you can use it like any other python module.

```
from alphapept.fasta import get_frag_dict, parse
from alphapept import constants

peptide = 'PEPT'

get_frag_dict(parse(peptide), constants.mass_dict)
```




    {'b1': 98.06004032687,
     'b2': 227.10263342686997,
     'b3': 324.15539728686997,
     'y1': 120.06551965033,
     'y2': 217.11828351033,
     'y3': 346.16087661033}



### Using as a tool

To launch the command line interface use:
* `python alphapept`

This allows us to select different modules. To start the GUI use:
* `python alphapept gui`

Likewise, to start the watcher use:
* `python alphapept watcher`

Note that when working on the GitHub repository, you might want to launch the codebase you are working on and not the installed version. Here, call AlphaPept as a module: `python -m alphapept`, `python -m alphapept gui` and `python -m alphapept watcher`

### Watcher
AlphaPept has a watcher module that continuously monitors a target folder and automatically performs file conversion and feature finding on new files.

### Processing experiments

AlphaPept is centered around settings-files. Here you can specify the settings and then use `run_alphapept` function to perform processing.

## Analyzing an experiment
This describes the minimal steps to analyze an experiment.

### GUI

1. Open the GUI. Drag and drop experimental files and at least one fasta in the `Experiment` tab.
2. Default settings are loaded and can be changed or saved in the `Settings` tab
3. Navigate to the Run panel and click `Start`

### Investigating the result files
The experimental results will be stored in the corresponding *.hdf-files and loaded with pandas.

### CMD / Python
1. Create a settings-file. This can be done by changing the `default_settings.yaml` in the repository or using the GUI.
2. Run the analysis with the new settings file. `python -m alphapept run new_settings.yaml`

Within Python (i.e., Jupyter notebook) the following code would be required)
```
from alphapept.settings import load_settings
from alphapept.runner import run_alphapept
settings = load_settings('new_settings.yaml')
r = run_alphapept(settings)
```

## Contributing
If you have a feature request or a bug report, please post it as an issue on the GitHub issue tracker. If you want to contribute, put a PR for it. You can find more guidelines for contributing and how to get started [here](https://github.com/MannLabs/alphapept/blob/master/CONTRIBUTING.md). I will gladly guide you through the codebase and credit you accordingly. Additionally, you can check out the Projects-page on GitHub. You can also contact me via opensource@alphapept.com.
