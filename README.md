<div align="center">
  <img src="./docs/source/_static/bbf_logo_readme.svg" alt="BESSER Bot Framework" width="500"/>
</div>

[![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11-blue?logo=python&logoColor=gold)](https://pypi.org/project/besser-bot-framework/)
[![PyPI version](https://img.shields.io/pypi/v/besser-bot-framework?logo=pypi&logoColor=white)](https://pypi.org/project/besser-bot-framework/)
[![PyPI - Downloads](https://static.pepy.tech/badge/besser-bot-framework)](https://pypi.org/project/besser-bot-framework/)
[![Documentation Status](https://readthedocs.org/projects/besser-bot-framework/badge/?version=latest)](https://besser-bot-framework.readthedocs.io/latest/?badge=latest)
[![PyPI - License](https://img.shields.io/pypi/l/besser-bot-framework)](https://opensource.org/license/MIT)
[![LinkedIn](https://img.shields.io/badge/-LinkedIn-blue?logo=Linkedin&logoColor=white&link=https://www.linkedin.com/in/pireseduardo/)](https://www.linkedin.com/company/besser-bot-framework)
[![GitHub Repo stars](https://img.shields.io/github/stars/besser-pearl/besser-bot-framework?style=social)](https://star-history.com/#besser-pearl/besser-bot-framework)

The BESSER Bot Framework (BBF) is part of the [BESSER](https://modeling-languages.com/a-smart-low-code-platform-for-smart-software-in-luxembourg-goodbye-barcelona/) (Building Better Smart Software Faster) project. It aims to make
the design and implementation of chatbots easier and accessible for everyone.

**Check out the official [documentation](https://besser-bot-framework.readthedocs.io/).**

## Quick start

### Requirements

- Python 3.11
- Recommended: Create a virtual environment
  (e.g. [venv](https://docs.python.org/3/library/venv.html),
  [conda](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html))
- Install the [package](https://pypi.org/project/besser-bot-framework/):

```bash
pip install besser-bot-framework
```
Note that if you want to set your bot's language to Luxembourgish and are using the package installed with pip, you will need to manually install the [spellux](https://github.com/questoph/spellux) library. 
If you clone this project, installing the requirements from the requirements.txt file is enough.


### Example bots

- [greetings_bot](https://github.com/BESSER-PEARL/BESSER-Bot-Framework/blob/main/besser/bot/test/examples/greetings_bot.py): Very simple bot for the first contact with the framework
- [weather_bot](https://github.com/BESSER-PEARL/BESSER-Bot-Framework/blob/main/besser/bot/test/examples/weather_bot.py): Introducing [entities](https://besser-bot-framework.readthedocs.io/latest/wiki/core/entities.html)
- [llm_bot](https://github.com/BESSER-PEARL/BESSER-Bot-Framework/blob/main/besser/bot/test/examples/llm_bot.py): Introducing [Large Language Models (LLMs)](https://besser-bot-framework.readthedocs.io/latest/wiki/nlp/llm.html)
- [rag_bot](https://github.com/BESSER-PEARL/BESSER-Bot-Framework/blob/main/besser/bot/test/examples/rag_bot.py): Introducing [Retrieval Augmented Generation (RAG)](https://besser-bot-framework.readthedocs.io/latest/wiki/nlp/rag.html)
- [telegram_bot](https://github.com/BESSER-PEARL/BESSER-Bot-Framework/blob/main/besser/bot/test/examples/telegram_bot.py): Introducing the [TelegramPlatform](https://besser-bot-framework.readthedocs.io/latest/wiki/platforms/telegram_platform.html)

For more example bots, check out the [BBF-bot-examples](https://github.com/BESSER-PEARL/BBF-bot-examples) repository!
