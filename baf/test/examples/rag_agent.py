# You may need to add your working directory to the Python path. To do so, uncomment the following lines of code
# import sys
# sys.path.append("/Path/to/directory/agentic-framework") # Replace with your directory path

import logging
import uuid

from chromadb import EphemeralClient
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

from baf import nlp
from baf.core.agent import Agent
from baf.core.session import Session
from baf.exceptions.logger import logger
from baf.nlp.llm.llm_huggingface_api import LLMHuggingFaceAPI
from baf.nlp.llm.llm_openai_api import LLMOpenAI
from baf.nlp.llm.llm_replicate_api import LLMReplicate
from baf.nlp.rag.rag import RAGMessage, RAG
from baf.library.transition.events.base_events import ReceiveTextEvent, ReceiveMessageEvent, ReceiveFileEvent

# Configure the logging module (optional)
logger.setLevel(logging.INFO)

# Create the agent
agent = Agent('rag_agent')
# Load agent properties stored in a dedicated file
agent.load_properties('config.yaml')
# Define the platform your agent will use
websocket_platform = agent.use_websocket_platform(use_ui=True)

#To keep RAG as session scoped or not
SESSION_SCOPED=True


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


# Create Vector Store (RAG's DB)
def create_vector_store(agent):
    '''
    This vector store creator a callable as Session based RAG needs a different store for different sessions. 
    '''
    return Chroma(
        embedding_function=OpenAIEmbeddings(openai_api_key=agent.get_property(nlp.OPENAI_API_KEY)),
        collection_name=f"rag_{uuid.uuid4().hex[:8]}",
        client=EphemeralClient(),
    )


# To directly provide text to RAG instead of uploading at runtime:
# 1. Uncomment the relevant line in the following block
# 2. Comment the line having ReceiveFileEvent() state and proceed.
# rag.load_documents('C:/Users/chidambaram/Downloads/example', formats=['docx'])   # read all the files of the given format in the directory
# rag.add_text('raw text to index and base your RAG on.') # add a text string directly


# STATES

initial_state = agent.new_state('initial_state', initial=True)
ask_question_state = agent.new_state('ask_question_state')
rag_state = agent.new_state('rag_state')


# STATES BODIES' DEFINITION + TRANSITIONS

def initial_body(session: Session):
    session.reply('Hi!, upload your text, if done, ask your question directly')
    session.set('session_scoped',SESSION_SCOPED)

initial_state.set_body(initial_body)
# TODO : fix no_intent_matched
initial_state.when_event(ReceiveFileEvent()).go_to(ask_question_state)
initial_state.when_no_intent_matched().go_to(rag_state)


def ask_question_body(session: Session):
    '''
    Create the RAG and index the uploaded file
    '''
    agent = session._agent
    llm_name = 'gpt-4o-mini'
    session_scoped = session.get('session_scoped')
    if session_scoped:
        if session.session_rag is None:
            session.session_rag = RAG(
                agent, vector_store=create_vector_store(agent), splitter=splitter,
                llm_name=llm_name, k=4, num_previous_messages=0, 
                session_scoped=session_scoped
            )
        else:
            session.session_rag.clear()
        session.session_rag.add_file(session.event.file)

    else:
        rag = RAG(
            agent, vector_store=create_vector_store(agent), splitter=splitter,
            llm_name=llm_name, k=4, num_previous_messages=0, 
            session_scoped=session_scoped
        )
        rag.add_file(session.event.file)
    
    session.reply('Ask your question!')

ask_question_state.set_body(ask_question_body)
ask_question_state.when_no_intent_matched().go_to(rag_state)


def rag_body(session: Session):
    session_scoped = session.get('session_scoped')
    if session_scoped:
        rag_message: RAGMessage = session.run_session_rag(session.event.message)
    else:
        rag_message: RAGMessage = session.run_rag(session.event.message)
    websocket_platform.reply_rag(session, rag_message)

rag_state.set_body(rag_body)
rag_state.go_to(initial_state)


# RUN APPLICATION

if __name__ == '__main__':
    agent.run()
