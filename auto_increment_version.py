import sys
import os
import re
import logging

LOGGER = logging.getLogger()
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(" %(levelname)-8s : %(message)s")
handler.setFormatter(formatter)
LOGGER.setLevel(logging.DEBUG)
LOGGER.addHandler(handler)


def auto_increment(top_module_name):
    local_path = os.path.dirname(os.path.abspath(__file__))
    path_to_init = os.path.join(local_path, top_module_name, "__init__.py")

    with open(path_to_init, "r") as f:
        init_contents = f.read()
    match = re.search(r"""__version__ *= *(?:"|')(\d+\.\d+)\.(\d+)(?:"|')""", init_contents)
    if match is None:
        return
    major_minor, patch = match.groups()
    new_patch = int(patch) + 1
    new_contents = re.sub(
        """(__version__ *= *(?:"|')(?:\d+\.\d+)\.)(\d+)("|')""", rf"\g<1>{new_patch}\g<3>", init_contents
    )
    LOGGER.debug("Original content : ")
    LOGGER.debug(init_contents)
    LOGGER.debug("Changed content : ")
    LOGGER.debug(new_contents)
    with open(path_to_init, "w") as f:
        f.write(new_contents)


if __name__ == "__main__":
    try:
        top_module_name = str(sys.argv[1])
    except IndexError:
        raise ValueError(
            "auto_increment_version.py must be called with the name of the packaged sources folder as"
            " argument.\nexample : 'python auto_increment_version.py Inflow'"
        )
    auto_increment(top_module_name)
