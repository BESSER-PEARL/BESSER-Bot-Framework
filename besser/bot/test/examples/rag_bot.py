# You may need to add your working directory to the Python path. To do so, uncomment the following lines of code
# import sys
# sys.path.append("/Path/to/directory/bot-framework") # Replace with your directory path

import logging

from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

from besser.bot import nlp
from besser.bot.core.bot import Bot
from besser.bot.core.session import Session
from besser.bot.nlp.llm.llm_huggingface_api import LLMHuggingFaceAPI
from besser.bot.nlp.llm.llm_openai_api import LLMOpenAI
from besser.bot.nlp.llm.llm_replicate_api import LLMReplicate
from besser.bot.nlp.rag.rag import RAGMessage, RAG

logging.basicConfig(level=logging.INFO, format='{levelname} - {asctime}: {message}', style='{')

# Create the bot
bot = Bot('rag_bot')
# Load bot properties stored in a dedicated file
bot.load_properties('config.ini')
# Define the platform your chatbot will use
websocket_platform = bot.use_websocket_platform(use_ui=True)

# Create Vector Store (RAG's DB)
vector_store: Chroma = Chroma(
    embedding_function=OpenAIEmbeddings(openai_api_key=bot.get_property(nlp.OPENAI_API_KEY)),
    persist_directory='vector_store'
)
# Create text splitter (RAG creates a vector for each chunk)
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
# Create the LLM (for the answer generation)
gpt = LLMOpenAI(
    bot=bot,
    name='gpt-4o-mini',
    parameters={},
    num_previous_messages=10
)

# Other example LLM

# gemma = LLMHuggingFace(bot=bot, name='google/gemma-2b-it', parameters={'max_new_tokens': 1}, num_previous_messages=10)
# llama = LLMHuggingFaceAPI(bot=bot, name='meta-llama/Meta-Llama-3.1-8B-Instruct', parameters={}, num_previous_messages=10)
# mixtral = LLMReplicate(bot=bot, name='mistralai/mixtral-8x7b-instruct-v0.1', parameters={}, num_previous_messages=10)

# Create the RAG
rag = RAG(
    bot=bot,
    vector_store=vector_store,
    splitter=splitter,
    llm_name='gpt-4o-mini',
    k=4,
    num_previous_messages=0
)
# Uncomment to fill the DB
# rag.load_pdfs('./pdfs')

# STATES

initial_state = bot.new_state('initial_state', initial=True)
rag_state = bot.new_state('rag_state')


# STATES BODIES' DEFINITION + TRANSITIONS

def initial_body(session: Session):
    session.reply('Hi!')


initial_state.set_body(initial_body)
initial_state.when_no_intent_matched_go_to(rag_state)


def rag_body(session: Session):
    rag_message: RAGMessage = session.run_rag()
    websocket_platform.reply_rag(session, rag_message)


rag_state.set_body(rag_body)
rag_state.go_to(initial_state)


# RUN APPLICATION

if __name__ == '__main__':
    bot.run()
