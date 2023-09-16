# You may need to add your working directory to the Python path. To do so, uncomment the following lines of code
# import sys
# sys.path.append("/Path/to/directory/bot-framework") # Replace with your directory path

import logging
import random

from besser.bot.core.bot import Bot
from besser.bot.core.session import Session
from besser.bot.nlp.intent_classifier.intent_classifier_prediction import IntentClassifierPrediction

# Configure the logging module
logging.basicConfig(level=logging.INFO, format='{levelname} - {asctime}: {message}', style='{')

bot = Bot('weather_bot')
# Load bot properties stored in a dedicated file
bot.load_properties('config.ini')
# Define the platform your chatbot will use
websocket_platform = bot.use_websocket_platform(use_ui=True)

# STATES

s0 = bot.new_state('s0', initial=True)
weather_state = bot.new_state('weather_state')

# ENTITIES

city_entity = bot.new_entity('city_entity', entries={
    'Barcelona': ['BCN', 'barna'],
    'Madrid': [],
    'Luxembourg': ['LUX']
})

# INTENTS

weather_intent = bot.new_intent('weather_intent', [
    'what is the weather in CITY?',
    'weather in CITY',
])
weather_intent.parameter('city1', 'CITY', city_entity)

# STATES BODIES' DEFINITION + TRANSITIONS


def s0_body(session: Session):
    session.reply('Waiting...')


s0.set_body(s0_body)
s0.when_intent_matched_go_to(weather_intent, weather_state)


def weather_body(session: Session):
    predicted_intent: IntentClassifierPrediction = session.predicted_intent
    city = predicted_intent.get_parameter('city1')
    temperature = round(random.uniform(0, 30), 2)
    if city.value is None:
        session.reply("Sorry, I didn't get the city")
    else:
        session.reply(f"The weather in {city.value} is {temperature}°C")
        if temperature < 15:
            session.reply('🥶')
        else:
            session.reply('🥵')


weather_state.set_body(weather_body)
weather_state.go_to(s0)

# RUN APPLICATION

if __name__ == '__main__':
    bot.run()
