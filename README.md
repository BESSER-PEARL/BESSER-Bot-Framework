<div align="center">
  <img src="./docs/source/_static/baf_logo_readme.svg" alt="BESSER Agentic Framework" width="500"/>
</div>

[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue?logo=python&logoColor=gold)](https://pypi.org/project/besser-agentic-framework/)
[![PyPI version](https://img.shields.io/pypi/v/besser-agentic-framework?logo=pypi&logoColor=white)](https://pypi.org/project/besser-agentic-framework/)
[![PyPI - Downloads](https://static.pepy.tech/badge/besser-agentic-framework)](https://pypi.org/project/besser-agentic-framework/)
[![Documentation Status](https://readthedocs.org/projects/besser-agentic-framework/badge/?version=latest)](https://besser-agentic-framework.readthedocs.io/latest/?badge=latest)
[![PyPI - License](https://img.shields.io/pypi/l/besser-agentic-framework)](https://opensource.org/license/MIT)
[![LinkedIn](https://img.shields.io/badge/-LinkedIn-blue?logo=Linkedin&logoColor=white&link=https://www.linkedin.com/in/pireseduardo/)](https://www.linkedin.com/company/besser-agentic-framework)
[![GitHub Repo stars](https://img.shields.io/github/stars/besser-pearl/besser-agentic-framework?style=social)](https://star-history.com/#besser-pearl/besser-agentic-framework)
[![SWH](https://archive.softwareheritage.org/badge/origin/https://github.com/BESSER-PEARL/BESSER-Agentic-Framework/)](https://archive.softwareheritage.org/browse/origin/?origin_url=https://github.com/BESSER-PEARL/BESSER-Agentic-Framework)

> ⭐ **Part of [BESSER](https://github.com/BESSER-PEARL/BESSER)**, the open-source low-code platform that turns models into working apps. If this project is useful to you, please [star the main repo](https://github.com/BESSER-PEARL/BESSER) too.

The BESSER Agentic Framework (BAF) is part of the [BESSER](https://modeling-languages.com/a-smart-low-code-platform-for-smart-software-in-luxembourg-goodbye-barcelona/) (Building Better Smart Software Faster) project. It aims
to make the design and implementation of agents, bots and chatbots easier and accessible for everyone.

**Check out the official [documentation](https://besser-agentic-framework.readthedocs.io/).**

## Quick start

### Requirements

- Python >=3.10
- Recommended: Create a virtual environment
  (e.g. [venv](https://docs.python.org/3/library/venv.html),
  [conda](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html))
- Install the [package](https://pypi.org/project/besser-agentic-framework/):

```bash
pip install besser-agentic-framework
```

This command will install the base package with the core dependencies, but will omit some optional dependencies.

You can add the following tags to the installation:

- ``extras``: It will install the necessary dependencies for some additional agent functionalities (e.g., RAG, Speech-to-Text, plotly, opencv).
- ``llms``: Necessary dependencies to run LLMs (openai, replicate, transformers)
- ``torch``: To install PyTorch, necessary for the Simple Intent Classifier (PyTorch implementation) and HuggingFace models
- ``tensorflow``: Necessary for the Simple Intent Classifier (Tensorflow implementation) and some HuggingFace models. Since tensorflow is a very heavy package, this allows to install it only if necessary
- ``docs``: Dependencies to compile the project documentation (the one you are reading now)
- ``all``: **It installs all the dependencies at once**

This is how you would install the package with additional dependencies:

```bash
  pip install besser-agentic-framework[extras,llms,tensorflow]
```

If you cloned this repository, you can install the dependencies in 2 ways:

```bash
pip install -e .[extras]
```

or by referencing to the requirements files:

```bash
pip install -r requirements/requirements-extras.txt
```

Note that if you want to set your agent's language to **Luxembourgish**, you will need to manually install the [spellux](https://github.com/questoph/spellux) library. 

### Example agents

- [greetings_agent](https://github.com/BESSER-PEARL/BESSER-Agentic-Framework/blob/main/baf/test/examples/greetings_agent.py): Very simple agent for the first contact with the framework
- [weather_agent](https://github.com/BESSER-PEARL/BESSER-Agentic-Framework/blob/main/baf/test/examples/weather_agent.py): Introducing [entities](https://besser-agentic-framework.readthedocs.io/latest/wiki/core/entities.html)
- [llm_agent](https://github.com/BESSER-PEARL/BESSER-Agentic-Framework/blob/main/baf/test/examples/llm_agent.py): Introducing [Large Language Models (LLMs)](https://besser-agentic-framework.readthedocs.io/latest/wiki/nlp/llm.html)
- [rag_agent](https://github.com/BESSER-PEARL/BESSER-Agentic-Framework/blob/main/baf/test/examples/rag_agent.py): Introducing [Retrieval Augmented Generation (RAG)](https://besser-agentic-framework.readthedocs.io/latest/wiki/nlp/rag.html)
- [telegram_agent](https://github.com/BESSER-PEARL/BESSER-Agentic-Framework/blob/main/baf/test/examples/telegram_agent.py): Introducing the [TelegramPlatform](https://besser-agentic-framework.readthedocs.io/latest/wiki/platforms/telegram_platform.html)
- [github_agent](https://github.com/BESSER-PEARL/BESSER-Agentic-Framework/blob/main/baf/test/examples/github_agent.py): Introducing [GitHubPlatform](https://besser-agentic-framework.readthedocs.io/latest/wiki/platforms/github_platform.html)
- [gitlab_agent](https://github.com/BESSER-PEARL/BESSER-Agentic-Framework/blob/main/baf/test/examples/gitlab_agent.py): Introducing the [GitLabPlatform](https://besser-agentic-framework.readthedocs.io/latest/wiki/platforms/gitlab_platform.html)
- [a2a_multiagent](https://github.com/BESSER-PEARL/BESSER-Agentic-Framework/blob/main/baf/test/examples/a2a_multiagent.py): Introducing the [A2APlatform](https://besser-agentic-framework.readthedocs.io/latest/wiki/platforms/a2a_platform.html)

For more example agents, check out the [BAF-agent-examples](https://github.com/BESSER-PEARL/BAF-agent-examples) repository!
