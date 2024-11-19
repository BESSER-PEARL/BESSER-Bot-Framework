# Streamlit session_state keys
ASSISTANT = 'assistant'
BUTTONS = 'buttons'
HISTORY = 'history'
IMG = 'img'
LAST_IMG = 'last_img'
QUEUE = 'queue'
SESSION_MONITORING = 'session_monitoring'
SUBMIT_FILE = 'submit_file'
SUBMIT_TEXT = 'submit_text'
SUBMIT_AUDIO = 'submit_audio'
USER = 'user'
VIDEO_INPUT = 'video_input'
WEBSOCKET = 'websocket'

# Time interval to check if a streamlit session is still active, in seconds
SESSION_MONITORING_INTERVAL = 1

# New bot messages are printed with a typing effect. This is the time between words being printed, in seconds
TYPING_TIME = 0.05

# To enable/disable video input (images from camera input sent to the bot)
# TODO: Temporary solution
VIDEO_INPUT_ENABLED = True
# Time interval to send images to the bot
VIDEO_INPUT_INTERVAL = 0.2
