# You may need to add your working directory to the Python path. To do so, uncomment the following lines of code
# import sys
# sys.path.append("/Path/to/directory/agentic-framework") # Replace with your directory path

import logging

from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

from baf import nlp
from baf.core.agent import Agent
from baf.core.session import Session
from baf.exceptions.logger import logger
from baf.library.transition.events.base_events import ReceiveFileEvent
from baf.nlp.llm.llm_huggingface_api import LLMHuggingFaceAPI
from baf.nlp.llm.llm_openai_api import LLMOpenAI
from baf.nlp.llm.llm_replicate_api import LLMReplicate
from baf.nlp.rag.rag import RAGMessage, RAG

# Configure the logging module (optional)
logger.setLevel(logging.INFO)

# Create the agent
agent = Agent('rag_agent')
# Load agent properties stored in a dedicated file
agent.load_properties('config.yaml')
# Define the platform your agent will use
websocket_platform = agent.use_websocket_platform(use_ui=True)

# Create Vector Store (RAG's DB)
vector_store: Chroma = Chroma(
    embedding_function=OpenAIEmbeddings(openai_api_key=agent.get_property(nlp.OPENAI_API_KEY)),
    persist_directory='vector_store'
)
# Create text splitter (RAG creates a vector for each chunk)
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
# Create the LLM (for the answer generation)
gpt = LLMOpenAI(
    agent=agent,
    name='gpt-4o-mini',
    parameters={},
    num_previous_messages=10
)

# Other example LLM

# gemma = LLMHuggingFace(agent=agent, name='google/gemma-2b-it', parameters={'max_new_tokens': 1}, num_previous_messages=10)
# llama = LLMHuggingFaceAPI(agent=agent, name='meta-llama/Meta-Llama-3.1-8B-Instruct', parameters={}, num_previous_messages=10)
# mixtral = LLMReplicate(agent=agent, name='mistralai/mixtral-8x7b-instruct-v0.1', parameters={}, num_previous_messages=10)

# Create the RAG
rag = RAG(
    agent=agent,
    vector_store=vector_store,
    splitter=splitter,
    llm_name='gpt-4o-mini',
    k=4,
    num_previous_messages=0
)
# Uncomment the relevant line to directly provide text to RAG instead of uploading at runtime
# rag.load_documents('C:/Users/chidambaram/Downloads/example', formats=['docx'])   # read all the files of the given format in the directory
# rag.add_text('raw text to index and base your RAG on.') # add a text string directly

# If not uploading at runtime, comment the following function, L84, L87 and L88, and uncomment L85. 
def upload_file_body(session: Session):
    rag.add_file(session.event.file)


# STATES

initial_state = agent.new_state('initial_state', initial=True)
upload_file_state = agent.new_state('upload_file_state')
ask_question_state = agent.new_state('ask_question_state')


# STATES BODIES' DEFINITION + TRANSITIONS

def initial_body(session: Session):
    session.reply('Hi!, upload a file to use as RAG context. If already done, ask your question.')


initial_state.set_body(initial_body)
initial_state.when_event(ReceiveFileEvent()).go_to(upload_file_state)
# initial_state.when_no_intent_matched().go_to(ask_question_state)

upload_file_state.set_body(upload_file_body)
upload_file_state.when_no_intent_matched().go_to(ask_question_state)


def ask_question_body(session: Session):
    rag_message: RAGMessage = session.run_rag(session.event.message)
    websocket_platform.reply_rag(session, rag_message)


ask_question_state.set_body(ask_question_body)
ask_question_state.go_to(initial_state)


# RUN APPLICATION

if __name__ == '__main__':
    agent.run()
