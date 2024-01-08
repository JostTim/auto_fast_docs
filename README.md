[![Upload Python Package](https://github.com/JostTim/auto_fast_docs/actions/workflows/python-publish.yml/badge.svg?branch=main)](https://github.com/JostTim/auto_fast_docs/actions/workflows/python-publish.yml)
[![Deploy](https://github.com/JostTim/auto_fast_docs/actions/workflows/ci-cd.yml/badge.svg?branch=main)](https://github.com/JostTim/auto_fast_docs/actions/workflows/ci-cd.yml)

# Automatic documentation for your python repository. 
With fast setup and no extra effort.
This package is designed to be ran in containerized CI/CD.

It's purpose is quite simple : 
leveraging mkdocs, mkdocs-material and mkdocstrings, and scanning your repository's pyhton source files.  
When it finds a function or class, it groups it nicely, and generates folders and markdown files with the appropriate mkdocstrings headers, inside a `docs` folder, used for the static website generation on github or gitlab pages.

This folder will not appear in your repo if you run this package in a github/gitlab  CI/CD container, but will still exist at container runtime to generate and publish the website.

## Usage 

Drop it on top level of your package wrapper folder, and add two lines in your github/gitlab [ci/cd file](https://github.com/JostTim/auto_fast_docs/blob/main/.github/workflows/ci-cd.yml) : (click the link to see a working example, that built [this present repo's documentation page](https://josttim.github.io/auto_fast_docs/))

```bash
pip install auto_fast_docs
auto_fast_docs MyPackage
```

**I strongly recommand giving it your username so that it can also build an mkdocs.yml file by itself !**

```bash
pip install auto_fast_docs
auto_fast_docs MyPackage --username MyGtihubUsername
```

## Check the result

[Here is an example of the result](https://josttim.github.io/auto_fast_docs/) (and also a documentation for this repo's code)

## Install

Pypi releases : https://pypi.org/project/auto-fast-docs/

```bash
pip install auto_fast_docs
```

or most recent commit from github :

```bash
pip install git+https://github.com/JostTim/auto_fast_docs.git
```

## Options :

It supports a few options to simplify your dev life even more and be platform a-specific: 

All options are case insensitive

### --username
Name of the user that owns the repository.
If it is supplied and no ``mkdocs.yml`` file is present in the repo, auto_fast_doc will attempt to fill in the information automatically. If you don't supply this info, it will not generate the mkocs.yml file by itself.
```bash
auto_fast_docs MyPackage --username MyUsername 
```

### --layout
Flat or src layout style of your code in the repository. By default, `layout="flat"`

```bash
auto_fast_docs MyPackage --layout src 
```

The flat layout structure is standardized like this :

> - :open_file_folder: PackageRepo
>   - :page_facing_up: setup.py
>   - :page_facing_up: pyproject.toml
>   - :page_facing_up: mkdocs.yml
>   - :open_file_folder: docs
>     - :page_facing_up: index.md
>   - :open_file_folder: Package
>     - :page_facing_up: \_\_init__.py
>     - :page_facing_up: myfile.py
>     - :open_file_folder: mysubpackage
>       - :page_facing_up: \_\_init__.py
>       - :page_facing_up: myfile2.py
    
While the src layout is standardized like this :

> - :open_file_folder: PackageRepo
>   - :page_facing_up: setup.py
>   - :page_facing_up: pyproject.toml
>   - :page_facing_up: mkdocs.yml
>   - :open_file_folder: docs
>     - :page_facing_up: index.md
>   - :open_file_folder: src
>     - :open_file_folder: Package
>       - :page_facing_up: \_\_init__.py
>       - :page_facing_up: myfile.py
>       - :open_file_folder: mysubpackage
>         - :page_facing_up: \_\_init__.py
>         - :page_facing_up: myfile2.py

Note that auto_fast_docs doesn't care about ``pyproject.toml`` or ``setup.py``, any can be used.
Also note that the docs folder, and the mkdocs.yml file here are both also not necessary, if you supply at least the ``--username`` option (see above)  
(and of course, if you are on github on a user hosted repo. Otherwise, see ``--platform`` and ``--groups`` options below)

### --platform
The platform (``github`` or ``gitlab``) on wich you are building the pages into.
The default is ``github``

```bash
auto_fast_docs MyPackage --platform gitlab 
```

Note that in the case of gitlab, if you are not on the central gitlab.com repository but on a instance hosted by a compagny, you can supply the suffix after gitlab, separated with a semicolon ``:``

```bash
auto_fast_docs MyPackage --platform gitlab:pasteur.fr
```

By default, if nothing is supplied with a semicolon after the platform name, the suffix is set to `com` (giving out github.com and gitlab.com)

### --groups
If your repository is not in your own package, you must supply the group name.(that's the organization name on github)

```bash
auto_fast_docs MyPackage --platform gitlab:pasteur.fr --groups mymaingroup/mysubgroup 
```

Note that if group is used, it is still necessary to supply the username - even thoug it is not used for the repository path assembly - if you want the ``mkdocs.yml`` file to be generated.

In the case of gitlab, an arbitrary number of groups can be nested (while github doesn't allow nested organizations). Simmply separate them using forward slashes `/` and auto_fast_docs should manage to assemble the final path by itself, depending on your platform.

_____

## Small note :
On github, you will also need :
- to allow Read and write permissions for workflow in your repo settings, under  
  ``settings > actions > general > Workflow permissions``
- to set the pages deployments branch to gh-pages, under :  
  ``settings > pages > Build and deployment > Source`` to `deploy from a branch` and  
  ``settings > pages > Build and deployment >  Branch`` to your `gh-pages` branch  
  (this branch will appear after the first sucessfull mkocs build, except if you created it yourself.)

