# -*- coding: utf-8 -*-
"""
Created on Wed Mar 15 15:18:03 2023

@author: tjostmou
"""

import os, sys
import logging
import ast

_EXCLUDE_BALISES = {
    "exclude_module":"EXCLUDE_MODULE_FROM_MKDOCSTRINGS",
    "exclude_callable":"EXCLUDE_CALLABLE_FROM_MKDOCSTRINGS",
    }

#Options list are available here : https://mkdocstrings.github.io/python/usage/#globallocal-options

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

import re
try : 
    import natsort
except :
    pass

LOGGER = logging.getLogger()
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(' %(levelname)-8s : %(message)s')
handler.setFormatter(formatter)
LOGGER.setLevel(logging.DEBUG)
LOGGER.addHandler(handler)

def unix_join(*args, **kwargs):
    return os.path.join(*args, **kwargs).replace(os.sep,'/')

def qregexp(regex, input_line, groupidx=None, matchid=None , case=False):
    """
    Simplified implementation for matching regular expressions. Utility for python's built_in module re .

    Tip:
        Design your patterns easily at [Regex101](https://regex101.com/)

    Args:
        input_line (str): Source on wich the pattern will be searched.
        regex (str): Regex pattern to match on the source.
        **kwargs (optional):
            - groupidx : (``int``)
                group index in case there is groups. Defaults to None (first group returned)
            - matchid : (``int``)
                match index in case there is multiple matchs. Defaults to None (first match returned)
            - case : (``bool``)
                `False` / `True` : case sensitive regexp matching (default ``False``)

    Returns:
        Bool , str: False or string containing matched content.

    Warning:
        This function returns only one group/match.

    """

    if case :
        matches = re.finditer(regex, input_line, re.MULTILINE|re.IGNORECASE)
    else :
        matches = re.finditer(regex, input_line, re.MULTILINE)

    if matchid is not None :
        matchid = matchid +1

    for matchnum, match in enumerate(matches,  start = 1):

        if matchid is not None :
            if matchnum == matchid :
                if groupidx is not None :
                    for groupx, groupcontent in enumerate(match.groups()):
                        if groupx == groupidx :
                            return groupcontent
                    return False

                else :
                    MATCH = match.group()
                    return MATCH

        else :
            if groupidx is not None :
                for groupx, groupcontent in enumerate(match.groups()):
                    if groupx == groupidx :
                        return groupcontent
                return False
            else :
                MATCH = match.group()
                return MATCH
    return False

def relative_path(absolute_path, common_root_path):
    """
    Compare an input path and a path with a common root with the input path, and returns only the part of the input path that is not shared with the _common_root_path.

    Args:
        input_path (TYPE): DESCRIPTION.
        common_root_base (TYPE): DESCRIPTION.

    Returns:
        TYPE: DESCRIPTION.

    """
    absolute_path = os.path.normpath(absolute_path)
    common_root_path = os.path.normpath(common_root_path)
    
    commonprefix = os.path.commonprefix([common_root_path,absolute_path])
    if commonprefix == '':
        raise IOError(f"These two pathes have no common root path : {absolute_path} and {common_root_path}")
    return os.path.relpath(absolute_path, start = commonprefix )

def find_files(input_path, re_pattern = None, relative = False,levels = -1, get = "files", parts = "all", sort = True):
    """
    Get full path of files from all folders under the ``input_path`` (including itself).
    Can return specific files with optionnal conditions 
    Args:
        input_path (str): A valid path to a folder. 
            This folder is used as the root to return files found 
            (possible condition selection by giving to re_callback a function taking a regexp pattern and a string as argument, an returning a boolean).
    Returns:
        list: List of the file fullpaths found under ``input_path`` folder and subfolders.
    """
    #if levels = -1, we get  everything whatever the depth (at least up to 32767 subfolders, but this should be fine...)

    if levels == -1 :
        levels = 32767
    current_level = 0
    output_list = []
    
    def _recursive_search(_input_path):
        nonlocal current_level
        for subdir in os.listdir(_input_path):
            fullpath = unix_join(_input_path,subdir)
            if os.path.isfile(fullpath): 
                if (get == "all" or get == "files") and (re_pattern is None or qregexp(re_pattern,fullpath)):
                    output_list.append(os.path.normpath(fullpath))
                    
            else :
                if (get == "all" or get == "dirs" or get == "folders") and (re_pattern is None or qregexp(re_pattern,fullpath)):
                    output_list.append(os.path.normpath(fullpath))
                if current_level < levels:
                    current_level += 1 
                    _recursive_search(fullpath)
        current_level -= 1
        
    if os.path.isfile(input_path):
        raise ValueError(f"Can only list files in a directory. A file was given : {input_path}")
 
    _recursive_search(input_path)
    
    if relative :
        output_list = [os.path.relpath(file,start = input_path) for file in output_list]
    if parts == "name" :
        output_list = [os.path.basename(file) for file in output_list]
    if sort :
        try :
            output_list = natsort.natsorted(output_list)
        except :
            pass
    return output_list

class mkds_pyfile_parser(ast.NodeVisitor):
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
        self.content = {"functions":[],"classes":[]}

    def is_empty(self):
        """
        Returns:
            bool: DESCRIPTION.
        """
        if len(self.content["functions"]) == 0 and len(self.content["classes"]) == 0 :
            return True
        return False

    def check_exclusion(self,node,exclusion_context):
        node_doctring = ast.get_docstring(node)
        if node_doctring is not None and "<" + _EXCLUDE_BALISES[exclusion_context] + ">" in node_doctring :
            # hashtags are added around the balise to make this able to see this file even thou it contains the balise in it's text.
            # Note : not usefull anymore as we check only the presence of the balises inside doctrings and not inside code.
            # Let's keept this feature anyway to prevent any unexpected behavior trouble.
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

    def visit_FunctionDef(self, node):
        self.context.append(node.name)
        if len(self.context) == 2 and not self.check_exclusion(node,"exclude_callable"):
            #len(context) == 2 when we are inside module, and function. If we are inside module, class, function , we are == 3. And we don't want to register class functions.
            self.content["functions"].append(self.aggreg_context())
        self.generic_visit(node)
        self.context.pop()

    # treat coroutines the same way
    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node):
        self.context.append(node.name)
        if not self.check_exclusion(node,"exclude_callable"):
            self.content["classes"].append(self.aggreg_context())
        self.generic_visit(node)
        self.context.pop()

    def visit_Lambda(self, node):
        # lambdas are just functions, albeit with no statements, so no assignments.
        # As they have no name though, they won't be documented
        self.generic_visit(node)

    def visit_Module(self, node):
        if self.check_exclusion(node,"exclude_module"):
            return None
        self.generic_visit(node)

    def visit(self,generic_arg=None):
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
            To explude functions/classes from being returned and lead to the creation of a mkdoctrings entry, use the balise :
            ``EXCLUDE_FUNC_OR_CLASS_FROM_MKDOCSTRINGS`` anywhere in the doctring of your function/class.
            In the same way, a whole module can be excluded by including the balise
            <``EXCLUDE_MODULE_FROM_MKDOCSTRINGS``> (with angle brackets) anywhere in the boilerplate at the top of your module.
        """
        if generic_arg is None :
            #This case is entered when a user externally calls visit with no argument.
            with open(self.path,"r") as pyf:
                parsed_data = ast.parse(pyf.read())
            return super().visit(parsed_data)
        else :
            #This case is required when visit is called internally, by the super class ast.NodeVisitor.generic_visit(), with one argument.
            #In that case, we just call the parent implementation of visit and return it's result transparently to not affect the class's behaviour.
            return super().visit(generic_arg)


class mkds_markdown_indexfile():
    """TODO : make this class so we can add modules, their top doctring and their
    child classes and function as list in a summary inside index.md in the doc folder or any project.
    Also : add balises <div id = "contributors"> </div> around the boilerplate
    'Created on Wed Aug 25 10:40:20 2021 @author: Timothe' to avoid putting it everywhere in the doc.
    Add a balise to skip a part of the doctring <div id = "exclude_part_from_mkds"> </div>
    Add a balise to skip the entire doctring <div id = "exclude_boilerplate_from_mkds">
    Add a balise to specify the position of the content_index. <div id = "content_index">
    Add links between summary items and their .md pages
    """
    def __init__(self,path):
        pass



def mkds_mod_mkdocs_yml_archi(path : str,appendings : dict) -> None:
    def _entry_level(level : int, entry_name : str, entry_value : str = None ) -> str :
        line =  "    "*(level+1) + "- "
        line += _quoting(entry_name) if entry_value is not None else entry_name #add quotes
        line += ": "
        if entry_value is not None :
            line += _quoting(entry_value)
        return line + _eol()
    
    def _quoting(name : str) -> str:
        return "'" + name + "'"

    def _eol() -> str:
        return "\n"
    
    def recursive_writer(dico, depth):
        nonlocal fo
        for key, value in dico.items():
            if hasattr(value,"items"):
                line = _entry_level(depth,key)
                fo.write(line)
                recursive_writer(value,depth + 1)
            else :
                line = _entry_level(depth,key,value)
                fo.write(line)
    
    
    filepath = unix_join(path,"mkdocs.yml")
    original_content = []
    
    with open(filepath,"r") as fi :
        for line in fi.readlines():
            original_content.append(line)
            if "index.md" in line :
                break
            
    with open(filepath,"w") as fo :
        for line in original_content :
            fo.write(line)
        recursive_writer(appendings,depth = 0)

def mkds_markdownfile_content(item_name : str,item_type : str ) -> str:
    content = []
    content.append("::: "+item_name)

    if item_type == "functions" :
        content.append(_FUNCTION_OPTIONS)

    if item_type == "classes" :
        content.append(_CLASS_OPTIONS)

    return ''.join(content)

def mkds_make_docfiles(path : str, top_module_name : str, docs_dir : str = "docs") -> None:
        
    def _create_layer(layer, reference):
        if layer in reference.keys():
            return
        reference[layer] = {}
        
    def _create_layers(layers):
        nonlocal nav_dic
        reference = nav_dic
        for layer in layers :
            _create_layer(layer, reference)
            reference = reference[layer]
            
    def _select_layer(layers):
        nonlocal nav_dic
        reference = nav_dic
        for layer in layers :
            reference = reference[layer]
        return reference

    docpath = unix_join(path,docs_dir)
    os.makedirs(docpath, exist_ok = True)
    LOGGER.info("Root package path is " + os.path.join(path,top_module_name))
    matched_py_files = find_files(os.path.join(path,top_module_name), r".*\.py$", relative = True)    
    LOGGER.info("Matched package files are :\n\t - " + matched_py_files.__str__()
        .replace("'","")
        .replace(" ","")
        .lstrip("[")
        .rstrip("]")
        .replace(",","\n\t - ")
        )
    nav_dic = {}
    
    for filepath in matched_py_files :

        file_name = os.path.splitext(os.path.basename(filepath))[0]
        if file_name in ["auto-doc","__init__"]:
            continue

        parser = mkds_pyfile_parser(os.path.join(path,top_module_name,filepath))
        parser.visit()
        if parser.is_empty():
            continue
        
        directories = os.path.dirname(filepath)
        
        if directories == '':
            directories = []
        else :
            directories = directories.split(os.sep)
        
        directories += [file_name]
        
        file_root_path = unix_join(docpath,*directories)
        os.makedirs(file_root_path, exist_ok = True)

        _create_layers(directories)

        nav_sublayer = _select_layer(directories)

        for func_type in ["classes","functions"]:
            for func_item in parser.content[func_type] :
                
                func_name = func_item.split(".")[1]
                nav_sublayer[func_name] = unix_join(*directories,func_name+'.md')
                
                function_docfile_name = unix_join(docs_dir,*directories,func_name+'.md')
                
                if os.path.isfile(function_docfile_name):
                    LOGGER.warning(f"doc file {function_docfile_name} has been overwritten")
                
                module_location = ".".join([top_module_name] + directories + [func_name])
     
                with open(function_docfile_name, "w") as mof :
                    mof.write(mkds_markdownfile_content(module_location,func_type))

    mkds_mod_mkdocs_yml_archi(path,nav_dic)

def console_mkds_make_docfiles():
    import sys
    LOGGER.info("RUNNING AUTO-DOC.py")
    try :
        top_module_name = str(sys.argv[1])
    except IndexError:
        raise ValueError("auto-doc.py must be called with the name of the packaged sources folder as argument.\nexample : 'python auto-doc.py Inflow'")
    try :
        temp = str(sys.argv[2])
        local_path = top_module_name
        top_module_name = temp
    except IndexError:
        local_path = os.getcwd()
        LOGGER.warning("No second argument was supplied. The localpath was determined relatively to the console current directory. This may not yield the desired effect")
    LOGGER.info("Local path is " + local_path)
    
    mkds_make_docfiles(local_path,top_module_name)
    
if __name__ == "__main__" :
    console_mkds_make_docfiles()
