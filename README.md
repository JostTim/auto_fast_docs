[![Upload Python Package](https://github.com/JostTim/auto_fast_docs/actions/workflows/python-publish.yml/badge.svg?branch=main)](https://github.com/JostTim/auto_fast_docs/actions/workflows/python-publish.yml)
[![Deploy](https://github.com/JostTim/auto_fast_docs/actions/workflows/ci-cd.yml/badge.svg?branch=main)](https://github.com/JostTim/auto_fast_docs/actions/workflows/ci-cd.yml)

# Auto-Doc
A single file auto documentation builder made to be interfaced with mkdocstrings, and ran in containerized CI/CD

## Usage 

Drop it on top level of your package wrapper folder.
It requires a setup.py wrapped package structure like so :

> - :open_file_folder: PackageRepo
>   - :page_facing_up: setup.py
>   - :page_facing_up: auto-doc.py
>   - :page_facing_up: mkdocs.yml
>   - :open_file_folder: docs
>     - :page_facing_up: index.md
>   - :open_file_folder: Package
>     - :page_facing_up: \_\_init__.py
>     - :page_facing_up: myfile.py
>     - :open_file_folder: mysubpackage
>       - :page_facing_up: \_\_init__.py
>       - :page_facing_up: myfile2.py
    
Then, inside the top wrapping folder, PackageRepo, you can call `auto-docs.py` like this :
```bash
python auto-docs.py Package
```
It requires a single command line argument that tells it what is the folder that contains the python source files in your wrapping folder.   

That's all !
_____

**Small note :**  
On github, you will also need :
- to allow Read and write permissions for workflow in your repo settings, under  
  ``settings > actions > general > Workflow permissions``
- to set the pages deployments branch to gh-pages, under :  
  ``settings > pages > Build and deployment > Source`` to `deploy from a branch` and  
  ``settings > pages > Build and deployment >  Branch`` to your `gh-pages` branch  
  (this branch will appear after the first sucessfull mkocs build, except if you created it yourself.)

## Check the result

[Here is an example of the result](https://josttim.github.io/auto_fast_docs/) (and also a documentation for this repo's code)

## Install

Install from Pypi : https://pypi.org/project/auto-fast-docs/

```bash
pip install auto_fast_docs
```