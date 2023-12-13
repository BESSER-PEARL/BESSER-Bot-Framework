# BESSER Bot Framework

The BESSER Bot Framework (BBF) is part of the [BESSER](https://modeling-languages.com/a-smart-low-code-platform-for-smart-software-in-luxembourg-goodbye-barcelona/) (Building Better Smart Software Faster) project. It aims to make
the design and implementation of chatbots easier and accessible for everyone.

**Check out the official [documentation](https://besserbot-framework.readthedocs.io/en/latest/).**

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
- [weather_bot](https://github.com/BESSER-PEARL/BESSER-Bot-Framework/blob/main/besser/bot/test/examples/weather_bot.py): Introducing entities
- [telegram_bot](https://github.com/BESSER-PEARL/BESSER-Bot-Framework/blob/main/besser/bot/test/examples/telegram_bot.py): Introducing the [TelegramPlatform](https://besserbot-framework.readthedocs.io/en/latest/wiki/platforms/telegram_platform.html)

For more example bots, check out the [BBF-bot-examples](https://github.com/BESSER-PEARL/BBF-bot-examples) repository!
