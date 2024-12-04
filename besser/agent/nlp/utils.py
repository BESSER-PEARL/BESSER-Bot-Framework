import json
import re


def value_in_sentence(value: str, sentence: str) -> bool:
    regex = re.compile(r'\b' + re.escape(value) + r'\b', re.IGNORECASE)
    return value.lower() == sentence.lower() or (regex.search(sentence) is not None)


def replace_value_in_sentence(sentence: str, frag: str, repl: str) -> str:
    if sentence.lower() == frag.lower():
        return repl
    if frag[0] == '-':
        # Necessary to replace negative numbers properly
        regex = re.compile(re.escape(frag) + r'\b', re.IGNORECASE)
    else:
        regex = re.compile(r'\b' + re.escape(frag) + r'\b', re.IGNORECASE)
    return regex.sub(repl=repl, string=sentence, count=1)


def replace_temp_value_in_sentence(sentence: str, frag: str, repl: str) -> str:
    regex = re.compile(frag, re.IGNORECASE)
    return regex.sub(repl=repl, string=sentence, count=1)


def find_first_temp(sentence: str) -> str:
    regex = re.compile(r'/temp[0-9]+/')
    return regex.search(sentence).group()


def find_json(text: str) -> dict:
    text = re.sub(r"([^']*)'([^']*[^'])", r'\1"\2', text)
    start = text.find('{')
    end = text.rfind('}') + 1
    json_string = text[start:end]
    return json.loads(json_string)


def merge_llm_consecutive_messages(messages: list[dict]) -> list[dict]:
    """Merges consecutive user and assistant messages. Necessary for HuggingFace LLMs, where the message pattern must be
    user/assistant/user/assistant...

    A message looks like the following:

    .. code-block::

        {'role': 'user', 'content': 'Hi'}  # For user messages
        {'role': 'assistant', 'content': 'Hi'}  # For assistant, i.e. LLM, messages

    Args:
        messages (list[dict): the messages to be merged by user type

    Returns:
        list[dict]: the merged messages
    """
    if not messages:
        return []

    merged_messages = []
    if messages[0]['role'] != 'user':
        merged_messages.append({'role': 'user', 'content': 'Hello'})
    current_message = messages[0]

    for next_message in messages[1:]:
        if next_message['role'] == current_message['role']:
            current_message['content'] += "\n" + next_message['content']
        else:
            merged_messages.append(current_message)
            current_message = next_message

    merged_messages.append(current_message)
    return merged_messages
