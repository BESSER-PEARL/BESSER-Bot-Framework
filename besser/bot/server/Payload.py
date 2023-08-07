import json


class Payload:

    # Actions
    USER_MESSAGE = 'user_message'
    RESET = 'reset'
    BOT_REPLY_STR = 'bot_reply_str'
    BOT_REPLY_DF = 'bot_reply_dataframe'

    @staticmethod
    def decode(payload_str):
        payload_dict = json.loads(payload_str)
        return Payload(payload_dict['action'], payload_dict['message'])

    def __init__(self, action: str, message: str = None):
        self.action: str = action
        self.message: str = message


class PayloadEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Payload):
            # Convert the Payload object to a dictionary
            payload_dict = {
                'action': obj.action,
                'message': obj.message,
            }
            return payload_dict
        return super().default(obj)

# TODO Decoder???