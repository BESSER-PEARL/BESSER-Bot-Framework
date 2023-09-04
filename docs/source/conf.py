# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
import importlib
import inspect
# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import os
import sys

sys.path.insert(0, os.path.abspath('../../'))

project = 'bot-framework'
copyright = '2023, Luxembourg Institute of Science and Technology (LIST)'
author = 'Marcos Gomez'
release = '0.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.duration',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'sphinx.ext.linkcode',
    'sphinx_copybutton',
    'sphinx_paramlinks',
    'm2r2',
]


autosummary_generate = True

templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# html_title = "your custom sidebar title"
html_logo = "logo.png"
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

# TODO: SKIP TEST PACKAGE
# TODO: GROUP BY PACKAGES
# CORE
# EXCEPTIONS
# LIBRARY
# NLP
# PLATFORMS
def generate_api_rst_files(root_dir, output_dir):
    api_excluded_files = [
        'streamlit_ui.py'
    ]
    os.makedirs(output_dir, exist_ok=True)
    api_rst = \
f"""
API
====

.. toctree::

"""
    for dirpath, dirnames, filenames in os.walk(root_dir):
        rel_path = 'besser.' + os.path.relpath(dirpath, root_dir).replace(os.path.sep, '.')
        for filename in filenames:
            if (filename.endswith('.py')) and (not filename.startswith('_')):
                module_name = os.path.splitext(filename)[0]
                api_rst += \
f"""   api/{module_name}
"""
                if filename not in api_excluded_files:
                    full_module_name = rel_path + '.' + module_name if rel_path != '.' else module_name
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

    with open('api.rst', 'w') as file:
        file.write(api_rst)


api_starting_directory = '../../besser'  # Change this to your desired starting directory
api_output_directory = './api'
generate_api_rst_files(api_starting_directory, api_output_directory)




def linkcode_resolve(domain, info):
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