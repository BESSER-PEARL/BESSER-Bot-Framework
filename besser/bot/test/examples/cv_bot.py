from besser.bot.cv.object_detection.yolo_object_detector import YOLOObjectDetector


import logging

from besser.bot.core.bot import Bot
from besser.bot.core.session import Session

# Configure the logging module
logging.basicConfig(level=logging.INFO, format='{levelname} - {asctime}: {message}', style='{')

# Create the bot
bot = Bot('greetings_bot')
# Load bot properties stored in a dedicated file
bot.load_properties('config.ini')
# Define the platform your chatbot will use
websocket_platform = bot.use_websocket_platform(use_ui=True, video_input=True)

yolo_model = YOLOObjectDetector(bot=bot, name='yolov8n', model_path='YOLO Weights/yolov8n.pt')
# bot.cv_engine.object_detector = yolo_model  # Not necessary to set, implicitly done

person = bot.new_image_object('person')
dog = bot.new_image_object('dog')
bottle = bot.new_image_object('bottle')


initial_state = bot.new_state('initial_state', initial=True)
person_state = bot.new_state('person_state')


initial_state.when_image_object_detected_go_to(person, 0.5, person_state)


def hello_body(session: Session):
    session.reply('Hi!')


def person_body(session: Session):
    session.reply('I can see you!')


person_state.set_body(person_body)
person_state.when_no_intent_matched_go_to(initial_state)

# RUN APPLICATION

if __name__ == '__main__':
    bot.run()
