# Auto-Doc
A single file auto documentation builder made to be interfaced with mkdocstrings, and ran in containerized CI/CD

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
