# auto-doc
A single file auto documentation builder made to be interfaced with mkdocstrings, and ran in containerized CI/CD

Drop it on top level of your package. Requires wrapped package structure like so :

- :: PackageRepo
  - /Package
    - __init__.py
    - myfile.py
    - /mysubpackage
      - __init__.py
      - myfile2.py
  - setup.py
  - auto-doc.py
  - mkdocs.yml
  - /docs
    - index.md
    
Then, inside the top wrapping folder, PackageRepo, you can call `auto-docs.py` like this :
```
python auto-docs.py Package
```
It requires a single command line argument that tells it what is the folder that contains the python source files in your wrapping folder.   

That's all !
