# BESSER Bot Framework

The BESSER Bot Framework (BBF) is part of the BESSER (BEtter Smart Software fastER) project. It aims to make the design and implementation of chatbots easier and accessible for everyone.

**Check out the official [documentation](https://besserbot-framework.readthedocs.io/en/latest/).**

## Quick start

### Requirements

- Python 3.11
- Recommended: Create a virtual environment
  (e.g. [venv](https://docs.python.org/3/library/venv.html),
  [conda](https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html))
- Install the [requirements](requirements.txt):

```bash
pip install -r requirements.txt
```

### Example bots

- [greetings_bot](besser/bot/test/examples/greetings_bot.py): Very simple bot for the first contact with the framework
- [weather_bot](besser/bot/test/examples/weather_bot.py): Introducing entities
- [telegram_bot](besser/bot/test/examples/telegram_bot.py): Introducing the [TelegramPlatform](besser/bot/test/examples/telegram_bot.py)
