# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import os
import sys

sys.path.insert(0, os.path.abspath('../../'))

project = 'bot-framework'
copyright = '2023, Marcos Gomez'
author = 'Marcos Gomez'
release = '0.1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.duration',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary',
    'm2r2',
]
autosummary_generate = True

templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# html_theme = 'alabaster'
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']


# API GENERATION

# TODO: SKIP TEST PACKAGE
# TODO: GROUP BY PACKAGES
# CORE
# EXCEPTIONS
# LIBRARY
# NLP
# PLATFORMS
def generate_rst_files(root_dir, output_dir):
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
                full_module_name = rel_path + '.' + module_name if rel_path != '.' else module_name
                rst_filename = os.path.join(output_dir, module_name + '.rst')
                with open(rst_filename, 'w') as rst_file:
                    # rst_file.write(full_module_name)
                    content = \
f"""{module_name}
{'=' * len(module_name)}

.. automodule:: {full_module_name}
   :members:
   :undoc-members:
   :show-inheritance:
"""
                    rst_file.write(content)
                    api_rst += \
f"""   api/{module_name}
"""

    with open('api.rst', 'w') as file:
        file.write(api_rst)


starting_directory = '../../besser'  # Change this to your desired starting directory
output_directory = './api'
generate_rst_files(starting_directory, output_directory)
