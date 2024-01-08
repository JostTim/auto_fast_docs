import os
import re
import natsort


# def unix_join(*args, **kwargs):
#     return os.path.join(*args, **kwargs).replace(os.sep, '/')

unix_join = os.path.join


def find_python_files(search_path):
    matched_py_files = find_files(search_path, r".*\.py$", relative=True)
    return matched_py_files


def find_files(input_path, re_pattern=None, relative=False, levels=-1, get="files", parts="all", sort=True):
    """
    Get full path of files from all folders under the ``input_path`` (including itself).
    Can return specific files with optionnal conditions
    Args:
        input_path (str): A valid path to a folder.
            This folder is used as the root to return files found
            (possible condition selection by giving to re_callback a function taking a regexp pattern and a string as
            argument, an returning a boolean).
    Returns:
        list: List of the file fullpaths found under ``input_path`` folder and subfolders.
    """

    # if levels = -1, we get everything whatever the depth, at least up to 32767 subfolders, should be fine.. ;)
    if levels == -1:
        levels = 32767
    current_level = 0
    output_list = []

    def _recursive_search(_input_path):
        nonlocal current_level
        for subdir in os.listdir(_input_path):
            fullpath = unix_join(_input_path, subdir)
            if os.path.isfile(fullpath):
                if (get == "all" or get == "files") and (re_pattern is None or qregexp(re_pattern, fullpath)):
                    output_list.append(os.path.normpath(fullpath))

            else:
                if (get == "all" or get == "dirs" or get == "folders") and (
                    re_pattern is None or qregexp(re_pattern, fullpath)
                ):
                    output_list.append(os.path.normpath(fullpath))
                if current_level < levels:
                    current_level += 1
                    _recursive_search(fullpath)
        current_level -= 1

    if os.path.isfile(input_path):
        raise ValueError(
            f"Can only list files in a directory. A file was given : {input_path}")

    _recursive_search(input_path)

    if relative:
        output_list = [os.path.relpath(file, start=input_path)
                       for file in output_list]
    if parts == "name":
        output_list = [os.path.basename(file) for file in output_list]
    if sort:
        try:
            output_list = natsort.natsorted(output_list)
        except Exception:
            pass
    return output_list


def qregexp(regex, input_line, groupidx=None, matchid=None, case=False):
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

    if case:
        matches = re.finditer(regex, input_line, re.MULTILINE | re.IGNORECASE)
    else:
        matches = re.finditer(regex, input_line, re.MULTILINE)

    if matchid is not None:
        matchid = matchid + 1

    for matchnum, match in enumerate(matches, start=1):

        if matchid is not None:
            if matchnum == matchid:
                if groupidx is not None:
                    for groupx, groupcontent in enumerate(match.groups()):
                        if groupx == groupidx:
                            return groupcontent
                    return False

                else:
                    MATCH = match.group()
                    return MATCH

        else:
            if groupidx is not None:
                for groupx, groupcontent in enumerate(match.groups()):
                    if groupx == groupidx:
                        return groupcontent
                return False
            else:
                MATCH = match.group()
                return MATCH
    return False
