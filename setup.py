import sys
import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.md')).read()

setup(name='auto_doc',
      version='1.0.0',
      description='',
      long_description=README,
      author='Timothe Jost-Mousseau',
      author_email='timothe.jost-mousseau@pasteur.fr',
      url='https://github.com/JostTim/auto-doc/',
      packages=find_packages(),
      license='',
      classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        ],
      entry_points={
        'console_scripts': ['auto_doc= auto_doc:console_mkds_make_docfiles'],
       },
      scripts={},
     )
