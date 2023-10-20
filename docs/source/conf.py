# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import datetime
import importlib
import inspect
import os
import sys
from configparser import ConfigParser

# Add the project root directory to the path
sys.path.insert(0, os.path.abspath('../../'))

config: ConfigParser = ConfigParser()
config.read('../../setup.cfg')

project = config.get('metadata', 'description')
author = config.get('metadata', 'author')
release = config.get('metadata', 'version')
year = datetime.date.today().year
copyright = f'{year}, {author}'


# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.duration',  # measure durations of Sphinx processing
    'sphinx.ext.autodoc',  # include documentation from docstrings
    'sphinx.ext.autosummary',  # generate autodoc summaries
    'sphinx.ext.linkcode',  # add external links to source code
    'sphinx_copybutton',  # add a little “copy” button to the right of the code blocks
    'sphinx_paramlinks',  # allows :param: directives within Python documentation to be linkable
    'sphinx.ext.intersphinx',  # link to other projects’ documentation
    'sphinx.ext.napoleon',  # support for Google (and also NumPy) style docstrings
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "pandas": ("https://pandas.pydata.org/docs", None),
    "python-telegram-bot": ("https://docs.python-telegram-bot.org/en/v20.5", None),
}

autosummary_generate = True

templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_title = f"{project} {release}"
html_logo = "img/logo.png"
#html_theme_options = {
#    "light_logo": "logo-light-mode.png",
#    "dark_logo": "logo-dark-mode.png",
#}
html_theme = 'furo'
html_static_path = ['_static']

# Don't show type hints in the signature - that just makes it hardly readable
# and we document the types anyway
autodoc_typehints = "none"

# The master toctree document.
master_doc = "index"

# Paramlink style
paramlinks_hyperlink_param = "name"


# API GENERATION
def generate_api_rst_files(preffix, dir, output_dir):
    api_excluded_files = [
        'streamlit_ui.py'
    ]
    os.makedirs(output_dir, exist_ok=True)
    root_dir = preffix + dir
    package_name = root_dir.split('/')[-1]
    package_rst = \
f"""
{package_name}
{'=' * len(package_name)}

.. toctree::

"""
    for dirpath, dirnames, filenames in os.walk(root_dir):
        for filename in filenames:
            if (filename.endswith('.py')) and (not filename.startswith('_')):
                module_name = os.path.splitext(filename)[0]
                package_rst += \
f"""   {package_name}/{module_name}
"""
                if filename not in api_excluded_files:
                    rel_path = os.path.relpath(dirpath, root_dir).replace(os.path.sep, '.')
                    full_module_name = dir.replace('/', '.').replace(os.path.sep, '.') + '.' + rel_path + '.' + module_name \
                        if rel_path != '.' else \
                        dir.replace('/', '.').replace(os.path.sep, '.') + rel_path + module_name
                    rst_filename = os.path.join(output_dir, module_name + '.rst')
                    with open(rst_filename, 'w') as rst_file:
                        content = \
f"""{module_name}
{'=' * len(module_name)}

.. automodule:: {full_module_name}
   :members:
   :private-members:
   :undoc-members:
   :show-inheritance:
"""
                        rst_file.write(content)

    with open(f'api/{package_name}.rst', 'w') as file:
        file.write(package_rst)


generate_api_rst_files('../../', 'besser/bot/core', './api/core')
generate_api_rst_files('../../', 'besser/bot/exceptions', './api/exceptions')
generate_api_rst_files('../../', 'besser/bot/library', './api/library')
generate_api_rst_files('../../', 'besser/bot/nlp', './api/nlp')
generate_api_rst_files('../../', 'besser/bot/platforms', './api/platforms')


def linkcode_resolve(domain, info):
    """Generate links to module components."""
    if domain != 'py':
        return None
    if not info['module']:
        return None
    mod = importlib.import_module(info["module"])
    if "." in info["fullname"]:
        objname, attrname = info["fullname"].split(".")
        obj = getattr(mod, objname)
        try:
            # object is a method of a class
            obj = getattr(obj, attrname)
        except AttributeError:
            # object is an attribute of a class
            return None
    else:
        obj = getattr(mod, info["fullname"])

    try:
        lines = inspect.getsourcelines(obj)
    except TypeError:
        return None
    start, end = lines[1], lines[1] + len(lines[0]) - 1
    filename = info['module'].replace('.', '/')
    return f"https://github.com/BESSER-PEARL/bot-framework/blob/main/{filename}.py#L{start}-L{end}"
