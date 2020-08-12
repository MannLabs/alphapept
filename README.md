# AlphaPept
> A modular, python-based framework for mass spectrometry. Powered by nbdev. Supercharged with numba.


![](nbs\images\alphapept_logo.png)
![CI](https://github.com/MannLabs/alphapept/workflows/CI/badge.svg)

## Documentation

The documentation is automatically build based the jupyter notebooks and can be found [here](https://mannlabs.github.io/alphapept/):

## Installation Instructions
> To access Thermo files, we rely on [pymsfilereader](https://github.com/frallain/pymsfilereader), which requires to have `MSFileReader` installed. You can find installation instructions in the GitHub repository.> To access Bruker files, we rely on the `timsdata`-library. Currently only Windows is supported. For feature finding, we use the Bruker Feature Finder, which can be found in the `ext` folder of this repository.

### Standalone Windows Installer

> TODO. Here you will find a link to a windows installer for one-click installation.

### Python

We highly recommend the [Anaconda](https://www.anaconda.com) or [Miniconda](https://docs.conda.io/en/latest/miniconda.html) Python distribution which comes with a powerful package manager.
It is strongly recommended to install AlphaPept in its own environment.
1. Open the console and create a new conda environment: conda create --name alphapept python
2. Activate the environment: `source activate alphapept` for Linux / Mac Os X or `activate alphapept` for Windows
2. Redirect to the folder of choice and clone the repository: `git clone https://github.com/MannLabs/alphapept.git`
3. Install the packages with `pip install -r requirements.txt`
4. Install the package with `python setup.py install`
5. Install pytables with `conda install pytables`
{% include note.html content='If you would like to use alphapept in your jupyter notebook environment, additionally install nb_conda: `conda install nb_conda`' %}
If AlphaPept is installed correctly, you should be able to import Alphapept as a package within the environment, see below.

## How to use

AlphaPept is meant to be a framework to implement and test new ideas quickly but also to serve as a performant processing pipeline. In principle, there are three use-cases:

* GUI: Use the graphical user interface to manually select settings and process files.
* CMD: Use the command-line interface to process files. Useful when building automatic pipelines.
* Python: Use python modules to build individual workflows. Useful when building customized pipelines and using Python as a scripting language or when implementing new ideas. 

### Windows Installation

For the windows installation, simply click on the shortcut after installation. The windows installation also installs the command line tool so that you can call alphapept via `alphapept` in the command line.

### Python Package

Once AlphaPept is correctly installed you can use it like any other python module.

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



To launch the command line interface use:
* `python alphapept`

This allows to select the different modules. To start the GUI use:
* `python alphapept gui`

Likewise, to start the watcher use:
* `python alphapept watcher`

Note that when working on the GitHub repository, you might want to launch the codebase you are working on and not the installed version. Here, call AlphaPept as a module: `python -m alphapept`, `python -m alphapept gui` and `python -m alphapept watcher`

### Watcher
AlphaPept has a watcher module that continously monitors a target folder and automatically performs file conversion and feature finding on new files.

### Processing experiments

AlphaPept is centered around settings-files. Here you can specify the settings and then use `run_alphapept` function to perform processing.

## Notes for Programmers

### Contributing guidelines

See the contributing file for more information.

### Literal Programming
A key feature is the use of [nbdev](https://github.com/fastai/nbdev). We like to keep the entrance barrier low to attract new coders to contribute to the AlphaPept package. For this, we see nbedv as an ideal tool to document and modify code. To install nbdev use `pip install nbdev` and then install the git hooks in the folder where your GitHub repository is cloned (`nbdev_install_git_hooks`). The key commands for nbdev are: 
* `nbdev_build_lib`: build the library from the notebooks
* `nbdev_test_nbs`: test all notebooks
* `nbdev_clean_nbs`: clean the notebooks (strip from unnecessary metadata)


### Testing

In order to make AlphaPept a sustainable package, it is imperative that all functions have tests. This is not only to ensure the proper execution of the function but also for the long run when wanting to keep up-to-date with package updates. For tracking package updates, we rely on [dependabot](https://dependabot.com). For continuous integration, we use GitHub Actions.

##### Unit tests

Within the nbdev notebooks, we try to write small tests for each function. They should be lightweight so that running (and hence testing) the notebooks should not take too long. Each test is defined as `test_function` and then that function is called with `test_function()` in a cell and not exported to the codebase. If, at a later stage, we want to switch to pytest or abandon nbdev this would alleviate reorganizing the code to a test folder.

##### Integration and performance tests (in progress)

A complete run of a proteomics pipeline is computationally intensive and requires large files that exceed the typical workflow in a GitHub Actions runner. For this, we use self-hosted [runners](https://docs.github.com/en/actions/hosting-your-own-runners/about-self-hosted-runners). Likewise, we aim to benchmark every release of AlphaPept and automatically run each release on a number of test sets.

### Numba - first

We heavily rely on the [Numba](http://numba.pydata.org) package for efficient computation. As writing classes in numba with `@jitclass` requires type specification, in most cases, we prefer functional programming over
Object-oriented programming for simplicity. Here, adding the decorator `@njit` is mostly enough. Numba also allows alleviates transfering code to GPU.

### Parallelization strategies

Python has some powerful parallelization tools, such as the `multiprocessing` library. `Numba` allows loops to be executed in parallel when flagging with `prange`, which is, from a syntactic point of view, a very elegant solution to parallel processing. It comes with the downside that we cannot easily track the progress of parallel functions that use `prange`. We, therefore, chunk data where possible to be able to have a progress bar. Additionally, currently, it is not possible to set the number of cores that should be used.

From a data analysis point of view, there are several considerations to be taken into account: When processing multiple files in parallel, it would be suitable to launch several processes in parallel, where the multiprocessing library would come in handy. On the other hand, when only wanting to investigate a single file, having the individual functions parallelized would be beneficial.

Hence, the core idea is to write fast single-core functions and also have parallelized versions where applicable. When processing a large number of files, we are relying on the `multiprocessing` module.

### Constants 

One good way to handle constants would be to use globals. However, numba is not able to use typed dictionaries/classes as globals. We therefore pass them as variables (such as the mass_dict), which in some cases leads to functions with a lot of arguments. Note that `numba` is not able to handle `kwargs` and `args` at this point.

### Callbacks

As AlphaPept is intended to be the backend of a tool with GUI, we ideally want to be able to get a progress bar out of the major functions. For this, we can pass a `callback`-argument to the major functions. If the argument is passed, it will return the current progress in the range from 0 to 1.

### Version bumping

We are using the python package [`bump2version`](https://github.com/c4urself/bump2version). You can use this to bump the version number. Currently specified is: `bump2version`: (`major`, `minor`, `patch`):

* e.g.: `bump2version patch` for a patch


### Data flow

Having access to intermediate results is very beneficial if individual modules need to be optimized. To achieve this, we rely on *.hdf containers and save intermediate results here. For each file that gets processed, we create a *.hdf file with the same name and add the results of each processing step as groups in the container.


### Imports
TODO: Write about how imports need to be made so that they work with the installer.

Include in manifest -> 
