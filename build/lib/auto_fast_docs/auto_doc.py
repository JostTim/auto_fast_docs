# -*- coding: utf-8 -*-
"""
Created on Wed Mar 15 15:18:03 2023

@author: tjostmou
"""

from dataclasses import dataclass
import os
import argparse
import logging
import ast
import subprocess
from sys import stdout
from datetime import datetime
from typing import Any

from . discover import find_python_files

_EXCLUDE_BALISES = {
    "exclude_module": "EXCLUDE_MODULE_FROM_MKDOCSTRINGS",
    "exclude_callable": "EXCLUDE_CALLABLE_FROM_MKDOCSTRINGS",
}

# Options list are available here : https://mkdocstrings.github.io/python/usage/#globallocal-options

_FUNCTION_OPTIONS = """
    handler: python
    options:
      show_root_heading: true
      show_root_full_path : false
      show_object_full_path : true
      show_category_heading : false
      separate_signature : true
      heading_level : 1"""

_CLASS_OPTIONS = """
    handler: python
    options:
      show_root_heading: true
      show_root_full_path : false
      show_root_members_full_path : false
      show_object_full_path : true
      show_category_heading : true
      show_if_no_docstring : true
      merge_init_into_class : true
      separate_signature : true
      heading_level : 1"""

LOGGER = logging.getLogger()
handler = logging.StreamHandler(stdout)
formatter = logging.Formatter(' %(levelname)-8s : %(message)s')
handler.setFormatter(formatter)
LOGGER.setLevel(logging.DEBUG)
LOGGER.addHandler(handler)

unix_join = os.path.join


class PyfileParser(ast.NodeVisitor):
    """
    Attributes:
        modulename str:
            the name of the module without the .py extension
        content dict:
            a dictionnary with two keys : `functions` and `classes`,
            each of wich containing a list of the classes and functions in the module
            with the format : "module.fooclass" or "module.foofunction".
            ``content`` doesn't registers classes internal functions.
    """

    def __init__(self, path):
        """
        Constructor method of the class.
        Args:
            path (str): The full path to a python file that has been parsed.
        Returns:
            mkds_pyfile_parser : An instance of this class.
        """
        # track context name and set of names marked as `global`
        self.path = path
        self.modulename = os.path.splitext(os.path.split(self.path)[1])[0]
        self.context = [self.modulename]
        self.content = {"functions": [], "classes": []}

    def is_empty(self):
        """
        Returns:
            bool: DESCRIPTION.
        """
        if len(self.content["functions"]) == 0 and len(self.content["classes"]) == 0:
            return True
        return False

    def check_exclusion(self, node, exclusion_context):
        node_doctring = ast.get_docstring(node)
        if node_doctring is not None and "<" + _EXCLUDE_BALISES[exclusion_context] + ">" in node_doctring:
            # hashtags are added around the balise to make this able to see this file even thought it contains
            # the balise in it's text.
            # Note : not usefull anymore as we check only the presence of the balises
            # inside doctrings and not inside code.
            # Let's keept this feature anyway to prevent any unexpected behavior trouble.
            # TODO : unclear comment and behaviour
            return True
        return False

    def aggreg_context(self):
        aggregator = []
        for item in self.context:
            aggregator.append(item)
            aggregator.append(".")
        aggregator.pop()
        agg = ''.join(aggregator)
        return agg

    def visit_FunctionDef(self, node) -> Any:
        self.context.append(node.name)
        if len(self.context) == 2 and not self.check_exclusion(node, "exclude_callable"):
            # len(context) == 2 when we are inside module, and function.
            # If we are inside module, class, function we are == 3.
            # And we don't want to register class functions.
            self.content["functions"].append(self.aggreg_context())
        self.generic_visit(node)
        self.context.pop()

    # treat coroutines the same way
    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node):
        self.context.append(node.name)
        if not self.check_exclusion(node, "exclude_callable"):
            self.content["classes"].append(self.aggreg_context())
        self.generic_visit(node)
        self.context.pop()

    def visit_Lambda(self, node):
        # lambdas are just functions, albeit with no statements, so no assignments.
        # As they have no name though, they won't be documented
        self.generic_visit(node)

    def visit_Module(self, node):
        if self.check_exclusion(node, "exclude_module"):
            return None
        self.generic_visit(node)

    def visit(self, generic_arg=None):
        """
        Takes as argument the output of ast.parse().
        Itself takes as argument the str returned by reading a whole ``.py`` file.
        This method is the way we visit every node of the file and on the way,
        we register the classes and functions names.
        Returns:
            NoneType : Returns None. Use to be able to fill ``content`` with the classes and methods of the file.
        Example:
            ```python
            parser = mkds_pyfile_parser(filepath)
            parser.visit()
            print(parser.content)
            ```
        Tip:
            To explude functions/classes from being returned and lead to the creation of a mkdoctrings entry,
            use the balise :
            ``EXCLUDE_FUNC_OR_CLASS_FROM_MKDOCSTRINGS``
            anywhere in the doctring of your function/class.
            In the same way, a whole module can be excluded by including the balise
            <``EXCLUDE_MODULE_FROM_MKDOCSTRINGS``> (with angle brackets)
            anywhere in the boilerplate at the top of your module.
        """
        if generic_arg is None:
            # This case is entered when a user externally calls visit with no argument.
            with open(self.path, "r") as pyf:
                parsed_data = ast.parse(pyf.read())
            return super().visit(parsed_data)
        else:
            # This case is required when visit is called internally, by the super class ast.NodeVisitor.generic_visit(),
            #  with one argument.
            # In that case, we just call the parent implementation of visit and return it's result transparently
            # to not affect the class's behaviour.
            return super().visit(generic_arg)


def mkds_markdownfile_content(item_name: str, item_type: str) -> str:
    content = []
    content.append("::: " + item_name)

    if item_type == "functions":
        content.append(_FUNCTION_OPTIONS)

    if item_type == "classes":
        content.append(_CLASS_OPTIONS)

    return ''.join(content)


class RepositoryConfigurator:

    def __init__(self, args):
        self.set_package_name(args.package_name)
        self.set_cwd(args.current_path)
        self.set_layout_type(args.layout)
        self.set_username(args.username)
        self.set_git_platform(args.platform)
        self.set_platform_groups(args.groups)

        self.update_package_path()
        self.update_package_url()
        self.update_static_doc_url()
        self.update_doc_path()

        LOGGER.info(f"Working path is :{self.cwd}")
        LOGGER.info(f"Package layout style :{self.layout_type}")
        LOGGER.info(
            f"Package is expected to be located at :{self.package_path}")

    def run(self):
        LOGGER.info("Building with auto-doc :")
        self.auto_configure_mkdocs()
        nav_dic = self.make_markdown_files()
        self.write_mkdocs_nav(nav_dic)

    def set_cwd(self, path):
        self.cwd = path

    def set_package_name(self, name):
        self.package_name = name

    def set_layout_type(self, layout):
        self.layout_type = layout

    def set_username(self, username):
        self.username = username

    def set_git_platform(self, git_platform: str):
        parameters = git_platform.split(":")
        # parameters should be : "github" or "gitlab:pasteur.fr"
        self.git_platform = parameters[0]
        if len(parameters) == 2:
            self.git_address = parameters[1]
        else:
            self.git_address = "com"

    def set_platform_groups(self, groups: str):
        groups_list = groups.split("/")

        if groups_list == ['']:
            self.platform_group = ""
            self.platform_sub_groups = []
            return

        self.platform_group = groups_list[0]
        if len(groups_list) == 1:
            self.platform_sub_groups = []
        else:
            self.platform_sub_groups = groups_list[1:]

    def update_package_path(self):
        local_path = os.path.join(
            "src", self.package_name) if self.layout_type == "src" else self.package_name
        self.package_path = os.path.join(self.cwd, local_path)

    def update_package_url(self):
        if self.username is None:
            self.package_url = None
            return

        if self.platform_group:
            path = "/".join([self.platform_group] +
                            self.platform_sub_groups + [self.package_name])
        else:
            path = "/".join([self.username] + [self.package_name])

        self.package_url = f"https://{self.git_platform}.{self.git_address}/{path}"

        # examples :
        # "https://github.com/FreelyMovingSetup/Documentation_center"
        # "https://github.com/josttim/Inflow"

        # "https://gitlab.pasteur.fr/haisslab/analysis-packages/Inflow"
        # "https://gitlab.pasteur.fr/tjostmou/Inflow"

    def update_doc_path(self):
        self.docpath = os.path.join(self.cwd, "docs")
        os.makedirs(self.docpath, exist_ok=True)
        index_file_path = os.path.join(self.docpath, "index.md")
        if not os.path.isfile(index_file_path):
            with open(index_file_path, "w") as f:
                f.write(f"# {self.package_name}\n\n")
                f.write(f"{self.package_name} source code documentation.\n")

    def update_static_doc_url(self):
        if self.username is None:
            self.static_doc_url = None
            return

        if self.platform_group:
            prefix = self.platform_group
        else:
            prefix = self.username

        if self.git_platform == "github":
            suffix = "github.io"
        elif self.git_platform == "gitlab":
            if self.git_address == "com":
                suffix = "gitlab.io"
            else:
                suffix = f"pages.{self.git_address}"
        else:
            raise NotImplementedError(
                f"Value for git_platform can oly be github of gitlab. Got {self.git_platform}")

        path = "/".join(self.platform_sub_groups + [self.package_name])

        self.static_doc_url = f"https://{prefix}.{suffix}/{path}"

        # examples :
        # "https://freelymovingsetup.github.io/Documentation_center/"
        # 'https://josttim.github.io/pLabUtils/'

        # "https://haisslab.pages.pasteur.fr/analysis-packages/Inflow/"
        # "https://josttim.pages.pasteur.fr/analysis-packages/Inflow/"

    def auto_configure_mkdocs(self):
        mkd_conf = MkdocsConfigurator(os.path.join(self.cwd, "mkdocs.yml"))
        if mkd_conf.skip_config():
            return

        LOGGER.info(
            "No mkdocs file is present in package. Auto generating one")
        mkd_conf.add_line(f"site_name: {self.package_name}")
        if self.username is not None:
            mkd_conf.add_line(f"site_author: '{self.username}'")
            mkd_conf.add_line(
                f"copyright: '{datetime.now().strftime('%Y')} - {self.username}'")
        if self.static_doc_url is not None:
            mkd_conf.add_line(f"site_url: '{self.static_doc_url}'")
        if self.package_url is not None:
            mkd_conf.add_line(f"repo_url: '{self.package_url}'")

        mkd_conf.add_lines_from_template()
        mkd_conf.write_file()

    def write_mkdocs_nav(self, nav_dic: dict) -> None:
        def _entry_level(level: int, entry_name: str, entry_value: str | None = None) -> str:
            line = "    " * (level + 1) + "- "
            # add quotes
            line += _quoting(entry_name) if entry_value is not None else entry_name
            line += ": "
            if entry_value is not None:
                line += _quoting(entry_value)
            return line + _eol()

        def _quoting(name: str) -> str:
            return "'" + name + "'"

        def _eol() -> str:
            return "\n"

        def recursive_writer(dico, depth):
            nonlocal fo
            for key, value in dico.items():
                if hasattr(value, "items"):
                    line = _entry_level(depth, key)
                    fo.write(line)
                    recursive_writer(value, depth + 1)
                else:
                    line = _entry_level(depth, key, value)
                    fo.write(line)

        filepath = os.path.join(self.cwd, "mkdocs.yml")
        original_content = []

        with open(filepath, "r") as fi:
            for line in fi.readlines():
                original_content.append(line)
                if "-home:index.md" in line.lower().replace(" ", ""):
                    break

        with open(filepath, "w") as fo:
            for line in original_content:
                fo.write(line)
            recursive_writer(nav_dic, depth=0)

    def make_markdown_files(self):

        def _create_layer(layer, reference):
            if layer in reference.keys():
                return
            reference[layer] = {}

        def _create_layers(layers):
            nonlocal nav_dic
            reference = nav_dic
            for layer in layers:
                _create_layer(layer, reference)
                reference = reference[layer]

        def _select_layer(layers):
            nonlocal nav_dic
            reference = nav_dic
            for layer in layers:
                reference = reference[layer]
            return reference

        matched_py_files = find_python_files(self.package_path)
        matched_files_digest = ' ,\n\t- '.join(matched_py_files)
        LOGGER.info(f"Discovered python files :\n\t - {matched_files_digest}")
        LOGGER.info("Making markdown files")

        nav_dic = {}
        for filepath in matched_py_files:

            file_name = os.path.splitext(os.path.basename(filepath))[0]
            if file_name in ["auto-doc", "__init__"]:
                continue

            parser = PyfileParser(
                os.path.join(self.package_path, filepath))
            parser.visit()
            if parser.is_empty():
                continue

            directories = os.path.dirname(filepath)

            if directories == '':
                directories = []
            else:
                directories = directories.split(os.sep)

            directories += [file_name]

            file_root_path = unix_join(self.docpath, *directories)
            os.makedirs(file_root_path, exist_ok=True)

            _create_layers(directories)

            nav_sublayer = _select_layer(directories)

            for func_type in ["classes", "functions"]:
                for func_item in parser.content[func_type]:

                    func_name = func_item.split(".")[1]
                    func_markdown_file = f'{func_name}.md'
                    nav_sublayer[func_name] = unix_join(
                        *directories, func_markdown_file)

                    function_docfile_name = unix_join(
                        file_root_path, func_markdown_file)

                    if os.path.isfile(function_docfile_name):
                        LOGGER.warning(
                            f"doc file {function_docfile_name} has been overwritten")

                    module_location = ".".join(
                        [self.package_name] + directories + [func_name])

                    with open(function_docfile_name, "w") as mof:
                        mof.write(mkds_markdownfile_content(
                            module_location, func_type))

        return nav_dic


@dataclass
class MkdocsConfigurator:
    file_path: str
    content = ""

    def add_line(self, line):
        self.content += (line + "\n")

    def add_lines_from_template(self):
        template_path = os.path.join(os.path.dirname(
            __file__), "mkdocs_template.yml")
        with open(template_path, "r") as f:
            content = f.read()

        self.content += (content + "\n")

    def skip_config(self) -> bool:
        if os.path.isfile(self.file_path):
            return True
        return False

    def write_file(self):
        with open(self.file_path, 'w') as f:
            f.write(self.content)


parser = argparse.ArgumentParser(
    description='Automatic markdown documentation mkdocstrings formated files generator',
)
parser.add_argument("package_name",
                    help="Name of the packaged sources folder")
parser.add_argument("current_path",
                    default=os.getcwd(),
                    nargs="?",
                    help="local path used througout the program to generate the doc files. by default,"
                    "it's the current working directory")
parser.add_argument('-l',
                    "--layout",
                    default="flat",
                    help="Layout style for the source code to document, default is 'flat' and optionnal is src",
                    )
parser.add_argument('-u',
                    "--username",
                    default=None,
                    help="Name of the user to wich the repo belongs to."
                    "Used to automatically determine things for auto mkdocs config."
                    )
parser.add_argument('-p',
                    "--platform",
                    default="github",
                    help="Platform on wich auto_doc is ran in CI/CD container. Supports github and gitlab, "
                    "and is used to automatically determine the url of the published "
                    "static documentation site homepage."
                    )
parser.add_argument('-g',
                    "--groups",
                    default="",
                    help="Groups (on gitlab) or organisation (on hithub) on wich the repo is located. "
                    "Use / to separate groups if multiple are present (gitlab only)"
                    )


def console_mkds_make_docfiles():
    """Calls the auto-doc program on a code repository.

    Args:
        see argparse.ArgumentParser.
        This function is not meant to be called internally in python but through CLI.
    """
    LOGGER.info("RUNNING AUTO-DOC.py")

    args = parser.parse_args()

    configurator = RepositoryConfigurator(args)
    configurator.run()

    subprocess.run("mkdocs build --verbose")


if __name__ == "__main__":
    console_mkds_make_docfiles()
