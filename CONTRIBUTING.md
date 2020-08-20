# How to contribute

Contributions are welcome, and they are greatly appreciated! Every
little bit helps, and credit will always be given.

You can contribute in many ways:

## Report Bugs

Report bugs at https://github.com/MannLabs/alphapept/issues.

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

## Fix Bugs

Look through the GitHub issues for bugs. Anything tagged with "bug"
and "help wanted" is open to whoever wants to implement it.

## Implement Features

Look through the GitHub issues for features. Anything tagged with "enhancement"
and "help wanted" is open to whoever wants to implement it.

## Write Documentation

AlphaPept could always use more documentation, whether as part of the
official AlphaPept documentation, in docstrings, or even on the web in blog posts,
articles, and such.

## Submit Feedback

The best way to send feedback is to file an issue at https://github.com/MannLabs/alphapept/issues.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions
  are welcome :)

## Get Started!

Ready to contribute? Here's how to set up `alphapept` for local development.

1. Fork the `alphapept` repo on GitHub.
2. Clone your fork locally:

    $ git clone git@github.com:your_name_here/alphapept.git

3. Follow the installation instructions in the readme to install a alphapept environment.

4. Create a branch for local development::

    $ git checkout -b name-of-your-bugfix-or-feature

   Now you can make your changes locally.

5. See below in the Notes for Programmers about how to use the nbdev environment.

6. Commit your changes and push your branch to GitHub::

    $ git add .
    $ git commit -m "Your detailed description of your changes."
    $ git push origin name-of-your-bugfix-or-feature

7. Submit a pull request through the GitHub website.

## Notes for Programmers

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


## PR submission guidelines

* Keep each PR focused. While it's more convenient, do not combine several unrelated fixes together. Create as many branches as needing to keep each PR focused.
* Do not mix style changes/fixes with "functional" changes. It's very difficult to review such PRs and it most likely get rejected.
* Do not add/remove vertical whitespace. Preserve the original style of the file you edit as much as you can.
* Do not turn an already submitted PR into your development playground. If after you submitted PR, you discovered that more work is needed - close the PR, do the required work and then submit a new PR. Otherwise each of your commits requires attention from maintainers of the project.
* If, however, you submitted a PR and received a request for changes, you should proceed with commits inside that PR, so that the maintainer can see the incremental fixes and won't need to review the whole PR again. In the exception case where you realize it'll take many many commits to complete the requests, then it's probably best to close the PR, do the work and then submit it again. Use common sense where you'd choose one way over another.
